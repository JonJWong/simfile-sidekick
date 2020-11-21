from pathlib import Path
from tinydb import Query, TinyDB, where
import enum
import getopt
import hashlib
import io
import json
import os
import plotly.graph_objects as go
import re
import statistics
import string
import sys
import time

SHORT_OPTIONS = "rvd:m"
LONG_OPTIONS = ["rebuild", "verbose", "directory=", "mediaremove"]

DATABASE_NAME = "new.json"

L_REG = "[124]+000"
D_REG = "0[124]+00"
U_REG = "00[124]+0"
R_REG = "000[124]+"
NL_REG = "[\s]+"
OR_REG = "|"
NO_NOTES_REG = "[03M][03M][03M][03M]"
ANY_NOTES_REG = "(.*)[124]+(.*)"


class RunDensity(enum.Enum):
    Break = 0
    Run_16 = 1
    Run_24 = 2
    Run_32 = 3


class ChartInfo:
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

class PatternAnalysis:
    left_foot_candles = 0
    right_foot_candles = 0
    total_candles = 0
    candles_percent = 0
    
    mono_percent = 0
    
    lr_boxes = 0
    ud_boxes = 0
    corner_ld_boxes = 0
    corner_lu_boxes = 0
    corner_rd_boxes = 0
    corner_ru_boxes = 0
    
    anchor_left = 0
    anchor_down = 0
    anchor_up = 0
    anchor_right = 0

def remove_comments(chart):
    return re.sub("//(.*)", "", chart)

def findall_with_regex_dotall(data, regex):
    try:
        return re.findall(regex, data, re.DOTALL)
    except AttributeError:
        return -1

def findall_with_regex(data, regex):
    try:
        return re.findall(regex, data)
    except AttributeError:
        return -1

def find_with_regex_dotall(data, regex):
    try:
        return re.search(regex, data, re.DOTALL).group(1)
    except AttributeError:
        return -1

def find_with_regex(data, regex):
    try:
        return re.search(regex, data).group(1)
    except AttributeError:
        return "N/A"

def add_to_database(chartinfo, db, analysis):
    result = db.search(where("md5") == chartinfo.md5)
    
    if not result:
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
        data = json.loads(json.dumps(result[0]))
        pack = data["pack"] + ", " + chartinfo.pack
        Chart = Query()
        db.update({"pack": pack}, Chart.md5 == chartinfo.md5)
    

def generate_md5(data):
    return hashlib.md5("".join(data).strip().replace(" ","").replace("\n","").replace("\r","").encode("UTF-8")).hexdigest()
    
def get_seperator(length):
    if length <= 1:
        return " "
    elif length > 1 and length <= 4:
        return "-"
    elif length > 4 and length <= 32:
        return "/"
    else:
        return "|"

# Adjusts the total break counter to consider long fadeouts
def adjust_total_break(total_break, measures):
    count = 0
    for i, measure in enumerate(reversed(measures)):
        lines = measure.strip().split("\n")
        for line in lines:
            count += 1
            if re.search(r"[124]", line):
                # Since we're navigating backwards through the list, break out
                # on the first arrow we find
                return total_break
            else:
                if count % len(lines) == 0:
                    if total_break > 0:
                        total_break -= 1
                    count = 0

def remove_breakdown_characters(data):
    data = data.replace("(", "").replace(")", "")
    data = data.replace("*", "")
    data = data.replace("=", "").replace("\\", "")
    return data

def find_max_bpm(bpms):
    max_bpm = 0
    for bpm in bpms:
        if float(bpm[1]) > float(max_bpm):
            max_bpm = bpm[1]
    return max_bpm

def find_min_bpm(bpms):
    min_bpm = sys.maxsize
    for bpm in bpms:
        if float(bpm[1]) < float(min_bpm):
            min_bpm = bpm[1]
    return min_bpm

def find_max(data):
    max_data = 0
    for d in data:
        if d > max_data:
            max_data = d
    return max_data

def find_current_bpm(measure, bpms):
    for bpm in bpms:
        if float(bpm[0]) <= measure:
            return bpm[1]

