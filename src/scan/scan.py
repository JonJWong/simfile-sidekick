# -*- coding: utf-8 -*-
"""
Searches for .sm files and creates a database of information based on their contents.

This is a tool used to scan StepMania (.sm) files
<https://www.stepmania.com>. StepMania is a cross-platform rhythm video game and engine.
This tool is intended only for "Dance" game files and will only scan "dance-single"
charts. It creates a database of information from the scanned files. The database
contains information such as a song's length, BPM, density breakdown, and pattern
analysis. The purpose of this file is to be used in conjunction with the Discord bot.py
program, to allow users to search for information from within Discord.

This is free and unencumbered software released into the public domain. For more
information, please refer to the LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst for the Dickson City Heroes and Stamina Nation.
"""

from helpers import BreakdownHelper as bh
from helpers import GeneralHelper as gh
from helpers import Normalize as normalizer
from helpers import ImageHelper as ih
from objects import NotesInfo as ni, ChartInfo as ci, FileInfo as fi, PatternInfo as pi
from helpers import Test as test
from helpers import VerboseHelper as vh
from enums.RunDensity import RunDensity
from pathlib import Path
from tinydb import TinyDB
from tinydb.storages import JSONStorage, MemoryStorage
from tinydb.middlewares import CachingMiddleware
import getopt
import glob
import logging
import math
import os
import re
import statistics
import string
import sys

from .scanconstants import SHORT_OPTIONS, LONG_OPTIONS, REBUILD, VERBOSE, DIRECTORY, MEDIA_REMOVE,\
    UNIT_TEST, CSV, NL_REG, NO_NOTES_REG, ANY_NOTES_REG, LOG_TIMESTAMP, LOG_FORMAT, UNITTEST_FOLDER,\
    DATABASE_NAME, LOGFILE_NAME, STEP_TO_DIR, LEFT_CANDLES, RIGHT_CANDLES, COMBINED_PATTERN,\
    LEFT_ANCHOR_PATTERN, DOWN_ANCHOR_PATTERN, UP_ANCHOR_PATTERN, RIGHT_ANCHOR_PATTERN, DBL_STAIRS,\
    DBL_STEPS, BOXES
from .regexfinds import findall_with_regex_dotall, findall_with_regex, find_with_regex_dotall, find_with_regex
from .dbhelpers import load_md5s_into_cache, database_to_csv, add_to_database
from .scanutils import last_left_right, find_starting_foot, ensure_only_step, process_mistake_data, fill_mistake_data, process_mono


def adjust_total_break(total_break, measures):
    """Adjust the "total break" statistic to remove unused measures.

    This will adjust the "total break" statistic to account for songs that have a long fadeout, fadeout mine, or
    charts that do not end in a stream. This is because we do not consider notes after the last stream as a break.
    The "total break" is used to denote the measures of break between the first and last run."""
    if total_break > 0:
        for i, measure in enumerate(reversed(measures)):
            # Since we're navigating backwards in the chart, we want to break at the first full run we see
            lines = measure.strip().split("\n")
            if len(lines) < 16:  # measure only contains 4th or 8th notes
                total_break -= 1
                continue
            notes_in_measure = len(findall_with_regex(measure, ANY_NOTES_REG))
            if notes_in_measure < 16:  # measure is not a full run
                total_break -= 1
                continue
            break
    return total_break


def find_current_bpm(measure, bpms):
    """Finds the current BPM in a given measure of a song."""
    for bpm in bpms:
        if float(bpm[0]) <= measure:
            return bpm[1]


