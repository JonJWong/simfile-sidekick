# -*- coding: utf-8 -*-
"""Contains common helper methods used in various parts of Simfile Sidekick.

Various common functions are defined here that are used throughout Simfile Sidekick.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst, this version is maintained/updated by JWong.
"""

from typing import List
import hashlib
import re
import sys


def find_max_bpm(bpms: List[List[str]]) -> str:
    """ Finds largest BPM in an array of BPMs.

    @param bpms: The bpms array.
    @return: The largest BPM found in the array.
    """
    max_bpm = 0
    for bpm in bpms:
        if float(bpm[1]) > float(max_bpm):
            max_bpm = bpm[1]
    return max_bpm


def find_min_bpm(bpms: List[List[str]]) -> str:
    """ Finds smallest BPM in an array of BPMs.

    @param bpms: The bpms array.
    @return: The smallest BPM found in the array.
    """
    min_bpm = sys.maxsize
    for bpm in bpms:
        if float(bpm[1]) < float(min_bpm):
            min_bpm = bpm[1]
    return min_bpm


def remove_comments(chart: str) -> str:
    """ Removes lines in a chat that begin with //.

    @param chart: The chart.
    @return: The chart without comment lines starting with //.
    """
    return re.sub("//(.*)", "", chart)


def generate_md5(bpms: List[List[str]], measures: List[str]) -> str:
    """ Generates an md5 fingerprint for the chart, using the measures and BPMs as input. Since the MD5 is used in cache
    generation to identify identical charts, the BPMs array needs to be part of the MD5 to differentiate between for
    business/for pleasure charts.

    @param bpms: The bpms array.
    @param measures: The chart, each measure in an array.
    @return: The generated MD5 fingerprint.
    """
    bpm_string = ""
    for bpm in bpms:
        # Parsed to int, as we want to match 215.0000 with 215.0; we only need a rough estimate for matching.
        bpm_string += str(int(float(bpm[0]))) + str(int(float(bpm[1])))
    data = "".join(measures) + bpm_string
    return hashlib.md5("".join(data).strip().replace(" ", "").replace(
        "\n", "").replace("\r", "").encode("UTF-8")).hexdigest()
