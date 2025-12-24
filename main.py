from fastapi import FastAPI, HTTPException
import requests
import json
from datetime import datetime

app = FastAPI(title="Darino API Bridge")

DARINO_API = "https://api.darino.vip/create"  # example
HEADERS = {
    "User-Agent": "DarinoTerminal/1.0",
    "Content-Type": "application/json"
}

DB_FILE = "accounts.json"


def save_account(data):
    try:
        with open(DB_FILE, "r") as f:
            db = json.load(f)
    except:
        db = []

    db.append(data)

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


@app.get("/")
def home():
    return {"status": "online", "service": "Darino API Bridge"}


@app.post("/create-account")
def create_account(payload: dict):
    """
    Expected payload example:
    {
        "email": "...",
        "password": "...",
        "phone": "..."
    }
    """

    try:
        response = requests.post(
            DARINO_API,
            json=payload,
            headers=HEADERS,
            timeout=30
        )

        result = response.json()

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=result)

        save_account({
            "payload": payload,
            "response": result,
            "created_at": datetime.utcnow().isoformat()
        })

        return {
            "success": True,
            "darino_response": result
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
