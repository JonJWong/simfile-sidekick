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
    candles_percent: float = 0.0

    mono_percent: float = 0.0

    lr_boxes: int = 0
    ud_boxes: int = 0
    corner_ld_boxes: int = 0
    corner_lu_boxes: int = 0
    corner_rd_boxes: int = 0
    corner_ru_boxes: int = 0

    anchor_left: int = 0
    anchor_down: int = 0
    anchor_up: int = 0
    anchor_right: int = 0

    def __init__(self, left_foot_candles: int, right_foot_candles: int, total_candles: int, candles_percent: float,
                 mono_percent: float, lr_boxes: int, ud_boxes: int, corner_ld_boxes: int, corner_lu_boxes: int,
                 corner_rd_boxes: int, corner_ru_boxes: int, anchor_left: int, anchor_down: int, anchor_up: int,
                 anchor_right: int):
        self.left_foot_candles = left_foot_candles
        self.right_foot_candles = right_foot_candles
        self.total_candles = total_candles
        self.candles_percent = candles_percent
        self.mono_percent = mono_percent
        self.lr_boxes = lr_boxes
        self.ud_boxes = ud_boxes
        self.corner_ld_boxes = corner_ld_boxes
        self.corner_lu_boxes = corner_lu_boxes
        self.corner_rd_boxes = corner_rd_boxes
        self.corner_ru_boxes = corner_ru_boxes
        self.anchor_left = anchor_left
        self.anchor_down = anchor_down
        self.anchor_up = anchor_up
        self.anchor_right = anchor_right