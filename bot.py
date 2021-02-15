# -*- coding: utf-8 -*-

"""Searches a TinyDB database created by scan.py and reports information back to a Discord user.

This program is to be used in conjunction with scan.py. It will scan the database created by scan.py and allow users
to search this database through a Discord interface. Also allows users to upload their own data and have the scanner
parse through the uploaded file.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst for the Dickson City Heroes and Stamina Nation.
"""

from common import DBManager as dbm
from common import UserDBManager as udbm
from discord.ext import commands
from discord.ext.commands import has_permissions
from dotenv import load_dotenv
from scan import parse_file, scan_folder
from tinydb import Query, TinyDB, where
from zipfile import BadZipFile, ZipFile
import asyncio
import discord
import gdown
import json
import os
import re
import shutil
import sys
import urllib.request

# File name and folder constants. Change these if you want to use a different name or folder.
SERVER_SETTINGS = "server_settings.json"
USER_SETTINGS = "user_settings.json"
DATABASE_NAME = "db.json"  # Name of the TinyDB database file that contains parsed song information
TMP_DIR = "./tmp/"  # Directory to temporarily store user's uploaded .sm files to parse

# The database that contains server configurations, such as what prefix is set
server_db = TinyDB(SERVER_SETTINGS)

# The database that contains user configurations
user_db = TinyDB(USER_SETTINGS)

DATABASE_NAME = "db.json"               # Name of the TinyDB database file that contains parsed song information

# The default prefix for the bot
DEFAULT_PREFIX = "-"

# Default behavior to automatically delete user's uploaded .sm files
DEFAULT_AUTODELETE_BEHAVIOR = True

# The array of valid prefixes. This is updated when the bot starts to include all prefixes for Discord servers that has
# set a non-default prefix. See get_prefixes, is_prefix_for_server, and on_message functions for more info.
prefixes = [DEFAULT_PREFIX]

# Loads the discord token from the .env file.
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:  # if the DISCORD_TOKEN is blank in the .env file, or if the .env file doesn't exist
    print("It looks like you don't have an \".env\" file, or it's not setup correctly.")
    print("Please make sure you have an \".env\" file in the same directory as this file.")
    print("The \".env\" file should contain one line:")
    print("DISCORD_TOKEN=YourBotsDiscordTokenHere")
    sys.exit(1)

# Author avatar, used in footer
AVATAR_URL = "https://cdn.discordapp.com/avatars/542501947547320330/a_fd4512e7da6691d45387618677c3f01b.gif?size=1024"

# User Agent needed in order to download user's uploaded .sm files.
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36"

HELP_MESSAGE = """ \
Hello, I'm Simfile Sidekick, a Discord bot inspired by Nav's
Breakdown Buddy.

I can currently parse .sm files using a library of popular packs. Use
`-search` followed by the song name.

If you want me to parse a .sm file, attach the .sm file to your message and
type `-parse`.

To adjust your user settings, type `-settings help`. I can automatically
delete uploaded .sm files.

Admins can change the prefix using `-prefix` followed by the prefix they
want to use, e.g. `-prefix !`. Admins can also add packs to the database
by using `-dlpack URL`.

I also have built in stream visualizer functionality. Use `-sv` followed
by the characters `L`, `U`, `D`, or `R` to represent arrows. You can put
brackets around arrows to denote jumps, e.g. `[LR]`
"""


def get_prefixes():
    """Loads server prefixes from database.

    Even though servers can have their own prefixes, each one of these prefixes will need to be in the prefixes array
    created above. When the bot starts, this function is called. It will check the server database settings and add each
    servers chosen prefix to the prefixes array.
    """
    for item in server_db:
        prefix = item["prefix"]
        if prefix not in prefixes:
            prefixes.append(prefix)
    return prefixes


def is_prefix_for_server(id, prefix):
    """Check to see if prefix is used for server.

    This function checks if a command entered by a user is using the servers set prefix.
    """
    results = server_db.search(where("id") == id)

    if not results:
        # There is no entry in the database for this server. No configurations were set, so check if it matches the
        # default prefix.
        if prefix == DEFAULT_PREFIX:
            return True
        else:
            return False
    else:
        # The server has a set prefix
        data = json.loads(json.dumps(results[0]))
        if prefix == data["prefix"]:
            return True
        else:
            return False


