from ..solver import Solver    

class Day2Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.example_strategy = self.parse_input(self.example_path)
        self.strategy = self.parse_input(self.input_path)

        # Same: 0%3 = 0 -> draw
        # R vs P: 1-2 = -1%3 = -1 -> I Lose
        # P vs S: 2-3 = -1%3 = -1 -> I Lose
        # S vs R: 3-1 = +2%3 = +2 -> I Lose
        # R vs S: 1-3 = -2%3 = -2 -> I win
        # P vs R: 2-1 = +1%3 = +1 -> I win
        # S vs P: 3-2 = +1%3 = +1 -> I win
        
    def parse_input(self, path: str) -> list[tuple[int, int]]:
        strategy = []
        translator = {
            "A": 1,
            "X": 1,
            "B": 2,
            "Y": 2,
            "C": 3,
            "Z": 3
        }
        with open(path, "r") as input_file:
            for line in input_file.readlines():
                options = line[:-1].split(" ")
                strategy.append((translator[options[0]], translator[options[1]]))

        return strategy

    def match(self, me: int, enemy: int) -> int:
        result = (me - enemy)%3

        # Draw
        if result == 0:
            return 3 + me

        # Win
        if result == 1 or result == -2:
            return 6 + me

        #Lost
        return me
    
    def solve_first(self, is_example: bool = False):
        if is_example:
            strategy = self.example_strategy
        else:
            strategy = self.strategy

        return self.first_alg(strategy)
        
    def first_alg(self, strategy: list[tuple[int, int]]):
        return sum(self.match(me, enemy) for enemy, me in strategy)

    def solve_second(self, is_example: bool = False):
        if is_example:
            strategy = self.example_strategy
        else:
            strategy = self.strategy

        return self.second_alg(strategy)

    # Outcome 1
    # 1 -> 3
    # 2 -> 1
    # 3 -> 2

    # Outcome 3
    # 1 -> 2
    # 2 -> 3
    # 3 -> 1
    def second_alg(self, strategy: list[tuple[int, int]]):
        score = 0
        for enemy, outcome in strategy:
            if outcome == 2: # Draw
                score += 3 + enemy
                continue

            if outcome == 1: # Lose
                score += 3 if enemy == 1 else enemy-1
                continue

            # Win
            score += 6 + (1 if enemy == 3 else enemy + 1)

        return score
            

            
            