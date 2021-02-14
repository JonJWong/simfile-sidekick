from tinydb import TinyDB, Query
import json

def set_autodelete(id, flag, db):
    user_db = TinyDB(db)
    UserDBQuery = Query()
    user_db.upsert({"id": id, "autodelete": flag}, UserDBQuery.id == id)
    user_db.close()

def get_autodelete(id, db):
    user_db = TinyDB(db)
    UserDBQuery = Query()
    results = user_db.search(UserDBQuery.id == id)
    if results:
        result = json.loads(json.dumps(results[0]))
        user_db.close()
        return result["autodelete"]
    else:
        return None

def get_autodelete_with_default(id, db, default):
    result = get_autodelete(id, db)
    if result is None:
        return default
    else:
        return result