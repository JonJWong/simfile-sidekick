import discord
from globals import STR_TO_EMOJI, MAX_DISCORD_FIELD_CHARS, VALID_PARAMS


def get_mono_desc(mono):
    """Helper function to return pre-formatted text used in mono pattern analysis."""
    if mono == 0:
        return "*None*"
    if mono > 0 and mono < 10:
        return "*Low*"
    elif mono >= 10 and mono < 30:
        return "Kinda"
    elif mono >= 30 and mono < 50:
        return "**Quite Mono**"
    elif mono > 50:
        return "__**WTF**__"


def normalize_float(num):
    """Helper function that returns a floating point number to 2 decimal places."""
    return "{:.2f}".format(float(num))


def __create_pattern_info(pattern_name, pattern_type, step_data):
    pattern_count = step_data[pattern_type + "_count"]
    # If there's no data, return an empty string
    if pattern_count <= 0:
        return ""
    
    pattern_str = f'**{pattern_name}**: {pattern_count}, found in measure:\n'
    
    data_obj = {}

    # Group data by measure
    for entry in step_data[pattern_type + "_array"]:
        measure, datum = entry
        data_obj.setdefault(measure, []).append(datum)

    # Sort measures numerically if possible, placing "Sweep" before 7 but after 6
    data_obj_keys = sorted(data_obj.keys(), key=lambda x: (isinstance(x, int), x if isinstance(x, int) else float('inf'), x))

    # Build the pattern string
    for pattern_name in data_obj_keys:
        datum = data_obj[pattern_name]
        pattern_str += f'**{pattern_name}**: {", ".join(map(str, datum))}\n'

    pattern_str = f'**{pattern_name}**: {pattern_count}, found in measure:\n'

    data_obj = {}

    # Group data by measure
    for entry in step_data[pattern_type + "_array"]:
        measure, datum = entry
        data_obj.setdefault(measure, []).append(datum)

    # Sort measures numerically if possible, placing "Sweep" before 7 but after 6
    data_obj_keys = sorted(data_obj.keys(),
                           key=lambda x:
                           (isinstance(x, int), x
                            if isinstance(x, int) else float('inf'), x))

    # Build the pattern string
    for pattern_name in data_obj_keys:
        datum = data_obj[pattern_name]
        pattern_str += f'**{pattern_name}**: {", ".join(map(str, datum))}\n'

    return pattern_str


def get_footer_image(level):
    """Helper function that returns a fancy image for the difficulty of a chart."""
    if STR_TO_EMOJI.get(level):
        return STR_TO_EMOJI[level]
    else:
        return STR_TO_EMOJI["wun"]


def splice_until_last_space(string, max_length=MAX_DISCORD_FIELD_CHARS):
    if len(string) <= max_length:
        return string

    last_space_index = string.rfind(" ", 0, max_length)

    if last_space_index == -1:
        return string[:max_length]

    return string[:last_space_index], string[last_space_index:]


def __break_string_into_sections(string, max_length=MAX_DISCORD_FIELD_CHARS):
    sections = []

    if len(string) > max_length:
        string_to_slice = string

        while len(string_to_slice) > max_length:
            first_half, last_half = splice_until_last_space(string_to_slice)
            sections.append(first_half)
            string_to_slice = last_half

    return sections


def float_to_string(input):
    return str(int(float(input)))

def add_field_with_split(embed, name, value):
    if len(value) > MAX_DISCORD_FIELD_CHARS:
        parts = [value[i:i + MAX_DISCORD_FIELD_CHARS] for i in range(0, len(value), MAX_DISCORD_FIELD_CHARS)]
        for num, part in enumerate(parts, start=1):
            embed.add_field(name=f"{name} *(Part {num})*", value=part, inline=False)
    else:
        embed.add_field(name=name, value=value, inline=False)

def __append_appropriate_info(params, step_data, pattern_embed):
    param_to_pattern = {
        "box": ("Boxes", "box"),
        "dstep": ("Doublesteps", "doublesteps"),
        "dstair": ("Double stairs", "double_stairs"),
        "ju": ("Mid Stream Jumps", "jumps"),
        "mono": ("Monos", "mono")
    }

    formatted_params = set(param.lower() for param in params)

    if "all" in formatted_params:
        formatted_params = param_to_pattern.keys()

    for param, (pattern, param_str) in param_to_pattern.items():
        if param in formatted_params:
            param_pattern_str = __create_pattern_info(pattern, param_str,
                                                      step_data)

            if param_pattern_str and len(param_pattern_str) > 1024:
                for pattern_section in __break_string_into_sections(
                        param_pattern_str):
                    pattern_embed.add_field(name='',
                                            value=pattern_section,
                                            inline=False)
            elif param_pattern_str:
                pattern_embed.add_field(name='',
                                        value=param_pattern_str,
                                        inline=False)


def add_field_with_split(embed, name, value):
    if len(value) > MAX_DISCORD_FIELD_CHARS:
        parts = [
            value[i:i + MAX_DISCORD_FIELD_CHARS]
            for i in range(0, len(value), MAX_DISCORD_FIELD_CHARS)
        ]
        for num, part in enumerate(parts, start=1):
            embed.add_field(name=f"{name} *(Part {num})*",
                            value=part,
                            inline=False)
    else:
        embed.add_field(name=name, value=value, inline=False)


