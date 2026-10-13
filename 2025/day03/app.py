import pathlib


# input_list = pathlib.Path("example.txt").read_text().strip().split("\n")
input_list = pathlib.Path("input.txt").read_text().strip().split("\n")


def find_largest(input_str: str, reserved: int):
    max_number = max(input_str[:-reserved if reserved else None])
    return max_number, input_str.find(max_number)


values = []
for bank in input_list:
    curr_bank = bank
    curr_number = ""
    for reserved in range(11, -1, -1):
        number, number_i = find_largest(curr_bank, reserved)
        curr_bank = curr_bank[number_i+1:]
        curr_number += number
    values.append(int(curr_number))

print(*values, sep=" + ")
print("--------------------------------")
print(sum(values))

# 987654321111 + 811111111119 + 434234234278 + 888911112111 = 3121910778619
# 987654321111 + 811111111119 + 434234234278 + 888911112111