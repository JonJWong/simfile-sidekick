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
        try:
            return result["autodelete"]
        except KeyError:
            return None
    else:
        return None

def get_autodelete_with_default(id, db, default):
    result = get_autodelete(id, db)
    if result is None:
        return default
    else:
        return result

def set_normalize(id, flag, db):
    user_db = TinyDB(db)
    UserDBQuery = Query()
    user_db.upsert({"id": id, "normalize": flag}, UserDBQuery.id == id)
    user_db.close()

def get_normalize(id, db):
    user_db = TinyDB(db)
    UserDBQuery = Query()
    results = user_db.search(UserDBQuery.id == id)
    if results:
        result = json.loads(json.dumps(results[0]))
        user_db.close()
        try:
            return result["normalize"]
        except KeyError:
            return None
    else:
        return None

def get_normalize_with_default(id, db, default):
    result = get_normalize(id, db)
    if result is None:
        return default
    else:
        return result