# Loads the bot's prefixes using the get_prefixes function above
bot = commands.Bot(command_prefix=get_prefixes())

bot.remove_command("help")  # Needed in order to replace existing help command with our own


def get_mono_desc(mono):
    """Helper function to return pre-formatted text used in mono pattern analysis."""
    if mono == 0:
        return "*None*"
    if mono > 0 and mono < 10:
        return "*Sparse*"
    elif mono >= 10 and mono < 30:
        return "Infrequent"
    elif mono >= 30 and mono < 50:
        return "**Moderate**"
    elif mono > 50:
        return "__**Repetitive**__"


def normalize_float(num):
    """Helper function that returns a floating point number to 2 decimal places."""
    return "{:.2f}".format(float(num))


def get_footer_image(level):
    """Helper function that returns a fancy image for the difficulty of a chart."""
    if level == 1:
        return "<:1footer:772954101960015923>"
    elif level == 2:
        return "<:2footer:772954139411087421>"
    elif level == 3:
        return "<:3footer:772954170776617021>"
    elif level == 4:
        return "<:4footer:772954196193443842>"
    elif level == 5:
        return "<:5footer:772954224836870215>"
    elif level == 6:
        return "<:6footer:772954252740919317>"
    elif level == 7:
        return "<:7footer:772954279123484723>"
    elif level == 8:
        return "<:8footer:772954309302288384>"
    elif level == 9:
        return "<:9footer:772954334736023582>"
    elif level == 10:
        return "<:10footer:772954360089935882>"
    elif level == 11:
        return "<:11footer:772954385890148353>"
    elif level == 12:
        return "<:12footer:772954408714633226>"
    elif level == 13:
        return "<:13footer:772954433826848809>"
    elif level == 14:
        return "<:14footer:772954457965068378>"
    elif level == 15:
        return "<:15footer:772954496644546582>"
    elif level == 16:
        return "<:16footer:772954525610672139>"
    elif level == 17:
        return "<:17footer:772954552429183007>"
    elif level == 18:
        return "<:18footer:772954583751458816>"
    elif level == 19:
        return "<:19footer:772954623010668554>"
    elif level == 20:
        return "<:20footer:772954651637186580>"
    elif level == 21:
        return "<:21footer:772954679272407070>"
    elif level == 22:
        return "<:22footer:772954718489018429>"
    elif level == 23:
        return "<:23footer:772954755126657056>"
    elif level == 24:
        return "<:24footer:772954785518190614>"
    elif level == 25:
        return "<:25footer:772954813197320203>"
    elif level == 26:
        return "<:26footer:772954849054163014>"
    elif level == 27:
        return "<:27footer:772954877470048286>"
    elif level == 28:
        return "<:28footer:772954909410721813>"
    elif level == 29:
        return "<:29footer:772954946521137173>"
    elif level == 30:
        return "<:30footer:772954974266982430>"
    else:
        return "<:uhhfooter:772955010522808353>"


