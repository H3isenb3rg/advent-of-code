from ..solver import Solver    
import re

class Day5Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.example_stacks, self.example_moves = self.parse_input(self.example_path)
        self.stacks, self.moves = self.parse_input(self.input_path)

    def parse_input(self, path: str) -> tuple[list[list[str]], list[list[int]]]:
        moves = []

        with open(path, "r") as input_file:
            raw_lines: list[str] = []
            while True:
                curr_line = input_file.readline()
                if curr_line == "\n":
                    break
                raw_lines.append(curr_line[:-1])

            stacks = [[] for _ in re.findall(r"\s(\S)\s", raw_lines[-1])]
            indexes = raw_lines.pop(-1)
            for line in reversed(raw_lines):
                for i in range(1, len(line), 4):
                    if line[i] != " ": stacks[int(indexes[i])-1].append(line[i])

            for line in input_file.readlines():
                moves.append([int(digit) for digit in re.findall(r"move (\d+) from (\d+) to (\d+)", line)[0]])


        return stacks, moves    
    
    def solve_first(self, is_example: bool = False):
        if is_example:
            stacks = self.example_stacks
            moves = self.example_moves
        else:
            stacks = self.stacks
            moves = self.moves

        return self.first_alg([stack.copy() for stack in stacks], moves)
        
    def first_alg(self, stacks: list[list[str]], moves: list[list[int]]):
        for move in moves:
            for _ in range(move[0]):
                stacks[move[2]-1].append(stacks[move[1]-1].pop())

        return "".join(stack[-1] for stack in stacks)
            
    def solve_second(self, is_example: bool = False):
        if is_example:
            stacks = self.example_stacks
            moves = self.example_moves
        else:
            stacks = self.stacks
            moves = self.moves

        return self.second_alg([stack.copy() for stack in stacks], moves)
    
    def second_alg(self, stacks: list[list[str]], moves: list[list[int]]):
        for move in moves:
            origin = move[1]-1
            destination = move[2]-1
            stacks[destination].extend(stacks[origin][-move[0]:])
            for _ in range(move[0]): stacks[origin].pop()

        return "".join(stack[-1] for stack in stacks)
