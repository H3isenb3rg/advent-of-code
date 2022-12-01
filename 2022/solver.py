import os
from abc import abstractmethod, ABC

class Solver(ABC):
    
    def __init__(self, day_folder: str) -> None:
        super().__init__()
        self.example_path = os.path.join(day_folder, "input_example.txt")
        self.input_path = os.path.join(day_folder, "input.txt")

    @abstractmethod
    def solve_first(self, is_example: bool = False):
        pass

    @abstractmethod
    def solve_second(self, is_example: bool = False):
        pass