def create_embed(data, ctx):
    embed = discord.Embed(description="Requested by {}".format(ctx.author.mention))
    
    # Add requester's avatar, commented out since displaying Chart Info on same
    # line would be too tight.
    # embed.set_thumbnail(url=ctx.message.author.avatar_url)
    
    # - - - SONG DETAILS - - -
    song_details = ""
    # Title, Subtitle, and Artist
    if data["title"] == "*Hidden*" and data["artist"] == "*Hidden*":
        song_details += "*<Title and artist hidden>*\n"
    else:
        song_details += "**" + data["title"] + "** "
        if data["subtitle"] and data["subtitle"] != "N/A":
            song_details += "*" + data["subtitle"] + "* "
        song_details += "by **" + data["artist"] + "**" + "\n"
    song_details += "From pack(s): " + data["pack"] + "\n"
    # Rating, Difficulty, and Stepartist
    try:
        song_details += get_footer_image(int(data["rating"])) + " "
    except ValueError:
        song_details += get_footer_image(-1) + " "
    stepartist = data["stepartist"].replace("*", "\*")
    song_details += data["difficulty"] + " - " + stepartist + "\n\n"
    # Length
    song_details += "__Song Length__: " + data["length"] + "\n"
    # Display BPM
    if data["display_bpm"] and data["display_bpm"] != "N/A":
        song_details += "__Display BPM__: "
        if re.search(r"[:]+", data["display_bpm"]):
            display_bpm_range = data["display_bpm"].split(":")
            song_details += str(int(float(display_bpm_range[0]))) + "-"
            song_details += str(int(float(display_bpm_range[1]))) + "\n"
        else:
            song_details += str(int(float(data["display_bpm"]))) + "\n"
    # BPM
    song_details += "__BPM__: "
    if int(float(data["min_bpm"]) == int(float(data["max_bpm"]))):
        song_details += str(int(float(data["min_bpm"]))) + "\n"
    else:
        song_details += str(int(float(data["min_bpm"]))) + "-"
        song_details += str(int(float(data["max_bpm"]))) + "\n"
    # NPS
    song_details += "__Peak NPS__: **" + normalize_float(data["max_nps"]) + "** notes/s." + "\n"
    song_details += "__Median NPS__: **" + normalize_float(data["median_nps"]) + "** notes/s." + "\n"
    # Total Stream/Break
    total_measures = data["total_stream"] + data["total_break"]
    if total_measures != 0:
        stream_percent = normalize_float((data["total_stream"] / total_measures) * 100)
        break_percent = normalize_float((data["total_break"] / total_measures) * 100)
        song_details += "__Total Stream__: **" + str(data["total_stream"]) + "** measures "
        song_details += "(" + stream_percent + "%)" + "\n"
        song_details += "__Total Break__: **" + str(data["total_break"]) + "** measures "
        song_details += "(" + break_percent + "%)" + ""
    
    embed.add_field(name="__Song Details__", value=song_details)
    
    
    # - - - CHART INFO - - -
    chart_info = ""
    chart_info += "__Notes__: " + str(data["notes"]) + "\n"
    chart_info += "__Jumps__: " + str(data["jumps"]) + "\n"
    chart_info += "__Holds__: " + str(data["holds"]) + "\n"
    chart_info += "__Mines__: " + str(data["mines"]) + "\n"
    chart_info += "__Hands__: " + str(data["hands"]) + "\n"
    chart_info += "__Rolls__: " + str(data["rolls"])
    
    embed.add_field(name="__Chart Info__", value=chart_info, inline=True)
    
    
    # - - - PATTERN ANALYSIS - - -
    pattern_analysis = "*Analysis does not consider patterns in break segments.*" + "\n"
    # Candles
    pattern_analysis += "__Candles__: **" + str(data["total_candles"]) + "** "
    pattern_analysis += "(" + str(data["left_foot_candles"]) + " left, "
    pattern_analysis += str(data["right_foot_candles"]) + " right)" + "\n"
    candle_density = data["total_candles"] / (data["notes"] / 16)
    pattern_analysis += "__Candle density__: " + str(normalize_float(candle_density)) + " candles/measure" + "\n"
    # Mono
    pattern_analysis += "__Mono__: " + str(normalize_float(data["mono_percent"])) + "% "
    pattern_analysis += "(" + get_mono_desc(data["mono_percent"]) + ")" + "\n"
    # Boxes
    corner_boxes = data["corner_ld_boxes"] + data["corner_lu_boxes"] + data["corner_rd_boxes"] + data["corner_ru_boxes"]
    total_boxes = data["lr_boxes"] + data["ud_boxes"] + corner_boxes
    pattern_analysis += "__Boxes__: **" + str(total_boxes) + "** "
    pattern_analysis += "(" + str(data["lr_boxes"]) + " LRLR, " + str(data["ud_boxes"]) + " UDUD, "
    pattern_analysis += str(corner_boxes) + " corner)" + "\n"
    # Anchors
    total_anchors = data["anchor_left"] + data["anchor_down"] + data["anchor_up"] + data["anchor_right"]
    pattern_analysis += "__Anchors__: **" + str(total_anchors) + "** "
    pattern_analysis += "(" + str(data["anchor_left"]) + " left, "
    pattern_analysis += str(data["anchor_down"]) + " down, "
    pattern_analysis += str(data["anchor_up"]) + " up, "
    pattern_analysis += str(data["anchor_right"]) + " right)"
    
    embed.add_field(name="__Pattern Analysis__", value=pattern_analysis, inline=False)
    
    
    # - - - BREAKDOWNS - - -
    if data["breakdown"]:
        # Discord API only lets us post 1024 characters per field. Some marathon breakdowns are
        # larger than this restriction.
        # TODO: revisit this and perhaps just sent a .txt file if it's too large, instead of splitting up in sections
        if len(data["breakdown"]) > 1024:
            embed.add_field(name="__Detailed Breakdown__", value="***Too large to display***", inline=False)
        else:
            embed.add_field(name="__Detailed Breakdown__", value=data["breakdown"], inline=False)
        if data["partial_breakdown"] != data["simple_breakdown"]:
            if len(data["partial_breakdown"]) > 1024:
                embed.add_field(name="__Partially Simplified__", value="***Too large to display***", inline=False)
            else:
                embed.add_field(name="__Partially Simplified__", value=data["partial_breakdown"], inline=False)
        if len(data["simple_breakdown"]) > 1024:
            simple_breakdown = ""
            simple_breakdown_array = data["simple_breakdown"].split(" ")
            num_breaks = 1
            for i in simple_breakdown_array:
                if (len(simple_breakdown) + len(i)) > 1024:
                    embed.add_field(name="__Simplified Breakdown *(Part " + str(num_breaks) + ")*__", value=simple_breakdown, inline=False)
                    num_breaks += 1
                    simple_breakdown = ""
                simple_breakdown += i + " "
            embed.add_field(name="__Simplified Breakdown *(Part " + str(num_breaks) + ")*__", value=simple_breakdown, inline=False)
        else:
            embed.add_field(name="__Simplified Breakdown__", value=data["simple_breakdown"], inline=False)
    
    
    # - - - FOOTER - - -
    footer_text = "Made with love by Artimst for the Dickson City Heroes and Stamina Nation. "
    footer_text += "Icon by Johahn."
    embed.set_footer(text=footer_text, icon_url=AVATAR_URL)
    
    file = discord.File(data["graph_location"], filename="density.png")
    embed.set_image(url="attachment://density.png")
    
    return embed, file

