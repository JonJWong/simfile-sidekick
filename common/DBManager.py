from tinydb import Query, TinyDB
from tinydb.operations import delete
from typing import List, Union
import json
import re

# TODO: handle db.close on bad results (i.e. db.close() isn't called if we return 0/-1)

def search_by_title(song_title: str, db: Union[str, TinyDB]) -> Union[int, List]:
    """ Search the database for a song.

    :param song_title: The title of the song to search for.
    :param db: The name of the database, or the TinyDB object for that database.
    :return: Array of results that match criteria.
    """
    db_param_is_string = False

    if isinstance(db, str):
        db = TinyDB(db)
        db_param_is_string = True

    results = db.search(Query().title.search(song_title, flags=re.IGNORECASE))

    if len(results) == 0:
        return 0
    elif len(results) >= 1:
        results_array = []
        for r in results:
            results_array.append(json.loads(json.dumps(r)))
        if db_param_is_string:
            db.close()
        return results
    else:
        return -1


def delete_pack_search_results(pack_name: str, db: Union[str, TinyDB]):
    """ When deleting a pack, this will return a list of all songs that will be updated/deleted
    """

    db_param_is_string = False

    if isinstance(db, str):
        db = TinyDB(db)
        db_param_is_string = True

    results = db.search(Query().pack.search(pack_name, flags=re.IGNORECASE))

    songs_to_update = {}
    songs_to_delete = {}

    if len(results) == 0:
        return 0
    elif len(results) >= 1:
        for r in results:
            packs = r["pack"].split(",")
            if len(packs) > 1:
                songs_to_update[r.doc_id] = r["title"]
            else:
                songs_to_delete[r.doc_id] = r["title"]
        if db_param_is_string:
            db.close()
        return songs_to_update, songs_to_delete
    else:
        return -1

def delete_by_ids(ids, db):
    db_param_is_string = False

    if isinstance(db, str):
        db = TinyDB(db)
        db_param_is_string = True

    db.remove(doc_ids=ids)

    if isinstance(db, str):
        db.close()

    return True

def remove_pack_from_songs_by_id(pack, ids, db):
    db_param_is_string = False

    if isinstance(db, str):
        db = TinyDB(db)
        db_param_is_string = True

    for id in ids:
        result = db.get(doc_id=id)
        packs = result["pack"]
        packs = packs.split(",")
        for i, p in enumerate(packs):
            if re.search(pack, p, re.IGNORECASE):
                if i < len(packs):
                    # remove prepending space in next element if it exists
                    packs[i+1] = packs[i+1].strip()
                # delete from packs array
                del packs[i]
        db.update({"pack": ", ".join(packs)}, doc_ids=[id])

    if isinstance(db, str):
        db.close()

    return True

def pack_exists(pack_name, db):
    db_param_is_string = False

    if isinstance(db, str):
        db = TinyDB(db)
        db_param_is_string = True

    results = db.search(Query().pack.search(pack_name, flags=re.IGNORECASE))

    if results:
        return True
    else:
        return False