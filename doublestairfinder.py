import io
import sys

# TODO: Refactor so that quantizations/measure lengths are taken into account.
# Right now, microhold streams and spaced out odd quantization streams are not
# checked.

def check_and_replace_mine(row):
    chars = row.split()

    for i, char in enumerate(chars):
        if char == "M":
            chars[i] = "0"

    return "".join(chars)


def find_measure_with_double_stair(dir):
    # Dictionary to help translate into legible sequences
    STEPS = {
        # Steps
        "1000": "L",
        "0100": "D",
        "0010": "U",
        "0001": "R",
        # Holds
        "2000": "L",
        "0200": "D",
        "0020": "U",
        "0002": "R",
        # Rolls
        "4000": "L",
        "0400": "D",
        "0040": "U",
        "0004": "R",
    }

    DIFFICULTIES = [
        "Beginner",
        "Easy",
        "Medium",
        "Hard",
        "Challenge",
        "Edit"
    ]

    OTHER_STEPS = [
        "3000", "0300", "0030", "0003", # Hold/roll end
        "M000", "0M00", "00M0", "000M", # Mine
        "0000"                          # Empty note
    ]

    DBL_STAIRS = [
        "LDURLDUR",
        "LUDRLUDR",
        "RUDLRUDL",
        "RDULRDUL"
    ]

    try:
        with io.open(dir, 'r', encoding='utf8') as file:
            # Open file and split where each row is an element in chart_rows arr
            chart = file.read()
            chart_rows = chart.split("\n")

            measure = 0
            curr_pattern = ""
            curr_difficulty = ""
            description = ""
            printed_diff = ""
            chart_started = False

            # Iterate through the chart_rows array
            for i, row in enumerate(chart_rows):
                # Grab the description, necessary to distinguish edit charts
                if "DESCRIPTION" in row:
                    description = row.split(":")[1][:-1]

                # Grab the current difficulty, necessary to distinguish charts
                for difficulty in DIFFICULTIES:
                    if difficulty in row:
                        curr_difficulty = difficulty


                # Looks for the first empty note, arrow, mine, roll, or hold
                if STEPS.get(row) or row in OTHER_STEPS:
                    chart_started = True

                mineless_row = check_and_replace_mine(row)

                # If the chart has not been found yet, we don't need to continue
                # with our logic yet
                if not chart_started:
                    continue

                # If the chart has been found, and we are crossing difficulties,
                # we need to reset our temporary metadata, as well as flip the
                # chart_started flag
                if row.startswith("//") and chart_started == True:
                    measure = 0
                    curr_pattern = ""
                    curr_difficulty = ""
                    description = ""
                    chart_started = False
                    continue

                # Commas indicate measure endings in .sm and .ssc files
                if row == ",":
                    measure += 1
                    continue

                # Add step to pattern if it's an arrow
                if STEPS.get(mineless_row):
                    curr_pattern += STEPS[mineless_row]
                else:
                    # If current row is a hold/roll end and the previous
                    # row is a step, we should continue iteration without
                    # resetting the current pattern. This accounts for
                    # some microhold stream situations.
                    if "3" in row and STEPS.get(check_and_replace_mine(chart_rows[i-1])) and len(curr_pattern) > 0:
                        continue

                    # If current row is hold/roll end, mine, or empty,
                    # reset current pattern.
                    curr_pattern = ""

                # If our current pattern deviates from double stairs, we want
                # to reset the pattern at the next applicable instance of left
                # or right. This ensures that we are not losing previously
                # counted stairs/beginnings of stairs.
                if not any(dbl_stair.startswith(curr_pattern) for dbl_stair in DBL_STAIRS):
                    # Slices the current pattern at the next left or right.
                    for j in range(1, len(curr_pattern)):
                        if j < len(curr_pattern) and (curr_pattern[j] == "L" or curr_pattern[j] == "R"):
                            curr_pattern = curr_pattern[j:]
                    continue

                # If the current pattern length reaches 8, we have found a
                # double stair, so we reset curr_pattern after printing the
                # metadata.
                if len(curr_pattern) == 8:
                    if curr_difficulty != printed_diff:
                        print("Difficulty: " + curr_difficulty)
                        printed_diff = curr_difficulty
                        
                    if (curr_difficulty == "Edit"):
                        print ("Description: " + description)
                    print("{} found ending in measure {}".format(str(curr_pattern), str(measure)))
                    curr_pattern = ""

            print("Finished checking for double-stairs.")

    except Exception as e:
        print("Error: {}".format(e))
        print("Line {}".format(sys.exc_info()[-1].tb_lineno))

dir = "C:\\Users\\China\\OneDrive\\Desktop\\itgmania\\Songs\\Big Wong\\Russian Roulette\\russianroulette.sm"
# dir = sys.argv[1]
find_measure_with_double_stair(dir)