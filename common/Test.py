from common import DBManager as dbm
import json

def run_tests():

    passed = 0
    failed = 0

    f = open("tests/scan.log")
    log_contents = f.read()
    result = log_contents.find("scan.py finished at: ")

    if result != -1:
        print("PASSED: scan.py parsed all songs.")
        passed += 1
    else:
        print("FAILED: scan.py did not parse all songs.")
        failed += 1

    # 30MIN Harder has a missing semicolon (;) in the BPMs list.

    result = log_contents.find("04 - 30MIN HARDER.sm\" is missing semicolon.")

    if result != -1:
        print("PASSED: scan.py correctly handles missing semicolon in BPM list.")
        passed += 1
    else:
        print("FAILED: scan.py did not handle missing semicolon in BPM list.")
        failed += 1

    # I'm A Maid has a colon (:) where a semicolon (;) should be

    result = log_contents.find("Completed parsing \"tests/songs/I'm A Maid (C-Type Remix)/Im a maid.sm\".")

    if result != -1:
        print("PASSED: scan.py correctly handles misplaced colon.")
        passed += 1
    else:
        print("FAILED: scan.py did not handle misplaced colon.")
        failed += 1

    # OceanLab Megamix has strange non-printable characters in the BPM section

    result = log_contents.find("oceanlab.sm\" contains non-printable characters. Handled and continuing.")

    if result != -1:
        print("PASSED: scan.py correctly handles non-printable characters in BPM section.")
        passed += 1
    else:
        print("FAILED: scan.py did not handle non-printable characters in BPM section.")
        failed += 1

    # DEATHMATCH has charts initialised to 0's, that is, a chart exists but is simply a placeholder
    # and no arrows have yet been added. This resolved a division by zero error when calculating statistics.

    result = log_contents.find("The Hard 1 chart for DEATHMATCH is empty. Skipping")

    if result != -1:
        print("PASSED: scan.py correctly handles empty charts.")
        passed += 1
    else:
        print("FAILED: scan.py did not properly handle an empty chart.")
        failed += 1

    # Generic tests to check measure counter

    # We want to make sure Encoder's breakdown is 32. We don't want to capture any break segments before or after
    # the one and only run.

    data = dbm.search_ut("Encoder")
    result = json.loads(json.dumps(data[4])) # [5] so we grab the challenge chart, and not the easy or medium, etc.

    if result["breakdown"] == "32":
        print("PASSED: Encoder's breakdown is correct.")
        passed += 1
    else:
        print("FAILED: Encoder's breakdown is incorrect.")
        failed += 1