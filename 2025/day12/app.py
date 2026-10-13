from __future__ import annotations

import pathlib
import time


def part1(input_lines: list[str]):
    ...

def part2(input_lines: list[str]):
    ...


if __name__ == "__main__":
    # input_list = pathlib.Path("example2.txt").read_text().strip().split("\n")
    input_list = pathlib.Path("input.txt").read_text().strip().split("\n")

    start_time = time.time()
    # result = part1(input_list)
    result = part2(input_list)
    print(f"Exec time: {time.time() - start_time}s")
    print(result)
