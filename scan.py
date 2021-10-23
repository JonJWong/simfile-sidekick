# -*- coding: utf-8 -*-

"""Searches for .sm files and creates a database of information based off their contents.

This is a tool used to scan StepMania (.sm) files <https://www.stepmania.com>. StepMania is a cross-platform rhythm
video game and engine. This tool is intended only for "Dance" game files and will only scan "dance-single" charts. This
tool creates a database of information from the scanned files. The database contains information such as a song's
length, BPM, density breakdown, and pattern analysis. The purpose of this file is to be used in conjunction with the
Discord bot.py program, to allow users to search for information from within Discord.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

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
LONG_OPTIONS = ["rebuild", "verbose", "directory=", "mediaremove", "log=", "unittest", "csv"]

# Positions in args array.
REBUILD = 0
VERBOSE = 1
DIRECTORY = 2
MEDIA_REMOVE = 3
LOG = 4
UNIT_TEST = 5
CSV = 6

# Regex constants. Used mainly in the pattern recognition section.
L_REG = "[124]+000"                     # Left arrow (1000)
D_REG = "0[124]+00"                     # Down arrow (0100)
U_REG = "00[124]+0"                     # Up Arrow (0010)
R_REG = "000[124]+"                     # Right Arrow (0001)
NL_REG = "[\s]+"                        # New line
OR_REG = "|"                            # Regex for "or"
NO_NOTES_REG = "[03M][03M][03M][03M]"   # Matches a line containing no notes (0000)
ANY_NOTES_REG = "(.*)[124]+(.*)"        # Matches a line containing at least 1 note

# Other constants.
LOG_TIMESTAMP = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(asctime)s %(levelname)s - %(message)s"

# File name and folder constants. Change these if you want to use a different name or folder.
UNITTEST_FOLDER = "tests"               # The folder the unit test songs are located
DATABASE_NAME = "db.json"               # Name of the TinyDB database file that contains parsed song information
LOGFILE_NAME = "scan.log"               # Name of the log file that will be created if enabled
CSV_FILENAME = "charts.csv"             # Name of the .csv that will be created if enabled


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
            "color_breakdown": fileinfo.chartinfo.color_breakdown_location,
            "color_partial_breakdown": fileinfo.chartinfo.color_partial_breakdown_location,
            "color_simple_breakdown": fileinfo.chartinfo.color_simple_breakdown_location,
            "color_normalized_breakdown": fileinfo.chartinfo.color_normalized_breakdown_location,
            "normalized_breakdown": fileinfo.chartinfo.normalized_breakdown,
            "left_foot_candles": fileinfo.chartinfo.patterninfo.left_foot_candles,
            "right_foot_candles": fileinfo.chartinfo.patterninfo.right_foot_candles,
            "total_candles": fileinfo.chartinfo.patterninfo.total_candles,
            "candles_percent": fileinfo.chartinfo.patterninfo.candles_percent,
            "mono_percent": fileinfo.chartinfo.patterninfo.mono_percent,
            "lr_boxes": fileinfo.chartinfo.patterninfo.lr_boxes,
            "ud_boxes": fileinfo.chartinfo.patterninfo.ud_boxes,
            "corner_ld_boxes": fileinfo.chartinfo.patterninfo.corner_ld_boxes,
            "corner_lu_boxes": fileinfo.chartinfo.patterninfo.corner_lu_boxes,
            "corner_rd_boxes": fileinfo.chartinfo.patterninfo.corner_rd_boxes,
            "corner_ru_boxes": fileinfo.chartinfo.patterninfo.corner_ru_boxes,
            "anchor_left": fileinfo.chartinfo.patterninfo.anchor_left,
            "anchor_down": fileinfo.chartinfo.patterninfo.anchor_down,
            "anchor_up": fileinfo.chartinfo.patterninfo.anchor_up,
            "anchor_right": fileinfo.chartinfo.patterninfo.anchor_right,
            "display_bpm": fileinfo.displaybpm,
            "max_bpm": fileinfo.max_bpm,
            "min_bpm": fileinfo.min_bpm,
            "max_nps": fileinfo.chartinfo.max_nps,
            "median_nps": fileinfo.chartinfo.median_nps,
            "graph_location": fileinfo.chartinfo.graph_location,
            "joined_graph_and_color_bd": fileinfo.chartinfo.joined_graph_and_color_bd,
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


def get_pattern_analysis(chart, num_notes):
    """Performs pattern analysis on a chart.

    This function will perform a series of pattern analysis of the chart that is passed in. It uses a series of regex
    search functions to obtain the data. It will return an analysis object.
    """
    # - - - CANDLE ANALYSIS - - -
    # Capture patterns that require one foot to move up to down, or vice versa.
    pattern = "(?=("  # Adds lookahead for ULDLU patterns
    pattern += D_REG + NL_REG + R_REG + NL_REG + U_REG + OR_REG
    pattern += U_REG + NL_REG + R_REG + NL_REG + D_REG
    pattern += "))"
    left_foot_candles = len(re.findall(re.compile(pattern), chart))

    pattern = "(?=("  # Adds lookahead for ULDLU patterns
    pattern += D_REG + NL_REG + L_REG + NL_REG + U_REG + OR_REG
    pattern += U_REG + NL_REG + L_REG + NL_REG + D_REG
    pattern += "))"
    right_foot_candles = len(re.findall(re.compile(pattern), chart))

    # - - - MONO ANALYSIS - - -
    # Capture patterns that lock the direction you face. To be considered a mono segment, your feet will be locked to
    # the 2 same arrows for 4 notes.
    # TODO: How to properly calculate mono with more than 4 notes per foot?

    # For patterns that lock your left foot to LD and right foot to RU
    pattern = ""
    for i in range(4):
        pattern += "(" + L_REG + OR_REG + D_REG + ")+" + NL_REG
        pattern += "(" + R_REG + OR_REG + U_REG + ")+"
        if i != 3:
            pattern += NL_REG
    ld_ru_mono = len(re.findall(re.compile(pattern), chart))

    # For patterns that lock your left foot to LU and right foot to RD
    pattern = ""
    for i in range(4):
        pattern += "(" + L_REG + OR_REG + U_REG + ")+" + NL_REG
        pattern += "(" + R_REG + OR_REG + D_REG + ")+"
        if i != 3:
            pattern += NL_REG
    lu_rd_mono = len(re.findall(re.compile(pattern), chart))

    # - - - BOX ANALYSIS - - -
    # For patterns that lock both feet to an arrow for 2 notes each
    # TODO: How to properly calculate boxes with 3 notes?
    pattern = L_REG + NL_REG + R_REG + NL_REG + L_REG + NL_REG + R_REG + OR_REG
    pattern += R_REG + NL_REG + L_REG + NL_REG + R_REG + NL_REG + L_REG
    lr_boxes = len(re.findall(re.compile(pattern), chart))

    pattern = U_REG + NL_REG + D_REG + NL_REG + U_REG + NL_REG + D_REG + OR_REG
    pattern += D_REG + NL_REG + U_REG + NL_REG + D_REG + NL_REG + U_REG
    ud_boxes = len(re.findall(re.compile(pattern), chart))

    pattern = L_REG + NL_REG + D_REG + NL_REG + L_REG + NL_REG + D_REG + OR_REG
    pattern += D_REG + NL_REG + L_REG + NL_REG + D_REG + NL_REG + L_REG
    corner_ld_boxes = len(re.findall(re.compile(pattern), chart))

    pattern = L_REG + NL_REG + U_REG + NL_REG + L_REG + NL_REG + U_REG + OR_REG
    pattern += U_REG + NL_REG + L_REG + NL_REG + U_REG + NL_REG + L_REG
    corner_lu_boxes = len(re.findall(re.compile(pattern), chart))

    pattern = R_REG + NL_REG + D_REG + NL_REG + R_REG + NL_REG + D_REG + OR_REG
    pattern += D_REG + NL_REG + R_REG + NL_REG + D_REG + NL_REG + R_REG
    corner_rd_boxes = len(re.findall(re.compile(pattern), chart))

    pattern = R_REG + NL_REG + U_REG + NL_REG + R_REG + NL_REG + U_REG + OR_REG
    pattern += U_REG + NL_REG + R_REG + NL_REG + U_REG + NL_REG + R_REG
    corner_ru_boxes = len(re.findall(re.compile(pattern), chart))

    # - - - ANCHOR ANALYSIS - - -
    # For patterns that lock one foot to an arrow for 3 notes
    # TODO: How to properly calculate anchors with more than 3 notes?
    pattern = L_REG + NL_REG + ANY_NOTES_REG + NL_REG + L_REG + NL_REG + ANY_NOTES_REG + NL_REG + L_REG
    anchor_left = len(re.findall(re.compile(pattern), chart))

    pattern = D_REG + NL_REG + ANY_NOTES_REG + NL_REG + D_REG + NL_REG + ANY_NOTES_REG + NL_REG + D_REG
    anchor_down = len(re.findall(re.compile(pattern), chart))

    pattern = U_REG + NL_REG + ANY_NOTES_REG + NL_REG + U_REG + NL_REG + ANY_NOTES_REG + NL_REG + U_REG
    anchor_up = len(re.findall(re.compile(pattern), chart))

    pattern = R_REG + NL_REG + ANY_NOTES_REG + NL_REG + R_REG + NL_REG + ANY_NOTES_REG + NL_REG + R_REG
    anchor_right = len(re.findall(re.compile(pattern), chart))


    total_candles = left_foot_candles + right_foot_candles
    candles_percent = (total_candles / math.floor((num_notes - 1) / 2)) * 100

    # Multiplied by 8 as there are 8 notes for every instance of mono
    mono_percent = (((ld_ru_mono + lu_rd_mono) * 8)/num_notes) * 100

    analysis = pi.PatternInfo(left_foot_candles, right_foot_candles, total_candles, candles_percent, mono_percent,
                              lr_boxes, ud_boxes, corner_ld_boxes, corner_lu_boxes, corner_rd_boxes, corner_ru_boxes,
                              anchor_left, anchor_down, anchor_up, anchor_right)

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
                b = bh.get_separator(int(bh.remove_all_breakdown_chars(simplified[i])))
            else:
                if int(bh.remove_all_breakdown_chars(b)) <= 4:
                    b = bh.remove_all_breakdown_chars(b)
                    small_break = True
                else:
                    b = bh.get_separator(int(bh.remove_all_breakdown_chars(simplified[i])))
                    current_measure = RunDensity.Break
        else:
            current_measure = RunDensity.Run_16

        if current_measure == previous_measure and i > 0:
            previous_value = bh.remove_all_breakdown_chars(simplified[i - 1])
            b = bh.remove_all_breakdown_chars(b)
            simplified[i - 1] = ""
            if small_break and simplified:
                if current_measure == RunDensity.Run_32:
                    simplified[i] = "=" + str(int(previous_value) + int(b) - 1) + "=*"
                elif current_measure == RunDensity.Run_24:
                    # Needs to be double escaped, as Discord will parse "\*" as just "*"
                    simplified[i] = "\\" + str(int(previous_value) + int(b) - 1) + "\\\\*"
                elif current_measure == RunDensity.Run_20:
                    simplified[i] = "~" + str(int(previous_value) + int(b) - 1) + "~*"
                else:
                    simplified[i] = str(int(previous_value) + int(b) - 1) + "*"
                small_break = False
            else:
                if current_measure == RunDensity.Run_32:
                    simplified[i] = "=" + str(int(previous_value) + int(b) - 1) + "=*"
                    simplified[i] = "=" + str(int(previous_value) + int(b) + 1) + "=*"
                elif current_measure == RunDensity.Run_24:
                    # Needs to be double escaped, as Discord will parse "\*" as just "*"
                    simplified[i] = "\\" + str(int(previous_value) + int(b) - 1) + "\\\\*"
                    simplified[i] = "\\" + str(int(previous_value) + int(b) + 1) + "\\\\*"
                elif current_measure == RunDensity.Run_20:
                    simplified[i] = "~" + str(int(previous_value) + int(b) - 1) + "~*"
                    simplified[i] = "~" + str(int(previous_value) + int(b) + 1) + "~*"
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
    notes = 0
    holds = 0
    jumps = 0
    mines = 0
    hands = 0
    rolls = 0
    holding = 0
    total_stream = 0
    total_break = 0
    chart_runs_only = ""

    for i, measure in enumerate(measures):
        bpm = find_current_bpm(i * 4, bpms)
        lines = measure.strip().split("\n")
        measure_density = 0
        for line in lines:
            if re.search(r"[124]", line):
                measure_density += 1
                notes += 1
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
            for j, char in enumerate(line): # For each of the 4 possible arrows
                if char == "2" or char == "4": # If arrow is hold or roll
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
            chart_runs_only += m
        else:
            chart_runs_only += "\n"

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
                breakdown += "=" + str(measures_of_run[RunDensity.Run_32.value]) + "= "
                measures_of_run[RunDensity.Run_32.value] = 0
            elif previous_measure == RunDensity.Run_24:
                breakdown += "\\" + str(measures_of_run[RunDensity.Run_24.value]) + "\\ "
                measures_of_run[RunDensity.Run_24.value] = 0
            elif previous_measure == RunDensity.Run_20:
                breakdown += "~" + str(measures_of_run[RunDensity.Run_20.value]) + "~ "
                measures_of_run[RunDensity.Run_20.value] = 0
            elif previous_measure == RunDensity.Run_16:
                breakdown += str(measures_of_run[RunDensity.Run_16.value]) + " "
                measures_of_run[RunDensity.Run_16.value] = 0
            elif previous_measure == RunDensity.Break:
                if measures_of_run[RunDensity.Break.value] > 1:
                    breakdown += "(" + str(measures_of_run[RunDensity.Break.value]) + ") "
                measures_of_run[RunDensity.Break.value] = 0

        previous_measure = current_measure

    # This will handle if the last note of the song is part of a run
    if measures_of_run[RunDensity.Run_32.value] > 0:
        breakdown += "=" + str(measures_of_run[RunDensity.Run_32.value]) + "= "
    elif measures_of_run[RunDensity.Run_24.value] > 0:
        breakdown += "\\" + str(measures_of_run[RunDensity.Run_24.value]) + "\\ "
    elif measures_of_run[RunDensity.Run_20.value] > 0:
        breakdown += "~" + str(measures_of_run[RunDensity.Run_20.value]) + "~ "
    elif measures_of_run[RunDensity.Run_16.value] > 0:
        breakdown += str(measures_of_run[RunDensity.Run_16.value]) + " "

    chartinfo.patterninfo = get_pattern_analysis(chart_runs_only, notes)

    del chart_runs_only

    minutes = length // 60
    seconds = length % 60
    length = str(int(minutes)) + "m " + str(int(seconds)) + "s"

    total_break = adjust_total_break(total_break, measures)

    notesinfo = ni.NotesInfo(notes, jumps, holds, mines, hands, rolls)
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
        logging.info("The {} {} chart for {} is empty. Skipping.".format(difficulty, rating, fileinfo.title))
        return                          # empty chart

    if not findall_with_regex(chart, ANY_NOTES_REG):
        logging.info("The {} {} chart for {} is empty. Skipping.".format(difficulty, rating, fileinfo.title))
        return                          # chart only contains 0's

    measures = findall_with_regex(chart, r"[01234MF\s]+(?=[,|;])")

    chartinfo = ci.ChartInfo(fileinfo, stepartist, difficulty, rating, measures)



    if measures == -1:
        logging.warning("Unable to parse the {} {} chart for {}. Skipping.".format(difficulty, rating, fileinfo.title))
        return

    density, breakdown, chartinfo = get_density_and_breakdown(chartinfo, measures, fileinfo.bpms)
    partially_simplified = get_simplified(breakdown, True)
    simplified = get_simplified(breakdown, False)

    normalized_img = None

    if chartinfo.total_stream:
        should_normalize = normalizer.if_should_normalize(breakdown, chartinfo.total_stream)
        if should_normalize != RunDensity.Run_16:
            bpm_to_use = normalizer.get_best_bpm_to_use(fileinfo.min_bpm, fileinfo.max_bpm, chartinfo.median_nps,
                                                        fileinfo.displaybpm)
            normalized_breakdown = normalizer.normalize(breakdown, bpm_to_use, should_normalize)
            if normalized_breakdown != breakdown:
                chartinfo.normalized_breakdown = normalized_breakdown
                if normalized_breakdown:
                    normalized_img = ih.create_breakdown_image(normalized_breakdown, "Normalized Breakdown")
                    ih.save_image(normalized_img, chartinfo.color_normalized_breakdown_location)


    chartinfo.breakdown = breakdown
    chartinfo.partial_breakdown = partially_simplified
    chartinfo.simple_breakdown = simplified

    # create color breakdown images

    detailed_breakdown_img = ih.create_breakdown_image(breakdown, "Detailed Breakdown")
    ih.save_image(detailed_breakdown_img, chartinfo.color_breakdown_location)

    partially_simplified_bd_img = ih.create_breakdown_image(partially_simplified, "Partially Simplified")
    ih.save_image(partially_simplified_bd_img, chartinfo.color_partial_breakdown_location)

    simplified_bd_img = ih.create_breakdown_image(simplified, "Simplified Breakdown")
    ih.save_image(simplified_bd_img, chartinfo.color_simple_breakdown_location)

    chartinfo.max_nps = max(density)
    chartinfo.median_nps = statistics.median(density)

    fileinfo.chartinfo = chartinfo

    ih.create_and_save_density_graph(list(range(0, len(measures))), density, fileinfo.chartinfo.graph_location)

    # Join the color breakdown images with the density graph. Don't join images that have the same breakdowns.

    graph_img = ih.load_image(fileinfo.chartinfo.graph_location)
    temp_merged_img = None

    if fileinfo.chartinfo.breakdown:
        if fileinfo.chartinfo.breakdown == fileinfo.chartinfo.partial_breakdown:
            # Only show detailed breakdown
            temp_merged_img = detailed_breakdown_img
        elif fileinfo.chartinfo.partial_breakdown == fileinfo.chartinfo.simple_breakdown:
            # Show detailed and partial breakdowns
            temp_merged_img = ih.merge_images_vertically(detailed_breakdown_img, partially_simplified_bd_img)
        else:
            # Show all 3 breakdowns
            temp_merged_img = ih.merge_images_vertically(detailed_breakdown_img, partially_simplified_bd_img)
            temp_merged_img = ih.merge_images_vertically(temp_merged_img, simplified_bd_img)
        if fileinfo.chartinfo.normalized_breakdown:
            # Add normalized breakdown to end
            temp_merged_img = ih.merge_images_vertically(temp_merged_img, normalized_img)

    if temp_merged_img:
        # Merge graph then save
        temp_merged_img = ih.merge_images_vertically(temp_merged_img, graph_img)
    else:
        # Only show graph in merged image
        temp_merged_img = graph_img

    ih.save_image(temp_merged_img, fileinfo.chartinfo.joined_graph_and_color_bd)

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
        logging.warning("BPM for file \"{}\" is not readable. Skipping.".format(filename))
        return
    else:
        bpms = bpms.split(",")
        temp = []
        for bpm in bpms:
            if "#" in bpm:
                # Some BPMs are missing a trailing ; (30MIN HARDER in Cirque du Beast)
                bpm = bpm.split("#", 1)[0]
                logging.warning("BPM for file \"{}\" is missing semicolon. Handled and continuing.".format(filename))
            # Quick way to remove non-printable characters that, for whatever reason,
            # exist in a few .sm files (Oceanlab Megamix)
            old_bpm = bpm
            bpm = "".join(filter(lambda c: c in string.printable, bpm))
            if old_bpm != bpm:
                logging.warning("BPM for file \"{}\" contains non-printable characters. Handled and continuing.".format(filename))
            bpm = bpm.strip().split("=")
            temp.insert(0, bpm)
        bpms = temp
    displaybpm = find_with_regex(data, r"#DISPLAYBPM:(.*);")
    charts = findall_with_regex_dotall(data, r"#NOTES:(.*?);")

    if charts == -1:
        logging.warning("Unable to parse chart(s) data for \"{}\". Skipping.".format(filename))
        return
    else:
        for i, chart in enumerate(charts):
            sanity_check = chart.split("\n", 6)
            if len(sanity_check) != 7:
                logging.warning("Unable to parse chart(s) data for \"{}\". Attempting to handle...".format(filename))
                # There's something in this file that is causing the regex to not parse properly.
                # Usually a misplaced ; instead of a :
                # This is a quick and dirty attempt to salvage it.
                # e.g. SHARPNELSTREAMZ v2 I'm a Maid has this issue
                chart = chart.splitlines()
                problem_line = chart[len(chart) - 1]
                substring_index = data.find(problem_line)
                possible_bad_semicolon_index = substring_index + len(problem_line)

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
                    logging.warning("Unable to parse \"{}\" correctly. Skipping.".format(filename))
                    return

            fileinfo = fi.FileInfo(title, subtitle, artist, pack, bpms, displaybpm, folder)
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
        logging.debug("Exiting scan_folder function; no .sm files found in directory \"{}\".".format(args[DIRECTORY]))
        return

    i = 0  # Current file
    for root, dirs, files in os.walk(args[DIRECTORY]):

        sm_counter = len(glob.glob1(root, "*.[sS][mM]"))

        if sm_counter <= 0:
            logging.info("There are no .sm file(s) in folder \"{}\". Skipping folder/scanning children.".format(root))
            continue
        elif sm_counter >= 2:
            logging.warning("Found more than 1 .sm files in folder \"{}\". Skipping folder.".format(root))
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
                if file.lower().endswith(".ogg") or file.lower().endswith(".mpg") or file.lower().endswith(".avi"):
                    os.remove(root + "/" + file)
                    logging.info("Removed \"{}\" from \"{}\".".format(filename, root))

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
        arguments, values = getopt.getopt(argv[1:], SHORT_OPTIONS, LONG_OPTIONS)
    except getopt.error as err:
        print("An unexpected error occurred with getopt. Error message:\n" + str(err) + "\nExiting.")
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
                logging.basicConfig(filename=LOGFILE_NAME, level=numeric_level, datefmt=LOG_TIMESTAMP, format=LOG_FORMAT)
            except AttributeError:
                logging.basicConfig(filename=LOGFILE_NAME, level=logging.ERROR, datefmt=LOG_TIMESTAMP, format=LOG_FORMAT)
                print("Log level \"{}\" is not a valid log level. Defaulting to ERROR.".format(val))
                print("Valid log levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL")
            logging.info("Logfile initialized.")
        elif arg in ("-c", "--csv"):
            args[CSV] = True

    if not logging.getLogger().hasHandlers():
        # Logging argument wasn't passed in. Default to logging level ERROR and output to stdout.
        logging.basicConfig(level=logging.ERROR, datefmt=LOG_TIMESTAMP, format=LOG_FORMAT)

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
        logging.basicConfig(filename=log_location, level=logging.INFO, datefmt=LOG_TIMESTAMP, format=LOG_FORMAT)
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
                print("\"" + args[DIRECTORY] + "\" is not a valid directory. Exiting.")
                sys.exit(2)

            os.chmod(DATABASE_NAME, 0o777)

            if args[CSV]:
                # read database we just created
                # for each row, print to CSV
                database_to_csv(db)
            sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
