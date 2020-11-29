class ChartInfo:
    """
    An object to contain all of a chart's info.
    """

    title = ""
    subtitle = ""
    artist = ""
    pack = ""

    length = ""
    notes = 0
    jumps = 0
    holds = 0
    mines = 0
    hands = 0
    rolls = 0
    total_stream = 0
    total_break = 0

    displaybpm = ""
    stepartist = ""
    difficulty = ""
    rating = ""
    breakdown = ""
    partial_breakdown = ""
    simple_breakdown = ""
    max_bpm = ""
    min_bpm = ""
    max_nps = ""
    median_nps = ""
    graph_location = ""
    md5 = ""

    def __init__(self, length, notes, jumps, holds, mines, hands, rolls, total_stream, total_break):
        self.length = length
        self.notes = notes
        self.jumps = jumps
        self.holds = holds
        self.mines = mines
        self.hands = hands
        self.rolls = rolls
        self.total_stream = total_stream
        self.total_break = total_break