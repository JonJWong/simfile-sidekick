# Module Imports
from tinydb import where

# External Imports
import json

# Internal Imports
from globals import PREFIXES, DEFAULT_PREFIX


def get_prefixes(server_db):
    """Loads server prefixes from database.

    Even though servers can have their own prefixes, each one of these prefixes will need to be in the prefixes array
    created above. When the bot starts, this function is called. It will check the server database settings and add each
    servers chosen prefix to the prefixes array.
    """
    for item in server_db:
        prefix = item["prefix"]
        if prefix not in PREFIXES:
            PREFIXES.append(prefix)
    return PREFIXES


def is_prefix_for_server(server_db, id, prefix):
    """Check to see if prefix is used for server.

    This function checks if a command entered by a user is using the servers set prefix.
    """
    results = server_db.search(where("id") == id)

    if not results:
        # There is no entry in the database for this server. No configurations were set, so check if it matches the
        # default prefix.
        if prefix == DEFAULT_PREFIX:
            return True
        else:
            return False
    else:
        # The server has a set prefix
        data = json.loads(json.dumps(results[0]))
        if prefix == data["prefix"]:
            return True
        else:
            return False
