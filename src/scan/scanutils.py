def first_left_right(pattern):
    """
        Takes in a string as a pattern/, and returns the index of the
        first instance of "L" or "R". Returns -1 if no L/R
    """
    first_L = pattern.find("L")
    first_R = pattern.find("R")

    if first_L == -1 and first_R == -1:
        return -1
    elif first_L == -1:
        return first_R
    elif first_R == -1:
        return first_L

    return first_L if first_L < first_R else first_R


def last_left_right(pattern):
    """
        Takes in a string as a pattern/, and returns the index of the
        first instance of "L" or "R". Assumes input includes at least 1
    """
    last_l = pattern.rfind("L")
    last_r = pattern.rfind("R")

    return last_l if last_l > last_r else last_r


def find_starting_foot(pattern):
    """
        Takes in a string as a pattern/, and returns "L", "R" according
        to which foot starts the run. Returns -1 if there are no L/R
        in the input.
    """
    first_lr = first_left_right(pattern)
    if first_lr == -1:
        return -1

    starting_foot = pattern[first_lr]

    for i in reversed(range(1, first_lr)):
        if pattern[i] != pattern[i-1]:
            starting_foot = "L" if starting_foot == "R" else "R"

    return starting_foot


def ensure_only_step(note):
    """
        Filters a row in chart to ensure that it only contains arrows. This is to
        catch edge cases where hold ends and arrows might be on the same row, or
        even mines and arrows.
        Necessary because the main pattern analysis function only checks for notes
        without mines, hold ends, or holds/rolls in the rows.
    """
    # If not a note, return no note
    if len(note) != 4:
        return "0000"

    # If there is no notes in input, return no note
    for i, char in enumerate(["0", "1", "2", "3", "4", "M"]):
        if i == len(note) and char not in note:
            return "0000"
        elif char in note:
            break

    # put chars of note in a list
    chars = [step for step in note]

    # if there is a hold end, or a mine, remove it
    for i, step in enumerate(chars):
        if step == "3" or step == "M":
            chars[i] = "0"

    return "".join(chars)


def process_mistake_data(data, category_counts, category_key, array_key):
    for measure, datum in data.items():
        for data in datum:
            category_counts[category_key] += 1
            category_counts[array_key].append([data, measure])


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
