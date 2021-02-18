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

from common import ChartInfo as ci
from common import PatternAnalysis as pa
from common import Test as test
from common import VerboseHelper as vh
from pathlib import Path
from tinydb import Query, TinyDB, where
import datetime
import enum
import getopt
import glob
import hashlib
import json
import os
import plotly.graph_objects as go
import re
import statistics
import string
import sys

# Flag constants. These are the available command line arguments you can use when running this application.
SHORT_OPTIONS = "rvd:mlu"
LONG_OPTIONS = ["rebuild", "verbose", "directory=", "mediaremove", "log", "unittest"]

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
LOG_TIMESTAMP = "%Y-%m-%d %I:%M:%S %p"

# File name and folder constants. Change these if you want to use a different name or folder.
UNITTEST_FOLDER = "tests"               # The folder the unit test songs are located
DATABASE_NAME = "db.json"               # Name of the TinyDB database file that contains parsed song information
LOGFILE_NAME = "scan.log"               # Name of the log file that will be created if enabled


class RunDensity(enum.Enum):
    """Represents the different types of stream in a series of measures.

    This enum is used when calculating the measure breakdown of a song.
    """
    Break = 0                           # Denotes a break (measure with less than 16 notes)
    Run_16 = 1                          # Denotes a full measure of 16th notes
    Run_24 = 2                          # Denotes a full measure of 24th notes
    Run_32 = 3                          # Denotes a full measure of 32nd notes


def remove_comments(chart):
    """Removes lines in .sm file that begin with //."""
    return re.sub("//(.*)", "", chart)


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


def add_to_database(chartinfo, db, analysis):
    """Adds the chart information and pattern analysis to the TinyDB database."""
    # Search if the chart already exists in our database.
    result = db.search(where("md5") == chartinfo.md5)

    if not result:
        # If the chart doesn't exist, add a new entry.
        db.insert({
            "title": chartinfo.title,
            "subtitle": chartinfo.subtitle,
            "artist": chartinfo.artist,
            "pack": chartinfo.pack,
            "length": chartinfo.length,
            "notes": chartinfo.notes,
            "jumps": chartinfo.jumps,
            "holds": chartinfo.holds,
            "mines": chartinfo.mines,
            "hands": chartinfo.hands,
            "rolls": chartinfo.rolls,
            "total_stream": chartinfo.total_stream,
            "total_break": chartinfo.total_break,
            "stepartist": chartinfo.stepartist,
            "difficulty": chartinfo.difficulty,
            "rating": chartinfo.rating,
            "breakdown": chartinfo.breakdown,
            "partial_breakdown": chartinfo.partial_breakdown,
            "simple_breakdown": chartinfo.simple_breakdown,
            "left_foot_candles": analysis.left_foot_candles,
            "right_foot_candles": analysis.right_foot_candles,
            "total_candles": analysis.total_candles,
            "candles_percent": analysis.candles_percent,
            "mono_percent": analysis.mono_percent,
            "lr_boxes": analysis.lr_boxes,
            "ud_boxes": analysis.ud_boxes,
            "corner_ld_boxes": analysis.corner_ld_boxes,
            "corner_lu_boxes": analysis.corner_lu_boxes,
            "corner_rd_boxes": analysis.corner_rd_boxes,
            "corner_ru_boxes": analysis.corner_ru_boxes,
            "anchor_left": analysis.anchor_left,
            "anchor_down": analysis.anchor_down,
            "anchor_up": analysis.anchor_up,
            "anchor_right": analysis.anchor_right,
            "display_bpm": chartinfo.displaybpm,
            "max_bpm": chartinfo.max_bpm,
            "min_bpm": chartinfo.min_bpm,
            "max_nps": chartinfo.max_nps,
            "median_nps": chartinfo.median_nps,
            "graph_location": chartinfo.graph_location,
            "md5": chartinfo.md5
        })
    else:
        # If the chart already exists (i.e. we have a matching MD5), we want to update the entry and append the pack to
        # it. This usually happens with ECS or SRPG songs taken from other packs.
        data = json.loads(json.dumps(result[0]))
        pack = data["pack"] + ", " + chartinfo.pack
        Chart = Query()
        db.update({"pack": pack}, Chart.md5 == chartinfo.md5)


