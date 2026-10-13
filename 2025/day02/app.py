import pathlib


# input_list = pathlib.Path("example.txt").read_text().strip().replace("\n", "").split(",")
input_list = pathlib.Path("input.txt").read_text().strip().replace("\n", "").split(",")


def parse_range(raw: str):
    start, finish = raw.split("-", 1)
    start = int(start)
    finish = int(finish)
    return range(start, finish+1)


def is_invalid_pt1(id_str: str):
    if len(id_str) <= 1 or len(id_str) % 2 != 0:
        return False
    
    first_half = id_str[:len(id_str)//2]
    last_half = id_str[len(id_str)//2:]

    return first_half == last_half


def is_invalid(id_str: str):
    if len(id_str) <= 1:
        return False
    
    for divisor in range(2, len(id_str)+1):
        if len(id_str) % divisor != 0:
            continue

        curr_slice = id_str[:len(id_str)//divisor]
        if curr_slice*divisor == id_str:
            return True

    return False


invalid = []
checked_invalid = set()
checked_valid = set()

for raw_range in input_list:
    for curr_id in parse_range(raw_range):
        if curr_id in checked_invalid:
            invalid.append(curr_id)
        elif curr_id in checked_valid:
            continue
        elif is_invalid(str(curr_id)):
            invalid.append(curr_id)
            checked_invalid.add(curr_id)
        else:
            checked_valid.add(curr_id)

print(sum(invalid))

