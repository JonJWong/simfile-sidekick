# -*- coding: utf-8 -*-
"""An object that contains chart information for a simfile.

This object contains information relevant to a chart, such as the step artist, difficulty, rating, etc.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst, this version is maintained/updated by JWong.
"""

from helpers.GeneralHelper import generate_md5
from objects import NotesInfo, PatternInfo
from typing import List
import weakref


class ChartInfo(object):
    stepartist: str = ""
    difficulty: str = ""
    rating: str = ""
    measures: List[str] = []

    md5: str = ""
    path_prefix: str = ""  # Used when saving images like the density graph
    graph_location: str = ""

    length: str = ""
    max_nps: float = 0.0
    median_nps: float = 0.0
    total_stream: int = 0
    total_break: int = 0
    breakdown: str = ""  # Entire breakdown of density
    partial_breakdown: str = ""  # Uses all break symbols
    simple_breakdown: str = ""  # Uses all break symbols except -
    normalized_breakdown: str = ""
    notesinfo: NotesInfo = None
    patterninfo: PatternInfo = None

    def __init__(self, parent, stepartist: str, difficulty: str, rating: str,
                 measures: List[str]):
        self.parent = weakref.ref(
            parent)  # Allows ChartInfo to access FileInfo

        self.stepartist = stepartist
        self.difficulty = difficulty
        self.rating = rating
        self.measures = measures

        self.md5 = generate_md5(parent.bpms, measures)
        self.path_prefix = difficulty + rating
        self.graph_location = parent.folder + self.path_prefix + "graph.png"
