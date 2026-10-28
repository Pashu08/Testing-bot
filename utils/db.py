# utils/db.py
import json
import os

DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def init_guild(data, guild_id):
    if guild_id not in data:
        data[guild_id] = {"words": {}, "mods": []}
    if "mods" not in data[guild_id]:
        data[guild_id]["mods"] = []
    if "words" not in data[guild_id]:
        data[guild_id]["words"] = {}
    return data