def new_pattern_analysis(measure_obj):
    """
        Refactored pattern analysis. Considering how niche microholds are in runs,
        I decided to ignore them.

        #TODO: Consider microholds in runs
            Move Anchor and candle calculation into mono calculation iteration
            Add doublestep, jump detection

        Parameters
        -----------
        measure_obj:
            key: int
            val: arr

        Measure_obj contains all the measures of run in a chart, where the key is the
            measure numbner, and the value is an array containing all the notes.
            Notes are in string format.

            ex. 1: ['1000', '0100', '0010', '0001']
    """

    # Initialize counters
    category_counts = {
        "Left Candles": 0,
        "Right Candles": 0,
        "Total Candles": 0,
        "Left Anchors": 0,
        "Down Anchors": 0,
        "Up Anchors": 0,
        "Right Anchors": 0,
        "Mono Notes": 0,
        "Mono Percent": 0.0,
        "Double Stairs Count": 0,
        "Doublesteps Count": 0,
        "Double Stairs Array": [],
        "Doublesteps Array": [],
        "Jumps Count": 0,
        "Jumps Array": [],
        "Mono Count": 0,
        "Mono Array": [],
        "Box Count": 0,
        "Box Array": []
    }

    total_notes_in_runs = 0

    curr_run = ""
    prev_measure = None
    most_recent_starting_measure = None

    def __analyze(run, quantization=16):
        """
        Method to find Anchors and Candles via regex, double stairs and double
        steps via iterative string matching, and mono through iteration paying
        attention to direction changes based on which foot hits the U/D arrow.

        Finds all the double stairs/doublesteps in a run, and notates them with
        their measure.

        Does not return anything, but modifies a `nonlocal category_counts`
        variable, which contains data pertinent to the patterning of a chart.

        Parameters
        -----------
        Input: string
            Takes in a string where each character denotes an arrow in the run.
            ex. "LDURLUDRLRUDL"

        Output: None
        """
        nonlocal category_counts, total_notes_in_runs, curr_run, most_recent_starting_measure

        double_stair_data = {}
        doublesteps_data = {}
        jumps_data = {}
        mono_data = {}
        box_data = {}

        # - - - - - ANCHOR FINDER - - - - -
        # Uses regex matching like the previous method
        # TODO: Use recursive algorithm in step iteration
        matches = re.findall(COMBINED_PATTERN, run)
        for match in matches:
            if re.search(LEFT_ANCHOR_PATTERN, match):
                category_counts["Left Anchors"] += 1
            elif re.search(DOWN_ANCHOR_PATTERN, match):
                category_counts["Down Anchors"] += 1
            elif re.search(UP_ANCHOR_PATTERN, match):
                category_counts["Up Anchors"] += 1
            elif re.search(RIGHT_ANCHOR_PATTERN, match):
                category_counts["Right Anchors"] += 1

        # - - - - - CANDLE FINDER - - - - -
        # Candles are relatively straightforward, if any of those 4 candle
        # variants exist, then it is a candle.
        category_counts["Left Candles"] += sum(
            run.count(pattern) for pattern in LEFT_CANDLES)
        category_counts["Right Candles"] += sum(
            run.count(pattern) for pattern in RIGHT_CANDLES)

        current_foot = None
        prev_direction = None
        curr_direction = None
        mono_pattern = ""
        ds_pattern = ""
        jumping = False
        no_lr = False
        amt_to_subtract = 0

        starting_foot = find_starting_foot(run)
        # If the starting foot can't be found, the entire run is U/D
        # so we mark the entire run as mono.
        if starting_foot == -1:
            category_counts["Mono Notes"] += len(run)
            total_notes_in_runs += len(run)
            no_lr = True

        current_foot = starting_foot

        # - - - - - RUN ITERATION LOOP - - - - -
        # One step at a time.
        for i, curr_step in enumerate(run):
            curr_measure = most_recent_starting_measure + \
                math.floor((i + 1 - amt_to_subtract) / quantization)
            # - - - - - JUMP DETECTION - - - - -
            # If there is a jump we need to reset the direction the player is facing
            # on the next step, since it is most likely ambiguous.
            if curr_step == "[" and not jumping:
                jump_end_idx = run.find("]", i)
                jump_str = run[i + 1:jump_end_idx]
                jumping = True
                amt_to_subtract += jump_end_idx - i
                current_foot, curr_direction, mono_pattern, dbl_stair_pattern = (
                    None, None, "", None)
                fill_mistake_data(jumps_data, curr_measure, jump_str)
            elif curr_step == "]":
                if jumping:
                    jumping = False
                    continue

            if not no_lr:
                total_notes_in_runs += 1

            if jumping:
                continue

            # - - - - - DOUBLESTEP FINDER - - - - -
            # There are two types of doublesteps, repeated arrows "DD"
            # and accidents like L"UR"DL. Thanks StoryTime
            # Calculate the current measure based on how far in the run we are
            # added to the starting measure number of the run
            # checks for a double-step pattern at every index of the run
            # currently being iterated on.
            # TODO: improve runtime complexity if possible? Integrate into mono
            # detection?
            for pattern in DBL_STEPS:
                if run.startswith(pattern, i):
                    amt_to_add = math.floor(
                        (i + len(pattern) - 1) / quantization)
                    if i + len(pattern) - 1 >= len(run):
                        dblstep_measure = most_recent_starting_measure + 1
                    else:
                        dblstep_measure = most_recent_starting_measure + amt_to_add

                    fill_mistake_data(doublesteps_data, dblstep_measure,
                                      pattern)

            # - - - - - BOX FINDER - - - - -
            # Uses same logic as doublesteps, but with boxes.
            for pattern in BOXES:
                if run.startswith(pattern, i):
                    fill_mistake_data(box_data, curr_measure, pattern)

            # Since there can't be double stairs or mono if there are no l/R
            #  notes, we can go ahead and skip the rest of the logic
            if no_lr:
                continue

            # - - - - - MONO ANALYSIS - - - - -
            # switch feet every step unless it's a doublestep
            if i != 0:
                prev_step = run[i - 1]
                if prev_step != curr_step:
                    current_foot = "L" if current_foot == "R" else "R"
                else:
                    current_foot = find_starting_foot(run[i + 1:])
                    process_mono(mono_data, category_counts, mono_pattern,
                                 curr_measure)

            # Add step to pattern
            mono_pattern += curr_step
            ds_pattern += curr_step

            prev_direction = curr_direction
            # the foot on the U/D determines which direction we're facing
            if current_foot == "L":
                if curr_step == "D":
                    curr_direction = "L"
                elif curr_step == "U":
                    curr_direction = "R"
            if current_foot == "R":
                if curr_step == "D":
                    curr_direction = "R"
                elif curr_step == "U":
                    curr_direction = "L"

            # Check for directional changes, if the direction changed, and the
            # mono_pattern string is longer than 6 notes, we add it to the mono
            # count.
            if prev_direction != curr_direction:
                process_mono(mono_data, category_counts, mono_pattern,
                             curr_measure)
                last_lr = last_left_right(mono_pattern)
                mono_pattern = mono_pattern[last_lr:]

            # - - - - - DOUBLE STAIR FINDER - - - - -
            # If our ds_pattern deviates from double stairs, we want
            # to reset the pattern at the next applicable instance of left
            # or right. This ensures that we are not losing previously
            # counted stairs/beginnings of stairs.
            # This only finds the first instance of double stairs, and quad
            # stairs will count as 2 entries.
            if not any(
                    dbl_stair.startswith(ds_pattern)
                    for dbl_stair in DBL_STAIRS):
                # Slices the current pattern at the next left or right.
                for j in range(1, len(ds_pattern)):
                    if j < len(ds_pattern) and (ds_pattern[j] == "L"
                                                or ds_pattern[j] == "R"):
                        ds_pattern = ds_pattern[j:]
                continue

            # If the ds_pattern length reaches 8, we have found a
            # double stair, so we reset ds_pattern after printing the
            # metadata.
            if len(ds_pattern) == 8:
                dbl_stair_pattern = ds_pattern[:4]

                fill_mistake_data(double_stair_data, curr_measure,
                                  dbl_stair_pattern)

                ds_pattern = ""

        # - - - - - ITERATION END - - - - -

        # Process box_data
        process_mistake_data(box_data, category_counts, "Box Count",
                             "Box Array")

        # Process double_stair_data
        process_mistake_data(double_stair_data, category_counts,
                             "Double Stairs Count", "Double Stairs Array")

        # Process doublesteps_data
        process_mistake_data(doublesteps_data, category_counts,
                             "Doublesteps Count", "Doublesteps Array")

        # Process jump_data
        process_mistake_data(jumps_data, category_counts, "Jumps Count",
                             "Jumps Array")

        # Process mono_data
        process_mistake_data(mono_data, category_counts, "Mono Count",
                             "Mono Array")

    def __populate(notes_in_measure):
        nonlocal curr_run
        for note in notes_in_measure:
            curr_run += STEP_TO_DIR[ensure_only_step(note)]

    def __reset(measure):
        nonlocal curr_run, prev_measure, most_recent_starting_measure
        curr_run = ""
        most_recent_starting_measure = measure
        prev_measure = measure

    # we want to get all the runs isolated so we can check each of them for
    # patterns. We also count the total notes within runs for mono calculation.
    for i, (measure_num, notes_in_measure) in enumerate(measure_obj.items()):
        quantization = len(notes_in_measure)
        if i == 0 or measure_num - prev_measure > 1:
            # Analyze and reset if it's the first measure or a gap is detected.
            if i != 0:
                __analyze(curr_run, quantization)
                __reset(measure_num)
            most_recent_starting_measure = measure_num
            curr_run = ""

        # Populate notes for the current measure.
        __populate(notes_in_measure)

        if i == len(measure_obj) - 1:
            # Analyze if it's the last measure.
            __analyze(curr_run, quantization)

        prev_measure = measure_num

    if total_notes_in_runs == 0:
        total_notes_in_runs = 1

    category_counts["Mono Percent"] = (
        (category_counts["Mono Notes"] / total_notes_in_runs) * 100)

    category_counts["Total Candles"] = (category_counts["Left Candles"] +
                                        category_counts["Right Candles"])

    analysis = pi.PatternInfo(
        category_counts["Left Candles"], category_counts["Right Candles"],
        category_counts["Total Candles"], category_counts["Mono Percent"],
        category_counts["Left Anchors"], category_counts["Down Anchors"],
        category_counts["Up Anchors"], category_counts["Right Anchors"],
        category_counts["Double Stairs Count"],
        category_counts["Double Stairs Array"],
        category_counts["Doublesteps Count"],
        category_counts["Doublesteps Array"], category_counts["Jumps Count"],
        category_counts["Jumps Array"], category_counts["Mono Count"],
        category_counts["Mono Array"], category_counts["Box Count"],
        category_counts["Box Array"])

    return analysis


