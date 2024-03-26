# -*- coding: utf-8 -*-

"""Searches a TinyDB database created by scan.py and reports information back to a Discord user.

This program is to be used in conjunction with scan.py. It will scan the database created by scan.py and allow users
to search this database through a Discord interface. Also allows users to upload their own data and have the scanner
parse through the uploaded file.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst, this version is maintained/updated by JWong.
"""

# Module Imports
from tinydb import Query, TinyDB, where
from discord.ext.commands import has_permissions, Bot
from dotenv import load_dotenv

# External Imports
import asyncio
import discord
import gdown
import json
import os
import re
import shutil
import sys
import urllib.request
import logging

# Internal Imports
from db import DBManager as dbm
from db import UserDBManager as udbm
from scan.scan import parse_file, scan_folder
from zipfile import BadZipFile, ZipFile

from globals import DLPACK_ON_SELECTED_SERVERS_ONLY, DLPACK_DESTINATION_URL, TMP_DIR, USER_AGENT, DEFAULT_PREFIX, PREFIXES, DEFAULT_AUTODELETE_BEHAVIOR, SERVER_SETTINGS, USER_SETTINGS, DATABASE_NAME, APPROVED_SERVERS, HELP_MESSAGE, STR_TO_EMOJI
from helpers.bothelpers import get_prefixes, is_prefix_for_server
from helpers.messagehelpers import get_footer_image, create_embed

# The database that contains server configurations, such as what prefix is set
server_db = TinyDB(SERVER_SETTINGS)

# The database that contains user configurations
user_db = TinyDB(USER_SETTINGS)

# Loads the discord token from the .env file.
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:  # if the DISCORD_TOKEN is blank in the .env file, or if the .env file doesn't exist
    print("It looks like you don't have an \".env\" file, or it's not set up correctly.")
    print("Please make sure you have a \".env\" file in the same directory as this file.")
    print("The \".env\" file should contain one line:")
    print("DISCORD_TOKEN=YourBotsDiscordTokenHere")
    sys.exit(1)

# Allows SS to see members in other servers
intents = discord.Intents.all()
intents.members = True

# Loads the bot's prefixes using the get_prefixes function above
simfileSidekick = Bot(command_prefix=get_prefixes(server_db), intents=intents)

# Needed in order to replace existing help command with our own
simfileSidekick.remove_command("help")


@simfileSidekick.command(name="search", rest_is_raw=True)
async def search_song(ctx, *, song_name: str):
    # async def search_song(ctx, song_name: str):
    if not song_name:
        embed = discord.Embed(
            description=f"Sorry {ctx.author.mention}, but please supply a title.")
        await ctx.send(embed=embed)
        return

    # Strip the whitespaces since query is unstripped due to rest_is_raw=True
    query = song_name.strip()

    results = dbm.search(query, DATABASE_NAME)

    if isinstance(results, int):
        if results == 0:
            embed = discord.Embed(
                description="Sorry {}, but I could not find any songs.".format(ctx.author.mention))
            await ctx.send(embed=embed)
        elif results == -1:
            embed = discord.Embed(
                description="There was an error processing this request.")
            await ctx.send(embed=embed)
    elif isinstance(results, list):
        if len(results) == 1:
            data = results[0]

            embed, _, file = create_embed(data, ctx)
            await ctx.send(file=file, embed=embed)

        elif len(results) > 1:
            data = results

            user = "{}".format(ctx.author.mention)
            max_results = len(data)
            if max_results >= 26:
                max_results = 25
                search_description = "There were too many results, but I can show you the first 25." + "\n"
                search_description += "If your song isn't listed, please refine your search." + "\n"
                search_description += user + \
                    ", enter a number from `1` to `" + str(max_results) + "` "
                search_description += "to select the search result."
                embed = discord.Embed(
                    title="Search Results", description=search_description)
            else:
                embed = discord.Embed(title="Search Results", description=user +
                                      ", enter a number from `1` to `" + str(len(data)) + "` to select the search result.")

            for i, d in enumerate(data):
                if i >= 25:
                    break
                title = "` " + str(i + 1) + " ` " + d["title"] + " "
                if d["subtitle"] and d["subtitle"] != "N/A":
                    title += "*" + d["subtitle"] + "* "
                title += "by " + d["artist"]

                value = "Pack(s): " + d["pack"] + "\n"
                value += get_footer_image(int(d["rating"])) + " " + \
                    d["difficulty"] + " - " + \
                    d["stepartist"].replace("*", "\*")

                embed.add_field(name=title, value=value, inline=False)

            if len(embed) > 6000:
                embed = discord.Embed(
                    description="Sorry {}, but there are too many results for me to display.".format(ctx.author.mention))
                await ctx.send(embed=embed)
                return
            else:
                await ctx.send(embed=embed)

            try:
                msg = await simfileSidekick.wait_for("message", check=lambda message: message.author == ctx.author, timeout=30)
            except asyncio.TimeoutError:
                # User didn't respond in 30s, just exit
                return

            if msg:
                embed, file = None, None
                try:
                    index = int(msg.content) - 1

                    if index < 0 or index >= len(data):
                        raise IndexError

                    embed, _, file = create_embed(data[index], ctx)
                except ValueError:
                    # Users may be continuing a conversation, or using another command. This would prevent the bot from
                    # saying "invalid input" if the user searches for another song/uses another command.
                    pass
                except IndexError:
                    embed = discord.Embed(
                        description=f"Sorry {ctx.author.mention}, that's out of range. Try searching again.")
                finally:
                    if embed:
                        await ctx.send(file=file, embed=embed)


