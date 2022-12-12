from ..solver import Solver
import numpy as np
import re


directions = {"R": (1, 0), "L": (-1, 0), "U": (0, 1), "D": (0, -1)}


class Board:
    def __init__(self) -> None:
        self.head = [0, 0]
        self.tail = [0, 0]
        self.tail_visited: set[tuple[int, int]] = {(0, 0)}
        self.update_tail()

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
        self.tail = [self.tail[0]+direction[0], self.tail[1] + direction[1]]


class Day9Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.moves_example = self.parse_input(self.example_path)
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
        pass