def get_simplified(breakdown, partially):
    """Takes the detailed breakdown and creates a simplified breakdown.

    Function that generates both the "Partially Simplified" and "Simplified Breakdown" sections. It uses the separators
    in get_separator function.

    The "Partially Simplified" will use all symbols. Runs that are separated by a 1 measure break will be grouped
    together and marked with a *.

    The "Simplified Breakdown" won't use the "-" symbol. Runs that are separated by a <= 4 measure break will be grouped
    together and marked with a *.

    Parameters
    -----------
    breakdown:
        The detailed breakdown.
    partially:
        A boolean. If true will generate the "Partially Simplified" breakdown. False will generate the "Simplified
        Breakdown" section.
    """
    breakdown = breakdown.split(" ")
    simplified = breakdown
    previous_measure = RunDensity.Break
    current_measure = RunDensity.Break
    small_break = False
    for i, b in enumerate(breakdown):
        if re.search(r"[=]", b):
            current_measure = RunDensity.Run_32
        elif re.search(r"[\\]", b):
            current_measure = RunDensity.Run_24
        elif re.search(r"[~]", b):
            current_measure = RunDensity.Run_20
        elif re.search(r"[()]", b):
            if partially:
                current_measure = RunDensity.Break
                b = bh.get_separator(
                    int(bh.remove_all_breakdown_chars(simplified[i])))
            else:
                if int(bh.remove_all_breakdown_chars(b)) <= 4:
                    b = bh.remove_all_breakdown_chars(b)
                    small_break = True
                else:
                    b = bh.get_separator(
                        int(bh.remove_all_breakdown_chars(simplified[i])))
                    current_measure = RunDensity.Break
        else:
            current_measure = RunDensity.Run_16

        if current_measure == previous_measure and i > 0:
            previous_value = bh.remove_all_breakdown_chars(simplified[i - 1])
            b = bh.remove_all_breakdown_chars(b)
            simplified[i - 1] = ""
            if small_break and simplified:
                if current_measure == RunDensity.Run_32:
                    simplified[i] = "=" + \
                        str(int(previous_value) + int(b) - 1) + "=*"
                elif current_measure == RunDensity.Run_24:
                    # Needs to be double escaped, as Discord will parse "\*" as just "*"
                    simplified[i] = "\\" + \
                        str(int(previous_value) + int(b) - 1) + "\\\\*"
                elif current_measure == RunDensity.Run_20:
                    simplified[i] = "~" + \
                        str(int(previous_value) + int(b) - 1) + "~*"
                else:
                    simplified[i] = str(int(previous_value) + int(b) - 1) + "*"
                small_break = False
            else:
                if current_measure == RunDensity.Run_32:
                    simplified[i] = "=" + \
                        str(int(previous_value) + int(b) - 1) + "=*"
                    simplified[i] = "=" + \
                        str(int(previous_value) + int(b) + 1) + "=*"
                elif current_measure == RunDensity.Run_24:
                    # Needs to be double escaped, as Discord will parse "\*" as just "*"
                    simplified[i] = "\\" + \
                        str(int(previous_value) + int(b) - 1) + "\\\\*"
                    simplified[i] = "\\" + \
                        str(int(previous_value) + int(b) + 1) + "\\\\*"
                elif current_measure == RunDensity.Run_20:
                    simplified[i] = "~" + \
                        str(int(previous_value) + int(b) - 1) + "~*"
                    simplified[i] = "~" + \
                        str(int(previous_value) + int(b) + 1) + "~*"
                else:
                    simplified[i] = str(int(previous_value) + int(b) - 1) + "*"
                    simplified[i] = str(int(previous_value) + int(b) + 1) + "*"
        else:
            simplified[i] = b

        previous_measure = current_measure

    return " ".join(filter(None, simplified))


