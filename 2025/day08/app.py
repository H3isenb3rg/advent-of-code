from __future__ import annotations
import pathlib
import operator
from functools import reduce


class Box:
    x: int
    y: int
    z: int
    distances: dict[Box, float]
    closest_list: list[Box]
    circuit: int

    @staticmethod
    def parse_boxes(input_lines: list[str]):
        for line in input_lines:
            coord = (int(c) for c in line.split(","))
            yield Box(*coord)

    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z
        self.circuit = 0
        self.distances = dict()
    
    @property
    def coordinates(self):
        return (self.x,self.y,self.z)
    
    @property
    def closest_distance(self):
        return self.closest_list[0], self.distances[self.closest_list[0]]

    def __repr__(self) -> str:
        return f"{self.coordinates}"
    
    def __hash__(self) -> int:
        return (self.x,self.y,self.z).__hash__()

    def distance(self, other: Box) -> float:
        return (
            (self.x - other.x)**2 +
            (self.y - other.y)**2 +
            (self.z - other.z)**2
        )**0.5
    
    def set_distances(self, others: list[Box]):
        for box in others:
            curr_distance = self.distance(box)
            if box in self.distances:
                pass
            self.distances[box] = curr_distance

            if self in box.distances:
                pass
            box.distances[self] = curr_distance
        
        self.closest_list = sorted(self.distances, key=lambda box: self.distances[box])
        pass


def iterate_distances(boxes: list[Box]):
    paths: set[tuple[Box,Box]] = set()
    for box in boxes:
        for other in box.closest_list:
            curr = (box,other)
            if any(pair in paths for pair in (curr, (other,box))):
                continue
            paths.add(curr)
            yield curr
        

        


def part1(input_lines: list[str], n: int):
    # Create list of boxes
    boxes = list(Box.parse_boxes(input_lines))

    # Compute distances between boxes
    for i in range(len(boxes)):
        curr_box = boxes[i]
        curr_box.set_distances(boxes[i+1:])
    
    # Extract and sort complete list of distances
    all_pairs = sorted(iterate_distances(boxes), key=lambda b: b[0].distances[b[1]])

    circuit_id_counter = 1
    circuits: dict[int, set[Box]] = dict()
    while len(all_pairs) > 0:
        box_1, box_2 = all_pairs.pop(0)
        if box_1.circuit and box_2.circuit:
            if box_1.circuit != box_2.circuit:
                circuits[circuit_id_counter] = circuits.pop(box_1.circuit) | circuits.pop(box_2.circuit)
                for b in circuits[circuit_id_counter]:
                    b.circuit = circuit_id_counter
                if len(circuits[circuit_id_counter]) == len(boxes):
                    break
                circuit_id_counter += 1
            else:
                continue
        else:
            if exist_circuit := box_1.circuit or box_2.circuit:
                box_1.circuit = exist_circuit
                box_2.circuit = exist_circuit
                circuits[exist_circuit].update((box_1, box_2))
                if len(circuits[exist_circuit]) == len(boxes):
                    break
            else:
                box_1.circuit = circuit_id_counter
                box_2.circuit = circuit_id_counter
                circuits[circuit_id_counter] = {box_1, box_2}
                circuit_id_counter += 1
    
    return box_1.x * box_2.x
    # return reduce(operator.mul, sorted((len(c) for _, c in circuits.items()), reverse=True)[:3], 1)
    # IDEA:
    # - for n times:
    #   - Extract min from all closest distances
    #   - Connect the 2
    #     - handle circuits with ids → when I create a new circuit assign id and have a dict with box → circuit id
    #     - at the end iterate over this dict and extract result
    #   - del from both sides → next iteration this distance won't appear
    #   - 


# raw_lines, n = pathlib.Path("example.txt").read_text().strip().split("\n"), 10
raw_lines, n = pathlib.Path("input.txt").read_text().strip().split("\n"), 1000

result = part1(raw_lines, n)
print(result)
