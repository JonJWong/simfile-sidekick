import math

def normalize(breakdown):
    breakdown_arr = breakdown.split(" ")

    # first check to see if there are any 24th/32nd note runs
    # if there are, we continue logic, if not, break

    can_normalize = False
    normalize_24ths = False
    normalize_32nds = False

    for b in breakdown_arr:
        if b.find("\\") != -1:
            can_normalize = True
            normalize_24ths = True
        if b.find("=") != -1:
            can_normalize = True
            normalize_32nds = True
            # TODO: check for at least 4 measures?


    if not can_normalize:
        # return the original breakdown
        return breakdown

    normalized_breakdown = []

    if normalize_32nds:
        # normalize to 32nds
        for b in breakdown_arr:
            if b.find("=") != -1:
                # this measure is a 32nd run
                b = b.replace("=", "")
                b = str(math.floor(int(b) * 2))  # floor, incase of decimal, we only count "full" measure runs
                normalized_breakdown.append(b)
            elif b.find("(") != -1:
                # measure is a break
                normalized_breakdown.append(b)
            else:
                # measure is 16th note or 24th note run
                # we need to treat this as a break
                b = b.replace("\\", "")
                normalized_breakdown.append("(" + b + ")")
    elif normalize_24ths:
        # normalize to 24ths
        for b in breakdown_arr:
            if b.find("\\") != -1:
                #this measure is a 24th run
                b = b.replace("\\", "")
                b = str(math.floor(int(b) * 1.5)) # floor, incase of decimal, we only count "full" measure runs
                normalized_breakdown.append(b)
            elif b.find("(") != -1:
                # measure is a break
                normalized_breakdown.append(b)
            else:
                # measure is 16th note run
                # we need to treat this as a break
                normalized_breakdown.append("(" + b + ")")

    prev_measure = None
    this_measure = None
    for i, b in enumerate(normalized_breakdown):

        if b.find("(") != -1:
            # curr measure is break
            this_measure = "break"
        else:
            # curr measure is run
            this_measure = "run"

        if i == 0:
            prev_measure = this_measure
            continue # don't do anything to first element

        if prev_measure == "break" and this_measure == "break":
            prev_val = normalized_breakdown[i-1].replace("(", "").replace(")", "")
            prev_val = int(prev_val)

            this_val = normalized_breakdown[i].replace("(", "").replace(")", "")
            this_val = int(this_val)

            normalized_breakdown[i-1] = ""
            normalized_breakdown[i] = "(" + str(int(prev_val + this_val + 1)) + ")"

        prev_measure = this_measure

    return " ".join(list(filter(None, normalized_breakdown))).strip()