def get_density_and_breakdown(chartinfo, measures, bpms):
    """Retrieves generic chart info, and generates the detailed breakdown and density.

    Generates the number of notes, holds, jumps, etc. in a chart, and generates the detailed breakdown. The density
    is also calculated here and used to generate the density graph later.

    Parameters
    -----------
    measures:
        An array, each entry is 1 measure of the chart.
    bpms:
        A 2D array, each entry contains the BPM and the measure it changes to that BPM
    """
    density = []
    breakdown = ""
    measures_of_run = [0] * 5
    previous_measure = RunDensity.Break
    current_measure = RunDensity.Break
    hit_first_run = False
    length = 0
    note_count = 0
    holds = 0
    jumps = 0
    mines = 0
    hands = 0
    rolls = 0
    holding = 0
    total_stream = 0
    total_break = 0
    measures_and_steps = {}

    for i, measure in enumerate(measures):
        bpm = find_current_bpm(i * 4, bpms)
        lines = measure.strip().split("\n")
        measure_density = 0
        for line in lines:
            if re.search(r"[124]", line):
                measure_density += 1
                note_count += 1
            holds += len(re.findall(r"[2]", line))
            mines += len(re.findall(r"[M]", line))
            rolls += len(re.findall(r"[4]", line))

            notes_on_line = len(re.findall(r"[124]", line))
            if notes_on_line >= 2:
                jumps += 1

            # - - - HANDS CALCULATION - - -
            # How many 1s (notes), 2s (initial holds), or 4s (initial rolls) are
            # on the current line?
            notes_on_line = len(re.findall(r"[124]", line))
            if notes_on_line >= 3:
                # If more than 3, hands++
                hands += 1
            # What if we started holding a note last measure, and a jump occurs?
            if holding == 1 and notes_on_line >= 2:
                hands += 1
            # What if we're holding two notes and an arrow appears?
            if holding == 2 and notes_on_line >= 1:
                hands += 1
            # What if we're holding 3 notes and an arrow appears?
            if holding == 3 and notes_on_line >= 1:
                hands += 1
            # Holding computation is done last, as it doesn't affect the current line
            # since current line, if jump or roll, would be 2 or 4 respectively.
            for j, char in enumerate(
                    line):  # For each of the 4 possible arrows
                if char == "2" or char == "4":  # If arrow is hold or roll
                    # We are currently holding an arrows
                    holding += 1
                if char == "3":
                    # We have let go of a hold or roll
                    holding -= 1
            # - - - END HANDS CALCULATION - - -

        nps = ((float(bpm) / 4) * measure_density) / 60
        density.append(nps)

        length += (4 / float(bpm)) * 60

        # We don't want to count measures of break before first run
        if measure_density >= 16:
            hit_first_run = True
        if not hit_first_run:
            continue

        # This creates a chart of only the run sections, that will be used to run pattern analysis against
        if measure_density >= 16:
            m = measure
            if len(re.findall(re.compile(NO_NOTES_REG),
                              measure)) >= measure_density:
                # We will hop into here if there are just as many or more "blank lines" (0000) than actual notes.
                # This tends to happen if a chart was auto-gen'ed or other manual manipulations of the file occured,
                # as Stepmania (AFAIK) usually optimizes this.
                # e.g. if a measure contains only 16th notes, SM will not put 0000 for every other 32nd note.
                # This is just a failsafe to capture that scenario.
                m = re.sub(re.compile(NO_NOTES_REG + NL_REG), "", measure)
            index = m.rfind("\n")
            m = m[:index]

            # REFACTOR BEGIN
            m = [note for note in m.split("\n") if note != ""]
            measures_and_steps[i] = m

        if measure_density >= 32:
            measures_of_run[RunDensity.Run_32.value] += 1
            current_measure = RunDensity.Run_32
            total_stream += 1
        elif measure_density >= 24:
            measures_of_run[RunDensity.Run_24.value] += 1
            current_measure = RunDensity.Run_24
            total_stream += 1
        elif measure_density >= 20:
            measures_of_run[RunDensity.Run_20.value] += 1
            current_measure = RunDensity.Run_20
            total_stream += 1
        elif measure_density >= 16:
            measures_of_run[RunDensity.Run_16.value] += 1
            current_measure = RunDensity.Run_16
            total_stream += 1
        else:
            measures_of_run[RunDensity.Break.value] += 1
            current_measure = RunDensity.Break
            total_break += 1

        if current_measure != previous_measure:
            if previous_measure == RunDensity.Run_32:
                breakdown += "=" + \
                    str(measures_of_run[RunDensity.Run_32.value]) + "= "
                measures_of_run[RunDensity.Run_32.value] = 0
            elif previous_measure == RunDensity.Run_24:
                breakdown += "\\" + \
                    str(measures_of_run[RunDensity.Run_24.value]) + "\\ "
                measures_of_run[RunDensity.Run_24.value] = 0
            elif previous_measure == RunDensity.Run_20:
                breakdown += "~" + \
                    str(measures_of_run[RunDensity.Run_20.value]) + "~ "
                measures_of_run[RunDensity.Run_20.value] = 0
            elif previous_measure == RunDensity.Run_16:
                breakdown += str(
                    measures_of_run[RunDensity.Run_16.value]) + " "
                measures_of_run[RunDensity.Run_16.value] = 0
            elif previous_measure == RunDensity.Break:
                if measures_of_run[RunDensity.Break.value] > 1:
                    breakdown += "(" + \
                        str(measures_of_run[RunDensity.Break.value]) + ") "
                measures_of_run[RunDensity.Break.value] = 0

        previous_measure = current_measure

    # This will handle if the last note of the song is part of a run
    if measures_of_run[RunDensity.Run_32.value] > 0:
        breakdown += "=" + str(measures_of_run[RunDensity.Run_32.value]) + "= "
    elif measures_of_run[RunDensity.Run_24.value] > 0:
        breakdown += "\\" + \
            str(measures_of_run[RunDensity.Run_24.value]) + "\\ "
    elif measures_of_run[RunDensity.Run_20.value] > 0:
        breakdown += "~" + str(measures_of_run[RunDensity.Run_20.value]) + "~ "
    elif measures_of_run[RunDensity.Run_16.value] > 0:
        breakdown += str(measures_of_run[RunDensity.Run_16.value]) + " "

    chartinfo.patterninfo = new_pattern_analysis(measures_and_steps)

    minutes = length // 60
    seconds = length % 60
    length = str(int(minutes)) + "m " + str(int(seconds)) + "s"

    total_break = adjust_total_break(total_break, measures)

    notesinfo = ni.NotesInfo(note_count, jumps, holds, mines, hands, rolls)
    chartinfo.notesinfo = notesinfo
    chartinfo.length = length
    chartinfo.total_stream = total_stream
    chartinfo.total_break = total_break

    return density, breakdown.strip(), chartinfo


