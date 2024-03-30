# -*- coding: utf-8 -*-

"""Helper function that is responsible for normalizing breakdowns if the song is mostly 32nds,
24ths, 20ths, etc.
"""

from helpers.BreakdownHelper import remove_all_breakdown_chars
from enums.RunDensity import RunDensity
import math

# Percent of the song that meets normalization criteria. If, for example, the song has over 50%
# 20th notes, it will normalize the breakdown to 20th notes.
NORMALIZE_THRESHOLD = 0.50


def if_should_normalize(breakdown: str, total_stream: int):
    """
    Takes the breakdown and total_stream. Returns the enum that meets NORMALIZE_THRESHOLD. The most
    dense normalizations are prioritized (e.g. it will first check if the chart can be normalized
    to 32nds, then 24ths, then 20ths, etc.)

    :param breakdown: chart's detailed breakdown
    :param total_stream: measures of stream that exist in chart
    :return: enum RunDensity (see scan.py)
    """

    # An array that will keep track of the total number of runs at the specific density (16ths,
    # 20ths, 24ths, 32nds, etc.)
    measures_of_run = [0] * len(RunDensity)

    for b in breakdown.split(" "):
        if b.find("=") != -1:
            measures_of_run[RunDensity.Run_32.value] += int(b.replace("=", ""))
        elif b.find("\\") != -1:
            measures_of_run[RunDensity.Run_24.value] += int(
                b.replace("\\", ""))
        elif b.find("~") != -1:
            measures_of_run[RunDensity.Run_20.value] += int(b.replace("~", ""))
        elif b.find("(") != -1:
            measures_of_run[RunDensity.Break.value] += int(
                b.replace("(", "").replace(")", ""))
        else:
            measures_of_run[RunDensity.Run_16.value] += int(b)

    # Start with the most dense. If we don't meet the threshold, see if we can normalize to the
    # next lowest density.
    for rd in reversed(RunDensity):
        if rd == RunDensity.Run_16 or rd == RunDensity.Break:
            # The density is already created using 16th notes. Checking breaks as a failsafe.
            continue
        if (measures_of_run[rd.value] / total_stream) > NORMALIZE_THRESHOLD:
            return rd

    # The chart doesn't have enough stream to meet our NORMALIZE_THRESHOLD, return default enum of
    # Run_16
    return RunDensity.Run_16


def normalize(breakdown: str, bpm: float, normalize_to: RunDensity):
    """
    Normalizes a breakdown for charts that are mostly 32nd, 24th, or 20th note runs.

    :param breakdown: chart's detailed breakdown
    :param bpm: BPM of the chart
    :param normalize_to: enum RunDensity (selected density to normalize to)
    :return: normalized breakdown of chart
    """

    # TODO
    # We will eventually have to make use of the density array in this function. Songs like "Groovy
    # Fire, Rushing Wind" switch between 234bpm 16th notes and 156bpm 24th notes - which is the
    # same density. This function currently doesn't account for BPM changes.

    breakdown_icon = ""
    multiplier = 1

    if normalize_to == RunDensity.Run_32:
        breakdown_icon = "="
        multiplier = 2
    elif normalize_to == RunDensity.Run_24:
        breakdown_icon = "\\"
        multiplier = 1.5
    elif normalize_to == RunDensity.Run_20:
        breakdown_icon = "~"
        multiplier = 1.25
    else:
        return None

    normalized_breakdown = []

    for b in breakdown.split(" "):

        # TODO
        # We will ultimately want to keep breakdown icons that are higher than the selected
        # normalization, e.g. in the instance we're supposed to normalize a song to 20ths but
        # the chart has minor 32nd note bursts. This is complicated, as we would have to define
        # new symbols. When a song is normalized to 20ths, 32nds would appear as some fraction of
        # a 25th note (32 / 1.25) if my understanding is correct.
        #
        # For now, we'll ignore those cases and simply add potential denser runs to the selected
        # normalization.

        if b.find(breakdown_icon) != -1:
            b = remove_all_breakdown_chars(b)
            # Use floor since we only want to multiply full measure runs
            b = str(math.floor(int(b) * multiplier))
            normalized_breakdown.append(b)
        else:
            # Treat everything slower* (see above) than selected density as break
            b = remove_all_breakdown_chars(b)
            # Use floor since we only want to multiply full measure runs
            b = str(math.floor(int(b) * multiplier))
            normalized_breakdown.append("(" + b + ")")

    # Runs through the normalized_breakdown and combines break segments
    for i, b in enumerate(normalized_breakdown):
        if i <= 0:
            # Don't do anything for the first element
            continue

        if normalized_breakdown[i-1].find("(") != -1 and b.find("(") != -1:
            # Previous measure and this measure are both breaks, so combine them
            prev_break = int(remove_all_breakdown_chars(
                normalized_breakdown[i-1]))
            this_break = int(remove_all_breakdown_chars(b))
            new_break = str(prev_break + this_break + 1)

            # Remove previous element (will be cleaned up with strip()) and add new break
            normalized_breakdown[i-1] = ""
            normalized_breakdown[i] = "(" + new_break + ")"

    # Appends the normalized BPM to the end of our breakdown array, if we have it
    if bpm:
        normalized_bpm = str(round(float(bpm) * multiplier))
        normalized_breakdown.append("*@" + normalized_bpm + "BPM*")

    return " ".join(list(filter(None, normalized_breakdown))).strip()


def get_best_bpm_to_use(min_bpm: float, max_bpm: float, median_nps: float, display_bpm: str):
    """
    Of the 4 provided parameters, takes the best guess at what the song's actual BPM is that's used
    throughout the majority of the song.
    :param min_bpm: minimum BPM of the chart
    :param max_bpm: maximum BPM of the chart
    :param median_nps: the charts median notes per second
    :param display_bpm: the display BPM of the chart
    :return: the best candidate of which BPM to use for normalization, or None
    """

    # Best scenario: the BPM doesn't change
    if min_bpm == max_bpm:
        return min_bpm

    # The BPM changes in the song. We'll assume it's minor BPM changes for sync purposes.
    # Try and use the display BPM.
    if display_bpm and display_bpm != "N/A":
        try:
            return float(display_bpm)
        except ValueError:
            pass

    # Try to derive BPM from the median NPS.
    if median_nps and median_nps != "N/A":
        return (float(median_nps) * 60) / 4

    return None
