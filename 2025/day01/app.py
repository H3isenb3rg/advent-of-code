import pathlib


# input_list = pathlib.Path("example1.txt").read_text().strip().split("\n")
input_list = pathlib.Path("input1.txt").read_text().strip().split("\n")
START = 50

curr_pos = START
zeros = 0
for item in input_list:
    direction = 1 if item[0] == "R" else -1
    steps = int(item[1:])

    # Count complete loops
    zeros += steps // 100

    # Move to new position
    steps = steps % 100 # After doing the loops we have the remainder which is the move
    change = direction * steps
    move_result = curr_pos + change
    if curr_pos != 0 and (move_result <= 0 or move_result >= 100):
        zeros += 1

    curr_pos = (move_result) % 100

print(zeros)
