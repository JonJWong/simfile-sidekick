# -*- coding: utf-8 -*-

"""A object that contains info about the notes in a simfile.

This object contains the number of notes in a chart, as well as what type of notes they are (holds, hands, mines, etc.)

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst for the Dickson City Heroes and Stamina Nation.
"""


class NotesInfo(object):
    notes: int = 0
    jumps: int = 0
    holds: int = 0
    mines: int = 0
    hands: int = 0
    rolls: int = 0

    def __init__(self, notes: int, jumps: int, holds: int, mines: int, hands: int, rolls: int):
        self.notes = notes
        self.jumps = jumps
        self.holds = holds
        self.mines = mines
        self.hands = hands
        self.rolls = rolls

