# Simfile Sidekick

A discord bot to scan and parse StepMania simfiles. Inspired by Nav's Breakdown Buddy.

## How to use

This was created and tested using Python 3.6.9, but will probably work with earlier versions of Python 3.

You'll need to install a few packages before using, most easily done using pip.

I use Plotly for the density graph creation. It is open source:
https://github.com/plotly/plotly.py

`pip install plotly`

Plotly has a dependencies on psutil and kaleido:

`pip install psutil`

`pip install kaleido`

I also use TinyDB to create the database. It essentially creates a JSON file, but figured a full-blown database was outside the scope of this project. It is also open source:
https://github.com/msiemens/tinydb

`pip install tinydb`

You'll want to run scan.py first, then after generating the database, you can run bot.py.

### scan.py

This file will scan a directory (and subdirectories) for a list of .sm files. It will parse through each .sm file, and retrieve useful information (such as rating, steps, pattern analysis and detailed density breakdown) and append it to a database (in our case, the TinyDB JSON file).

Note: Scanning a songs folder that has a few thousand songs will take a few hours (usually I let it run overnight).

To use:

`python3 scan.py -d "/home/steve/simfile-sidekick/songs"`

List of all command line options:

`-v` is verbose. It will output the song currently being scanned to stdout.

`-r` is rebuild. It will delete and completely rebuild the database. Normal behavior (without this flag) is to simply append new songs to the database.

`-m` is remove media. It will delete any .ogg, .mpg, or .avi files it finds. This is useful when scanning new packs if you wish to save disk space - the only thing we need is the .sm file.

`-d` is directory, and a mandatory option. It is the directory where all your song packs are located.

When finished, you should have a new db.json file in the same folder as scan.py.

### bot.py

This is the actual discord bot. It will search db.json for songs matching the entered criteria and return it to the user. If multiple matches are found, it will return a list for the user to select from.

To use:

`python3 bot.py`

### search.py

This is an intermediary file that is used by bot.py to communicate with db.json. It's purpose is to simply search for a song and return the information to bot.py. If more than one result is found, it will return a list to bot.py. I will probably just move this into bot.py at a later date when I get around to code cleanup.

## Tips

- I highly recommend using screen when using scan.py. Your first scan will take more than a few hours. See https://linuxize.com/post/how-to-use-linux-screen/
- If you never used python pip, see https://pip.pypa.io/en/stable/installing/

## Troubleshooting

- If you need to install pip and getting an error like:

`ModuleNotFoundError: No module named 'distutils.util'`

Just install python3-distutils:

`sudo apt-get install python3-distutils`


- If you're trying to install psutil and getting and error like:

`error: command 'x86_64-linux-gnu-gcc' failed with exit status 1`

Then install python3-dev:

`sudo apt-get install python3-dev`

## To-do
- [ ] Replace all instances of "Breakdown Buddy Jr." with "Simfile Sidekick"
- [ ] Log songs that couldn't be parsed by scan.py to a logfile
- [ ] Flag in scan.py to enter in a database name
- [ ] Create a tool to insert/update/delete from the TinyDB database
- [ ] Search by different or multiple paremeters (e.g. artist, stepartist, ranking, etc.)
- [ ] Parse manually uploaded .sm files from discord
- [ ] Preferences for users (hide title & artist and other original Breakdown Buddy features)