@simfileSidekick.command(name="sv")
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
                            message += STR_TO_EMOJI["red_L"]
                        elif j == 1:
                            message += STR_TO_EMOJI["red_D"]
                        elif j == 2:
                            message += STR_TO_EMOJI["red_U"]
                        elif j == 3:
                            message += STR_TO_EMOJI["red_R"]
                    else:
                        message += STR_TO_EMOJI["bg"]
                elif i % 2 == 0:
                    # Half note
                    if arrow == 1:
                        if j == 0:
                            message += STR_TO_EMOJI["blue_L"]
                        elif j == 1:
                            message += STR_TO_EMOJI["blue_D"]
                        elif j == 2:
                            message += STR_TO_EMOJI["blue_U"]
                        elif j == 3:
                            message += STR_TO_EMOJI["blue_R"]
                    else:
                        message += STR_TO_EMOJI["bg"]
                elif i % 1 == 0 or i % 3 == 0:
                    # Quarter note
                    if arrow == 1:
                        if j == 0:
                            message += STR_TO_EMOJI["green_L"]
                        elif j == 1:
                            message += STR_TO_EMOJI["green_D"]
                        elif j == 2:
                            message += STR_TO_EMOJI["green_U"]
                        elif j == 3:
                            message += STR_TO_EMOJI["green_R"]
                    else:
                        message += STR_TO_EMOJI["bg"]
            message += "\n"
        await ctx.send(message)


@simfileSidekick.command(name="settings")
async def settings(ctx, *input: str):
    user_id = ctx.message.author.id

    if not input or input[0] == "help":
        embed = discord.Embed(
            description="{}'s Settings".format(ctx.author.mention))

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
                message = "{}, it looks like you don't have this preference set. ".format(
                    ctx.author.mention)
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


@simfileSidekick.command(name="fix")
async def fix(ctx):
    """ Cleans up the user's temp directory for parsing files. If the scanner runs into an error when parsing a file,
    the bot will think he is still trying to parse something.
    """
    usr_tmp_dir = TMP_DIR + str(ctx.message.author.id) + "/"
    if os.path.exists(usr_tmp_dir):
        shutil.rmtree(usr_tmp_dir)
        await ctx.send("I did some cleanup {}, I should be able to parse files again for you!".format(ctx.author.mention))
    else:
        await ctx.send("{}, it looks like there's nothing for me to cleanup.".format(ctx.author.mention))


