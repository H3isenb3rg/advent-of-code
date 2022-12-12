from ..solver import Solver    
import re

class Day4Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.example_input = self.parse_input(self.example_path)
        self.input = self.parse_input(self.input_path)

    def parse_input(self, path: str) -> list[list[int]]:
        parsed_input = []
        
        with open(path, "r") as input_file:
            for line in input_file.readlines():
                parsed_input.append([int(digit) for digit in re.findall(r"(\d+)-(\d+),(\d+)-(\d+)", line[:-1])[0]])
                
        return parsed_input
    
    def solve_first(self, is_example: bool = False):
        if is_example:
            couples = self.example_input
        else:
            couples = self.input

        return self.first_alg(couples)
        
    def first_alg(self, couples: list[list[int]]):
        count=0

        for couple in couples:
            first = (couple[0], couple[1])
            second = (couple[2], couple[3])
            if contains(first, second) or contains(second, first):
                count+=1

        return count
            
    def solve_second(self, is_example: bool = False):
        if is_example:
            couples = self.example_input
        else:
            couples = self.input

        return self.second_alg(couples)
    
    def second_alg(self, couples: list[list[int]]):
        count=0

        for couple in couples:
            first = (couple[0], couple[1])
            second = (couple[2], couple[3])
            if contains(first, second) or contains(second, first) or overlaps(first, second):
                count+=1

        return count

def contains(big: tuple[int, int], small: tuple[int, int]):
    return big[0]<=small[0] and big[1]>=small[1]

def overlaps(first: tuple[int, int], second: tuple[int, int]):
    return (first[0]<=second[0] and first[1]<=second[1] and first[1]>=second[0]) or (first[0]>=second[0] and first[1]>=second[1] and first[0]<=second[1])