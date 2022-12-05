from ..solver import Solver    

class Day3Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.example_input = self.parse_input(self.example_path)
        self.input = self.parse_input(self.input_path)

    def parse_input(self, path: str) -> list[list[str]]:
        parsed_input = []
        
        with open(path, "r") as input_file:
            for line in input_file.readlines():
                parsed_input.append([*line[:-1]])

        return parsed_input
    
    def solve_first(self, is_example: bool = False):
        pass
        
    def first_alg(self, rucksacks):
        pass

    def solve_second(self, is_example: bool = False):
        pass
    
    def second_alg(self, rucksacks):
        pass