@bot.command(name="search")
async def search_song(ctx, *, song_name):
#async def search_song(ctx, song_name: str):
    results = dbm.search_by_title(song_name, DATABASE_NAME)
    
    if isinstance(results, int):
        if results == 0:
            embed = discord.Embed(description="Sorry {}, but I could not find any songs.".format(ctx.author.mention))
            await ctx.send(embed=embed)
        elif results == -1:
            embed = discord.Embed(description="There was an error processing this request.")
            await ctx.send(embed=embed)
    elif isinstance(results, list):
        if len(results) == 1:
            data = results[0]
            
            embed, file = create_embed(data, ctx)
            
            await ctx.send(file=file, embed=embed)
        elif len(results) > 1:
            data = results
            
            user = "{}".format(ctx.author.mention)
            max_results = len(data)
            if max_results >= 26:
                max_results = 25
                search_description = "There were too many results, but I can show you the first 25." + "\n"
                search_description += "If your song isn't listed, please refine your search." + "\n"
                search_description += user + ", enter a number from `1` to `" + str(max_results) + "` "
                search_description += "to select the search result."
                embed = discord.Embed(title="Search Results", description=search_description)
            else:
                embed = discord.Embed(title="Search Results", description=user + ", enter a number from `1` to `" + str(len(data)) + "` to select the search result.")
            
            for i, d in enumerate(data):
                if i >= 25:
                    break
                title = "` " + str(i + 1) + " ` " + d["title"] + " "
                if d["subtitle"] and d["subtitle"] != "N/A":
                    title += "*" + d["subtitle"] + "* "
                title += "by " + d["artist"]
                
                value = "Pack(s): " + d["pack"] + "\n"
                value += get_footer_image(int(d["rating"])) + " " + d["difficulty"] + " - " + d["stepartist"].replace("*", "\*")
                
                embed.add_field(name=title, value=value, inline=False)
                
                
                
            
            if len(embed) > 6000:
                embed = discord.Embed(description="Sorry {}, but there are too many results for me to display.".format(ctx.author.mention))
                await ctx.send(embed=embed)
                return
            else:
                await ctx.send(embed=embed)
            
            try:
                msg = await bot.wait_for("message", check=lambda message: message.author == ctx.author, timeout=30)
            except asyncio.TimeoutError:
                # User didn't respond in 30s, just exit
                return
            
            if msg:
                embed, file = create_embed(data[int(msg.content) - 1], ctx)
                # TODO: add check to make sure user input is proper value
                await ctx.send(file=file, embed=embed)



