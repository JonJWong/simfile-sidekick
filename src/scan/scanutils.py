def first_left_right(pattern):
    """
    Takes in a string pattern and returns the index of the first instance of "L" or "R". 
    Returns -1 if no L/R.
    """
    first_L = pattern.find("L")
    first_R = pattern.find("R")

    return min(first_L, first_R) if first_L != -1 and first_R != -1 else max(first_L, first_R, -1)


def last_left_right(pattern):
    """
    Takes in a string pattern and returns the index of the last instance of "L" or "R". 
    Assumes input includes at least one L/R.
    """
    last_L = pattern.rfind("L")
    last_R = pattern.rfind("R")

    return max(last_L, last_R)


def find_starting_foot(pattern):
    """
    Takes in a string pattern and returns "L" or "R" according to which foot starts the run. 
    Returns -1 if there are no L/R in the input.
    """
    first_lr = first_left_right(pattern)
    
    if first_lr == -1:
        return -1

    starting_foot = pattern[first_lr]

    for i in reversed(range(1, first_lr)):
        if pattern[i] != pattern[i - 1]:
            starting_foot = "L" if starting_foot == "R" else "R"

    return starting_foot


def ensure_only_step(note):
    """
    Filters a row in chart to ensure that it only contains arrows. 
    This is to catch edge cases where hold ends and arrows might be on the same row, or even mines and arrows.
    """
    valid_chars = {"0", "1", "2", "4"}
    chars = [char if char in valid_chars else "0" for char in note]
    return "".join(chars)


def process_mistake_data(data, category_counts, category_key, array_key):
    for measure, datum in data.items():
        for datum_entry in datum:
            category_counts[category_key] += 1
            category_counts[array_key].append([datum_entry, measure])


def is_sweep(pattern):
    sweep_permutations = {'LDURUDL', 'LUDRDUL', 'RDULUDR', 'RUDLDUR'}
    return pattern in sweep_permutations


def fill_mistake_data(data_obj, measure, pattern, pattern_str=None):
    if is_sweep(pattern_str):
        pattern = "Sweep"
        
    if data_obj.get(measure):
        data_obj[measure].append(pattern)
    else:
        data_obj[measure] = [pattern]


def process_mono(data_obj, count_obj, pattern, curr_measure):
    if len(pattern) >= 8:
        sliced = pattern[:-2]
        if sliced.endswith("U") or sliced.endswith("D"):
            sliced += pattern[-2]

        if sliced.endswith("LR") or sliced.endswith("RL"):
            sliced = sliced.rstrip("LR")
            sliced += pattern[len(sliced)]

        count_obj["Mono Notes"] += len(sliced)
        fill_mistake_data(data_obj, curr_measure, len(sliced), sliced)
