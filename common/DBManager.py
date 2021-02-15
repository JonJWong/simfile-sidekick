from tinydb import TinyDB, Query
from typing import List, Union
import json
import re

def search_by_title(song_title: str, db: Union[str, TinyDB]) -> Union[int, List]:
    """

    :param song_title: The
    :param db:
    :return:
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