@bot.command(name="sv")
async def stream_visualiser(ctx, input: str):
    regex = r"\[[LDUR]*\]|[LDUR]"
    input = input.upper()
    pattern = re.compile(regex)
    if not pattern.match(input):
        print("Invalid input")
    else:
        # https://github.com/andrewcalimlim/Stream-Visualizer-Bot/blob/master/bot.js
        input = re.findall(r"\[[LDUR]*\]|[LDUR]", input)
        
        normalized_input = []
        for i, line in enumerate(input):
            temp_line = [0, 0, 0, 0]
            current_input = line.replace("[", "").replace("]", "")
            for c in current_input:
                if c == "L":
                    temp_line[0] = 1
                elif c == "D":
                    temp_line[1] = 1
                elif c == "U":
                    temp_line[2] = 1
                elif c == "R":
                    temp_line[3] = 1
            normalized_input.append(temp_line)
        
        message = ""
        for i, line in enumerate(normalized_input):
            for j, arrow in enumerate(line):
                # j is the position of the arrow L=0, D=1, U=2, R=3
                # arrow is the value (0, blank space -- 1, arrow)
                # i is the measure
                if i % 4 == 0:
                    # Whole note
                    if arrow == 1:
                        if j == 0:
                            message += "<:red_L:772541312619642900>"
                        elif j == 1:
                            message += "<:red_D:772541311973589024>"
                        elif j == 2:
                            message += "<:red_U:772541312259719189>"
                        elif j == 3:
                            message += "<:red_R:772541312418840586>"
                    else:
                        message += "<:bg:772541312229703710>"
                elif i % 2 == 0:
                    # Half note
                    if arrow == 1:
                        if j == 0:
                            message += "<:blue_L:772541311235915827>"
                        elif j == 1:
                            message += "<:blue_D:772541311877906452>"
                        elif j == 2:
                            message += "<:blue_U:772541311575130154>"
                        elif j == 3:
                            message += "<:blue_R:772541311579979847>"
                    else:
                        message += "<:bg:772541312229703710>"
                elif i % 1 == 0 or i % 3 == 0:
                    # Quarter note
                    if arrow == 1:
                        if j == 0:
                            message += "<:green_L:772541312154992670>"
                        elif j == 1:
                            message += "<:green_D:772541312163250196>"
                        elif j == 2:
                            message += "<:green_U:772541312213843979>"
                        elif j == 3:
                            message += "<:green_R:772541312163512352>"
                    else:
                        message += "<:bg:772541312229703710>"
            message += "\n"
        await ctx.send(message)


@bot.command(name="settings")
async def settings(ctx, *input: str):
    user_id = ctx.message.author.id

    if not input or input[0] == "help":
        embed = discord.Embed(description="{}'s Settings".format(ctx.author.mention))
        title = "**Auto-delete** is "

        if udbm.get_autodelete_with_default(user_id, USER_SETTINGS, DEFAULT_AUTODELETE_BEHAVIOR):
            title += "`enabled`"
        else:
            title += "`disabled`"

        body = "This will automatically delete your uploaded .sm file when using `-parse`. Title and "
        body += "artist information will also be hidden. "
        body += "Use `-settings autodelete Y` to set, or `-settings autodelete N` to unset."

        embed.add_field(name=title, value=body, inline=False)
        await ctx.send(embed=embed)
        return

    if input[0] == "autodelete":
        if len(input) <= 1:
            result = udbm.get_autodelete(user_id, USER_SETTINGS)
            if result is None:
                message = "{}, it looks like you don't have this preference set. ".format(ctx.author.mention)
                message += "The default behavior is: "
                if DEFAULT_AUTODELETE_BEHAVIOR:
                    message += "I will automatically delete .sm files."
                else:
                    message += "I will not automatically delete .sm files."
                await ctx.send(message)
            elif result:
                await ctx.send("{}, I'm automatically deleting .sm files you upload.".format(ctx.author.mention))
            elif not result:
                await ctx.send("{}. I'm not automatically deleting .sm files you upload.".format(ctx.author.mention))
            return
        if input[1].upper() == "Y" or input[1].upper() == "T":
            udbm.set_autodelete(user_id, True, USER_SETTINGS)
            await ctx.send("{}, I will now auto-delete your uploaded .sm files.".format(ctx.author.mention))
        elif input[1].upper() == "N" or input[1].upper() == "F":
            udbm.set_autodelete(user_id, False, USER_SETTINGS)
            await ctx.send("{}, I will no longer auto-delete your uploaded .sm files.".format(ctx.author.mention))
        else:
            await ctx.send("{}, this is an invalid option. Use \"Y\" or \"N\".".format(ctx.author.mention))
        return