@simfileSidekick.command(name="parse")
async def parse(ctx, *params: str):
    try:
        """
        Parses a user's attached .sm file, and outputs the information into the chat channel.

        :param ctx: Discord API's context
                    https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#context
        :return: Nothing
        """

        if "bot" not in ctx.message.channel.name:
            message = "{}, I can only parse breakdowns in bot channels. Please post in the appropriate channel.".format(
                ctx.author.mention
            )
            await ctx.message.delete()
            await ctx.send(message)
            return

        if len(ctx.message.attachments) < 1:
            message = "{}, you need to attach a .sm file.".format(
                ctx.author.mention)
            await ctx.send(message)
            return
        elif len(ctx.message.attachments) > 1:
            message = "{}, it looks like you attached multiple files. ".format(
                ctx.author.mention)
            message += "I can currently only parse one file at a time."
            await ctx.send(message)
            return

        attachment = ctx.message.attachments[0]

        """
            Discord implemented changes to their CDN where attachments now have tokens to make files
            expire after inactivity, presumably to save space and disallow people from using their
            databases as cloud storage.

            Because of this change, the URL now has to be split on it's query separator ("?"),
            where the first half of the URL is formatted like it was before, and the latter half
            is the authentication token.
        """

        url_token_split = attachment.url.split("?")
        new_url_because_discord_sucks = url_token_split[0]
        if not new_url_because_discord_sucks.endswith(".sm"):
            message = "Sorry {}, I can only parse .sm files.".format(
                ctx.author.mention)
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
            message = "It looks like I'm already parsing a file for you {}.".format(
                ctx.author.mention)
            await ctx.send(message)
            fix(ctx)
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

        autodelete = udbm.get_autodelete_with_default(
            ctx.message.author.id, USER_SETTINGS, DEFAULT_AUTODELETE_BEHAVIOR)
        if autodelete:
            hide_artist_info = True
            await ctx.message.delete()

        # Call scan.py's parser function and put results in temporary database
        # parse_file(usr_tmp_file, usr_tmp_dir, "*<Uploaded>*", db, None, hide_artist_info, None)
        parse_file(db, usr_tmp_file, usr_tmp_dir,
                "*<Uploaded>*", hide_artist_info, None)

        # Get results from temporary database
        results = [result for result in db]

        # There may be multiple results, whether or not the .sm file had multiple difficulties
        for result in results:
            embed, pattern_embed, file = create_embed(result, ctx, params)
            await ctx.send(file=file, embed=embed)
            await ctx.send(file=None, embed=pattern_embed)
            # Removes density graph image for this difficulty
            if os.path.exists(result["graph_location"]):
                os.remove(result["graph_location"])

        # Deletes the previous "currently processing" message
        await process_msg.delete()

        # Cleanup and delete files/folders in temporary directory
        os.remove(usr_tmp_file)
        db.close()
        os.remove(usr_tmp_db)
        os.rmdir(usr_tmp_dir)
    except Exception as e:
        logging.exception("what the fuck is going on here")
        print(e)
        await ctx.send("Something went wrong, fixing.")
        usr_tmp_dir = TMP_DIR + str(ctx.message.author.id) + "/"
        if os.path.exists(usr_tmp_dir):
            shutil.rmtree(usr_tmp_dir)
            await ctx.send("I did some cleanup {}, I should be able to parse files again for you!".format(ctx.author.mention))
        else:
            await ctx.send("{}, it looks like there's nothing for me to cleanup.".format(ctx.author.mention))

@simfileSidekick.command(name="delpack")
@has_permissions(administrator=True)
async def delpack(ctx, input: str):
    server_id = ctx.message.guild.id
    if DLPACK_ON_SELECTED_SERVERS_ONLY and server_id not in APPROVED_SERVERS:
        await ctx.send("This command is currently disabled.")
        return

    try:
        updates, deletes = dbm.delete_pack_search_results(input, DATABASE_NAME)
    except TypeError:
        # Returned 0 or -1
        # TODO: clean this up
        await ctx.send("I can't find that pack, sorry!")
        return

    # Grabs unique results, since the arrays returned include multiple difficulties
    updates_list = list(set(updates[u] for u in updates))
    deletes_list = list(set(deletes[d] for d in deletes))

    embed = discord.Embed(description="Deleting Pack")

    body = ""

    for u in updates_list:
        body += " - " + u + "\n"

    if body:
        embed.add_field(
            name="Songs will be updated (they exist in other packs):", value=body, inline=False)

    body = ""

    for d in deletes_list:
        body += " - " + d + "\n"

    if body:
        embed.add_field(name="Songs will be deleted:",
                        value=body, inline=False)

    embed.add_field(name="Are you sure you want to do this?",
                    value="Type Y or N.", inline=False)

    await ctx.send(embed=embed)

    try:
        msg = await simfileSidekick.wait_for("message", check=lambda message: message.author == ctx.author, timeout=30)
    except asyncio.TimeoutError:
        # User didn't respond in 30s, just exit
        return

    if msg and msg.content.upper() == "Y":
        dbm.delete_by_ids(list(d for d in deletes), DATABASE_NAME)
        dbm.remove_pack_from_songs_by_id(
            input, list(u for u in updates), DATABASE_NAME)
        await ctx.send("Songs deleted.")


