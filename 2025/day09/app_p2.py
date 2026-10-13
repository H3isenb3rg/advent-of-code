from __future__ import annotations
import time
import pathlib


class Board:
    tiles: dict[tuple[int, int], Tile]
    edges: dict[tuple[int, int], Tile]

    def __init__(self, input_lines: list[str]) -> None:
        tiles = list(self._parse_coordinates(input_lines))
        self.edges = {t.coordinates: t for t in self._parse_edges(tiles)}
        self.tiles = {t.coordinates: t for t in tiles}
        # check_if_tile_no_vertex(self.tiles, self.edges)  → Both inputs passed
        self.max_y = max(self.tiles.values(), key=lambda t: t.y).y + 1
        self.max_x = max(self.tiles.values(), key=lambda t: t.x).x + 2
        self.min_y = min(self.tiles.values(), key=lambda t: t.y).y
        self.min_x = min(self.tiles.values(), key=lambda t: t.x).x
        self._is_inside: dict[tuple[int, int], int] = dict()
        """
        Contains count of intersection for ray_cast starting from the given coordinates
        
        To know if inside → value % 2 != 0
        """
        self.areas = sorted(self.compute_areas_p2(list(self.tiles.values()), set()), key=lambda r: r[1], reverse=True)

        # INIT RAY CAST
        tiles = set(self.edges.values()) | set(self.tiles.values())
        self.ray_cast_struct: dict[int, list[int]] = dict()
        for t in tiles:
            x, y = t.coordinates
            if isinstance(t, VerticalEdge) or t.is_bottom_vertex:
                self.ray_cast_struct.setdefault(y, []).append(x)

        # RAY CAST
        # Starting from the point we want to check:
        # Go to the right until the end of the board and count how many edges we intersect
        # (Count only edges going in vertical direction not horizontal edges)
        # - If EVEN number of edges → the point was outside
        # - If ODD number of edges → the point was inside
        # EDGE CASE → on our cast we are aligned with an horizontal edge (We encounter the vertex(tile) then all the horizontal edges)
        #             - We count only the vertexes with an edge on the top
        #             - IDEA → Ignore horizontal edges, count only vertical edges considering only the bottom vertex [y_min, y_max)
        #                      - Since we are casting straight to the right this should adjust the count in these edge cases

        # **NB** → If we are executing this check it means that our point:
        #          - Is not a vertex
        #          - Is not an edge
        #          So it's either inside the polygon or outside (not on the border)
        #          This means that if we encounter an horizontal edge it will always be a vertex as first tile
        #          → So to ignore it we just go to the other end of the edge were the other vertex is

    def get_tile_and_next(self, i: int, tiles: list[Tile]):
        if i >= len(tiles):
            raise ValueError("Index out of bounds")
        if i == len(tiles) - 1:
            return tiles[i], tiles[0]
        return tiles[i], tiles[i + 1]

    def max_area(self, illegals: set[tuple[Tile, Tile]] = set()):
        for i, area_item in enumerate(self.areas):
            if self.check_legal_square(area_item[0]):
                return area_item
        return (((0, 0), (0, 0)), 0)

    def check_legal_square(self, rectangle: tuple[Tile, Tile]):
        v1 = Tile(rectangle[0].x, rectangle[1].y)
        v2 = Tile(rectangle[1].x, rectangle[0].y)
        sides = [
            (rectangle[0], v1),
            (v1, rectangle[1]),
            (rectangle[1], v2),
            (v2, rectangle[0]),
        ]

        for side in sides:
            t1, t2 = side
            for edge in t1.edges(t2, False):
                if not self.is_inside(edge.coordinates):
                    return False

        return True

    def compute_areas_p2(self, tiles: list[Tile], illegals: set[tuple[Tile, Tile]]):
        for i in range(len(tiles)):
            i_tile = tiles[i]
            for j in range(i + 1, len(tiles)):
                j_tile = tiles[j]
                if (i_tile, j_tile) not in illegals:
                    area = i_tile.area(j_tile)
                    yield (i_tile, j_tile), area

    def is_inside(self, tile: tuple[int, int]):
        if tile in self.tiles or tile in self.edges:
            return True

        if tile not in self._is_inside:
            if tile[0] < self.min_x:
                self._is_inside[tile] = 0
            elif tile[1] < self.min_y:
                self._is_inside[tile] = 0
            else:
                x, y = tile
                ray_cast = sum(1 for c in self.ray_cast_struct.get(y) or [] if c > x)
                self._is_inside[tile] = ray_cast

        is_inside = self._is_inside[tile]
        return is_inside % 2 != 0

    def _parse_edges(self, tiles: list[Tile]):
        for i in range(len(tiles)):
            curr_tile, next_tile = self.get_tile_and_next(i, tiles)
            yield from curr_tile.edges(next_tile)

    def _parse_coordinates(self, input_lines: list[str]):
        for line in input_lines:
            x, y = line.split(",")
            yield Tile(int(x), int(y))