@bot.command(name="parse")
async def parse(ctx):
    """
    Parses a user's attached .sm file, and outputs the information into the chat channel.

    :param ctx: Discord API's context
                https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#context
    :return: Nothing
    """

    if len(ctx.message.attachments) < 1:
        message = "{}, you need to attach a .sm file.".format(ctx.author.mention)
        await ctx.send(message)
        return
    elif len(ctx.message.attachments) > 1:
        message = "{}, it looks like you attached multiple files. ".format(ctx.author.mention)
        message += "I can currently only parse one file at a time."
        await ctx.send(message)
        return

    attachment = ctx.message.attachments[0]

    if not attachment.url.endswith(".sm"):
        message = "Sorry {}, I can only parse .sm files.".format(ctx.author.mention)
        await ctx.send(message)
        return

    # We will later want to create a temporary folder based on user's unique ID to store the .sm file
    usr_tmp_dir = TMP_DIR + str(ctx.message.author.id) + "/"
    usr_tmp_file = usr_tmp_dir + attachment.filename
    usr_tmp_db = usr_tmp_file + ".json"

    # This bot only supports parsing one file at a time per user. If a user quickly submits multiple .sm files
    # in succession, it will most likely corrupt their results. We can prevent this by seeing if the temporary
    # directories have been created yet.
    # TODO: Revisit this section, as it looks like this function is thread-safe and these checks may not be needed (?)
    # I had the bot parse XS Project Collection, then tried uploading another .sm file immediately after. The message
    # below didn't appear until after XS Project Collection was complete.
    if os.path.exists(usr_tmp_dir):
        message = "It looks like I'm already parsing a file for you {}.".format(ctx.author.mention)
        await ctx.send(message)
        return
    else:
        # Create temporary directory if it doesn't exist
        os.makedirs(usr_tmp_dir)

    # If we don't have a User-Agent in our header, we won't be able to retrieve the file
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", USER_AGENT)]
    urllib.request.install_opener(opener)

    # Initializes the database that will contain info for only the attached .sm file
    db = TinyDB(usr_tmp_db)

    # Retrieve the .sm file, and place it in temporary directory
    urllib.request.urlretrieve(attachment.url, usr_tmp_file)

    message = "{}, ".format(ctx.author.mention)
    message += "I received your file `" + attachment.filename + "`. "
    message += "Currently processing... :hourglass:"
    process_msg = await ctx.send(message)

    hide_artist_info = False

    autodelete = udbm.get_autodelete_with_default(ctx.message.author.id, USER_SETTINGS, DEFAULT_AUTODELETE_BEHAVIOR)
    if autodelete:
        hide_artist_info = True
        await ctx.message.delete()

    # Call scan.py's parser function and put results in temporary database
    parse_file(usr_tmp_file, usr_tmp_dir, "*<Uploaded>*", db, None, hide_artist_info)

    # Get results from temporary database
    results = [result for result in db]

    # There may be multiple results, whether or not the .sm file had multiple difficulties
    for result in results:
        embed, file = create_embed(result, ctx)
        await ctx.send(file=file, embed=embed)
        # Removes density graph image for this difficulty
        os.remove(result["graph_location"])

    # Deletes the previous "currently processing" message
    await process_msg.delete()

    # Cleanup and delete files/folders in temporary directory
    os.remove(usr_tmp_file)
    db.close()
    os.remove(usr_tmp_db)
    os.rmdir(usr_tmp_dir)


