from __future__ import annotations
from ..solver import Solver
import numpy as np
import re


directions = {"R": (1, 0), "L": (-1, 0), "U": (0, 1), "D": (0, -1)}


class Rope:
    def __init__(self) -> None:
        self.tail = Knot(None)
        self.head = Knot(self.create_rope(8))
        self.tail_visited: set[tuple[int, int]] = {(0, 0)}

    def create_rope(self, curr_knot: int):
        return Knot(self.tail) if curr_knot == 1 else Knot(self.create_rope(curr_knot - 1))

    def get_move(self, direction: str, quantity: int):
        for _ in range(quantity):
            self.head.make_move(direction)
            self.tail_visited.add((self.tail.x, self.tail.y))


class Knot:
    def __init__(self, prev: Knot | None) -> None:
        self.prev = prev
        self.x = 0
        self.y = 0

    def make_move(self, direction: str):
        self.x += directions[direction][0]
        self.y += directions[direction][1]
        if self.prev:
            self.prev.update_pos(self)

    def update_pos(self, next: Knot):
        distance = (next.x - self.x, next.y - self.y)

        # Adjacent or Overlapping
        if abs(distance[0]) <= 1 and abs(distance[1]) <= 1:
            return

        # Same Column
        if distance[0] == 0:
            self.y += 1 if next.y > self.y else -1
            if self.prev:
                self.prev.update_pos(self)
            return

        # Same Row
        if distance[1] == 0:
            self.x += 1 if next.x > self.x else -1
            if self.prev:
                self.prev.update_pos(self)
            return

        direction = (np.sign(distance[0]), np.sign(distance[1]))
        self.x, self.y = self.x + direction[0], self.y + direction[1]

        if self.prev:
            self.prev.update_pos(self)


class Board:
    def __init__(self) -> None:
        self.head = [0, 0]
        self.tail = [0, 0]
        self.tail_visited: set[tuple[int, int]] = {(0, 0)}

    def execute_move(self, direction: str, quantity: int):
        for _ in range(quantity):
            self.move_head(direction, 1)

    def move_head_fast(self, direction: str, quantity: int):
        self.move_head(direction, quantity)

    def move_head(self, direction, quantity):
        self.head[0] += directions[direction][0] * quantity
        self.head[1] += directions[direction][1] * quantity
        self.update_tail()
        self.tail_visited.add((self.tail[0], self.tail[1]))

    def update_tail(self):
        distance = (self.head[0] - self.tail[0], self.head[1] - self.tail[1])

        # Adjacent or Overlapping
        if abs(distance[0]) <= 1 and abs(distance[1]) <= 1:
            return

        # Same Column
        if distance[0] == 0:
            self.tail[1] += 1 if self.head[1] > self.tail[1] else -1
            return

        # Same Row
        if distance[1] == 0:
            self.tail[0] += 1 if self.head[0] > self.tail[0] else -1
            return

        direction = (np.sign(distance[0]), np.sign(distance[1]))
        self.tail = [self.tail[0] + direction[0], self.tail[1] + direction[1]]


class Day9Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.moves_example = self.parse_input(self.example_path.replace(".txt", "2.txt"))
        self.moves = self.parse_input(self.input_path)

    def parse_input(self, file_path: str) -> list[tuple[str, int]]:
        parsed_moves = []
        with open(file_path, "r") as input_file:
            for line in input_file:
                findings = re.findall(r"(\S) (\d+)", line)[0]
                parsed_moves.append((findings[0], int(findings[1])))
        return parsed_moves

    def solve_first(self, is_example: bool = False):
        moves = self.moves_example if is_example else self.moves
        return self.first_alg(moves)

    def first_alg(self, moves: list[tuple[str, int]]):
        board = Board()
        for move in moves:
            board.execute_move(move[0], move[1])

        return len(board.tail_visited)

    def solve_second(self, is_example: bool = False):
        moves = self.moves_example if is_example else self.moves
        return self.second_alg(moves)

    def second_alg(self, moves: list[tuple[str, int]]):
        rope = Rope()
        for move in moves:
            rope.get_move(*move)

        return len(rope.tail_visited)
