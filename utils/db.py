# utils/db.py
import json
import os

DB_FILE = 'database.json'

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"words": {"general": ["discord", "python", "termux"]}, "stats": {}}, f, indent=4)
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Database Read Error: {e}")
        return {"words": {}, "stats": {}}

def save_db(data):
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ Database Save Error: {e}")