@bot.command(name="dlpack")
@has_permissions(administrator=True)
async def prefix(ctx, input: str):

    # TODO: server-role lock this to SN mods and approved people. The same db is used across multiple servers.
    # Adding per-server databases is outside the scope of this program and too much for my tiny server to handle.
    # TODO: update readme to remove the above limitation for users hosting their own bot.

    # This ONLY takes Google Drive URLs, and the file MUST be a zip!

    # Google Drive URLs should follow the pattern
    # https://drive.google.com/uc?id=1F3i3YXk-6EqMibl089d5jsVTA26eykSs

    #input = "thisisabadurl"
    #input = "https://drive.google.com/uc?id=1F3i3YXk-6EqMibl089d5jsVTA26eykSs"

    if input[-1] == "/":  # remove trailing /
        input = input[:-1]

    input = input.split("/")
    input = input[len(input) - 1]

    input = input.split("=")
    input = input[len(input) - 1]

    url = "https://drive.google.com/uc?id=" + input
    output = TMP_DIR + "pack.zip"

    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    message = "{}, I'm retrieving the file. ".format(ctx.author.mention)
    message += "*This might take awhile*... :hourglass:"
    process_msg = await ctx.send(message)

    success = gdown.download(url, output, quiet=True)

    if not success:
        message = "{}, ".format(ctx.author.mention)
        message += "please check if the URL is correct. I wasn't able to retrieve the file. :x:"
        await process_msg.edit(content=message)
        return

    message = "{}, ".format(ctx.author.mention)
    message += " I'm now extracting the .zip file. :hourglass:"
    await process_msg.edit(content=message)

    zipfile = None
    try:
        zipfile = ZipFile(output)
    except BadZipFile:
        message = "{}, ".format(ctx.author.mention)
        message += "please check if the URL is correct. I was able to download a file but it doesn't appear to be a .zip. :x:"
        await process_msg.edit(content=message)
        return

    zipfile.extractall(TMP_DIR + "pack/")

    message = "{}, ".format(ctx.author.mention)
    message += "I'm done extracting. Now scanning with the parse tool and adding to database. :hourglass:"
    await process_msg.edit(content=message)

    db = TinyDB(DATABASE_NAME)
    scan_folder(TMP_DIR + "pack/", False, True, db, False)
    db.close()

    pack = next(os.walk(TMP_DIR + "pack/"))[1]
    pack = pack[0]

    message = "{}, ".format(ctx.author.mention)
    message += "\"" + pack + "\""
    message += " was successfully added! :white_check_mark:"
    await process_msg.edit(content=message)

    os.remove(output)
    shutil.rmtree(TMP_DIR + "pack/")


@bot.command(name="prefix")
@has_permissions(administrator=True)
# TODO: handle this better, and allow roles to be added as a bot manager
# See https://stackoverflow.com/a/51246799
async def prefix(ctx, input: str):
    server_id = ctx.message.guild.id

    if len(input) > 1:
        await ctx.send("Sorry, the prefix can only be 1 character")
        return

    result = server_db.search(where("id") == server_id)
    old_prefix = None
    new_prefix = input

    if result:
        # There is a prefix already set in the server, update it
        result = json.loads(json.dumps(result[0]))
        old_prefix = result["prefix"]
        ServerDB = Query()
        server_db.update({"prefix": input}, ServerDB.id == server_id)
    else:
        # Server never set a prefix
        server_db.insert({
            "id": server_id,
            "prefix": input
        })

    if old_prefix != None and old_prefix != DEFAULT_PREFIX:
        # We should search for the old prefix and see if it's used in any of the other channels. If not, we can remove
        # it from the array of prefixes.
        ServerDB = Query()
        results = server_db.search(ServerDB.prefix.search(old_prefix))
        if not result:
            prefixes.remove(old_prefix)

    if new_prefix not in prefixes:
        # If new prefix isn't in the array of prefixes to listen for, we need to add it.
        prefixes.append(new_prefix)

    bot.command_prefix = prefixes

    await ctx.send("Prefix is now: " + new_prefix)



@bot.command(name="help")
async def help(ctx):
    """
    Outputs the bot's help message.

    :param ctx: Discord API's context
                https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#context
    :return: Nothing
    """
    await ctx.send(HELP_MESSAGE)

@bot.event
async def on_message(message):
    """Called when a message is created and sent.

    This function handles the bot prefix settings. It's a little complicated since each server can have its own prefix.
    Therefore this function checks if the prefix for the user's server is set, and if the user is using the correct
    prefix. If it is, we process the command.
    """
    prefix = message.content

    if prefix:  # if prefix is not null, this sometimes happens if a user/another bot sends an embedded message
        prefix = prefix[0]  # retrieves the first character

    server_id = message.guild.id  # ID for the Discord server the user is in

    if is_prefix_for_server(server_id, prefix):
        await bot.process_commands(message)

bot.run(TOKEN)
