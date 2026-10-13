from __future__ import annotations
import pathlib
import time


class Gate:
    name: str
    connections: set[Gate]

    def __init__(self, name: str, connections: set[Gate] = set()) -> None:
        self.name = name
        self.connections = connections
    
    def __repr__(self) -> str:
        return self.name
    
    def __hash__(self) -> int:
        return self.name.__hash__()

    @staticmethod
    def generate_gates_net(raw_gates: list[str], start_gate: str):
        gates: dict[str, tuple[Gate, set[str]]] = dict()
        out_gate = Gate("out")
        gates["out"] = (out_gate, set())
        fft_gate = None
        dac_gate = None

        for line in raw_gates:
            curr, raw_connections = line.split(":")
            curr = curr.strip()
            curr_gate = Gate(curr)
            connections = set(raw_connections.strip().split())
            gates[curr] = (curr_gate, connections)
            if curr_gate.name == "fft":
                fft_gate = curr_gate
            elif curr_gate.name == "dac":
                dac_gate = curr_gate
        
        for gate, connections in gates.values():
            gate.connections = {gates[c][0] for c in connections}
        
        return gates[start_gate][0], fft_gate, dac_gate
    

class Net:
    svr_gate: Gate
    cached_paths_to_out: dict[tuple[Gate, str], int]
    
    def __init__(self, svr_gate: Gate) -> None:
        self.svr_gate = svr_gate
        self.cached_paths_to_out = dict()
    
    def count_paths(self, start: Gate, end: str, visited_nodes: set[Gate]):
        if (start, end) in self.cached_paths_to_out:
            return self.cached_paths_to_out[start, end]
        result = self._count_paths(start, end, visited_nodes)
        self.cached_paths_to_out[start, end] = result
        return result

    def _count_paths(self, start: Gate, end: str, visited_nodes: set[Gate]):
        if any(c.name == end for c in start.connections):
            return 1
        
        result = 0
        for conn in start.connections:
            if conn in visited_nodes:
                continue  # Avoid Loops
            
            visited_nodes = visited_nodes | {conn}
            result += self.count_paths(conn, end, visited_nodes)
        
        return result

        


def part1(input_lines: list[str]):
    svr_gate, _, _ = Gate.generate_gates_net(input_lines, "you")
    net = Net(svr_gate)
    return net.count_paths(svr_gate, "out", set())

def part2(input_lines: list[str]):
    svr_gate, fft_gate, dac_gate = Gate.generate_gates_net(input_lines, "svr")
    if not dac_gate or not fft_gate:
        raise ValueError("Should not happen")
    net = Net(svr_gate)
    count = 0

    dac_fft_count = net.count_paths(dac_gate, fft_gate.name, set())
    fft_dac_count = net.count_paths(fft_gate, dac_gate.name, set())
    dac_out_count = net.count_paths(dac_gate, "out", set()) if fft_dac_count > 0 else 0
    fft_out_count = net.count_paths(fft_gate, "out", set()) if dac_fft_count > 0 else 0

    if fft_dac_count > 0 and dac_out_count > 0:
        count += net.count_paths(svr_gate, fft_gate.name, set())
        count *= fft_dac_count
        count *= dac_out_count
    
    if dac_fft_count > 0 and fft_out_count > 0:
        count += net.count_paths(svr_gate, dac_gate.name, set())
        count *= dac_fft_count
        count *= fft_out_count

    return count


if __name__ == "__main__":
    # input_list = pathlib.Path("example2.txt").read_text().strip().split("\n")
    input_list = pathlib.Path("input.txt").read_text().strip().split("\n")

    start_time = time.time()
    # result = part1(input_list)
    result = part2(input_list)
    print(f"Exec time: {time.time() - start_time}s")
    print(result)