def parse_chart(chart, fileinfo, db, cache=None):
    """Retrieves and sets chart information.

    Grabs the charts step artist, difficulty, rating, and actual chart data. Calls most other functions in this file to
    handle pattern recognition and density breakdown. Calls the function to generate the density graph, and finally
    calls the function to save the chart info to the database.
    """

    metadata = chart.split(":")

    charttype = metadata[0].strip().replace(":", "")  # dance-single, etc.
    stepartist = metadata[1].strip().replace(":", "")
    difficulty = metadata[2].strip().replace(":", "")
    rating = metadata[3].strip().replace(":", "")
    chart = gh.remove_comments(metadata[5])

    del metadata

    if charttype != "dance-single":
        return  # we only want single charts

    if chart.strip() == ";":
        logging.info("The {} {} chart for {} is empty. Skipping.".format(
            difficulty, rating, fileinfo.title))
        return  # empty chart

    if not findall_with_regex(chart, ANY_NOTES_REG):
        logging.info("The {} {} chart for {} is empty. Skipping.".format(
            difficulty, rating, fileinfo.title))
        return  # chart only contains 0's

    measures = findall_with_regex(chart, r"[01234MF\s]+(?=[,|;])")

    chartinfo = ci.ChartInfo(fileinfo, stepartist, difficulty, rating,
                             measures)

    if measures == -1:
        logging.warning(
            "Unable to parse the {} {} chart for {}. Skipping.".format(
                difficulty, rating, fileinfo.title))
        return

    density, breakdown, chartinfo = get_density_and_breakdown(
        chartinfo, measures, fileinfo.bpms)
    partially_simplified = get_simplified(breakdown, True)
    simplified = get_simplified(breakdown, False)

    if chartinfo.total_stream:
        should_normalize = normalizer.if_should_normalize(
            breakdown, chartinfo.total_stream)
        if should_normalize != RunDensity.Run_16:
            bpm_to_use = normalizer.get_best_bpm_to_use(
                fileinfo.min_bpm, fileinfo.max_bpm, chartinfo.median_nps,
                fileinfo.displaybpm)
            normalized_breakdown = normalizer.normalize(
                breakdown, bpm_to_use, should_normalize)
            if normalized_breakdown != breakdown:
                chartinfo.normalized_breakdown = normalized_breakdown

    chartinfo.breakdown = breakdown
    chartinfo.partial_breakdown = partially_simplified
    chartinfo.simple_breakdown = simplified

    chartinfo.max_nps = max(density)
    chartinfo.median_nps = statistics.median(density)

    fileinfo.chartinfo = chartinfo

    ih.create_and_save_density_graph(list(range(0, len(measures))), density,
                                     fileinfo.chartinfo.graph_location)
    add_to_database(fileinfo, db, cache)


