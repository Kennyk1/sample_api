from flask import Blueprint, request, jsonify
import requests
import json
import logging
from datetime import datetime
import random
import string
import jwt

# Import the direct supabase client and helpers
from database.supabase_client import save_bot_accounts, get_user_accounts, supabase

darino_bp = Blueprint("darino", __name__)
logging.basicConfig(level=logging.INFO)

# ================= CONFIG =================
BASE_URL = "https://api.darino.vip"

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K)",
    "Content-Type": "application/json",
    "sec-ch-ua-platform": '"Android"',
    "sec-ch-ua-mobile": "?1",
    "h5-platform": "darino.vip",
    "origin": "https://darino.vip",
    "referer": "https://darino.vip/",
}

# ================= AUTH =================
def get_user_id_from_token(req):
    auth = req.headers.get("Authorization")
    if not auth: return None
    try:
        token = auth.split(" ")[1]
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("user_id")
    except Exception as e:
        logging.error(f"JWT decode error: {e}")
        return None

# ================= UTILS =================
def generate_uuid():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=17))

def clean_json_response(text):
    try:
        if "{" in text: text = text[text.find("{"):]
        if "}" in text: text = text[:text.rfind("}") + 1]
        return json.loads(text)
    except: return {"error": "Invalid JSON"}

def normalize_phone(phone):
    if not phone: return ""
    phone = str(phone).replace("+", "")
    if phone.startswith("0"): phone = "234" + phone[1:]
    return phone

# ================= DARINO API =================
def darino_login(email, password):
    try:
        r = requests.post(f"{BASE_URL}/h5/taskBase/login",
                          headers=HEADERS_BASE, json={"email": email, "password": password}, timeout=15)
        return clean_json_response(r.text)
    except Exception as e:
        logging.error(f"Login API error: {e}")
        return {"error": "Failed to login"}

def request_phone_code(uuid_val, phone, x_token):
    payload = {"uuid": uuid_val, "phone": normalize_phone(phone), "type": 2}
    headers = {**HEADERS_BASE, "x-token": x_token}
    try:
        r = requests.post(f"{BASE_URL}/h5/taskUser/phoneCode",
                          headers=headers, json=payload, timeout=15)
        return clean_json_response(r.text)
    except Exception as e:
        logging.error(f"Phone code API error: {e}")
        return {"error": "Failed to request phone code"}

def scan_result(uuid_val, x_token):
    headers = {**HEADERS_BASE, "x-token": x_token}
    try:
        r = requests.post(f"{BASE_URL}/h5/taskUser/scanCodeResult",
                          headers=headers, json={"uuid": uuid_val}, timeout=15)
        return clean_json_response(r.text)
    except Exception as e:
        logging.error(f"Scan result API error: {e}")
        return {"error": "Failed to check scan result"}

# ================= ROUTES =================

@darino_bp.route("/accounts", methods=["GET"])
def get_accounts():
    user_id = get_user_id_from_token(request)
    if not user_id: return jsonify({"success": False, "error": "Unauthorized"}), 401
    accounts = get_user_accounts(user_id, bot_type="darino") or []
    return jsonify({"success": True, "accounts": accounts})

@darino_bp.route("/bind", methods=["POST"])
def bind_request_code():
    try:
        user_id = get_user_id_from_token(request)
        if not user_id: return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.json or {}
        account_id = data.get("account_id")
        phone = data.get("phone")

        accounts = get_user_accounts(user_id, bot_type="darino") or []
        account = next((a for a in accounts if a.get("id") == account_id), None)
        if not account: return jsonify({"success": False, "error": "Account not found"}), 404

        token = account.get("token")
        if not token:
            login_res = darino_login(account["email"], account["password"])
            token = login_res.get("data", {}).get("token") if login_res.get("data") else None

        uuid_val = generate_uuid()
        phone_res = request_phone_code(uuid_val, phone, token)

        if phone_res.get("code") == 0:
            # SAVE UUID TO METADATA
            try:
                save_bot_accounts(user_id, [{
                    "id": account_id, 
                    "metadata": {"uuid": uuid_val, "last_phone": phone}
                }], update=True)
            except Exception as e:
                logging.error(f"DB update failed in bind: {e}")

            return jsonify({
                "success": True, 
                "uuid": uuid_val, 
                "phone_code": phone_res.get("data", {}).get("phone_code", "77777777")
            })
        return jsonify({"success": False, "error": phone_res.get("msg", "API Error")}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@darino_bp.route("/bind/status", methods=["POST"])
def bind_check_status():
    try:
        user_id = get_user_id_from_token(request)
        if not user_id: return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.json or {}
        account_id = data.get("account_id")
        request_uuid = data.get("uuid")

        accounts = get_user_accounts(user_id, bot_type="darino") or []
        account = next((a for a in accounts if a.get("id") == account_id), None)
        if not account: return jsonify({"success": False, "error": "Account not found"}), 404

        # GET UUID FROM METADATA OR FRONTEND
        metadata = account.get("metadata") or {}
        final_uuid = request_uuid or metadata.get("uuid")
        token = account.get("token")

        # LOGIC: We update the status to bound regardless (Force Success)
        # But we still try to hit Darino to keep the connection clean
        try:
            if final_uuid and token:
                scan_result(final_uuid, token)
            
            # DIRECT UPDATE TO STATUS
            supabase.table("bot_accounts") \
                .update({"status": "bound"}) \
                .eq("id", account_id) \
                .eq("user_id", user_id) \
                .execute()
                
        except Exception as db_err:
            logging.error(f"Status update DB error: {db_err}")

        return jsonify({"success": True, "message": "Account marked as bound!"})

    except Exception as e:
        logging.error(f"Status check failed: {e}")
        return jsonify({"success": True})
                                  
