from __future__ import annotations
from ..solver import Solver
from dataclasses import dataclass, field
import re

TOTAL_AVAILABLE = 70_000_000
SPACE_NEEDED = 30_000_000


@dataclass
class Dir:
    name: str
    parent: Dir | None = field(default=None)
    content: dict = field(default_factory=lambda: {})

    def __eq__(self, __o: object) -> bool:
        if type(__o) is str:
            return self.name == __o

        if type(__o) is Dir:
            return self.name == __o.name

        if type(__o) is File:
            return False

        raise TypeError(f"Can't compare Dir with {type(__o)}")

    def get_size(self) -> int:
        return sum(item.get_size() for _, item in self.content.items())


@dataclass
class File:
    name: str
    size: int

    def get_size(self) -> int:
        return self.size


class Day7Solver(Solver):
    def __init__(self, day_folder: str) -> None:
        super().__init__(day_folder)
        self.fs_example = self.parse_input(self.example_path)
        self.fs = self.parse_input(self.input_path)

    def parse_input(self, file_path: str):
        root_dir = Dir("/", None)
        dirs: list[Dir] = [root_dir]
        curr_dir = root_dir
        with open(file_path, "r") as input_file:
            input_file.readline()  # Skip first '$ cd /'
            for line in input_file:
                if line[0] == "$":
                    # User command
                    if "cd" in line:
                        if ".." in line:
                            if curr_dir.parent is None:
                                raise RuntimeError("Can't find parent of /")
                            curr_dir = curr_dir.parent
                            continue

                        raw_dir = re.findall(r"\$\scd\s(\S+)", line)[0]
                        if raw_dir not in curr_dir.content:
                            new_dir = Dir(raw_dir, curr_dir)
                            dirs.append(new_dir)
                            curr_dir.content[raw_dir] = new_dir
                            curr_dir = new_dir
                            continue

                        curr_dir = curr_dir.content[raw_dir]

                else:
                    # Response to ls command
                    if "dir" in line:
                        raw_dir = re.findall(r"dir\s(\S+)", line)[0]
                        new_dir = Dir(raw_dir, curr_dir)
                        dirs.append(new_dir)
                        curr_dir.content[raw_dir] = new_dir
                        continue

                    file_info = re.findall(r"(\d+)\s(\S+)", line)[0]
                    new_file = File(file_info[1], int(file_info[0]))
                    curr_dir.content[new_file.name] = new_file

        return root_dir, dirs

    def solve_first(self, is_example: bool = False):
        fs = self.fs_example if is_example else self.fs
        return self.first_alg(fs[1])

    def first_alg(self, dirs: list[Dir]):
        return sum(dir.get_size() for dir in dirs if dir.get_size() <= 100_000)

    def solve_second(self, is_example: bool = False):
        fs = self.fs_example if is_example else self.fs
        return self.second_alg(fs)

    def second_alg(self, fs: tuple[Dir, list[Dir]]):
        root = fs[0]
        dirs = fs[1]

        free_space = TOTAL_AVAILABLE - root.get_size()
        required_space = SPACE_NEEDED - free_space

        return min(curr_dir.get_size() for curr_dir in dirs if curr_dir.get_size() >= required_space)
