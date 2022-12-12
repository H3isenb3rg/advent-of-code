from ..solver import Solver
import re


wanted = [20 + (40 * i) for i in range(7)]


class Sprite:
    def __init__(self) -> None:
        self.x = 1

    def get_sprite_range(self):
        return range(self.x - 1 if self.x > 0 else 0, self.x + 2 if self.x < 38 else 40)


class Day10Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.instructions_example = self.parse_input(self.example_path)
        self.instructions = self.parse_input(self.input_path)

    def parse_input(self, file_path: str) -> list[int]:
        parsed_instructions = []
        with open(file_path, "r") as input_file:
            for line in input_file:
                if "noop" in line:
                    parsed_instructions.append(0)
                    continue

                parsed_instructions.append(int(re.findall(r"addx (-?\d+)", line)[0]))

        return parsed_instructions

    def solve_first(self, is_example: bool = False):
        instructions = self.instructions_example if is_example else self.instructions
        values = self.first_alg(instructions)
        return sum(values)

    def first_alg(self, instructions: list[int]):
        cycle = 1
        x = 1
        values = []
        instructions_iter = iter(instructions)
        wanted_iter = iter(wanted)
        curr_wanted = next(wanted_iter)

        while cycle <= 220:
            curr_instruction = next(instructions_iter)
            cycle += 1 if curr_instruction == 0 else 2
            if cycle > curr_wanted:
                values.append(x * curr_wanted)
                curr_wanted = next(wanted_iter)

            x += curr_instruction

        return values

    def solve_second(self, is_example: bool = False):
        instructions = self.instructions_example if is_example else self.instructions
        return self.second_alg(instructions)

    def second_alg(self, instructions: list[int]):
        sprite = Sprite()
        instructions_iter = iter(instructions)
        curr_instruction = next(instructions_iter)
        curr_cycle_increment = 1 if curr_instruction == 0 else 2

        for line in range(6):
            line = ""
            for pixel in range(40):
                curr_cycle_increment -= 1
                line += "#" if pixel in sprite.get_sprite_range() else "."
                if curr_cycle_increment == 0:
                    sprite.x += curr_instruction
                    try:
                        curr_instruction = next(instructions_iter)
                    except StopIteration:
                        print(line)
                        return
                    curr_cycle_increment = 1 if curr_instruction == 0 else 2
            print(line)
