import os
from .day5.solver import Day5Solver as CurrSolver

latest = max(int(dir.replace("day", "")) for dir in next(os.walk(os.path.dirname(__file__)))[1] if dir.replace("day", "").isdigit())
latest_dir = os.path.join(os.path.dirname(__file__), f"day{latest}")

curr_solver = CurrSolver(latest_dir)

print(f"First puzzle Example solution -> {curr_solver.solve_first(is_example=True)}")
print(f"First puzzle solution -> {curr_solver.solve_first(is_example=False)}")
print(f"Second puzzle Example solution -> {curr_solver.solve_second(is_example=True)}")
print(f"Second puzzle solution -> {curr_solver.solve_second(is_example=False)}")