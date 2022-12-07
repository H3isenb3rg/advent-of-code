from ..solver import Solver


class Day6Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.example_line = self.parse_input(self.example_path)
        self.line = self.parse_input(self.input_path)

    def parse_input(self, file_path: str):
        return open(file_path, "r").readline()

    def solve_first(self, is_example: bool = False):
        cargo = self.example_line if is_example else self.line
        return self.first_alg(cargo)

    def first_alg(self, line: str):
        for i in range(3, len(line)):
            if len(set(line[i - 4:i])) == 4:
                return i

    def solve_second(self, is_example: bool = False):
        cargo = self.example_line if is_example else self.line
        return self.second_alg(cargo)

    def second_alg(self, line: str):
        for i in range(13, len(line)):
            if len(set(line[i - 14:i])) == 14:
                return i
