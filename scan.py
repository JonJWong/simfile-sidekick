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


from common import BreakdownHelper as bh
from common import GeneralHelper as gh
from common import Normalize as normalizer
from common import ImageHelper as ih
from common.objects import NotesInfo as ni, ChartInfo as ci, FileInfo as fi, PatternInfo as pi
from common import Test as test
from common import VerboseHelper as vh
from common.enums.RunDensity import RunDensity
from pathlib import Path
from tinydb import Query, TinyDB, where
from tinydb.storages import JSONStorage, MemoryStorage
from tinydb.middlewares import CachingMiddleware
import getopt
import glob
import json
import logging
import math
import os
import re
import statistics
import string
import sys

# Flag constants. These are the available command line arguments you can use when running this application.
SHORT_OPTIONS = "rvd:ml:uc"
LONG_OPTIONS = ["rebuild", "verbose", "directory=",
                "mediaremove", "log=", "unittest", "csv"]

# Positions in args array.
REBUILD = 0
VERBOSE = 1
DIRECTORY = 2
MEDIA_REMOVE = 3
LOG = 4
UNIT_TEST = 5
CSV = 6

# Regex constants. Used mainly in the pattern recognition section.
NL_REG = "[\s]+"                        # New line
OR_REG = "|"                            # Regex for "or"
# Matches a line containing no notes (0000)
NO_NOTES_REG = "[03M][03M][03M][03M]"
# Matches a line containing at least 1 note
ANY_NOTES_REG = "(.*)[124]+(.*)"

# Other constants.
LOG_TIMESTAMP = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(asctime)s %(levelname)s - %(message)s"

# File name and folder constants. Change these if you want to use a different name or folder.
# The folder the unit test songs are located
UNITTEST_FOLDER = "tests"
# Name of the TinyDB database file that contains parsed song information
DATABASE_NAME = "db.json"
# Name of the log file that will be created if enabled
LOGFILE_NAME = "scan.log"
# Name of the .csv that will be created if enabled
CSV_FILENAME = "charts.csv"


def findall_with_regex_dotall(data, regex):
    """Returns array of results from the given regex. Search will span over newline characters."""
    try:
        return re.findall(regex, data, re.DOTALL)
    except AttributeError:
        return -1


def findall_with_regex(data, regex):
    """Returns array of results from the given regex."""
    try:
        return re.findall(regex, data)
    except AttributeError:
        return -1


def find_with_regex_dotall(data, regex):
    """Returns the first match from a given regex. Search will span over newline characters."""
    try:
        return re.search(regex, data, re.DOTALL).group(1)
    except AttributeError:
        return -1


def find_with_regex(data, regex):
    """Returns the first match from a given regex."""
    try:
        return re.search(regex, data).group(1)
    except AttributeError:
        return "N/A"


def load_md5s_into_cache(db, cache):
    charts = db.all()
    for chart in charts:
        cache.insert({"md5": chart["md5"]})
    return cache


def database_to_csv(db):
    """Gets every row of the database and saves relevant info to a .csv"""
    charts = db.all()
    with open(CSV_FILENAME, 'w') as f:
        f.write("title,subtitle,artist,pack\n")
        for chart in charts:
            f.write(
                chart["title"] + "," +
                chart["subtitle"] + "," +
                chart["artist"] + "," +
                chart["pack"] + "\n"
            )
    return


