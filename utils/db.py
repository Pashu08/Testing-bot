# utils/db.py
import json
import os

DB_FILE = 'database.json'

def load_db():
    # If no database exists, create an empty one
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({}, f, indent=4)
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Database Read Error: {e}")
        return {}

def save_db(data):
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ Database Save Error: {e}")