def create_embed(data, ctx, params=None):
    embed = discord.Embed(description=f"Requested by {ctx.author.mention}")

    # Song Details
    song_details = ""
    if data["title"] == "*Hidden*" and data["artist"] == "*Hidden*":
        song_details += "*<Title and artist hidden>*\n"
    else:
        song_details += f'**{data["title"]}** '
        if data["subtitle"] and data["subtitle"] != "N/A":
            song_details += f'*{data["subtitle"]}* '
        song_details += f'by **{data["artist"]}** \n'

    song_details += f'From pack(s): {data["pack"]}\n'
    try:
        song_details += f'{get_footer_image(int(data["rating"]))} '
    except ValueError:
        song_details += f'{get_footer_image(-1)} '
    stepartist = data["stepartist"].replace("*", "\*")
    song_details += f'{data["difficulty"]} - {stepartist}\n\n'
    song_details += f'__Song Length__: {data["length"]}\n'

    if data["display_bpm"] and data["display_bpm"] != "N/A":
        song_details += "__Display BPM__: "
        display_bpm_range = data["display_bpm"].split(":")
        song_details += f'{float_to_string(display_bpm_range[0])}-{float_to_string(display_bpm_range[1])}\n' if ":" in data[
            "display_bpm"] else f'{float_to_string(data["display_bpm"])}\n'

    song_details += f"__BPM__: {float_to_string(data['min_bpm'])}-{float_to_string(data['max_bpm'])}\n"
    song_details += f'__Peak NPS__: **{normalize_float(data["max_nps"])}** notes/s.\n'
    song_details += f'__Median NPS__: **{normalize_float(data["median_nps"])}** notes/s.\n'

    total_measures = data["total_stream"] + data["total_break"]
    if total_measures != 0:
        stream_percent = normalize_float(
            (data["total_stream"] / total_measures) * 100)
        break_percent = normalize_float(
            (data["total_break"] / total_measures) * 100)
        song_details += f'__Total Stream__: **{data["total_stream"]}** measures ({stream_percent}%)\n'
        song_details += f'__Total Break__: **{data["total_break"]}** measures ({break_percent}%)\n'

    embed.add_field(name="__Song Details__", value=song_details)

    # Chart Info
    chart_info_keys = ["notes", "jumps", "holds", "mines", "hands", "rolls"]
    chart_info = "\n".join([
        f'__{key.capitalize()}:__ {str(data[key])}' for key in chart_info_keys
        if key in data
    ])
    embed.add_field(name="__Chart Info__", value=chart_info, inline=True)

    # Pattern Analysis
    pattern_analysis = (
        "*Analysis does not consider patterns in break segments, or microholds in runs.*\n"
    )

    # Candles
    pattern_analysis += (f'__Candles__: **{data["total_candles"]}** '
                         f'({data["left_foot_candles"]} left, '
                         f'{data["right_foot_candles"]} right)\n')
    candle_density = data["total_candles"] / data["total_stream"] if data[
        "total_stream"] else 0
    pattern_analysis += f'__Candle density__: {normalize_float(candle_density)} candles/measure\n'

    # Mono
    pattern_analysis += (f'__Mono__: {normalize_float(data["mono_percent"])}% '
                         f'({get_mono_desc(data["mono_percent"])})\n')

    # Anchors
    total_anchors = sum([
        data[key]
        for key in ["anchor_left", "anchor_down", "anchor_up", "anchor_right"]
    ])
    pattern_analysis += (f'__Anchors__: **{total_anchors}** '
                         f'({data["anchor_left"]} left, '
                         f'{data["anchor_down"]} down, '
                         f'{data["anchor_up"]} up, '
                         f'{data["anchor_right"]} right)\n')

    embed.add_field(name="__Pattern Analysis__",
                    value=pattern_analysis,
                    inline=False)

    pattern_embed = None

    valid_params_passed_in = [
        param for param in params if param in VALID_PARAMS
    ]

    if len(valid_params_passed_in) > 0:
        pattern_embed = discord.Embed(
            description=f"Pattern analysis for: {data['title']}")
        __append_appropriate_info(params, data, pattern_embed)


    # - - - BREAKDOWNS - - -

    # Detailed Breakdown
    if data["breakdown"]:
        add_field_with_split(embed, "__Detailed Breakdown__",
                             data["breakdown"])

    # Partially Simplified
    if data["partial_breakdown"] != data["simple_breakdown"]:
        add_field_with_split(embed, "__Partially Simplified__",
                             data["partial_breakdown"])

        # Simplified Breakdown
        add_field_with_split(embed, "__Simplified Breakdown__",
                             data["simple_breakdown"])

    # Normalized Breakdown
    if data["normalized_breakdown"]:
        text = "*This is in beta and may be inaccurate. Variable BPM songs may report incorrect BPM.*\n"
        add_field_with_split(embed, "__Normalized Breakdown__",
                             text + data["normalized_breakdown"])

    # - - - FOOTER - - -
    file = discord.File(data["graph_location"], filename="density.png")

    embed.set_image(url="attachment://density.png")

    return embed, pattern_embed, file
