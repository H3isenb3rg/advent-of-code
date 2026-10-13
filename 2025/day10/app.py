from typing import Iterable
import pathlib
import time


# Part 2 → https://www.reddit.com/r/adventofcode/comments/1pk87hl/2025_day_10_part_2_bifurcate_your_way_to_victory/


def is_all_even(state: Iterable[int]):
    return all(s % 2 == 0 for s in state)


class Button:
    lights_to_toggle: set[int]

    @staticmethod
    def parse_buttons(raw_buttons: list[str]):
        for raw_button in raw_buttons:
            raw_button = raw_button.replace("(", "").replace(")", "").split(",")
            yield Button(*raw_button)

    def __contains__(self, item):
        if type(item) is not int:
            raise ValueError("Unexpected type")
        return item in self.lights_to_toggle

    def __init__(self, *args: str) -> None:
        self.lights_to_toggle = {int(light) for light in args}

    def __repr__(self) -> str:
        return (
            str(tuple(self.lights_to_toggle))
            if len(self.lights_to_toggle) > 1
            else f"({next(iter(self.lights_to_toggle))})"
        )

    def __hash__(self) -> int:
        return tuple(self.lights_to_toggle).__hash__()

    def toggle(self, current: set[int]) -> set[int]:
        to_be_turned_off = current.intersection(self.lights_to_toggle)
        new_current = current - to_be_turned_off
        if toggle := self.lights_to_toggle - to_be_turned_off:
            new_current |= toggle
        return new_current

    def decrement_counter(self, counter: list[int]):
        return [c - 1 if i in self.lights_to_toggle else c for i, c in enumerate(counter)]


