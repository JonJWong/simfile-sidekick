from tinydb import TinyDB, Query
import re

db = TinyDB("db.json")

def search(title):
    q = Query()
    results = db.search(q.title.search(title, flags=re.IGNORECASE))
    if len(results) == 0:
        return 0
    elif len(results) >= 1:
        return results
    else:
        return -1