def add_to_database(fileinfo, db, cache):
    """Adds the chart information and pattern analysis to the TinyDB database."""

    result = None

    # Search if the chart already exists in our database.
    if cache is not None:
        # We are using the MD5 MemoryStorage. Check if the MD5 exists there
        result = cache.search(where("md5") == fileinfo.chartinfo.md5)
        cache.insert({"md5": fileinfo.chartinfo.md5})
    else:
        # We weren't provided a MD5 MemoryStorage, so we have to query the database.
        result = db.search(where("md5") == fileinfo.chartinfo.md5)

    if not result:
        # If the chart doesn't exist, add a new entry.
        db.insert({
            "title": fileinfo.title,
            "subtitle": fileinfo.subtitle,
            "artist": fileinfo.artist,
            "pack": fileinfo.pack,
            "length": fileinfo.chartinfo.length,
            "notes": fileinfo.chartinfo.notesinfo.notes,
            "jumps": fileinfo.chartinfo.notesinfo.jumps,
            "holds": fileinfo.chartinfo.notesinfo.holds,
            "mines": fileinfo.chartinfo.notesinfo.mines,
            "hands": fileinfo.chartinfo.notesinfo.hands,
            "rolls": fileinfo.chartinfo.notesinfo.rolls,
            "total_stream": fileinfo.chartinfo.total_stream,
            "total_break": fileinfo.chartinfo.total_break,
            "stepartist": fileinfo.chartinfo.stepartist,
            "difficulty": fileinfo.chartinfo.difficulty,
            "rating": fileinfo.chartinfo.rating,
            "breakdown": fileinfo.chartinfo.breakdown,
            "partial_breakdown": fileinfo.chartinfo.partial_breakdown,
            "simple_breakdown": fileinfo.chartinfo.simple_breakdown,
            "normalized_breakdown": fileinfo.chartinfo.normalized_breakdown,
            "left_foot_candles": fileinfo.chartinfo.patterninfo.left_foot_candles,
            "right_foot_candles": fileinfo.chartinfo.patterninfo.right_foot_candles,
            "total_candles": fileinfo.chartinfo.patterninfo.total_candles,
            "mono_percent": fileinfo.chartinfo.patterninfo.mono_percent,
            "anchor_left": fileinfo.chartinfo.patterninfo.anchor_left,
            "anchor_down": fileinfo.chartinfo.patterninfo.anchor_down,
            "anchor_up": fileinfo.chartinfo.patterninfo.anchor_up,
            "anchor_right": fileinfo.chartinfo.patterninfo.anchor_right,
            "double_stairs_count": fileinfo.chartinfo.patterninfo.double_stairs_count,
            "double_stairs_array": fileinfo.chartinfo.patterninfo.double_stairs_array,
            "doublesteps_count": fileinfo.chartinfo.patterninfo.doublesteps_count,
            "doublesteps_array": fileinfo.chartinfo.patterninfo.doublesteps_array,
            "jumps_count": fileinfo.chartinfo.patterninfo.jumps_count,
            "jumps_array": fileinfo.chartinfo.patterninfo.jumps_array,
            "display_bpm": fileinfo.displaybpm,
            "max_bpm": fileinfo.max_bpm,
            "min_bpm": fileinfo.min_bpm,
            "max_nps": fileinfo.chartinfo.max_nps,
            "median_nps": fileinfo.chartinfo.median_nps,
            "graph_location": fileinfo.chartinfo.graph_location,
            "md5": fileinfo.chartinfo.md5
        })
    else:
        # If the chart already exists (i.e. we have a matching MD5), we want to update the entry and append the pack to
        # it. This usually happens with ECS or SRPG songs taken from other packs.
        if cache:
            # result is currently set to MemoryStorage, so grab the db entry
            result = db.search(where("md5") == fileinfo.chartinfo.md5)
        data = json.loads(json.dumps(result[0]))
        pack = data["pack"] + ", " + fileinfo.pack
        Chart = Query()
        db.update({"pack": pack}, Chart.md5 == fileinfo.chartinfo.md5)


def adjust_total_break(total_break, measures):
    """Adjust the "total break" statistic to remove unused measures.

    This will adjust the "total break" statistic to account for songs that have a long fadeout, fadeout mine, or
    charts that do not end in a stream. This is because we do not consider notes after the last stream as a break.
    The "total break" is used to denote the measures of break between the first and last run."""
    if total_break > 0:
        for i, measure in enumerate(reversed(measures)):
            # Since we're navigating backwards in the chart, we want to break at the first full run we see
            lines = measure.strip().split("\n")
            if len(lines) < 16:             # measure only contains 4th or 8th notes
                total_break -= 1
                continue
            notes_in_measure = len(findall_with_regex(measure, ANY_NOTES_REG))
            if notes_in_measure < 16:       # measure is not a full run
                total_break -= 1
                continue
            break
    return total_break


