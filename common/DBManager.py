from tinydb import TinyDB, Query
import re

db = TinyDB("db.json")
db_ut = TinyDB("tests/db.json")

# TODO - combine these into one function and pass in DB as an argument.

def search(title):
    q = Query()
    results = db.search(q.title.search(title, flags=re.IGNORECASE))
    if len(results) == 0:
        return 0
    elif len(results) >= 1:
        return results
    else:
        return -1

def search_ut(title):
    q = Query()
    results = db_ut.search(q.title.search(title, flags=re.IGNORECASE))
    if len(results) == 0:
        return 0
    elif len(results) >= 1:
        return results
    else:
        return -1