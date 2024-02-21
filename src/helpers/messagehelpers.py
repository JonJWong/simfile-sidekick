import discord
import re
from globals import STR_TO_EMOJI


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


def __append_pattern_info(pattern_name, pattern_type, data, pattern_analysis):
    pattern_analysis += f'__{pattern_name}__: {data[pattern_type + "_count"]} \n'
    if data[pattern_type + '_count'] > 0:
        pattern_analysis += f'__{pattern_name[:-1]} locations__:\n'

        data_obj = {}
        for entry in data[pattern_type + "_array"]:
            measure, datum = entry
            if data_obj.get(measure):
                data_obj[measure].append(datum)
            else:
                data_obj[measure] = [datum]
        
        for measure in sorted(data_obj.keys()):
            datum = data_obj[measure]
            pattern_analysis += f'**{measure}**: '

            for i, entry in enumerate(datum):
                if i != len(datum) - 1:
                    pattern_analysis += f"{entry}, "
                else:
                    pattern_analysis += f"{entry}\n"

        # # Replace L, D, U, R with emojis
        # commented because the embed becomes too long
        # for entry in data[pattern_type + "_array"]:
        #     new_entry = entry.split(":")
        #     first_chars = [char for char in new_entry[0]]
        #     for i, char in enumerate(first_chars):
        #         if len(first_chars) > 2 and len(first_chars) % 2 == 0:
        #             if i % 2 == 0:
        #                 color = "red"
        #             else:
        #                 color = "blue"
        #         else:
        #             color = "red"

        #         first_chars[i] = STR_TO_EMOJI[f"{color}_{char}"]
        #     new_entry[0] = "".join(first_chars)
        #     new_entry = ":".join(new_entry)
        #     pattern_analysis += f'{new_entry}\n'

    return pattern_analysis


def get_footer_image(level):
    """Helper function that returns a fancy image for the difficulty of a chart."""
    if STR_TO_EMOJI.get(level):
        return STR_TO_EMOJI[level]
    else:
        return STR_TO_EMOJI["wun"]