def generate_md5(data):
    """Creates an MD5 hash using the songs chart and BPM data as the input, removing all whitespace before hashing."""
    return hashlib.md5(
        "".join(data).strip().replace(" ", "").replace("\n", "").replace("\r", "").encode("UTF-8")
    ).hexdigest()


def get_separator(length):
    """Returns the separator used in the simplified breakdowns."""
    if length <= 1:
        return " "
    elif length > 1 and length <= 4:
        return "-"
    elif length > 4 and length <= 32:
        return "/"
    else:
        return "|"


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


def remove_breakdown_characters(data):
    """Removes the breakdown separators.

    This removes the breakdown separators (i.e. parenthesis, asterisks, equal signs, and backslashes). Used when
    simplifying the partially simplified breakdown into the simplified breakdown."""
    data = data.replace("(", "").replace(")", "")
    data = data.replace("*", "")
    data = data.replace("=", "").replace("\\", "")
    return data


def find_max_bpm(bpms):
    """Finds largest BPM in an array of BPMs."""
    max_bpm = 0
    for bpm in bpms:
        if float(bpm[1]) > float(max_bpm):
            max_bpm = bpm[1]
    return max_bpm


def find_min_bpm(bpms):
    """Finds smallest BPM in an array of BPMs."""
    min_bpm = sys.maxsize
    for bpm in bpms:
        if float(bpm[1]) < float(min_bpm):
            min_bpm = bpm[1]
    return min_bpm


def find_max(data):
    """Finds largest number in an array of numbers."""
    max_data = 0
    for d in data:
        if d > max_data:
            max_data = d
    return max_data


def find_current_bpm(measure, bpms):
    """Finds the current BPM in a given measure of a song."""
    for bpm in bpms:
        if float(bpm[0]) <= measure:
            return bpm[1]


def create_density_graph(x, y, folder, difficulty, rating):
    """Creates the density graph.

    Parameters
    -----------
    x:
        An array containing the measure numbers.
    y:
        An array containing the density of each measure.
    folder:
        The folder to write the density graph to.
    difficulty:
        The difficulty of the chart. Used in the file creation of the image.
    rating:
        The rating of the chart. Used in the file creation of the image.
    """
    fig = go.Figure(go.Scatter(
        x=x, y=y, fill="tozeroy", fillcolor="yellow", line_color="orange", line=dict(width=0.5)
    ))
    fig.update_layout(
        plot_bgcolor="rgba(52,54,61,255)", paper_bgcolor="rgba(52,54,61,255)",
        margin=dict(l=10, r=10, b=10, t=10, pad=10),
        autosize=False, width=1000, height=400
    )
    fig.update_yaxes(visible=False)
    fig.update_xaxes(visible=False)
    fig.write_image(folder + difficulty + rating + "density.png")


