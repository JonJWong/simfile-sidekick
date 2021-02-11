from common import DBManager as dbm
import json

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
    result = log_contents.find("scan.py finished at: ")

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

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Generic tests to check measure counter

    # We want to make sure Encoder's breakdown is 32. We don't want to capture any break segments before or after
    # the one and only run.

    data = dbm.search_ut("Encoder")
    result = json.loads(json.dumps(data[4])) # [4] so we grab the challenge chart, and not the easy or medium, etc.

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

    data = dbm.search_ut("Ganbatte")
    result = json.loads(json.dumps(data[1]))  # [1] so we grab the challenge chart, and not the other

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

    # Generic breakdown test for Pendulum Essential Mix (Side A)

    data = dbm.search_ut("Pendulum Essential Mix")
    result = json.loads(json.dumps(data[0]))

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