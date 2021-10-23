# -*- coding: utf-8 -*-

"""An object that contains basic simfile info.

This object contains header level information that doesn't change between chart difficulties, for example: the title,
subtitle, artist, pack, and BPM information. This is the parent object that contains all other objects.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst for the Dickson City Heroes and Stamina Nation.
"""

from common.objects import ChartInfo
from common.GeneralHelper import find_max_bpm, find_min_bpm
from typing import List


class FileInfo(object):
    title: str = ""
    subtitle: str = ""
    artist: str = ""
    pack: str = ""
    bpms: List[List[str]] = []  # List that contains a list of measure/BPM pairs. [0] is measure # that BPM [1] is set.
    displaybpm: str = ""
    folder: str = ""

    max_bpm: float = 0.0
    min_bpm: float = 0.0

    chartinfo: ChartInfo = None

    def __init__(self, title: str, subtitle: str, artist: str, pack: str, bpms: List[List[str]], displaybpm: str,
                 folder: str):
        self.title = title
        self.subtitle = subtitle
        self.artist = artist
        self.pack = pack
        self.bpms = bpms
        self.displaybpm = displaybpm
        self.folder = folder

        self.max_bpm = float(find_max_bpm(bpms))
        self.min_bpm = float(find_min_bpm(bpms))
