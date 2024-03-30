# Flag constants. These are the available command line arguments you can use when running this application.
SHORT_OPTIONS = "rvd:ml:uc"
LONG_OPTIONS = [
    "rebuild", "verbose", "directory=", "mediaremove", "log=", "unittest",
    "csv"
]

# Positions in args array.
REBUILD = 0
VERBOSE = 1
DIRECTORY = 2
MEDIA_REMOVE = 3
LOG = 4
UNIT_TEST = 5
CSV = 6

# Regex constants. Used mainly in the pattern recognition section.
NL_REG = "[\s]+"  # New line
OR_REG = "|"  # Regex for "or"
# Matches a line containing no notes (0000)
NO_NOTES_REG = "[03M][03M][03M][03M]"
# Matches a line containing at least 1 note
ANY_NOTES_REG = "(.*)[124]+(.*)"

# Other constants.
LOG_TIMESTAMP = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(asctime)s %(levelname)s - %(message)s"

# File name and folder constants. Change these if you want to use a different name or folder.
# The folder the unit test songs are located
UNITTEST_FOLDER = "tests"
# Name of the TinyDB database file that contains parsed song information
DATABASE_NAME = "db.json"
# Name of the log file that will be created if enabled
LOGFILE_NAME = "scan.log"
# Name of the .csv that will be created if enabled
CSV_FILENAME = "charts.csv"

STEP_TO_DIR = {
    # Steps
    "1000": "L",
    "0100": "D",
    "0010": "U",
    "0001": "R",
    # Holds
    "2000": "L",
    "0200": "D",
    "0020": "U",
    "0002": "R",
    # Rolls
    "4000": "L",
    "0400": "D",
    "0040": "U",
    "0004": "R",
    # None
    "0000": "",
    # Jumps
    "1100": "[LD]",
    "1010": "[LU]",
    "1001": "[LR]",
    "0101": "[DR]",
    "0011": "[UR]",
    "0110": "[DU]",
    # Hands
    "1110": "[LDU]",
    "1101": "[LDR]",
    "1011": "[LUR]",
    "0111": "[DUR]",
    "1111": "[LDUR]"
}

# Candles
LEFT_CANDLES = ["DRU", "URD"]
RIGHT_CANDLES = ["DLU", "ULD"]

# Create a combined regex pattern for all substrings in each category
LEFT_ANCHOR_PATTERN = "L[DUR]L[DUR]L"
DOWN_ANCHOR_PATTERN = "D[LUR]D[LUR]D"
UP_ANCHOR_PATTERN = "U[LDR]U[LDR]U"
RIGHT_ANCHOR_PATTERN = "R[LDU]R[LDU]R"

COMBINED_PATTERN = (f"({LEFT_ANCHOR_PATTERN}|{DOWN_ANCHOR_PATTERN}|"
                    f"{UP_ANCHOR_PATTERN}|{RIGHT_ANCHOR_PATTERN})")

DBL_STAIRS = ["LDURLDUR", "LUDRLUDR", "RUDLRUDL", "RDULRDUL"]

DBL_STEPS = [
    "LL", "DD", "UU", "RR", "LUR", "LDR", "RUL", "RDL", "LUDL", "LDUL", "RUDR",
    "RDUR"
]

BOXES = [
    # left-foot leading
    "LULU",
    "LRLR",
    "LDLD",
    "DRDR",
    "URUR",
    # right-foot leading
    "RURU",
    "RLRL",
    "RDRD",
    "DLDL",
    "ULUL",
    # ambiguous
    "UDUD",
    "DUDU"
]

DORITO = ['LDUDLRD', 'LUDULRU', 'RDUDRLD', 'RUDURLU']
DORITO_DOUBLE_SIDE = ['LDUDLRL', 'LUDULRL', 'RDUDRLR', 'RUDURLR']
STAIR_DOUBLE_SIDE = ['LDURLRD', 'LUDRLRU', 'RDULRLD', 'RUDLRLU']
NOT_MONO = DORITO + DORITO_DOUBLE_SIDE + STAIR_DOUBLE_SIDE

SIX_MONO = ['LDLRUR', 'LULRDR', 'RDRLUL', 'RURLDL']