def create_density_graph(x, y, folder, difficulty, rating):
    fig = go.Figure(go.Scatter(
    x=x, y=y, fill="tozeroy", fillcolor="yellow", line_color="orange", line=dict(width=0.5)
    ))
    fig.update_layout(
        plot_bgcolor="rgba(52,54,61,255)", paper_bgcolor="rgba(52,54,61,255)",
        margin=dict(l = 10, r = 10, b = 10, t = 10, pad = 10),
        autosize=False, width=1000, height=400
    )
    fig.update_yaxes(visible=False)
    fig.update_xaxes(visible=False)
    fig.write_image(folder + difficulty + rating + "density.png")

def get_pattern_analysis(chart, num_notes):
    # Candle analysis
    pattern = D_REG + NL_REG + R_REG + NL_REG + U_REG + OR_REG
    pattern += U_REG + NL_REG + R_REG + NL_REG + D_REG
    left_foot_candles = len(re.findall(re.compile(pattern), chart))
    
    pattern = D_REG + NL_REG + L_REG + NL_REG + U_REG + OR_REG
    pattern += U_REG + NL_REG + L_REG + NL_REG + D_REG
    right_foot_candles = len(re.findall(re.compile(pattern), chart))
    
    # Mono analysis
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
    
    # Box analysis
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
    
    # Anchor analysis
    pattern = L_REG + NL_REG + ANY_NOTES_REG + NL_REG + L_REG + NL_REG + ANY_NOTES_REG + NL_REG + L_REG
    anchor_left = len(re.findall(re.compile(pattern), chart))
    
    pattern = D_REG + NL_REG + ANY_NOTES_REG + NL_REG + D_REG + NL_REG + ANY_NOTES_REG + NL_REG + D_REG
    anchor_down = len(re.findall(re.compile(pattern), chart))
    
    pattern = U_REG + NL_REG + ANY_NOTES_REG + NL_REG + U_REG + NL_REG + ANY_NOTES_REG + NL_REG + U_REG
    anchor_up = len(re.findall(re.compile(pattern), chart))
    
    pattern = R_REG + NL_REG + ANY_NOTES_REG + NL_REG + R_REG + NL_REG + ANY_NOTES_REG + NL_REG + R_REG
    anchor_right = len(re.findall(re.compile(pattern), chart))
    
    analysis = PatternAnalysis()
    analysis.left_foot_candles = left_foot_candles
    analysis.right_foot_candles = right_foot_candles
    
    total_candles = left_foot_candles + right_foot_candles
    analysis.total_candles = total_candles
    # Even though we use 3 notes to detect a candle, we only multiply by 2
    # since we only want to calculate the actual candle step, not the arrow in-between.
    # This means a song can be, at max, 66% candles
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
                b = get_seperator(int(remove_breakdown_characters(simplified[i])))
            else:
                if int(remove_breakdown_characters(b)) <= 4:
                    b = remove_breakdown_characters(b)
                    small_break = True
                else:
                    b = get_seperator(int(remove_breakdown_characters(simplified[i])))
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
            
            # HANDS CALCULATION
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
            for i, char in enumerate(line): # For each of the 4 possible arrows
                if char == "2" or char == "4": # If arrow is hold or roll
                    # We are currently holding an arrows
                    holding += 1
                if char == "3":
                    # We have let go of a hold or roll
                    holding -= 1
            #END HANDS CALCULATION
                    
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
    
    analysis = get_pattern_analysis(chart_runs_only, notes)
    del chart_runs_only
    
    minutes = length // 60
    seconds = length % 60
    length = str(int(minutes)) + "m " + str(int(seconds)) + "s"
    
    total_break = adjust_total_break(total_break, measures)
    
    
    
    chartinfo = ChartInfo(length, notes, jumps, holds, mines, hands, rolls, total_stream, total_break)
    
    
    return density, breakdown.strip(), chartinfo, analysis