def find_current_bpm(measure, bpms):
    """Finds the current BPM in a given measure of a song."""
    for bpm in bpms:
        if float(bpm[0]) <= measure:
            return bpm[1]


def last_left_right(pattern):
    """
        Takes in a string as a pattern, and returns "L", "R". Always returns
        whichever comes last in string.

        Input assumes that there is always at least 1 L/R in string.
    """
    last_L = pattern.rfind("L")
    last_R = pattern.rfind("R")

    return pattern[last_L:] if last_L > last_R else pattern[last_R:]


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


def rec_anchor_check(run, arrow_idx, next_idx, count=0):
    """
        Recursive function to check for anchors within a run
        TODO: Implement this in the iterative analysis
    """
    # If we've reached the end of the run and there were less than 3 instances
    # of the arrow in question, return false
    if next_idx >= len(run) and count < 3:
        return False

    # if the two input arrows are the same, call the function again for the next
    # step, otherwise return whether or not the count >= 3
    if run[arrow_idx] == run[next_idx]:
        # If the first two match, we need to count as two arrows, but only move
        # forward by 1 count thereafter.
        if count == 0:
            new_count = 2
        else:
            new_count += 1
        return rec_anchor_check(run, next_idx, next_idx + 2, new_count)
    else:
        return count >= 3


