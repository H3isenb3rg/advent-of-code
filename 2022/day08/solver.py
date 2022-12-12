from ..solver import Solver


def compute_visibles_vertical(range_x: range, range_y: range, forest: list[list[int]]):
    visibles = set()
    # Top Bottom
    for x in range_x:
        curr_max_height = -1
        for y in range_y:
            if forest[y][x] > curr_max_height:
                curr_max_height = forest[y][x]
                visibles.add((x, y))
                if curr_max_height == 9:
                    break

    return visibles


def compute_visibles_horizontal(range_y: range, range_x: range, forest: list[list[int]]):
    visibles = set()
    # Top Bottom
    for y in range_y:
        curr_max_height = -1
        for x in range_x:
            if forest[y][x] > curr_max_height:
                curr_max_height = forest[y][x]
                visibles.add((x, y))
                if curr_max_height == 9:
                    break

    return visibles


def compute_scenic_score(forest: list[list[int]], tree: tuple[int, int]) -> int:
    directions = [(0, -1), (-1, 0), (0, 1), (1, 0)]
    score = 1

    for direction in directions:
        if tree[0] + direction[0] not in range(len(forest[0])):
            continue
        if tree[1] + direction[1] not in range(len(forest)):
            continue
        # directionx2 since we always see the first tree so we start directly from the second one
        curr_x = tree[0] + direction[0]
        curr_y = tree[1] + direction[1]
        curr_dist = 0
        while curr_x in range(len(forest[0])) and curr_y in range(len(forest)):
            if forest[curr_y][curr_x] >= forest[tree[1]][tree[0]]:
                curr_dist += 1
                break

            curr_dist += 1
            curr_x += direction[0]
            curr_y += direction[1]
        score *= curr_dist

    return score


class Day8Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.forest_example = self.parse_input(self.example_path)
        self.forest = self.parse_input(self.input_path)

    def parse_input(self, file_path: str):
        with open(file_path, "r") as input_file:
            return [[int(tree) for tree in line[:-1]] for line in input_file]

    def solve_first(self, is_example: bool = False):
        forest = self.forest_example if is_example else self.forest
        return self.first_alg(forest)

    def first_alg(self, forest: list[list[int]]):
        visibles = set()
        # Top Bottom
        visibles = visibles.union(compute_visibles_vertical(range(len(forest[0])), range(len(forest)), forest))

        # Bottom Top
        visibles = visibles.union(compute_visibles_vertical(range(len(forest[0])), range(len(forest) - 1, -1, -1), forest))

        # Left Right
        visibles = visibles.union(compute_visibles_horizontal(range(len(forest)), range(len(forest[0])), forest))

        # Right Left
        visibles = visibles.union(compute_visibles_horizontal(range(len(forest)), range(len(forest[0]) - 1, -1, -1), forest))

        return len(visibles)

    def solve_second(self, is_example: bool = False):
        forest = self.forest_example if is_example else self.forest
        return self.second_alg(forest)

    def second_alg(self, forest: list[list[int]]):
        return max(max(compute_scenic_score(forest, (x, y)) for x in range(1, len(forest[0]) - 1)) for y in range(1, len(forest) - 1))