def get_pattern_analysis(chart, num_notes):
    """Performs pattern analysis on a chart.

    This function will perform a series of pattern analysis of the chart that is passed in. It uses a series of regex
    search functions to obtain the data. It will return an analysis object.
    """
    # - - - CANDLE ANALYSIS - - -
    # Capture patterns that require one foot to move up to down, or vice versa.
    pattern = D_REG + NL_REG + R_REG + NL_REG + U_REG + OR_REG
    pattern += U_REG + NL_REG + R_REG + NL_REG + D_REG
    left_foot_candles = len(re.findall(re.compile(pattern), chart))

    pattern = D_REG + NL_REG + L_REG + NL_REG + U_REG + OR_REG
    pattern += U_REG + NL_REG + L_REG + NL_REG + D_REG
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

    # Begin to populate PatternAnalysis object
    analysis = pa.PatternAnalysis()
    analysis.left_foot_candles = left_foot_candles
    analysis.right_foot_candles = right_foot_candles

    total_candles = left_foot_candles + right_foot_candles
    analysis.total_candles = total_candles
    # Even though we use 3 notes to detect a candle, we only multiply by 2
    # since we only want to calculate the actual candle step, not the arrow in-between.
    # This means a song can be, at max, 66% candles
    # TODO: Revisit this, as most would assume a chart of all candles would be 100%.
    analysis.candles_percent = ((total_candles * 2)/num_notes) * 100

    # Multiplied by 8 as there are 8 notes for every instance of mono
    analysis.mono_percent = (((ld_ru_mono + lu_rd_mono) * 8)/num_notes) * 100

    analysis.lr_boxes = lr_boxes
    analysis.ud_boxes = ud_boxes
    analysis.corner_ld_boxes = corner_ld_boxes
    analysis.corner_lu_boxes = corner_lu_boxes
    analysis.corner_rd_boxes = corner_rd_boxes
    analysis.corner_ru_boxes = corner_ru_boxes
    analysis.anchor_left = anchor_left
    analysis.anchor_down = anchor_down
    analysis.anchor_up = anchor_up
    analysis.anchor_right = anchor_right

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
        elif re.search(r"[()]", b):
            if partially:
                current_measure = RunDensity.Break
                b = get_separator(int(remove_breakdown_characters(simplified[i])))
            else:
                if int(remove_breakdown_characters(b)) <= 4:
                    b = remove_breakdown_characters(b)
                    small_break = True
                else:
                    b = get_separator(int(remove_breakdown_characters(simplified[i])))
                    current_measure = RunDensity.Break
        else:
            current_measure = RunDensity.Run_16

        if current_measure == previous_measure and i > 0:
            previous_value = remove_breakdown_characters(simplified[i - 1])
            b = remove_breakdown_characters(b)
            simplified[i - 1] = ""
            if small_break and simplified:
                if current_measure == RunDensity.Run_32:
                    simplified[i] = "=" + str(int(previous_value) + int(b) - 1) + "=*"
                elif current_measure == RunDensity.Run_24:
                    simplified[i] = "\\" + str(int(previous_value) + int(b) - 1) + "\\*"
                else:
                    simplified[i] = str(int(previous_value) + int(b) - 1) + "*"
                small_break = False
            else:
                if current_measure == RunDensity.Run_32:
                    simplified[i] = "=" + str(int(previous_value) + int(b) - 1) + "=*"
                elif current_measure == RunDensity.Run_24:
                    simplified[i] = "\\" + str(int(previous_value) + int(b) - 1) + "\\*"
                else:
                    simplified[i] = str(int(previous_value) + int(b) - 1) + "*"
                simplified[i] = str(int(previous_value) + int(b) + 1) + "*"
        else:
            simplified[i] = b

        previous_measure = current_measure

    return " ".join(filter(None, simplified))


def get_density_and_breakdown(measures, bpms):
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
    measures_of_run = [0] * 4
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
    elif measures_of_run[RunDensity.Run_16.value] > 0:
        breakdown += str(measures_of_run[RunDensity.Run_16.value]) + " "

    analysis = get_pattern_analysis(chart_runs_only, notes)
    del chart_runs_only

    minutes = length // 60
    seconds = length % 60
    length = str(int(minutes)) + "m " + str(int(seconds)) + "s"

    total_break = adjust_total_break(total_break, measures)

    chartinfo = ci.ChartInfo(length, notes, jumps, holds, mines, hands, rolls, total_stream, total_break)

    return density, breakdown.strip(), chartinfo, analysis