class Indicator:
    total_lights: int
    lights_objective: set[int]
    buttons: set[Button]
    tested_groups: list[set[Button]]

    def __init__(self, raw_diagram: str, buttons: set[Button], raw_joltages: str) -> None:
        self.buttons = buttons
        self.total_lights = len(raw_diagram)
        self.lights_objective = {i for i, c in enumerate(raw_diagram) if c == "#"}
        self.joltage_objective = tuple(int(j) for j in raw_joltages.split(","))
        self.i_buttons = {i: {btn for btn in self.buttons if i in btn} for i in range(len(self.joltage_objective))}
        self.cached_states: dict[tuple[int, ...], int] = dict()
        self.tested_groups = []

    def __repr__(self) -> str:
        obj = "".join("#" if i in self.lights_objective else "." for i in range(self.total_lights))
        return f"[{obj}]"

    def find_least_presses_p1(self, obj: set[int] | None):
        obj = obj or self.lights_objective
        grouping = self.extract_level_group()
        while grouping:
            for group in grouping:
                state: set[int] = set()
                for btn in group:
                    state = btn.toggle(state)
                if state == obj:
                    return group

            grouping = self.extract_level_group(grouping)
        raise ValueError("Could not find sequence to obtain objective")

    def extract_level_group(self, curr_groupings: list[set[Button]] = []):
        if not curr_groupings:
            return [{btn} for btn in self.buttons]
        new_groupings = []
        for btn_grouping in curr_groupings:
            for btn in self.buttons - btn_grouping:
                new_group = btn_grouping | {btn}
                if new_group not in new_groupings:
                    new_groupings.append(new_group)
        return new_groupings

    def extract_phase1_groups(self, obj: set[int]):
        grouping = self.extract_level_group()
        while grouping:
            for group in grouping:
                state: set[int] = set()
                for btn in group:
                    state = btn.toggle(state)
                if state == obj:
                    yield group
            grouping = self.extract_level_group(grouping)
    
    def available_buttons(self, state: list[int]):
        complete_counters = [i for i, c in enumerate(state) if c <= 0]
        forbidden_buttons = {btn for btn in self.buttons if any(complete in btn for complete in complete_counters)}
        return self.buttons - forbidden_buttons

    def group_buttons_least_count(self, curr_counter: list[int]) -> set[Button]:
        least_count = min(c for c in curr_counter if c > 0)
        complete_counters = [i for i, c in enumerate(curr_counter) if c <= 0]
        forbidden_buttons = {btn for btn in self.buttons if any(complete in btn for complete in complete_counters)}
        min_count_i = [i for i, value in enumerate(curr_counter) if value == least_count]

        # Check if there are counters with no buttons available
        for i, btns in self.i_buttons.items():
            if i not in complete_counters and len(btns - forbidden_buttons) == 0:
                raise ValueError(f"Impossible to fill counter position {i}, there are no available buttons")
        result = set().union(*(btns for i, btns in self.i_buttons.items() if i in min_count_i)) - forbidden_buttons
        max_len = max(len(btn.lights_to_toggle) for btn in result)
        return {btn for btn in result if len(btn.lights_to_toggle) == max_len}

    def find_least_presses_p2(self):
        return self.bifurcate_presses(self.joltage_objective)

    def bifurcate_presses(self, obj: tuple[int, ...]):
        if obj in self.cached_states:
            return self.cached_states[obj]
        result = self._bifurcate_presses(obj)
        self.cached_states[obj] = result
        return result

    def _bifurcate_presses(self, obj: tuple[int, ...]):
        if is_all_even(obj):
            btns = self.available_buttons(list(obj))
            groups_p1 = [{btn} for btn in btns]
        else:
            odd_indexes = {i for i, c in enumerate(obj) if c % 2 != 0}
            groups_p1 = sorted(self.extract_phase1_groups(odd_indexes), key=lambda b: len(b))
        results = []
        for p1_group in groups_p1:
            curr_state = list(obj)
            for btn in p1_group:
                curr_state = btn.decrement_counter(curr_state)

            if any(c < 0 for c in curr_state):
                continue

            if sum(curr_state) == 0:
                results.append(len(p1_group))
            elif is_all_even(curr_state):
                curr_state = [c // 2 for c in curr_state]
                result = self.bifurcate_presses(tuple(curr_state))
                if result >= 0:
                    results.append(2 * result + len(p1_group))
            else:
                result = self.bifurcate_presses(tuple(curr_state))
                if result >= 0:
                    results.append(result + len(p1_group))

        return min(results) if results else -1

    def generate_next_states(self, current_states: list[list[int]]):
        states: list[list[int]] = []
        for state in current_states:
            try:
                grouping = sorted(
                    self.group_buttons_least_count(state), key=lambda b: len(b.lights_to_toggle), reverse=True
                )
            except ValueError:
                continue
            for btn in grouping:
                new_state = btn.decrement_counter(state)
                if new_state not in states:  # we already went through this state, we can skip it
                    if tuple(new_state) in self.cached_states:
                        continue
                    states.append(new_state)
        return states


def parse_line(line: str):
    line = line.strip()
    diagram, remaining = line.split("]", 1)
    buttons, joltage = remaining.split("{", 1)

    # Clean Up
    diagram = diagram.replace("[", "").strip()
    buttons = buttons.strip().split(" ")
    return diagram, buttons, joltage.replace("}", "").strip()


def part1(input_lines: list[str]):
    for i, line in enumerate(input_lines, 1):
        raw_diagram, raw_buttons, joltage = parse_line(line)
        buttons = set(Button.parse_buttons(raw_buttons))
        indicator = Indicator(raw_diagram, buttons, joltage)
        # result = indicator.find_least_presses_p1()
        result = indicator.find_least_presses_p2()

        print(f"{i}\t{indicator} {result}")
        if not result:
            raise ValueError("Could not obtain objective")
        yield result


if __name__ == "__main__":
    # input_list = pathlib.Path("example.txt").read_text().strip().split("\n")
    input_list = pathlib.Path("input.txt").read_text().strip().split("\n")

    start_time = time.time()
    result = sum(part1(input_list))
    print(f"Exec time: {time.time() - start_time}s")
    print(result)