def parse_file(db, filename, folder, pack, hide_artist_info, cache=None):
    """Parses through a .sm file and separates charts."""
    file = open(filename, "r", errors="ignore")
    data = file.read()

    if not hide_artist_info:
        title = find_with_regex(data, r"#TITLE:(.*);")
        subtitle = find_with_regex(data, r"#SUBTITLE:(.*);")
        artist = find_with_regex(data, r"#ARTIST:(.*);")
    else:
        title = "*Hidden*"
        subtitle = ""
        artist = "*Hidden*"

    bpms = find_with_regex_dotall(data, r"#BPMS:(.*?)[;]+?")
    if bpms == -1:
        logging.warning(
            "BPM for file \"{}\" is not readable. Skipping.".format(filename))
        return
    else:
        bpms = bpms.split(",")
        temp = []
        for bpm in bpms:
            if "#" in bpm:
                # Some BPMs are missing a trailing ; (30MIN HARDER in Cirque du Beast)
                bpm = bpm.split("#", 1)[0]
                logging.warning(
                    "BPM for file \"{}\" is missing semicolon. Handled and continuing."
                    .format(filename))
            # Quick way to remove non-printable characters that, for whatever reason,
            # exist in a few .sm files (Oceanlab Megamix)
            old_bpm = bpm
            bpm = "".join(filter(lambda c: c in string.printable, bpm))
            if old_bpm != bpm:
                logging.warning(
                    "BPM for file \"{}\" contains non-printable characters. Handled and continuing."
                    .format(filename))
            bpm = bpm.strip().split("=")
            temp.insert(0, bpm)
        bpms = temp
    displaybpm = find_with_regex(data, r"#DISPLAYBPM:(.*);")
    charts = findall_with_regex_dotall(data, r"#NOTES:(.*?);")

    if charts == -1:
        logging.warning(
            "Unable to parse chart(s) data for \"{}\". Skipping.".format(
                filename))
        return
    else:
        for i, chart in enumerate(charts):
            sanity_check = chart.split("\n", 6)
            if len(sanity_check) != 7:
                logging.warning(
                    "Unable to parse chart(s) data for \"{}\". Attempting to handle..."
                    .format(filename))
                # There's something in this file that is causing the regex to not parse properly.
                # Usually a misplaced ; instead of a :
                # This is a quick and dirty attempt to salvage it.
                # e.g. SHARPNELSTREAMZ v2 I'm a Maid has this issue
                chart = chart.splitlines()
                problem_line = chart[len(chart) - 1]
                substring_index = data.find(problem_line)
                possible_bad_semicolon_index = substring_index + \
                    len(problem_line)

                if data[possible_bad_semicolon_index] == ";":
                    # Our guess is correct, we found a premature semicolon
                    # First, split the entire file into chars so we can work with it
                    # (Strings are immutable in Python)
                    data_as_chars = list(data)
                    # Replace our "incorrect" semicolon with a colon
                    data_as_chars[possible_bad_semicolon_index] = ":"
                    # Rejoin the array of chars back into a string
                    data = "".join(data_as_chars)
                    # Replace the charts object with our new, corrected data
                    charts = findall_with_regex_dotall(data, r"#NOTES:(.*?);")
                    # Replace our current chart with it's corrected data
                    chart = charts[i]
                    # Yes, this is probably inefficient, but saves me from modifying
                    # a few files manually.
                else:
                    # Our guess was incorrect
                    logging.warning(
                        "Unable to parse \"{}\" correctly. Skipping.".format(
                            filename))
                    return

            fileinfo = fi.FileInfo(title, subtitle, artist, pack, bpms,
                                   displaybpm, folder)
            parse_chart(chart + ";", fileinfo, db, cache)