def create_embed(data, ctx):
    embed = discord.Embed(
        description="Requested by {}".format(ctx.author.mention))

    # Add requester's avatar, commented out since displaying Chart Info on same
    # line would be too tight.
    # embed.set_thumbnail(url=ctx.message.author.avatar_url)

    # - - - SONG DETAILS - - -
    song_details = ""
    # Title, Subtitle, and Artist
    if data["title"] == "*Hidden*" and data["artist"] == "*Hidden*":
        song_details += "*<Title and artist hidden>*\n"
    else:
        song_details += f'**{data["title"]}** '
        if data["subtitle"] and data["subtitle"] != "N/A":
            song_details += f'*{data["subtitle"]}* '
        song_details += f'by **{data["artist"]}** \n'
    song_details += f'From pack(s): {data["pack"]}\n'
    # Rating, Difficulty, and Stepartist
    try:
        song_details += f'{get_footer_image(int(data["rating"]))} '
    except ValueError:
        song_details += f'{get_footer_image(-1)} '
    stepartist = data["stepartist"].replace("*", "\*")
    song_details += f'{data["difficulty"]} - {stepartist}\n\n'
    # Length
    song_details += f'__Song Length__: {data["length"]}\n'
    # Display BPM
    if data["display_bpm"] and data["display_bpm"] != "N/A":
        song_details += "__Display BPM__: "
        if re.search(r"[:]+", data["display_bpm"]):
            display_bpm_range = data["display_bpm"].split(":")
            song_details += f'{str(int(float(display_bpm_range[0])))}-'
            song_details += f'{str(int(float(display_bpm_range[1])))}\n'
        else:
            song_details += f'{str(int(float(data["display_bpm"])))}\n'
    # BPM
    song_details += "__BPM__: "
    if int(float(data["min_bpm"]) == int(float(data["max_bpm"]))):
        song_details += f'{str(int(float(data["min_bpm"])))}\n'
    else:
        song_details += f'{str(int(float(data["min_bpm"])))}-'
        song_details += f'{str(int(float(data["max_bpm"])))}\n'
    # NPS
    song_details += f'__Peak NPS__: **{normalize_float(data["max_nps"])}** notes/s. \n'
    song_details += f'__Median NPS__: **{normalize_float(data["median_nps"])}** notes/s.\n'
    # Total Stream/Break
    total_measures = data["total_stream"] + data["total_break"]
    if total_measures != 0:
        stream_percent = normalize_float(
            (data["total_stream"] / total_measures) * 100)
        break_percent = normalize_float(
            (data["total_break"] / total_measures) * 100)
        song_details += f'__Total Stream__: **{str(data["total_stream"])}** measures '
        song_details += f'({stream_percent}%)\n'
        song_details += f'__Total Break__: **{str(data["total_break"])}** measures '
        song_details += f'({break_percent}%)'

    embed.add_field(name="__Song Details__", value=song_details)

    # - - - CHART INFO - - -
    chart_info = ""
    chart_info += f'__Notes__: {str(data["notes"])}\n'
    chart_info += f'__Jumps__: {str(data["jumps"])}\n'
    chart_info += f'__Holds__: {str(data["holds"])}\n'
    chart_info += f'__Mines__: {str(data["mines"])}\n'
    chart_info += f'__Hands__: {str(data["hands"])}\n'
    chart_info += f'__Rolls__: {str(data["rolls"])}'

    embed.add_field(name="__Chart Info__", value=chart_info, inline=True)

    # - - - PATTERN ANALYSIS - - -
    pattern_analysis = f'*Analysis does not consider patterns in break segments, or microholds in runs.*\n'

    # Candles
    pattern_analysis += f'__Candles__: **{str(data["total_candles"])}** '
    pattern_analysis += f'({str(data["left_foot_candles"])} left, '
    pattern_analysis += f'{str(data["right_foot_candles"])} right)\n'
    candle_density = data["total_candles"] / (data["total_stream"]) if data["total_stream"] != 0 else 0
    pattern_analysis += f'__Candle density__: {str(normalize_float(candle_density))} candles/measure\n'

    # Mono
    pattern_analysis += f'__Mono__: {str(normalize_float(data["mono_percent"]))}% '
    pattern_analysis += f'({get_mono_desc(data["mono_percent"])})\n'

    # Anchors
    total_anchors = data["anchor_left"] + data["anchor_down"] + \
        data["anchor_up"] + data["anchor_right"]
    pattern_analysis += f'__Anchors__: **{str(total_anchors)}** '
    pattern_analysis += f'({str(data["anchor_left"])} left, '
    pattern_analysis += f'{str(data["anchor_down"])} down, '
    pattern_analysis += f'{str(data["anchor_up"])} up, '
    pattern_analysis += f'{str(data["anchor_right"])} right)\n'

    # (Potential) Errors
    if "-xtras" in ctx.message.content.split(" "):
        pattern_analysis = __append_pattern_info("Boxs", "box", data, pattern_analysis)
        pattern_analysis = __append_pattern_info("Doublesteps", "doublesteps", data, pattern_analysis)
        pattern_analysis = __append_pattern_info("Double stairs", "double_stairs", data, pattern_analysis)
        pattern_analysis = __append_pattern_info("Mid Stream Jumps", "jumps", data, pattern_analysis)
        pattern_analysis = __append_pattern_info("Monos", "mono", data, pattern_analysis)

    embed.add_field(name="__Pattern Analysis__", value=pattern_analysis,
                    inline=False)

    # - - - BREAKDOWNS - - -

    if data["breakdown"]:
        # Discord API only lets us post 1024 characters per field. Some marathon breakdowns are
        # larger than this restriction.
        # TODO: revisit this and perhaps just sent a .txt file if it's too large, instead of splitting up in sections
        if len(data["breakdown"]) > 1024:
            embed.add_field(name="__Detailed Breakdown__",
                            value="***Too large to display***", inline=False)
        else:
            embed.add_field(name="__Detailed Breakdown__",
                            value=data["breakdown"], inline=False)
        if data["partial_breakdown"] != data["simple_breakdown"]:
            if len(data["partial_breakdown"]) > 1024:
                embed.add_field(name="__Partially Simplified__",
                                value="***Too large to display***", inline=False)
            else:
                embed.add_field(name="__Partially Simplified__",
                                value=data["partial_breakdown"], inline=False)
        if len(data["simple_breakdown"]) > 1024:
            simple_breakdown = ""
            simple_breakdown_array = data["simple_breakdown"].split(" ")
            num_breaks = 1
            for i in simple_breakdown_array:
                if (len(simple_breakdown) + len(i)) > 1024:
                    embed.add_field(name="__Simplified Breakdown *(Part " +
                                    str(num_breaks) + ")*__", value=simple_breakdown, inline=False)
                    num_breaks += 1
                    simple_breakdown = ""
                simple_breakdown += i + " "
            embed.add_field(name="__Simplified Breakdown *(Part " +
                            str(num_breaks) + ")*__", value=simple_breakdown, inline=False)
        else:
            embed.add_field(name="__Simplified Breakdown__",
                            value=data["simple_breakdown"], inline=False)
    if data["normalized_breakdown"]:
        text = "*This is in beta and may be inaccurate. Variable BPM songs may report incorrect BPM.*\n"
        embed.add_field(name="__Normalized Breakdown__",
                        value=text + data["normalized_breakdown"], inline=False)

    # - - - FOOTER - - -
    file = discord.File(data["graph_location"], filename="density.png")

    embed.set_image(url="attachment://density.png")

    return embed, file
