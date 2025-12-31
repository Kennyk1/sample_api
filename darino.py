import requests
import json
import time
import random
import string
import logging
from datetime import datetime
from supabase_client import supabase  # your existing Supabase client

BASE = "https://api.darino.vip"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "origin": "https://darino.vip"
}

# ---------------- UTILITY FUNCTIONS ----------------

def clean_json(text):
    if "{" in text:
        text = text[text.find("{"):]
    if "}" in text:
        text = text[:text.rfind("}")+1]
    return json.loads(text)

def generate_email():
    names = ["qidazz", "Favour", "light", "daniel", "malik"]
    return f"{random.choice(names)}{random.randint(100000,999999)}@gmail.com"

def generate_password():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=10))

# ---------------- DARINO API ----------------

def register(email, password, promo=None):
    payload = {
        "email": email,
        "password": password,
        "confirmPassword": password,
        "promo_code": promo or ""
    }

    r = requests.post(
        f"{BASE}/h5/taskBase/biz3/register",
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=15
    )

    result = clean_json(r.text)
    return result.get("code") == 0, result

def login(email, password):
    payload = {"email": email, "password": password}
    r = requests.post(
        f"{BASE}/h5/taskBase/login",
        headers=HEADERS,
        data=json.dumps(payload)
    )
    return clean_json(r.text)

def request_phone_code(uuid, phone, token):
    h = HEADERS.copy()
    h["x-token"] = token
    payload = {"uuid": uuid, "phone": phone.replace("+", ""), "type": 2}
    r = requests.post(
        f"{BASE}/h5/taskUser/phoneCode",
        headers=h,
        data=json.dumps(payload)
    )
    return clean_json(r.text)

def scan_result(uuid, token):
    h = HEADERS.copy()
    h["x-token"] = token
    r = requests.post(
        f"{BASE}/h5/taskUser/scanCodeResult",
        headers=h,
        data=json.dumps({"uuid": uuid})
    )
    return clean_json(r.text)

# ---------------- SUPABASE INTEGRATION ----------------

def save_account_to_supabase(user_id, bot_type, email, password, promo_code, status="not_bound", metadata=None):
    if metadata is None:
        metadata = {}
    try:
        response = supabase.table("bot_accounts").insert({
            "user_id": user_id,
            "bot_type": bot_type,
            "email": email,
            "password": password,
            "promo_code": promo_code,
            "status": status,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        return response
    except Exception as e:
        logging.error(f"Supabase insert error: {e}")
        return None

def update_account_status(account_id, status, metadata=None):
    try:
        data = {"status": status}
        if metadata:
            data["metadata"] = metadata
        response = supabase.table("bot_accounts").update(data).eq("id", account_id).execute()
        return response
    except Exception as e:
        logging.error(f"Supabase update error: {e}")
        return None

# ---------------- HIGH-LEVEL FUNCTIONS ----------------

def create_darino_account(user_id, promo_code=None):
    email = generate_email()
    password = generate_password()
    success, result = register(email, password, promo_code)

    account_metadata = {"raw_response": result}
    save_account_to_supabase(user_id, "darino", email, password, promo_code or "", "not_bound", account_metadata)

    return success, email, password, result

def bind_account_flow(account_id, email, password, phone):
    # 1. login
    login_res = login(email, password)
    token = login_res.get("data", {}).get("token")
    uuid = login_res.get("data", {}).get("uuid")

    if not token or not uuid:
        return False, "Login failed"

    # 2. request phone code
    code_res = request_phone_code(uuid, phone, token)
    if code_res.get("code") != 0:
        return False, code_res

    # 3. wait or poll scan result (simulate user confirming in WhatsApp)
    for _ in range(15):
        scan_res = scan_result(uuid, token)
        if scan_res.get("data", {}).get("status") == "ok":
            # update supabase
            update_account_status(account_id, "bound", {"scan_result": scan_res})
            return True, scan_res
        time.sleep(2)

    # if still not bound
    update_account_status(account_id, "rebind_required", {"scan_result": scan_res})
    return False, scan_res