def scan_folder(args, db, cache=None):
    logging.info("Scanning started.")

    # First fetch total number of found .sm files
    total = 0
    for root, dirs, files in os.walk(args[DIRECTORY]):
        for file in files:
            if file.lower().endswith(".sm"):
                total += 1
    logging.debug("{} .sm file(s) detected in initial count.".format(total))

    if total <= 0:
        logging.debug(
            "Exiting scan_folder function; no .sm files found in directory \"{}\"."
            .format(args[DIRECTORY]))
        return

    i = 0  # Current file
    for root, dirs, files in os.walk(args[DIRECTORY]):

        sm_counter = len(glob.glob1(root, "*.[sS][mM]"))

        if sm_counter <= 0:
            logging.info(
                "There are no .sm file(s) in folder \"{}\". Skipping folder/scanning children."
                .format(root))
            continue
        elif sm_counter >= 2:
            logging.warning(
                "Found more than 1 .sm files in folder \"{}\". Skipping folder."
                .format(root))
            i += sm_counter
            continue

        for file in files:
            filename = root + "/" + file
            if file.lower().endswith(".sm"):
                i += 1
                folder = root + "/"
                pack = os.path.basename(Path(folder).parent)
                if args[VERBOSE]:
                    output_i, output_total = vh.normalize_num(i, total)
                    output = "[" + output_i + "/" + output_total + "] "
                    output_percent = "[" + vh.get_percent(i, total) + "]"
                    output += output_percent + " Pack: "
                    output += vh.normalize_string(pack, 30) + " File: "
                    output += vh.normalize_string(file, 30)
                    print(output, end="\r")
                logging.info("Preparing to parse \"{}\".".format(filename))
                parse_file(db, filename, folder, pack, False, cache)
                logging.info("Completed parsing \"{}\".".format(filename))
            if args[MEDIA_REMOVE]:
                # remove everything that isn't .sm or .ssc
                if file.lower().endswith(".sm") or file.lower().endswith(
                        ".ssc"):
                    continue
                else:
                    os.remove(root + "/" + file)
                    logging.info("Removed \"{}\" from \"{}\".".format(
                        filename, root))

    if args[VERBOSE]:
        output_i, output_total = vh.normalize_num(i, total)
        output = "[" + output_i + "/" + output_total + "] "
        output_percent = "[" + vh.get_percent(i, total) + "] "
        output += output_percent
        output += vh.normalize_string("Complete!", 75)
        print(output)

    logging.info("Scanning complete.")