def parse_chart(chart, title, subtitle, artist, pack, bpms, displaybpm, folder, db, log):
    """Retrieves and sets chart information.

    Grabs the charts step artist, difficulty, rating, and actual chart data. Calls most other functions in this file to
    handle pattern recognition and density breakdown. Calls the function to generate the density graph, and finally
    calls the function to save the chart info to the database.
    """
    metadata = chart.split(":")

    type = metadata[0].strip().replace(":", "")  # dance-single, etc.
    stepartist = metadata[1].strip().replace(":", "")
    difficulty = metadata[2].strip().replace(":", "")
    rating = metadata[3].strip().replace(":", "")
    chart = remove_comments(metadata[5])

    del metadata

    if type != "dance-single":
        return                          # we only want single charts

    if chart.strip() == ";":
        if log:
            log.write("INFO: The " + difficulty + " " + rating + " chart for " + title + " is empty. Skipping\n")
            log.flush()
        return                          # empty chart

    if not findall_with_regex(chart, ANY_NOTES_REG):
        if log:
            log.write("INFO: The " + difficulty + " " + rating + " chart for " + title + " is empty. Skipping\n")
            log.flush()
        return                          # chart only contains 0's

    measures = findall_with_regex(chart, r"[01234MF\s]+(?=[,|;])")

    # bpms need to be part of MD5 for most of the for business/for pleasure charts
    bpm_string = ""
    for bpm in bpms:
        # parsed to int, as we want to match 215.0000 with 215.0
        # only need a rough estimate for our purpose here
        bpm_string += str(int(float(bpm[0]))) + str(int(float(bpm[1])))

    md5 = generate_md5("".join(measures) + bpm_string)

    if measures == -1:
        if log:
            log.write("WARN: Unable to parse the " + difficulty + " " + rating + " chart for " + title + ". Skipping\n")
            log.flush()
        return

    density, breakdown, chartinfo, analysis = get_density_and_breakdown(measures, bpms)
    partially_simplified = get_simplified(breakdown, True)
    simplified = get_simplified(breakdown, False)

    max_bpm = find_max_bpm(bpms)
    min_bpm = find_min_bpm(bpms)
    max_nps = find_max(density)
    median_nps = statistics.median(density)

    create_density_graph(list(range(0, len(measures))), density, folder, difficulty, rating)

    chartinfo.title = title
    chartinfo.subtitle = subtitle
    chartinfo.artist = artist
    chartinfo.pack = pack
    chartinfo.stepartist = stepartist
    chartinfo.difficulty = difficulty
    chartinfo.displaybpm = displaybpm
    chartinfo.rating = rating
    chartinfo.breakdown = breakdown
    chartinfo.partial_breakdown = partially_simplified
    chartinfo.simple_breakdown = simplified
    chartinfo.max_bpm = max_bpm
    chartinfo.min_bpm = min_bpm
    chartinfo.max_nps = max_nps
    chartinfo.median_nps = median_nps
    chartinfo.graph_location = folder + difficulty + rating + "density.png"
    chartinfo.md5 = md5

    add_to_database(chartinfo, db, analysis)


def parse_file(filename, folder, pack, db, log, hide_artist_info):
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
        if log:
            log.write("ERROR: BPM for file \"" + filename + "\" is not readable. Skipping.\n")
            log.flush()
        return
    else:
        bpms = bpms.split(",")
        temp = []
        for bpm in bpms:
            if "#" in bpm:
                # Some BPMs are missing a trailing ; (30MIN HARDER in Cirque du Beast)
                bpm = bpm.split("#", 1)[0]
                if log:
                    log.write("WARN: BPM for file \"" + filename + "\" is missing semicolon. Handled and continuing.\n")
                    log.flush()
            # Quick way to remove non-printable characters that, for whatever reason,
            # exist in a few .sm files (Oceanlab Megamix)
            old_bpm = bpm
            bpm = "".join(filter(lambda c: c in string.printable, bpm))
            if log and old_bpm != bpm:
                log.write("WARN: BPM for file \"" + filename + "\" contains non-printable characters. Handled and continuing.\n")
                log.flush()
            bpm = bpm.strip().split("=")
            temp.insert(0, bpm)
        bpms = temp
    displaybpm = find_with_regex(data, r"#DISPLAYBPM:(.*);")
    charts = findall_with_regex_dotall(data, r"#NOTES:(.*?);")

    if charts == -1:
        if log:
            log.write("ERROR: Unable to parse chart(s) data for \"" + filename + "\". Skipping.\n")
            log.flush()
        return
    else:
        for i, chart in enumerate(charts):
            sanity_check = chart.split("\n", 6)
            if len(sanity_check) != 7:
                if log:
                    log.write("WARN: Unable to parse chart(s) data for \"" + filename + "\". Attempting to handle...\n")
                    log.flush()
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
                    if log:
                        log.write("ERROR: Unable to parse \"" + filename + "\" correctly. Skipping.\n")
                        log.flush()
                    return
            parse_chart(chart + ";", title, subtitle, artist, pack, bpms, displaybpm, folder, db, log)

