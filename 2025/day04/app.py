import pathlib


# input_list = [list(line) for line in pathlib.Path("example.txt").read_text().strip().split("\n")]
input_list = [list(line) for line in pathlib.Path("input.txt").read_text().strip().split("\n")]

ROLL = "@"
EMPTY = "."
MOVES = [
    (-1,-1),    # NW
    (0,-1),     # N
    (+1,-1),    # NE
    (+1,0),     # E
    (+1,+1),    # SE
    (0,+1),     # S
    (-1,+1),    # SW
    (-1,0)      # W
]
LEN_Y = len(input_list)
LEN_X = len(input_list[0])

def make_move(pos: tuple[int, int], move: tuple[int,int]):
    return (pos[0]+move[0], pos[1]+move[1])

def get_pos(grid: list[list[str]], pos: tuple[int, int]):
    return grid[pos[1]][pos[0]]

def remove_pos(grid: list[list[str]], pos: tuple[int, int]):
    grid[pos[1]][pos[0]] = EMPTY

def is_accessible(grid: list[list[str]], pos: tuple[int,int]):
    if get_pos(grid, pos) == EMPTY:
        return False
    
    # There is a roll in current pos
    count_surrounding = 0
    for move in MOVES:
        new_pos = make_move(pos, move)
        if new_pos[0] < 0 or new_pos[1] < 0 or new_pos[0] >= LEN_Y or new_pos[1] >= LEN_X:
            continue
        if get_pos(grid, new_pos) == ROLL:
            count_surrounding+=1
    
    return count_surrounding < 4

accessible_rolls = 0
rolls_pos = set()
for y in range(LEN_Y):
    for x in range(LEN_X):
        curr_pos = (x,y)
        if get_pos(input_list, curr_pos) == ROLL:
            rolls_pos.add(curr_pos)
        if is_accessible(input_list, curr_pos):
            accessible_rolls+=1
            remove_pos(input_list, curr_pos)
            rolls_pos.remove(curr_pos)

old_accessible_rolls = 0
while accessible_rolls > old_accessible_rolls:
    old_accessible_rolls = accessible_rolls
    pos_tb_checked = rolls_pos.copy()
    for roll_pos in pos_tb_checked:
        if is_accessible(input_list, roll_pos):
            accessible_rolls+=1
            remove_pos(input_list, roll_pos)
            rolls_pos.remove(roll_pos)
    


print(accessible_rolls)
