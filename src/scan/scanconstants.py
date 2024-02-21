# Flag constants. These are the available command line arguments you can use when running this application.
SHORT_OPTIONS = "rvd:ml:uc"
LONG_OPTIONS = ["rebuild", "verbose", "directory=",
                "mediaremove", "log=", "unittest", "csv"]

# Positions in args array.
REBUILD = 0
VERBOSE = 1
DIRECTORY = 2
MEDIA_REMOVE = 3
LOG = 4
UNIT_TEST = 5
CSV = 6

# Regex constants. Used mainly in the pattern recognition section.
NL_REG = "[\s]+"                        # New line
OR_REG = "|"                            # Regex for "or"
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
