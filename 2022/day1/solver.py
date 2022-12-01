from ..solver import Solver

class Day1Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.cargo_example = self.parse_input(self.example_path)
        self.cargo = self.parse_input(self.input_path)

    def parse_input(self, file_path: str):
        parsed_cargo = []
        with open(file_path, "r") as input_file:
            curr_cargo = []
            for line in input_file.readlines():
                line = line.replace("\n", "")
                if line == "":
                    parsed_cargo.append(curr_cargo)
                    curr_cargo = []
                else:
                    curr_cargo.append(int(line))
            parsed_cargo.append(curr_cargo)

        return parsed_cargo
    
    def solve_first(self, is_example: bool = False):
        cargo = self.cargo
        if is_example:
            cargo = self.cargo_example
            
        return self.first_alg(cargo)

    def first_alg(self, cargo):
        return max(sum(item for item in cargo) for cargo in cargo)
    
    def solve_second(self, is_example: bool = False):
        cargo = self.cargo
        if is_example:
            cargo = self.cargo_example  

        return self.second_alg(cargo)

    def second_alg(self, cargo):
        sums = [sum(items) for items in cargo]
        return sum(total for total in sorted(sums, reverse=True)[:3])
    