def parse_chart(chart, title, subtitle, artist, pack, bpms, displaybpm, folder, db):
    metadata = chart.split("\n", 6)
    
    type = metadata[1].strip().replace(":", "") # dance-single, etc.
    stepartist = metadata[2].strip().replace(":", "")
    difficulty = metadata[3].strip().replace(":", "")
    rating = metadata[4].strip().replace(":", "")
    chart = remove_comments(metadata[6])
    
    del metadata
    
    if type != "dance-single":
        return # we only want single charts
    
    if chart.strip() == ";":
        return # empty chart
        
    measures = findall_with_regex(chart, r"[01234MF\s]+(?=[,|;])")
    
    # bpms need to be part of MD5 for most of the for business/for pleasure charts
    bpm_string = ""
    for bpm in bpms:
        # parsed to int, as 215.0000 = 215.0
        # only need a rough estimate for our purpose here
        bpm_string += str(int(float(bpm[0]))) + str(int(float(bpm[1])))
    
    md5 = generate_md5("".join(measures) + bpm_string)
    
    if measures == -1:
        print("Unable to parse " + difficulty + " chart for \"" + title + "\" in " + pack)
        print("Skipping to next chart/file.")
    
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

def parse_file(filename, folder, pack, db):
    file = open(filename, "r", errors="ignore")
    data = file.read()
    
    title = find_with_regex(data, r"#TITLE:(.*);")
    subtitle = find_with_regex(data, r"#SUBTITLE:(.*);")
    artist = find_with_regex(data, r"#ARTIST:(.*);")
    bpms = find_with_regex_dotall(data, r"#BPMS:(.*?)[;]+?")
    if bpms == -1:
        print("BPM for file \"" + filename + "\" is not readable.")
        print("Skipping to next file.")
        return
    else:
        bpms = bpms.split(",")
        temp = []
        for bpm in bpms:
            if "#" in bpm:
                # Some BPMs are missing a trailing ;
                bpm = bpm.split("#", 1)[0]
            # Quick way to remove non-printable characters that, for whatever reason,
            # exist in a few .sm files
            bpm = "".join(filter(lambda c: c in string.printable, bpm))
            bpm = bpm.strip().split("=")
            temp.insert(0, bpm)
        bpms = temp
    displaybpm = find_with_regex(data, r"#DISPLAYBPM:(.*);")
    charts = findall_with_regex_dotall(data, r"#NOTES:(.*?);")
    
    if charts == -1:
        print("Unable to parse chart(s) data for \"" + filename + "\"")
        print("Skipping to next file.")
        return
    else:
        for i, chart in enumerate(charts):
            sanity_check = chart.split("\n", 6)
            if len(sanity_check) != 7:
                # There's something in this file that is causing the regex to not parse properly.
                # Usually a misplaced ; instead of a :
                # This is a quick and dirty attempt to salvage it.
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
                    print("Unable to parse " + filename + " correctly.")
                    print("Skipping to next file.")
                    return
            parse_chart(chart + ";", title, subtitle, artist, pack, bpms, displaybpm, folder, db)

def scan_folder(dir, verbose, media_remove, db):
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.lower().endswith(".sm"):
                filename = root + "/" + file
                folder = root + "/"
                pack = os.path.basename(Path(folder).parent)
                if verbose:
                    print("Currently processing: " + pack + " - " + file)
                parse_file(filename, folder, pack, db)
            if media_remove:
                if file.lower().endswith(".ogg") or file.lower().endswith(".mpg") or file.lower().endswith(".avi"):
                    os.remove(root + "/" + file)
                    if verbose:
                        print("Removed: " + pack + " - " + file)

def main(argv):
    try:
        arguments, values = getopt.getopt(argv[1:], SHORT_OPTIONS, LONG_OPTIONS)
    except getopt.error as err:
        print(str(err))
        sys.exit(2)
    
    verbose = False
    media_remove = False
    db = TinyDB(DATABASE_NAME)
    
    for arg, val in arguments:
        if arg in ("-r", "--rebuild"):
            if os.path.isfile(DATABASE_NAME):
                db.close()
                os.remove(DATABASE_NAME)
            db = TinyDB(DATABASE_NAME)
        elif arg in ("-v", "--verbose"):
            verbose = True
        elif arg in ("-d", "--directory"):
            dir = val
        elif arg in ("-m", "--mediaremove"):
            media_remove = True
    
    if os.path.isdir(dir):
        scan_folder(dir, verbose, media_remove, db)
    else:
        print("\"" + dir + "\" is not a valid directory. Exiting.")
        sys.exit(2)
    
    db.close()
    os.chmod(DATABASE_NAME, 0o777)
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)