# noinspection PyTypeChecker
# PyCharm assumes args will remain a strict type boolean array, so we disable PyTypeChecker to ignore these warnings.
def main(argv: list):
    try:
        arguments, values = getopt.getopt(argv[1:], SHORT_OPTIONS,
                                          LONG_OPTIONS)
    except getopt.error as err:
        print("An unexpected error occurred with getopt. Error message:\n" +
              str(err) + "\nExiting.")
        sys.exit(2)

    # An array that will contains the passed in arguments. Positions of elements are declared as
    # final variables at top of script.
    args = [False for i in range(len(LONG_OPTIONS))]

    for arg, val in arguments:
        if arg in ("-u", "--unittest"):
            args[UNIT_TEST] = True
        elif arg in ("-r", "--rebuild") and os.path.isfile(DATABASE_NAME):
            args[REBUILD] = True
            os.remove(DATABASE_NAME)
        elif arg in ("-v", "--verbose"):
            args[VERBOSE] = True
        elif arg in ("-d", "--directory"):
            args[DIRECTORY] = val
        elif arg in ("-m", "--mediaremove"):
            args[MEDIA_REMOVE] = True
        elif arg in ("-l", "--log"):
            try:
                numeric_level = getattr(logging, val.upper())
                logging.basicConfig(filename=LOGFILE_NAME,
                                    level=numeric_level,
                                    datefmt=LOG_TIMESTAMP,
                                    format=LOG_FORMAT)
            except AttributeError:
                logging.basicConfig(filename=LOGFILE_NAME,
                                    level=logging.ERROR,
                                    datefmt=LOG_TIMESTAMP,
                                    format=LOG_FORMAT)
                print(
                    "Log level \"{}\" is not a valid log level. Defaulting to ERROR."
                    .format(val))
                print(
                    "Valid log levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL"
                )
            logging.info("Logfile initialized.")
        elif arg in ("-c", "--csv"):
            args[CSV] = True

    if not logging.getLogger().hasHandlers():
        # Logging argument wasn't passed in. Default to logging level ERROR and output to stdout.
        logging.basicConfig(level=logging.ERROR,
                            datefmt=LOG_TIMESTAMP,
                            format=LOG_FORMAT)

    if not args[DIRECTORY] and not args[UNIT_TEST]:
        message = "The directory is a required parameter. Exiting."
        print(message)
        logging.critical(message)
        sys.exit(2)

    if args[UNIT_TEST]:
        args[DIRECTORY] = UNITTEST_FOLDER + "/" + "songs"
        database = UNITTEST_FOLDER + "/" + DATABASE_NAME
        log_location = UNITTEST_FOLDER + "/" + LOGFILE_NAME
        if os.path.isfile(log_location):
            os.remove(log_location)
        if os.path.isfile(database):
            os.remove(database)
        logging.getLogger().handlers = []
        logging.basicConfig(filename=log_location,
                            level=logging.INFO,
                            datefmt=LOG_TIMESTAMP,
                            format=LOG_FORMAT)
        with TinyDB(database) as db:
            scan_folder(args, db)
            test.run_tests()
    else:

        with TinyDB(DATABASE_NAME, storage=CachingMiddleware(JSONStorage)) as db, \
                TinyDB(storage=MemoryStorage) as cache:

            # Generate a cache of existing song MD5 values for quick comparisons later. No need
            # to populate this cache if database is being rebuilt.
            if not args[REBUILD]:
                load_md5s_into_cache(db, cache)

            if os.path.isdir(args[DIRECTORY]):
                scan_folder(args, db, cache)
            else:
                print("\"" + args[DIRECTORY] +
                      "\" is not a valid directory. Exiting.")
                sys.exit(2)

            os.chmod(DATABASE_NAME, 0o777)

            if args[CSV]:
                # read database we just created
                # for each row, print to CSV
                database_to_csv(db)
            sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
