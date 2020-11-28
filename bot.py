from discord.ext import commands
from dotenv import load_dotenv
from scan import parse_file
from search import *
from tinydb import TinyDB
import asyncio
import discord
import json
import os
import re
import urllib.request

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("It looks like you don't have an \".env\" file, or it's not setup correctly.")
    print("Please make sure you have an \".env\" file in the same directory as this file.")
    print("The \".env\" file should contain one line:")
    print("DISCORD_TOKEN=YourBotsDiscordTokenHere")
    sys.exit(1)

# Author avatar, used in footer
AVATAR_URL = "https://cdn.discordapp.com/avatars/542501947547320330/a_fd4512e7da6691d45387618677c3f01b.gif?size=1024"

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36"
TMP_DIR = "./tmp/"

bot = commands.Bot(command_prefix="-")

bot.remove_command("help") # Needed to replace existing help command

def get_mono_desc(mono):
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
    return "{:.2f}".format(float(num))

def get_footer_image(level):
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
    song_details += "**" + data["title"] + "** "
    if data["subtitle"] and data["subtitle"] != "N/A":
        song_details += "*" + data["subtitle"] + "* "
    song_details += "by **" + data["artist"] + "**" + "\n"
    song_details += "From pack(s): " + data["pack"] + "\n"
    # Rating, Difficulty, and Stepartist
    song_details += get_footer_image(int(data["rating"])) + " "
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
    footer_text = "Made with love by Artimst for the Dickson City Heroes. "
    footer_text += "Special thanks to feedbacker. "
    footer_text += "Icon by Johahn."
    embed.set_footer(text=footer_text, icon_url=AVATAR_URL)
    
    file = discord.File(data["graph_location"], filename="density.png")
    embed.set_image(url="attachment://density.png")
    
    return embed, file

@bot.command(name="search")
async def search_song(ctx, *, song_name):
#async def search_song(ctx, song_name: str):
    results = search(song_name)
    
    if isinstance(results, int):
        if results == 0:
            embed = discord.Embed(description="Sorry {}, but I could not find any songs.".format(ctx.author.mention))
            await ctx.send(embed=embed)
        elif results == -1:
            embed = discord.Embed(description="There was an error processing this request.")
            await ctx.send(embed=embed)
    elif isinstance(results, list):
        if len(results) == 1:
            data = json.loads(json.dumps(results[0]))
            
            embed, file = create_embed(data, ctx)
            
            await ctx.send(file=file, embed=embed)
        elif len(results) > 1:
            data = []
            for r in results:
                data.append(json.loads(json.dumps(r)))
            
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
                if(i >= 25):
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
                # TODO add check to make sure in value
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

@bot.command(name="parse")
async def parse(ctx):
    attachment = ctx.message.attachments[0]
    # TODO check if .sm file

    await ctx.send("I received your file. Currently processing...")

    opener = urllib.request.build_opener()
    opener.addheaders=[("User-Agent", USER_AGENT)]
    urllib.request.install_opener(opener)

    url = attachment.url

    usr_dir = TMP_DIR + str(ctx.message.author.id) + "/"
    usr_file = usr_dir + attachment.filename
    usr_db = usr_dir + attachment.filename + ".json"

    if not os.path.exists(usr_dir):
        os.makedirs(usr_dir)
    db = TinyDB(usr_db)

    urllib.request.urlretrieve(url, usr_file)

    parse_file(usr_file, usr_dir, "Uploaded", db)

    result = [r for r in db]

    for r in result:
        embed, file = create_embed(r, ctx)
        await ctx.send(file=file, embed=embed)
        os.remove(r["graph_location"])

    os.remove(usr_file)
    db.close()
    os.remove(usr_db)

    if len(os.listdir(usr_dir)) == 0:
        os.rmdir(usr_dir)

    if len(os.listdir(TMP_DIR)) == 0:
        os.rmdir(TMP_DIR)

@bot.command(name="help")
async def help(ctx):
    message="""
Hello, I'm Breakdown Buddy Jr., a Discord bot inspired by the original
Breakdown Buddy.

I can currently parse .sm files using a library of popular packs. Use
`-search` followed by the song name.

If you want me to parse a .sm file, attach the .sm file to your message and
type `-parse`.

I also have built in stream visualizer functionality. Use `-sv` followed
by the characters `L`, `U`, `D`, or `R` to represent arrows. You can put
brackets around arrows to denote jumps, e.g. `[LR]`
"""
    await ctx.send(message)

bot.run(TOKEN)