def rec_tower_check(run, arrow_idx, next_idx, count=0):
    """
        Recursive function to check for boxes within a run
        TODO: Implement this in the iterative analysis
    """
    # If we've reached the end of the run and there were less than 2 instances
    # of the arrow in question, return false
    if next_idx + 1 >= len(run) and count < 2:
        return False, "None"

    # if the two input arrows are the same, call the function again for the next
    # step, otherwise return whether or not the count >= 2
    if run[arrow_idx] == run[next_idx] and run[arrow_idx + 1] == run[next_idx + 1]:
        # If the first two match, we need to count as two arrows, but only move
        # forward by 1 count thereafter.
        if count == 0:
            new_count = 2
        else:
            new_count += 1

        return rec_tower_check(run, next_idx + 1, next_idx + 2, new_count)
    else:
        if count == 2:
            pattern_type = "Box"
        elif count >= 2:
            pattern_type = "Tower"
        else:
            pattern_type = "None"

        return count >= 2, pattern_type


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
    STEP_TO_DIR = {
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
        # None
        "0000": "",
        # Jumps
        "1100": "[LD]",
        "1010": "[LU]",
        "1001": "[LR]",
        "0101": "[DR]",
        "0011": "[UR]",
        "0110": "[DU]",
        # Hands
        "1110": "[LDU]",
        "1101": "[LDR]",
        "1011": "[LUR]",
        "0111": "[DUR]",
        "1111": "[LDUR]"
    }

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
        "Jumps Array": []
    }

    # Candles
    LEFT_CANDLES = ["DRU", "URD"]
    RIGHT_CANDLES = ["DLU", "ULD"]

    # Create a combined regex pattern for all substrings in each category
    left_anchor_pattern = "L[DUR]L[DUR]L"
    down_anchor_pattern = "D[LUR]D[LUR]D"
    up_anchor_pattern = "U[LDR]U[LDR]U"
    right_anchor_pattern = "R[LDU]R[LDU]R"

    combined_pattern = (
        f"({left_anchor_pattern}|{down_anchor_pattern}|"
        f"{up_anchor_pattern}|{right_anchor_pattern})"
    )

    total_notes_in_runs = 0

    curr_run = ""
    prev_measure = None
    most_recent_starting_measure = None

    def __process_mistake_data(data, category_counts, category_key, array_key, pattern_format):
        for measure, datum in data.items():
            if isinstance(datum, list):
                for data in datum:
                    category_counts[category_key] += 1
                    str_to_append = pattern_format.format(
                        str(data), str(measure))

                    if str_to_append not in category_counts[array_key]:
                        category_counts[array_key].append(str_to_append)
            else:
                category_counts[category_key] += 1
                str_to_append = pattern_format.format(str(datum), str(measure))

                if str_to_append not in category_counts[array_key]:
                    category_counts[array_key].append(str_to_append)

    def __double_parser(run, measure_num):
        """
        Finds all the double stairs/doublesteps in a run, and notates them with
        their measure.
        Returns a dictionary for each with measure: pattern as key: value pairs.

        ```
        Input: String ex. "LDURLUDR"
        Output: Dictionary, Dictionary
            ex. {
                15: "LDUR",
                33: "RUDL"
            }
            ex. {
                15: "LUUD",
                33: "DURR"
            }
        ```
        """
        nonlocal category_counts
        # Iterate through the run string

    def __analyze(run):
        """
        Method to find Anchors and Candles via regex, double stairs and double
        steps via iterative string matching, and mono through iteration paying
        attention to direction changes based on which foot hits the U/D arrow.

        Does not return anything, but modifies a `nonlocal category_counts`
        variable, which contains data pertinent to the patterning of a chart.

        Parameters
        -----------
        Input: string
            Takes in a string where each character denotes an arrow in the run.
            ex. "LDURLUDRLRUDL"

        Output: None
        """
        nonlocal combined_pattern, category_counts, LEFT_CANDLES, RIGHT_CANDLES, \
              total_notes_in_runs, curr_run, most_recent_starting_measure, STEP_TO_DIR
        
        DBL_STAIRS = [
            "LDURLDUR",
            "LUDRLUDR",
            "RUDLRUDL",
            "RDULRDUL"
        ]

        DBL_STEPS = [
            "LL", "DD", "UU", "RR",
            "LUR", "LDR", "RUL", "RDL",
            "LUDL", "LDUL", "RUDR", "RDUR"
        ]

        double_stair_data = {}
        doublesteps_data = {}
        jumps_data = {}

        # - - - - - ANCHOR FINDER - - - - -
        # Uses regex matching like the previous method
        # TODO: Use recursive algorithm in step iteration
        matches = re.findall(combined_pattern, run)
        for match in matches:
            if re.search(left_anchor_pattern, match):
                category_counts["Left Anchors"] += 1
            elif re.search(down_anchor_pattern, match):
                category_counts["Down Anchors"] += 1
            elif re.search(up_anchor_pattern, match):
                category_counts["Up Anchors"] += 1
            elif re.search(right_anchor_pattern, match):
                category_counts["Right Anchors"] += 1

        # - - - - - CANDLE FINDER - - - - -
        # Candles are relatively straightforward, if any of those 4 candle
        # variants exist, then it is a candle.
        category_counts["Left Candles"] += sum(run.count(pattern)
                                               for pattern in LEFT_CANDLES)
        category_counts["Right Candles"] += sum(run.count(pattern)
                                                for pattern in RIGHT_CANDLES)

        current_foot = None
        previous_foot = None
        currently_facing = None
        next_direction = None
        current_pattern = ""
        ds_pattern = ""
        jumping = False

        # - - - - - RUN ITERATION LOOP - - - - -
        # One step at a time.

        for i, note in enumerate(run):
            current_measure = most_recent_starting_measure + math.floor(i + 1 / 16)
            # - - - - - JUMP DETECTION - - - - -
            # If there is a jump we need to reset the direction the player is facing
            # on the next step, since it is most likely ambiguous.
            if note == "[" and not jumping:
                jump_end_idx = run.find("]", i)
                jump_str = run[i+1:jump_end_idx].split()
                jumping = True
                current_foot, previous_foot, currently_facing, current_pattern = (None, None, None, None)
                jumps_data[current_measure] = jump_str
            elif note == "]":
                if jumping:
                    jumping = False

            total_notes_in_runs += 1

            if jumping:
                continue

            # print(f"pattern: {current_pattern}\n prev_foot: {previous_foot} curr_foot: {current_foot} curr_facing: {currently_facing} next_direction: {next_direction} step:{step}\n")

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
                    amt_to_add = math.floor((i+len(pattern)-1) / 16)
                    if i+len(pattern)-1 >= len(run):
                        dblstep_measure = measure_num + 1
                    else:
                        dblstep_measure = measure_num + amt_to_add

                    if doublesteps_data.get(dblstep_measure):
                        if isinstance(doublesteps_data[dblstep_measure], str):
                            doublesteps_data[dblstep_measure] = [
                                doublesteps_data[dblstep_measure]]
                            doublesteps_data[dblstep_measure].append(pattern)
                        elif isinstance(doublesteps_data[dblstep_measure], list):
                            doublesteps_data[dblstep_measure].append(pattern)
                    else:
                        doublesteps_data[dblstep_measure] = pattern

            # Add step to pattern
            ds_pattern += note

            # - - - - - DOUBLE STAIR FINDER - - - - -
            # If our ds_pattern deviates from double stairs, we want
            # to reset the pattern at the next applicable instance of left
            # or right. This ensures that we are not losing previously
            # counted stairs/beginnings of stairs.
            if not any(dbl_stair.startswith(ds_pattern) for dbl_stair in DBL_STAIRS):
                # Slices the current pattern at the next left or right.
                for j in range(1, len(ds_pattern)):
                    if j < len(ds_pattern) and (ds_pattern[j] == "L" or ds_pattern[j] == "R"):
                        ds_pattern = ds_pattern[j:]
                continue

            # If the ds_pattern length reaches 8, we have found a
            # double stair, so we reset ds_pattern after printing the
            # metadata.
            if len(ds_pattern) == 8:
                calcd_idx = i - 7 if i - 7 > 0 else 0
                dbl_stair_measure = measure_num + math.floor(calcd_idx / 16)
                double_stair_data[dbl_stair_measure] = ds_pattern[:4]

                ds_pattern = ""

        # - - - - - ITERATION END - - - - -

        # Process double_stair_data
        __process_mistake_data(double_stair_data, category_counts,
                              "Double Stairs Count", "Double Stairs Array", "{}: measure {}")

        # Process doublesteps_data
        __process_mistake_data(doublesteps_data, category_counts,
                              "Doublesteps Count", "Doublesteps Array", "{}: measure {}")
        
        # Process jump_data
        __process_mistake_data(jumps_data, category_counts,
                            "Jumps Count", "Jumps Array", "{}: measure {}")

        category_counts["Mono Percent"] = (
            (category_counts["Mono Notes"] / total_notes_in_runs) * 100
        ) if category_counts["Mono Notes"] != 0 else 0

        category_counts["Total Candles"] = (
            category_counts["Left Candles"] +
            category_counts["Right Candles"]
        )

    def __populate(notes_in_measure):
        nonlocal curr_run, STEP_TO_DIR
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
        if i == 0 or measure_num - prev_measure > 1:
            # Analyze and reset if it's the first measure or a gap is detected.
            if i != 0:
                __analyze(curr_run)
                __reset(measure_num)
            most_recent_starting_measure = measure_num
            curr_run = ""

        # Populate notes for the current measure.
        __populate(notes_in_measure)

        if i == len(measure_obj) - 1:
            # Analyze if it's the last measure.
            __analyze(curr_run)

        prev_measure = measure_num

    category_counts["Double Stairs Count"] = len(
        category_counts["Double Stairs Array"])

    analysis = pi.PatternInfo(category_counts["Left Candles"],
                              category_counts["Right Candles"],
                              category_counts["Total Candles"],
                              category_counts["Mono Percent"],
                              category_counts["Left Anchors"],
                              category_counts["Down Anchors"],
                              category_counts["Up Anchors"],
                              category_counts["Right Anchors"],
                              category_counts["Double Stairs Count"],
                              category_counts["Double Stairs Array"],
                              category_counts["Doublesteps Count"],
                              category_counts["Doublesteps Array"],
                              category_counts["Jumps Count"],
                              category_counts["Jumps Array"],)

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
            for j, char in enumerate(line):  # For each of the 4 possible arrows
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
            if len(re.findall(re.compile(NO_NOTES_REG), measure)) >= measure_density:
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
        return                          # we only want single charts

    if chart.strip() == ";":
        logging.info("The {} {} chart for {} is empty. Skipping.".format(
            difficulty, rating, fileinfo.title))
        return                          # empty chart

    if not findall_with_regex(chart, ANY_NOTES_REG):
        logging.info("The {} {} chart for {} is empty. Skipping.".format(
            difficulty, rating, fileinfo.title))
        return                          # chart only contains 0's

    measures = findall_with_regex(chart, r"[01234MF\s]+(?=[,|;])")

    chartinfo = ci.ChartInfo(fileinfo, stepartist,
                             difficulty, rating, measures)

    if measures == -1:
        logging.warning("Unable to parse the {} {} chart for {}. Skipping.".format(
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
            bpm_to_use = normalizer.get_best_bpm_to_use(fileinfo.min_bpm, fileinfo.max_bpm, chartinfo.median_nps,
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

    ih.create_and_save_density_graph(
        list(range(0, len(measures))), density, fileinfo.chartinfo.graph_location)
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
                    "BPM for file \"{}\" is missing semicolon. Handled and continuing.".format(filename))
            # Quick way to remove non-printable characters that, for whatever reason,
            # exist in a few .sm files (Oceanlab Megamix)
            old_bpm = bpm
            bpm = "".join(filter(lambda c: c in string.printable, bpm))
            if old_bpm != bpm:
                logging.warning(
                    "BPM for file \"{}\" contains non-printable characters. Handled and continuing.".format(filename))
            bpm = bpm.strip().split("=")
            temp.insert(0, bpm)
        bpms = temp
    displaybpm = find_with_regex(data, r"#DISPLAYBPM:(.*);")
    charts = findall_with_regex_dotall(data, r"#NOTES:(.*?);")

    if charts == -1:
        logging.warning(
            "Unable to parse chart(s) data for \"{}\". Skipping.".format(filename))
        return
    else:
        for i, chart in enumerate(charts):
            sanity_check = chart.split("\n", 6)
            if len(sanity_check) != 7:
                logging.warning(
                    "Unable to parse chart(s) data for \"{}\". Attempting to handle...".format(filename))
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
                        "Unable to parse \"{}\" correctly. Skipping.".format(filename))
                    return

            fileinfo = fi.FileInfo(
                title, subtitle, artist, pack, bpms, displaybpm, folder)
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
        logging.debug("Exiting scan_folder function; no .sm files found in directory \"{}\".".format(
            args[DIRECTORY]))
        return

    i = 0  # Current file
    for root, dirs, files in os.walk(args[DIRECTORY]):

        sm_counter = len(glob.glob1(root, "*.[sS][mM]"))

        if sm_counter <= 0:
            logging.info(
                "There are no .sm file(s) in folder \"{}\". Skipping folder/scanning children.".format(root))
            continue
        elif sm_counter >= 2:
            logging.warning(
                "Found more than 1 .sm files in folder \"{}\". Skipping folder.".format(root))
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
                if file.lower().endswith(".sm") or file.lower().endswith(".ssc"):
                    continue
                else:
                    os.remove(root + "/" + file)
                    logging.info(
                        "Removed \"{}\" from \"{}\".".format(filename, root))

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
        arguments, values = getopt.getopt(
            argv[1:], SHORT_OPTIONS, LONG_OPTIONS)
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
                logging.basicConfig(
                    filename=LOGFILE_NAME, level=numeric_level, datefmt=LOG_TIMESTAMP, format=LOG_FORMAT)
            except AttributeError:
                logging.basicConfig(
                    filename=LOGFILE_NAME, level=logging.ERROR, datefmt=LOG_TIMESTAMP, format=LOG_FORMAT)
                print(
                    "Log level \"{}\" is not a valid log level. Defaulting to ERROR.".format(val))
                print("Valid log levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL")
            logging.info("Logfile initialized.")
        elif arg in ("-c", "--csv"):
            args[CSV] = True

    if not logging.getLogger().hasHandlers():
        # Logging argument wasn't passed in. Default to logging level ERROR and output to stdout.
        logging.basicConfig(level=logging.ERROR,
                            datefmt=LOG_TIMESTAMP, format=LOG_FORMAT)

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
        logging.basicConfig(filename=log_location, level=logging.INFO,
                            datefmt=LOG_TIMESTAMP, format=LOG_FORMAT)
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
