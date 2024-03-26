# Global Vars
DLPACK_ON_SELECTED_SERVERS_ONLY = False
DLPACK_DESTINATION_URL = "/Users/mm4/Desktop/songs"
TMP_DIR = "../tmp/"  # Directory to temporarily store user's uploaded .sm files to parse

# Author avatar, used in footer
AVATAR_URL = "https://cdn.discordapp.com/avatars/542501947547320330/a_fd4512e7da6691d45387618677c3f01b.gif?size=1024"

# User Agent needed in order to download user's uploaded .sm files.
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36"

# The default prefix for the bot
DEFAULT_PREFIX = "-"

# The array of valid prefixes. This is updated when the bot starts to include all prefixes for Discord servers that has
# set a non-default prefix. See get_prefixes, is_prefix_for_server, and on_message functions for more info.
PREFIXES = [DEFAULT_PREFIX]

# Default behavior to automatically delete user's uploaded .sm files
DEFAULT_AUTODELETE_BEHAVIOR = True
DEFAULT_NORMALIZE_BEHAVIOR = False

# File name and folder constants. Change these if you want to use a different name or folder.
SERVER_SETTINGS = "server_settings.json"
USER_SETTINGS = "user_settings.json"

# Name of the TinyDB database file that contains parsed song information
DATABASE_NAME = "db.json"

# Server IDs where the bot is allowed. Only admins in these channels will be able to use the "-dlpack" command
APPROVED_SERVERS = [
    317212788520910848,  # Big Ass Forehead
    1163182650241069066,  # BOT EMOJIS
    1163200677409988668,  # BOT EMOJIS 2
]

MAX_DISCORD_FIELD_CHARS = 1024

HELP_MESSAGE = """ \
Hello, I'm Simfile Sidekick, a Discord bot inspired by Nav's
Breakdown Buddy.

If you want to search for a song stored locally in the owner's database, use
`-search` followed by the song name. Once the results appear, enter the number
of the result that matches your desired search result.

If you want me to parse an .sm file, attach the .sm file to your message and
type `-parse`. If I get stuck parsing a file, try `-fix` and
I'll do my best to clean up so I can parse files again.
If you want to show double staircases, doublesteps and their locations,
use `-parse -xtras` when sending your file.

To adjust your user settings, type `-settings help`. I can automatically
delete uploaded .sm files.

I can also search by tags. The syntax is `-[tag]:[value]`
Currently supported tags are: `title`, `subtitle`, `artist`, `stepartist`, `rating`, and `bpm.`
Song title must come before the tags.

Example: `-search -bpm:160`
`-search sigatrev -rating:20`

Admins can:
Change the prefix using `-prefix` followed by the prefix they
want to use, e.g. `-prefix !`.
Add packs to the database by using `-dlpack URL`.
Delete packs from the database by using `-delpack packName`.

I also have built in stream visualizer functionality. Use `-sv` followed
by the characters `L`, `D`, `U`, or `R` to represent arrows. You can put
brackets around arrows to denote jumps, e.g. `[LR]`
"""

STR_TO_EMOJI = {
    1: "<:1footer:1163200171891495012>",
    2: "<:2footer:1163200173405655221>",
    3: "<:3footer:1163200174148042893>",
    4: "<:4footer:1163200180842139768>",
    5: "<:5footer:1163200183589404793>",
    6: "<:6footer:1163200184336007188>",
    7: "<:7footer:1163200185376194732>",
    8: "<:8footer:1163200187020349611>",
    9: "<:9footer:1163200189297856583>",
    10: "<:10footer:1163200191894138980>",
    11: "<:11footer:1163200192695255090>",
    12: "<:12footer:1163200193559269496>",
    13: "<:13footer:1163200292754559119>",
    14: "<:14footer:1163200197090885783>",
    15: "<:15footer:1163200294549721129>",
    16: "<:16footer:1163200299838754856>",
    17: "<:17footer:1163200300665020446>",
    18: "<:18footer:1163200301453549664>",
    19: "<:19footer:1163200302422425721>",
    20: "<:20footer:1163200199833944084>",
    21: "<:21footer:1163200392662880306>",
    22: "<:22footer:1163200204296683530>",
    23: "<:23footer:1163200394105733130>",
    24: "<:24footer:1163200207606005850>",
    25: "<:25footer:1163200394923618405>",
    26: "<:26footer:1163200395703767050>",
    27: "<:27footer:1163200396341301410>",
    28: "<:28footer:1163200211221499967>",
    29: "<:29footer:1163200211221499967>",
    30: "<:30footer:1163200398836891689>",
    31: "<:31footer:1163200399679946783>",
    32: "<:32footer:1163200475622027335>",
    33: "<:33footer:1163200477425573999>",
    34: "<:34footer:1163200214027477042>",
    35: "<:35footer:1163200478839054416>",
    36: "<:36footer:1163200218175643658>",
    37: "<:37footer:1163200479615004742>",
    38: "<:38footer:1163201160463781888>",
    39: "<:39footer:1163201161252319352>",
    "wun": "<:wun:1163199650916999228>",
    "red_L": "<:red_L:1163182809536532581>",
    "red_D": "<:red_D:1163182816230637628>",
    "red_U": "<:red_U:1163182822752800858>",
    "red_R": "<:red_R:1163182828201197729>",
    "blue_L": "<:blue_L:1163182833045622906>",
    "blue_D": "<:blue_D:1163182838225576096>",
    "blue_U": "<:blue_U:1163182842130477115>",
    "blue_R": "<:blue_R:1163182847394324600>",
    "green_L": "<:green_L:1163182853652234270>",
    "green_D": "<:green_D:1163182857838137405>",
    "green_U": "<:green_U:1163182863215243364>",
    "green_R": "<:green_R:1163182868269387927>",
    "bg": "<:bg:1163182776078581791>"
}
