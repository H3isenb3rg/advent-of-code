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
        if is_example:
            rucksacks = self.example_input
        else:
            rucksacks = self.input

        return self.first_alg(rucksacks)

    def compute_priority(self, char: str):
        if char == char.upper():
            offset = ord("A")-27
        else:
            offset = ord("a")-1

        return ord(char)-offset
        
    def first_alg(self, rucksacks: list[list[str]]):
        total = 0
        for sack in rucksacks:
            int = set(sack[:len(sack)//2]).intersection(set(sack[len(sack)//2:]))
            total += self.compute_priority(list(int)[0]) if len(int)>0 else 0

        return total
            
    def solve_second(self, is_example: bool = False):
        if is_example:
            rucksacks = self.example_input
        else:
            rucksacks = self.input

        return self.second_alg(rucksacks)
    
    def second_alg(self, rucksacks: list[list[str]]):
        groups = [list(set(rucksacks[i]).intersection(rucksacks[i+1]).intersection(rucksacks[i+2])) for i in range(0, len(rucksacks), 3)]
        total = sum(self.compute_priority(group[0]) for group in groups)

        return total
