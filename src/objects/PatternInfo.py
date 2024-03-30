# -*- coding: utf-8 -*-

"""A object that contains the pattern info for a chart.

This object contains the analysis of patterns in a chart, such as mono, candles, and anchors.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst for the Dickson City Heroes and Stamina Nation.
"""


class PatternInfo(object):
    left_foot_candles: int = 0
    right_foot_candles: int = 0
    total_candles: int = 0

    mono_percent: float = 0.0

    anchor_left: int = 0
    anchor_down: int = 0
    anchor_up: int = 0
    anchor_right: int = 0

    double_stairs_count: int = 0
    double_stairs_array: []
    doublesteps_count: int = 0
    doublesteps_array: []
    jumps_count: int = 0
    jumps_array: []
    mono_count: int = 0
    mono_array: []
    box_count: int = 0
    box_array: []

    def __init__(self, left_foot_candles: int, right_foot_candles: int,
                 total_candles: int, mono_percent: float, anchor_left: int,
                 anchor_down: int, anchor_up: int, anchor_right: int,
                 double_stairs_count: int, double_stairs_array: [],
                 doublesteps_count: int, doublesteps_array: [],
                 jumps_count: int, jumps_array: [], mono_count: int,
                 mono_array: [], box_count: int, box_array: []):
        self.left_foot_candles = left_foot_candles
        self.right_foot_candles = right_foot_candles
        self.total_candles = total_candles
        self.mono_percent = mono_percent
        self.anchor_left = anchor_left
        self.anchor_down = anchor_down
        self.anchor_up = anchor_up
        self.anchor_right = anchor_right
        self.double_stairs_count = double_stairs_count
        self.double_stairs_array = double_stairs_array
        self.doublesteps_count = doublesteps_count
        self.doublesteps_array = doublesteps_array
        self.jumps_count = jumps_count
        self.jumps_array = jumps_array
        self.mono_count = mono_count
        self.mono_array = mono_array
        self.box_count = box_count
        self.box_array = box_array