@simfileSidekick.command(name="dlpack")
@has_permissions(administrator=True)
async def dlpack(ctx, input: str):

    server_id = ctx.message.guild.id
    if DLPACK_ON_SELECTED_SERVERS_ONLY and server_id not in APPROVED_SERVERS:
        await ctx.send("This command is currently disabled.")
        return
    # Adding per-server databases is outside the scope of this program and too much for my tiny server to handle.

    # This ONLY takes Google Drive URLs, and the file MUST be a zip!

    # Google Drive URLs should follow the pattern
    # https://drive.google.com/uc?id=1F3i3YXk-6EqMibl089d5jsVTA26eykSs

    # String manipulations below will try to retrieve the ID from Google Drive multiple URL formats.

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
        os.remove(output)
        return

    temp_pack_dir = TMP_DIR + "pack/"

    # extract files to both the temp dir, and the destination for DB
    zipfile.extractall(temp_pack_dir)
    zipfile.extractall(DLPACK_DESTINATION_URL)

    pack = next(os.walk(temp_pack_dir))[1][0]

    zipfile.close()

    db = TinyDB(DATABASE_NAME)

    if dbm.pack_exists(pack, db):
        message = "{}, ".format(ctx.author.mention)
        message += "it looks like this pack is already added. :x:"
        await process_msg.edit(content=message)
        os.remove(output)
        shutil.rmtree(temp_pack_dir)
        return

    message = "{}, ".format(ctx.author.mention)
    message += "I'm done extracting. Now scanning with the parse tool and adding to database. :hourglass:"
    await process_msg.edit(content=message)

    # Args Ordered: Rebuild, Verbose, Directory, Media_remove, Log, Unit_test, CSV
    scan_args = [False, False, DLPACK_DESTINATION_URL,
                 True, False, False, False]
    scan_folder(scan_args, db)
    db.close()

    message = "{}, ".format(ctx.author.mention)
    message += "\"" + pack + "\""
    message += " was successfully added! :white_check_mark:"
    await process_msg.edit(content=message)

    os.remove(output)
    shutil.rmtree(temp_pack_dir)


@simfileSidekick.command(name="prefix")
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
            PREFIXES.remove(old_prefix)

    if new_prefix not in PREFIXES:
        # If new prefix isn't in the array of prefixes to listen for, we need to add it.
        PREFIXES.append(new_prefix)

    simfileSidekick.command_prefix = PREFIXES

    await ctx.send("Prefix is now: " + new_prefix)


@simfileSidekick.command(name="help")
async def help(ctx):
    """
    Outputs the bot's help message.

    :param ctx: Discord API's context
                https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#context
    :return: Nothing
    """
    await ctx.send(HELP_MESSAGE)


@simfileSidekick.event
async def on_message(message):
    """Called when a message is created and sent.

    This function handles the bot prefix settings. It's a little complicated since each server can have its own prefix.
    Therefore this function checks if the prefix for the user's server is set, and if the user is using the correct
    prefix. If it is, we process the command.
    """
    prefix = message.content

    if prefix:  # if prefix is not null, this sometimes happens if a user/another bot sends an embedded message
        prefix = prefix[0]  # retrieves the first character

    server_id = None

    # Needed so the bot doesn't spam error messages when DM'ing a user
    if message.guild:
        server_id = message.guild.id  # ID for the Discord server the user is in

    if is_prefix_for_server(server_db, server_id, prefix):
        await simfileSidekick.process_commands(message)

simfileSidekick.run(TOKEN)