class Tile:
    x: int
    y: int

    def __init__(self, x: int | str, y: int | str) -> None:
        self.x = x if type(x) is int else int(x)
        self.y = y if type(y) is int else int(y)
        self._areas: dict[Tile, int] = dict()
        self.is_bottom_vertex = False

    @property
    def coordinates(self):
        return (self.x, self.y)

    def __hash__(self) -> int:
        return (self.x, self.y).__hash__()

    def __repr__(self) -> str:
        return f"({self.x},{self.y})"

    def __getitem__(self, key: int):
        if type(key) is not int and (key > 1 or key < 0):
            raise KeyError("Only 0 (= X axis) or 1 (= Y axis)")
        return self.x if key == 0 else self.y

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Tile):
            return self.coordinates == value.coordinates
        if type(value) is tuple and len(value) == 2:
            return value == self.coordinates
        raise ValueError(f"Unexpected Value {value}")

    def area(self, opposite_tile: Tile):
        if area := (self._areas.get(opposite_tile) or opposite_tile._areas.get(self)):
            return area

        x_len = self.x - opposite_tile.x
        x_len = (x_len if x_len > 0 else -x_len) + 1

        y_len = self.y - opposite_tile.y
        y_len = (y_len if y_len > 0 else -y_len) + 1

        self._areas[opposite_tile] = x_len * y_len
        return self._areas[opposite_tile]

    def edges(self, opposite_tile: Tile, set_is_bottom: bool = True):
        if self.x == opposite_tile.x:
            # Vertical Edge
            step = 1 if self.y < opposite_tile.y else -1
            curr_range = range(self.y + step, opposite_tile.y, step)
            for i in curr_range:
                yield VerticalEdge(self.x, i)

            if set_is_bottom:
                if step < 0:
                    self.is_bottom_vertex = True
                else:
                    opposite_tile.is_bottom_vertex = True
        else:
            # Horizontal Edge
            step = 1 if self.x < opposite_tile.x else -1
            curr_range = range(self.x + step, opposite_tile.x, step)
            for i in curr_range:
                yield HorizontalEdge(i, self.y)


class VerticalEdge(Tile):
    def __repr__(self) -> str:
        return "V" + super().__repr__()


class HorizontalEdge(Tile):
    def __repr__(self) -> str:
        return "H" + super().__repr__()


def part2(input_lines: list[str]):
    board = Board(input_lines)
    # draw_board(board)
    print(len(board.areas))
    max_area = board.max_area()
    return max_area[1]


def draw_board(board: Board):
    with open("board.txt", "w") as f:
        for y in range(board.max_y):
            curr_line = ""
            for x in range(board.max_x):
                curr_coord = (x, y)
                if curr_coord in board.tiles:
                    curr_tile = "#"
                elif curr_coord in board.edges:
                    curr_tile = "X"
                elif board.is_inside(curr_coord):
                    curr_tile = "X"
                else:
                    curr_tile = "."
                curr_line += curr_tile
            f.write(curr_line + "\n")


if __name__ == "__main__":
    # input_list = pathlib.Path("example.txt").read_text().strip().split("\n")
    input_list = pathlib.Path("input.txt").read_text().strip().split("\n")

    start_time = time.time()
    result = part2(input_list)
    print(f"max_area exec time: {time.time() - start_time}s")
    print(result)
