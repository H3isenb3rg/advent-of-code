from __future__ import annotations
from typing import Callable
import pathlib


class Tile:
    x: int
    y: int

    def __init__(self, x: int | str, y: int | str) -> None:
        self.x = x if type(x) is int else int(x)
        self.y = y if type(y) is int else int(y)
        self._areas: dict[Tile, int] = dict()

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
        if type(value) is Tile:
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


def get_edge_tiles(tiles: set[Tile], axis: int, comparator: Callable[[int, int], bool], start_value: int):
    edge_value, edge_tiles = start_value, []
    for tile in tiles:
        if comparator(tile[axis], edge_value):
            edge_value = tile[axis]
            edge_tiles = [tile]
        elif tile[axis] == edge_value:
            edge_tiles.append(tile)

    return edge_tiles


def parse_coordinates(input_lines: list[str]):
    for line in input_lines:
        x, y = line.split(",")
        yield Tile(int(x), int(y))


def compute_areas_p1(tiles: list[Tile]):
    for i in range(len(tiles)):
        i_tile = tiles[i]
        for j in range(i + 1, len(tiles)):
            j_tile = tiles[j]
            area = i_tile.area(j_tile)
            yield (i_tile, j_tile), area


def part1(input_lines: list[str]):
    tiles = list(parse_coordinates(input_lines))
    max_y = max(tiles, key=lambda t: t.y).y
    max_x = max(tiles, key=lambda t: t.x).x
    o_x = max_x / 2
    o_y = max_y / 2

    q2_q4_tiles = [t for t in tiles if (t.x < o_x and t.y > o_y) or (t.x > o_x and t.y < o_y)]
    q1_q3_tiles = [t for t in tiles if (t.x > o_x and t.y > o_y) or (t.x < o_x and t.y < o_y)]

    q2_q4_max_area = max(compute_areas_p1(q2_q4_tiles), key=lambda r: r[1])
    q1_q3_max_area = max(compute_areas_p1(q1_q3_tiles), key=lambda r: r[1])
    max_area = q2_q4_max_area if q2_q4_max_area[1] > q1_q3_max_area[1] else q1_q3_max_area
    return max_area[1]


input_list = pathlib.Path("example.txt").read_text().strip().split("\n")
# input_list = pathlib.Path("input.txt").read_text().strip().split("\n")

result = part1(input_list)

print(result)


# DEPRECATED
# - no need to do this just look for max/min
# def explore_from_corner(tiles: set[tuple[int, int]], n: tuple[int, int], increments: tuple[int, int]):
#     # increments:
#     # - Top Left → (+1, +1)
#     # - Top Right → (-1, +1)
#     # - Bottom Right → (-1, -1)
#     # - Bottom Left → (+1, -1)
#     x_inc, y_inc = increments
#     x_n, y_n = n

#     # TODO: split x exploration and y exploration since the board is not a square
#     found = False
#     for i in range(n):
#         i_x = i if x_inc > 0 else n - i - 1
#         i_y = i if y_inc > 0 else n - i - 1
#         if found:
#             break

#         # X explore
#         range_x = range(i) if x_inc > 0 else range(n - 1, i_y - 1, -1)
#         for x in range_x:
#             if (x, i_y) in tiles:
#                 found = True
#                 yield Tile(x, i_y)

#         # Y explore
#         range_y = range(i) if y_inc > 0 else range(n - 1, i_x - 1, -1)
#         for y in range_y:
#             if (i_x, y) in tiles:
#                 found = True
#                 yield Tile(i_x, y)
