# -*- coding: utf-8 -*-
"""Creates the RunDensity enum used through various parts of Simfile Sidekick. Used when generating breakdown to denote
when density changes, and also used in the normalization logic.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst, this version is maintained/updated by JWong.
"""

import enum


class RunDensity(enum.Enum):
    Break = 0  # Denotes a break (measure with less than 16 notes)
    Run_16 = 1  # Denotes a full measure of 16th notes
    Run_20 = 2  # Denotes a full measure of 20th notes
    Run_24 = 3  # Denotes a full measure of 24th notes
    Run_32 = 4  # Denotes a full measure of 32nd notes