def scan_folder(dir, verbose, media_remove, db, log):
    # First fetch total number of found .sm files
    total = 0
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.lower().endswith(".sm"):
                total += 1

    if total <= 0:
        return # no .sm files found

    i = 0 # Current file
    for root, dirs, files in os.walk(dir):

        sm_counter = len(glob.glob1(root, "*.sm"))

        if sm_counter <= 0:
            if log:
                log.write("INFO: There are no .sm file(s) in folder \"" + root + "\". Skipping folder.\n")
                log.flush()
            continue  # no .sm files in current directory, continue to next folder
        elif sm_counter >= 2:
            if log:
                log.write("ERROR: There are more than 1 .sm file in folder \"" + root + "\". Skipping folder.\n")
                log.flush()
            i += sm_counter
            continue

        for file in files:
            filename = root + "/" + file
            if file.lower().endswith(".sm"):
                i += 1
                folder = root + "/"
                pack = os.path.basename(Path(folder).parent)
                if verbose:
                    output_i, output_total = vh.normalize_num(i, total)
                    output = "[" + output_i + "/" + output_total + "] "
                    output_percent = "[" + vh.get_percent(i, total) + "]"
                    output += output_percent + " Pack: "
                    output += vh.normalize_string(pack, 30) + " File: "
                    output += vh.normalize_string(file, 30)
                    print(output, end="\r")
                if log:
                    log.write("INFO: Preparing to parse \"" + filename + "\".\n")
                    log.flush()
                parse_file(filename, folder, pack, db, log, False)
                if log:
                    log.write("INFO: Completed parsing \"" + filename + "\".\n")
                    log.flush()
            if media_remove:
                if file.lower().endswith(".ogg") or file.lower().endswith(".mpg") or file.lower().endswith(".avi"):
                    os.remove(root + "/" + file)
                    if log:
                        log.write("INFO: Removed \"" + filename + "\".\n")
                        log.flush()

    if verbose:
        output_i, output_total = vh.normalize_num(i, total)
        output = "[" + output_i + "/" + output_total + "] "
        output_percent = "[" + vh.get_percent(i, total) + "] "
        output += output_percent
        output += vh.normalize_string("Complete!", 75)
        print(output)

    if log:
        ct = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        log.write("scan.py finished at: " + ct)
        log.write("\n")
        log.flush()

def main(argv):
    try:
        arguments, values = getopt.getopt(argv[1:], SHORT_OPTIONS, LONG_OPTIONS)
    except getopt.error as err:
        print(str(err))
        sys.exit(2)

    verbose = False
    media_remove = False
    unittest = False
    log = None

    for arg, val in arguments:
        if arg in ("-r", "--rebuild") and os.path.isfile(DATABASE_NAME):
            os.remove(DATABASE_NAME)
        elif arg in ("-v", "--verbose"):
            verbose = True
        elif arg in ("-d", "--directory"):
            dir = val
        elif arg in ("-m", "--mediaremove"):
            media_remove = True
        elif arg in ("-l", "--log"):
            log = open(LOGFILE_NAME, "a")
        elif arg in ("-u", "--unittest"):
            unittest = True
    
    db = TinyDB(DATABASE_NAME)

    if unittest:
        database = UNITTEST_FOLDER + "/" + DATABASE_NAME
        songs = UNITTEST_FOLDER + "/" + "songs"
        log_location = UNITTEST_FOLDER + "/" + LOGFILE_NAME
        if os.path.isfile(log_location):
            os.remove(log_location)
        if os.path.isfile(database):
            os.remove(database)
        log = open(log_location, "a")
        db = TinyDB(database)
        scan_folder(songs, verbose, media_remove, db, log)
        test.run_tests()
        sys.exit(0)
    else:
        if log:
            ct = datetime.datetime.now().strftime(LOG_TIMESTAMP)
            log.write("scan.py started at: " + ct)
            log.write("\n")
            log.flush()

        if os.path.isdir(dir):
            scan_folder(dir, verbose, media_remove, db, log)
        else:
            print("\"" + dir + "\" is not a valid directory. Exiting.")
            sys.exit(2)

        db.close()
        os.chmod(DATABASE_NAME, 0o777)
        sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)