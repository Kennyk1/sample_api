import json, os, time

FILE = "accounts.json"

def save_account(data):
    db = []
    if os.path.exists(FILE):
        with open(FILE) as f:
            db = json.load(f)

    data["created_at"] = time.time()
    db.append(data)

    with open(FILE, "w") as f:
        json.dump(db, f, indent=2)

def log_action(action, data=None):
    print(f"[LOG] {action}", data or "")
