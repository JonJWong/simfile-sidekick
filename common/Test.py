from common.enums.RunDensity import RunDensity
from common import DBManager as dbm
from common import Normalize as normalizer
import sys

DATABASE_FILE = "./tests/db.json"

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def good(desc):
    output = GREEN + "PASSED" + RESET + ": "
    output += desc
    print(output)

def fail_val(desc, cval, val):
    output = RED + "FAILED" + RESET + ": "
    output += desc
    output += " Value should be \"" + str(cval) + "\" but got \"" + str(val) + "\"."
    print(output)

def fail(desc):
    output = RED + "FAILED" + RESET + ": "
    output += desc
    print(output)

def run_tests():

    passed = 0
    failed = 0

    f = open("tests/scan.log")
    log_contents = f.read()
    result = log_contents.find("Scanning complete.")

    if result != -1:
        good("scan.py parsed all songs.")
        passed += 1
    else:
        fail("scan.py did not parse all songs.")
        failed += 1

    # 30MIN Harder has a missing semicolon (;) in the BPMs list.

    result = log_contents.find("04 - 30MIN HARDER.sm\" is missing semicolon.")

    if result != -1:
        good("scan.py correctly handled missing semicolon in BPM section.")
        passed += 1
    else:
        fail("scan.py did not identify or recover from missing semicolon in BPM section.")
        failed += 1

    # I'm A Maid has a colon (:) where a semicolon (;) should be

    result = log_contents.find("Completed parsing \"tests/songs/I'm A Maid (C-Type Remix)/Im a maid.sm\".")

    if result != -1:
        good("scan.py correctly handled misplaced colon in metadata section.")
        passed += 1
    else:
        fail("scan.py did not handle misplaced colon in metadata section.")
        failed += 1

    # OceanLab Megamix has strange non-printable characters in the BPM section

    result = log_contents.find("oceanlab.sm\" contains non-printable characters. Handled and continuing.")

    if result != -1:
        good("scan.py correctly handled non-printable characters in BPM section.")
        passed += 1
    else:
        fail("scan.py did not handle non-printable characters in BPM section.")
        failed += 1

    # DEATHMATCH has charts initialised to 0's, that is, a chart exists but is simply a placeholder
    # and no arrows have yet been added. This resolved a division by zero error when calculating statistics.

    result = log_contents.find("The Hard 1 chart for DEATHMATCH is empty. Skipping")

    if result != -1:
        good("scan.py correctly handled an empty chart.")
        passed += 1
    else:
        fail("scan.py did not properly handle an empty chart.")
        failed += 1

    # Fairytale is a chart that has an extra return in the stepartist section. Previously, the logic looked at this per
    # line, instead of splitting it by colon (:).

    data = dbm.search("Fairytale", DATABASE_FILE)
    result = data[1]  # [1] so we grab the hard chart, since it's the chart with the extra return

    if result["difficulty"] == "Hard":
        good("scan.py correctly handled extra return characters in metadata.")
        passed += 1
    else:
        fail("scan.py did not properly handle extra return characters in metadata.")
        failed += 1

    # Chelsea is a song that immediately stops on the last measure of the song, there is no padding. Due to the way I
    # previously calculated runs in 16ths, 24ths, or 32nds, I suspect that the parser did not properly switch back to
    # "Break" and add the appropriate run to the breakdown.

    data = dbm.search("Chelsea", DATABASE_FILE)
    result = data[2]  # [2] so we grab the challenge chart

    correct_breakdown = "15 7 (17) 3 11 (14) 15"

    if result["breakdown"] == correct_breakdown:
        good("scan.py correctly handled songs that end on the last measure.")
        passed += 1
    else:
        fail_val("scan.py did not properly handle songs that end on the last measure.", correct_breakdown, result["breakdown"])
        failed += 1

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Generic tests to check measure counter

    # We want to make sure Encoder's breakdown is 32. We don't want to capture any break segments before or after
    # the one and only run.

    data = dbm.search("Encoder", DATABASE_FILE)
    result = data[4] # [4] so we grab the challenge chart, and not the easy or medium, etc.

    if result["breakdown"] == "32":
        good("Encoder's breakdown is correct.")
        passed += 1
    else:
        fail_val("Encoder's breakdown is incorrect.", "32", result["breakdown"])
        failed += 1

    # Encoder's "total stream" should be 32, and "total break" should be 0. We don't include breaks before the first
    # run, and also don't include breaks after the last run. Since there is only one run, we're expecting 32 and 0.

    if result["total_stream"] == 32:
        good("Encoder's total stream is correct.")
        passed += 1
    else:
        fail_val("Encoder's total stream is incorrect.", 32, result["total_stream"])
        failed += 1

    if result["total_break"] == 0:
        good("Encoder's total break is correct.")
        passed += 1
    else:
        fail_val("Encoder's total break is incorrect.", 0, result["total_break"])
        failed += 1

    # Generic breakdown test for Ganbatte

    data = dbm.search("Ganbatte", DATABASE_FILE)
    result = data[0]  # [0] so we grab the challenge chart, and not the other

    correct_breakdown = "7 19 3 39 39 31 16 (4) 7 7 23 7 15 64 (8) 7 16 23"

    if result["breakdown"] == correct_breakdown:
        good("Ganbatte's breakdown is correct.")
        passed += 1
    else:
        fail_val("Ganbatte's breakdown is incorrect.", correct_breakdown, result["breakdown"])
        failed += 1

    correct_breakdown = "160* - 128* / 48*"

    if result["partial_breakdown"] == correct_breakdown:
        good("Ganbatte's partially simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("Ganbatte's partially simplified breakdown is incorrect.", correct_breakdown, result["partial_breakdown"])
        failed += 1

    correct_breakdown = "292* / 48*"

    if result["simple_breakdown"] == correct_breakdown:
        good("Ganbatte's simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("Ganbatte's simplified breakdown is incorrect.", correct_breakdown, result["simple_breakdown"])
        failed += 1

    if result["total_stream"] == 323:
        good("Ganbatte's total stream is correct.")
        passed += 1
    else:
        fail_val("Ganbatte's total stream is incorrect.", 323, result["total_stream"])
        failed += 1

    if result["total_break"] == 25:
        good("Ganbatte's total break is correct.")
        passed += 1
    else:
        fail_val("Ganbatte's total break is incorrect.", 25, result["total_break"])
        failed += 1

    data = dbm.search("Ganbatte", DATABASE_FILE)
    result = data[1]  # [0] so we grab the chart with the 20ths

    correct_breakdown = "7 19 3 39 24 ~4~ 4 ~4~ 3 31 16 (4) 7 7 23 7 15 32 ~4~ 12 ~4~ 12 (8) 7 16 11 ~4~ 8"

    if result["breakdown"] == correct_breakdown:
        good("Ganbatte (18)'s breakdown is correct.")
        passed += 1
    else:
        fail_val("Ganbatte (18)'s breakdown is incorrect.", correct_breakdown, result["breakdown"])
        failed += 1

    correct_breakdown = "96* ~4~ 4 ~4~ 52* - 96* ~4~ 12 ~4~ 12 / 36* ~4~ 8"

    if result["partial_breakdown"] == correct_breakdown:
        good("Ganbatte (18)'s partially simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("Ganbatte (18)'s partially simplified breakdown is incorrect.", correct_breakdown,
                 result["partial_breakdown"])
        failed += 1

    correct_breakdown = "96* ~4~ 4 ~4~ 152* ~4~ 12 ~4~ 12 / 36* ~4~ 8"

    if result["simple_breakdown"] == correct_breakdown:
        good("Ganbatte (18)'s simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("Ganbatte (18)'s simplified breakdown is incorrect.", correct_breakdown, result["simple_breakdown"])
        failed += 1

    should_normalize = normalizer.if_should_normalize(result["breakdown"], result["total_stream"])

    if should_normalize == RunDensity.Run_16:
        good("Ganbatte (18) is correctly NOT normalizing and keeping 16th note breakdown.")
        passed += 1
    else:
        fail_val("Ganbatte (18) is being normalized.", RunDensity.Run_20,
                 should_normalize)
        failed += 1

    # Generic breakdown test for Pendulum Essential Mix (Side A)

    data = dbm.search("Pendulum Essential Mix", DATABASE_FILE)
    result = data[0]

    correct_breakdown = "31 (2) 35 (46) 2 (2) 17 46 (2) 38 (2) 47 (2) 13 (4) 5 32 (6) 1 32 (2) 14 (2) 45 32 (2) 62 (32)"
    correct_breakdown += " 7 (14) 2 (9) 7 (2) 7 (13) 2 (3) 5 (2) 6 (2) 6 4 (4) 7 (3) 5 7 (3) 53 14 (2) 16 (16) 95 (2) 6"
    correct_breakdown += " 23 15 12 (4) 15 7 15 8 (2) 30 77 (2) 2 4 (113) 94 (2) 14 (2) 15 15 (5) 4 (24) 127 31 80 (2) "
    correct_breakdown += "30 (16) 49 30 (2) 15 15 111 3 8 (4) 15 12 (2) 34 (20) 43 (2) 44 63 104 (16) 7 (2) 19 (3) 33 "
    correct_breakdown += "(7) 1 (7) 16 16 (2) 13 16 (2) 14"

    if result["breakdown"] == correct_breakdown:
        good("PEMA's breakdown is correct.")
        passed += 1
    else:
        fail_val("PEMA's breakdown is incorrect.", correct_breakdown, result["breakdown"])
        failed += 1

    correct_breakdown = "31 - 35 | 2 - 64* - 38 - 47 - 13 - 38* / 34* - 14 - 78* - 62 / 7 / 2 / 7 - 7 / 2 - 5 - 6 - 11*"
    correct_breakdown += " - 7 - 13* - 68* - 16 / 95 - 59* - 48* - 108* - 7* | 94 - 14 - 31* / 4 / 240* - 30 / 80* - "
    correct_breakdown += "156* - 28* - 34 / 43 - 213* / 7 - 19 - 33 / 1 / 33* - 30* - 14"

    if result["partial_breakdown"] == correct_breakdown:
        good("PEMA's partially simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("PEMA's partially simplified breakdown is incorrect.", correct_breakdown, result["partial_breakdown"])
        failed += 1

    correct_breakdown = "68* | 214* / 194* / 7 / 2 / 16* / 147* / 327* | 143* / 4 / 272* / 306* / 258* / 64* / 1 / 81*"

    if result["simple_breakdown"] == correct_breakdown:
        good("PEMA's simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("PEMA's simplified breakdown is incorrect.", correct_breakdown, result["simple_breakdown"])
        failed += 1

    if result["total_stream"] == 2000:
        good("PEMA's total stream is correct.")
        passed += 1
    else:
        fail_val("PEMA's total stream is incorrect.", 2000, result["total_stream"])
        failed += 1

    if result["total_break"] == 448:
        good("PEMA's total break is correct.")
        passed += 1
    else:
        fail_val("PEMA's total break is incorrect.", 448, result["total_break"])
        failed += 1

    data = dbm.search("Hardware Store", DATABASE_FILE)
    result = data[0]

    correct_breakdown = "=3= =59= (8) =34= \\1\\ =7="

    if result["breakdown"] == correct_breakdown:
        good("Hardware Store's breakdown is correct.")
        passed += 1
    else:
        fail_val("Hardware Store's breakdown is incorrect.", correct_breakdown, result["breakdown"])
        failed += 1

    correct_breakdown = "=63=* / =34= \\1\\ =7="

    if result["partial_breakdown"] == correct_breakdown:
        good("Hardware Store's partially simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("Hardware Store's partially simplified breakdown is incorrect.", correct_breakdown, result["partial_breakdown"])
        failed += 1

    correct_breakdown = "=63=* / =34= \\1\\ =7="

    if result["simple_breakdown"] == correct_breakdown:
        good("Hardware Store's simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("Hardware Store's simplified breakdown is incorrect.", correct_breakdown, result["simple_breakdown"])
        failed += 1

    correct_normalized_breakdown = "6 118 (16) 68 (2) 14 *@253BPM*"
    bpm_to_use = normalizer.get_best_bpm_to_use(result["min_bpm"], result["max_bpm"], result["median_nps"], result["display_bpm"])
    should_normalize = normalizer.if_should_normalize(result["breakdown"], result["total_stream"])
    normalized_breakdown = normalizer.normalize(result["breakdown"], bpm_to_use, should_normalize)

    if normalized_breakdown == correct_normalized_breakdown:
        good("Hardware Store's normalized breakdown is correct.")
        passed += 1
    else:
        fail_val("Hardware Store's normalized breakdown is incorrect.", correct_normalized_breakdown, normalized_breakdown)
        failed += 1


    data = dbm.search("Noise Discipline", DATABASE_FILE)
    result = data[0]

    correct_breakdown = "~1~ ~7~ ~15~ ~39~ 1 (16) ~1~ 1 ~7~ ~15~ ~40~ (12) 1 ~1~ 2 ~8~ (2) ~30~ (2) ~4~ (2) ~48~ (8) ~183~ ~63~ (3) ~45~ ~39~ 1 ~12~ (4) ~39~ ~6~ (2) ~7~ 1 ~11~ 1 (4) ~64~ (32) ~64~ (47) 1 ~32~"

    if result["breakdown"] == correct_breakdown:
        good("Noise Discipline's breakdown is correct.")
        passed += 1
    else:
        fail_val("Noise Discipline's breakdown is incorrect.", correct_breakdown, result["breakdown"])
        failed += 1

    correct_breakdown = "~65~* 1 / ~1~ 1 ~64~* / 1 ~1~ 2 ~8~ - ~30~ - ~4~ - ~48~ / ~247~* - ~85~* 1 ~12~ - ~46~* - ~7~ 1 ~11~ 1 - ~64~ / ~64~ | 1 ~32~"

    if result["partial_breakdown"] == correct_breakdown:
        good("Noise Discipline's partially simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("Noise Discipline's partially simplified breakdown is incorrect.", correct_breakdown,
                 result["partial_breakdown"])
        failed += 1

    correct_breakdown = "~65~* 1 / ~1~ 1 ~64~* / 1 ~1~ 2 ~96~* / ~335~* 1 ~71~* 1 ~11~ 4* ~64~ / ~64~ | 1 ~32~"

    if result["simple_breakdown"] == correct_breakdown:
        good("Noise Discipline's simplified breakdown is correct.")
        passed += 1
    else:
        fail_val("Noise Discipline's simplified breakdown is incorrect.", correct_breakdown, result["simple_breakdown"])
        failed += 1

    correct_normalized_breakdown = "1 8 18 48 (22) 1 (1) 8 18 50 (17) 1 (2) 10 (2) 37 (2) 5 (2) 60 (10) 228 78 (3) 56 48 (1) 15 (5) 48 7 (2) 8 (1) 13 (7) 80 (40) 80 (60) 40 *@218BPM*"
    bpm_to_use = normalizer.get_best_bpm_to_use(result["min_bpm"], result["max_bpm"], result["median_nps"],
                                                result["display_bpm"])
    should_normalize = normalizer.if_should_normalize(result["breakdown"], result["total_stream"])
    normalized_breakdown = normalizer.normalize(result["breakdown"], bpm_to_use, should_normalize)

    if normalized_breakdown == correct_normalized_breakdown:
        good("Noise Discipline's normalized breakdown is correct.")
        passed += 1
    else:
        fail_val("Noise Discipline's normalized breakdown is incorrect.", correct_normalized_breakdown,
                 normalized_breakdown)
        failed += 1

    if should_normalize == RunDensity.Run_20:
        good("Noise Discipline is correctly normalizing to 20ths.")
        passed += 1
    else:
        fail_val("Noise Discipline is not being normalized.", RunDensity.Run_20,
                 should_normalize)
        failed += 1

    data = dbm.search("Sa MaRichi", DATABASE_FILE)
    result = data[0]

    if result["total_candles"] == 49:
        good("Sa MaRichi's candle count is correct.")
        passed += 1
    else:
        fail_val("Sa MaRichi's candle count is incorrect.", 49, result["total_candles"])
        failed += 1

    if failed > 0:
        sys.exit("Unit tests did not pass.")
    else:
        print("Unit tests passed!")
        sys.exit(0)