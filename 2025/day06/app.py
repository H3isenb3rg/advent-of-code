import pathlib
from typing import Iterable
from functools import reduce
import operator
import numpy as np


def compute(numbers: Iterable[int], op: str) -> int:
    if op == "+":
        return sum(numbers)
    if op == "*":
        return reduce(operator.mul, numbers, 1)

    raise KeyError(f"Unexpected operator `{op}`")


def get_results(operations: list[str], numbers: list[list[int]]):
    for op_i in range(len(operations)):
        op = operations[op_i]
        curr_numbers = (n[op_i] for n in numbers)
        yield compute(curr_numbers, op)


def part1(input_lines: list[str]):
    operations = input_lines[-1].split()
    numbers = [[int(n) for n in line.split()] for line in input_lines[:-1]]

    result = sum(get_results(operations, numbers))
    print(result)


def parse_numbers_lists(number_lines: list[str], col_ends: list[int]):
    curr_start = 0
    for end in col_ends:
        yield [ns[curr_start:end].replace(" ", "-") for ns in number_lines]
        curr_start = end+1
    
    # final column
    yield [ns[curr_start:].replace(" ", "-") for ns in number_lines]
    


def part2(input_lines: list[str]):
    operations = input_lines[-1]
    col_ends = [i-1 for i in range(1, len(operations)) if operations[i] in {"+", "*"}]
    numbers = list(parse_numbers_lists(input_lines[:-1], col_ends))
    numbers = [[list(n) for n in ns] for ns in numbers]
    numbers = [[int("".join(n).replace("-","")) for n in np.transpose(ns).tolist()] for ns in numbers]
    operations = operations.split()

    result = sum(compute(ns, op) for ns, op in zip(numbers, operations))
    print(result)


# raw_lines = pathlib.Path("example.txt").read_text().strip().split("\n")
raw_lines = pathlib.Path("input.txt").read_text().strip().split("\n")
part2(raw_lines)
