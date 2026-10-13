import pathlib
from typing import Generator, Any
from abc import ABC, abstractmethod


class Tile(ABC):
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.splits = None
        self.paths = None

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"

    @property
    def pos(self):
        return (self.x, self.y)
    
    def collect_splits(self) -> Generator[tuple[int, int], Any, None]:
        if not self.splits:
            self.splits = set(self._collect_splits())
        
        yield from self.splits
    
    def count_paths(self):
        if not self.paths:
            self.paths = self._count_paths()
        return self.paths

    @abstractmethod
    def beams_generated(self) -> Generator[int, Any, None]: ...

    @abstractmethod
    def _collect_splits(self) -> Generator[tuple[int, int], Any, None]: ...

    @abstractmethod
    def _count_paths(self) -> int: ...


class BaseTile(Tile):
    def __init__(self, x: int, y: int, next: Tile) -> None:
        super().__init__(x, y)
        self.next = next

    def beams_generated(self):
        yield from self.next.beams_generated()

    def __repr__(self) -> str:
        return "." + super().__repr__()

    def _collect_splits(self):
        yield from self.next.collect_splits()
    
    def _count_paths(self) -> int:
        return self.next._count_paths()


class SplitterTile(Tile):
    def __init__(self, x: int, y: int, next_dx: Tile | None, next_sx: Tile | None) -> None:
        super().__init__(x, y)
        self.next_dx = next_dx
        self.next_sx = next_sx

    def beams_generated(self):
        if self.next_dx:
            yield from self.next_dx.beams_generated()
        if self.next_sx:
            yield from self.next_sx.beams_generated()

    def __repr__(self) -> str:
        return "^" + super().__repr__()

    def _collect_splits(self):
        yield (self.x, self.y)
        if self.next_dx:
            yield from self.next_dx.collect_splits()
        if self.next_sx:
            yield from self.next_sx.collect_splits()
    
    def _count_paths(self) -> int:
        return (self.next_sx.count_paths() if self.next_sx else 0) + (self.next_dx.count_paths() if self.next_dx else 0)


class BottomTile(Tile):
    def beams_generated(self):
        yield self.x

    def __repr__(self) -> str:
        return "_" + super().__repr__()

    def _collect_splits(self):
        yield (-1, -1)
    
    def _count_paths(self) -> int:
        return 1


def get_start(input_lines: list[str]):
    curr_nodes: dict[tuple[int, int], Tile] = {
        (x, len(input_lines) - 1): BottomTile(x, len(input_lines) - 1) for x in range(len(input_lines[-1]))
    }

    for y in range(len(input_lines) - 2, 0, -1):
        # We start from 1 because start is handled differently
        # Bottom line special case defined before
        for x in range(len(input_lines[y])):
            curr_c = input_lines[y][x]
            if curr_c == ".":
                curr_nodes[(x, y)] = BaseTile(x, y, curr_nodes[(x, y + 1)])
            else:
                node_dx = (
                    curr_nodes.setdefault((x + 1, y), BaseTile(x + 1, y, curr_nodes[(x + 1, y + 1)]))
                    if x < len(input_lines[y]) - 1
                    else None
                )
                node_sx = (
                    curr_nodes.setdefault((x - 1, y), BaseTile(x, y, curr_nodes[(x - 1, y + 1)])) if x > 0 else None
                )
                curr_nodes[(x, y)] = SplitterTile(x, y, node_dx, node_sx)

    start = input_lines[0].index("S")
    return BaseTile(start, 0, curr_nodes[(start, 1)])


def part1(input_lines: list[str]):
    start_tile = get_start(input_lines)
    splits = set(start_tile.collect_splits())
    splits.remove((-1, -1))
    print(len(splits))

def part2(input_lines: list[str]):
    start_tile = get_start(input_lines)
    result = start_tile.count_paths()
    print(result)


raw_lines = pathlib.Path("example.txt").read_text().strip().split("\n")
# raw_lines = pathlib.Path("input.txt").read_text().strip().split("\n")
part2(raw_lines)
