from __future__ import annotations
import pathlib


class IRange:
    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end
    
    def is_in(self, ing_id: int):
        return ing_id <= self.end and ing_id >= self.start

    def mix(self, r: IRange):
        # check if self contains r
        if self.start <= r.start and self.end >= r.end:
            return self
        # check if r contains self
        if r.start <= self.start and r.end >= self.end:
            return r

        # Intersection
        if self.start <= r.start and r.end >= self.end and self.end >= r.start:
            return IRange(self.start, r.end)
        if r.start <= self.start and self.end >= r.end and r.end >= self.start:
            return IRange(r.start, self.end)

        return None
    
    def id_count(self):
        return self.end - self.start + 1
    
    def __hash__(self):
        return (self.start, self.end).__hash__()
    
    def __lt__(self, other: IRange):
        if self.start == other.start:
            return self.end < other.end
        return self.start < other.start

    def __repr__(self) -> str:
        return f"({self.start},{self.end})"


def parse_ing_ranges(raw_ranges: list[str]):
    for item in raw_ranges:
        ranges = item.split("-", 1)
        yield IRange(int(ranges[0]), int(ranges[1]))


def squash_ranges(ranges: list[IRange]):
    i=0
    
    while i<len(ranges):
        j = i+1
        while j<len(ranges):
            curr_i = ranges[i]
            curr_j = ranges[j]
            if mix_range := curr_i.mix(curr_j):
                ranges[i] = mix_range
                del ranges[j]
            j+=1
        i+=1
    
    return ranges


# ingredient_ranges, available_id = pathlib.Path("example.txt").read_text().strip().split("\n\n")
ingredient_ranges, available_id = pathlib.Path("input.txt").read_text().strip().split("\n\n")

ingredient_ranges = sorted(set(parse_ing_ranges(ingredient_ranges.strip().split("\n"))))

# Optimize ranges
old_len = len(ingredient_ranges)
ingredient_ranges = squash_ranges(ingredient_ranges)
while old_len != len(ingredient_ranges):
    old_len = len(ingredient_ranges)
    ingredient_ranges = squash_ranges(ingredient_ranges)


result = sum(1 for av_id in available_id.split("\n") if any(r.is_in(int(av_id)) for r in ingredient_ranges))
total_ids = sum(r.id_count() for r in ingredient_ranges)

print(result)
print(total_ids)
