import json
from tinydb import where, Query
from .scanconstants import CSV_FILENAME


def load_md5s_into_cache(db, cache):
    charts = db.all()
    for chart in charts:
        cache.insert({"md5": chart["md5"]})
    return cache


def database_to_csv(db):
    """Gets every row of the database and saves relevant info to a .csv"""
    charts = db.all()
    with open(CSV_FILENAME, 'w') as f:
        f.write("title,subtitle,artist,pack\n")
        for chart in charts:
            f.write(chart["title"] + "," + chart["subtitle"] + "," +
                    chart["artist"] + "," + chart["pack"] + "\n")
    return


def add_to_database(fileinfo, db, cache):
    """Adds the chart information and pattern analysis to the TinyDB database."""

    result = None

    # Search if the chart already exists in our database.
    if cache is not None:
        # We are using the MD5 MemoryStorage. Check if the MD5 exists there
        result = cache.search(where("md5") == fileinfo.chartinfo.md5)
        cache.insert({"md5": fileinfo.chartinfo.md5})
    else:
        # We weren't provided a MD5 MemoryStorage, so we have to query the database.
        result = db.search(where("md5") == fileinfo.chartinfo.md5)

    if not result:
        # If the chart doesn't exist, add a new entry.
        db.insert({
            "title": fileinfo.title,
            "subtitle": fileinfo.subtitle,
            "artist": fileinfo.artist,
            "pack": fileinfo.pack,
            "length": fileinfo.chartinfo.length,
            "notes": fileinfo.chartinfo.notesinfo.notes,
            "jumps": fileinfo.chartinfo.notesinfo.jumps,
            "holds": fileinfo.chartinfo.notesinfo.holds,
            "mines": fileinfo.chartinfo.notesinfo.mines,
            "hands": fileinfo.chartinfo.notesinfo.hands,
            "rolls": fileinfo.chartinfo.notesinfo.rolls,
            "total_stream": fileinfo.chartinfo.total_stream,
            "total_break": fileinfo.chartinfo.total_break,
            "stepartist": fileinfo.chartinfo.stepartist,
            "difficulty": fileinfo.chartinfo.difficulty,
            "rating": fileinfo.chartinfo.rating,
            "breakdown": fileinfo.chartinfo.breakdown,
            "partial_breakdown": fileinfo.chartinfo.partial_breakdown,
            "simple_breakdown": fileinfo.chartinfo.simple_breakdown,
            "normalized_breakdown": fileinfo.chartinfo.normalized_breakdown,
            "left_foot_candles":
            fileinfo.chartinfo.patterninfo.left_foot_candles,
            "right_foot_candles":
            fileinfo.chartinfo.patterninfo.right_foot_candles,
            "total_candles": fileinfo.chartinfo.patterninfo.total_candles,
            "mono_percent": fileinfo.chartinfo.patterninfo.mono_percent,
            "anchor_left": fileinfo.chartinfo.patterninfo.anchor_left,
            "anchor_down": fileinfo.chartinfo.patterninfo.anchor_down,
            "anchor_up": fileinfo.chartinfo.patterninfo.anchor_up,
            "anchor_right": fileinfo.chartinfo.patterninfo.anchor_right,
            "double_stairs_count":
            fileinfo.chartinfo.patterninfo.double_stairs_count,
            "double_stairs_array":
            fileinfo.chartinfo.patterninfo.double_stairs_array,
            "doublesteps_count":
            fileinfo.chartinfo.patterninfo.doublesteps_count,
            "doublesteps_array":
            fileinfo.chartinfo.patterninfo.doublesteps_array,
            "jumps_count": fileinfo.chartinfo.patterninfo.jumps_count,
            "jumps_array": fileinfo.chartinfo.patterninfo.jumps_array,
            "mono_count": fileinfo.chartinfo.patterninfo.mono_count,
            "mono_array": fileinfo.chartinfo.patterninfo.mono_array,
            "box_count": fileinfo.chartinfo.patterninfo.box_count,
            "box_array": fileinfo.chartinfo.patterninfo.box_array,
            "display_bpm": fileinfo.displaybpm,
            "max_bpm": fileinfo.max_bpm,
            "min_bpm": fileinfo.min_bpm,
            "max_nps": fileinfo.chartinfo.max_nps,
            "median_nps": fileinfo.chartinfo.median_nps,
            "graph_location": fileinfo.chartinfo.graph_location,
            "md5": fileinfo.chartinfo.md5
        })
    else:
        # If the chart already exists (i.e. we have a matching MD5), we want to update the entry and append the pack to
        # it. This usually happens with ECS or SRPG songs taken from other packs.
        if cache:
            # result is currently set to MemoryStorage, so grab the db entry
            result = db.search(where("md5") == fileinfo.chartinfo.md5)
        data = json.loads(json.dumps(result[0]))
        pack = data["pack"] + ", " + fileinfo.pack
        Chart = Query()
        db.update({"pack": pack}, Chart.md5 == fileinfo.chartinfo.md5)
