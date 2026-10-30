import json
import os

DB_FILE = 'imposter_words.json'

def load_imposter_db():
    # If the file doesn't exist yet, return an empty dictionary
    if not os.path.exists(DB_FILE):
        return {}
    
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_imposter_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)
