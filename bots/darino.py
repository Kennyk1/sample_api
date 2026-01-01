from flask import Blueprint, request, jsonify
import requests
import json
import logging
from datetime import datetime
import random
import string
import time
import jwt

from database.supabase_client import save_bot_accounts, get_user_accounts

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
    if not auth:
        return None
    try:
        token = auth.split(" ")[1]
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("user_id")
    except Exception as e:
        logging.error(f"JWT decode error: {e}")
        return None

# ================= UTILS =================
def generate_email():
    name = random.choice(["darino", "crypto", "trader", "invest", "digital"])
    digits = ''.join(random.choices(string.digits, k=6))
    return f"{name}{digits}@gmail.com"

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def generate_uuid():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=17))

def clean_json_response(text):
    try:
        if "{" in text:
            text = text[text.find("{"):]
        if "}" in text:
            text = text[:text.rfind("}") + 1]
        return json.loads(text)
    except Exception:
        return {"error": "Invalid JSON"}

def normalize_phone(phone):
    if not phone: return ""
    phone = str(phone).replace("+", "")
    if phone.startswith("0"):
        phone = "234" + phone[1:]
    return phone

# ================= DARINO API =================
def register_darino_account(email, password, promo_code):
    payload = {
        "email": email,
        "password": password,
        "confirmPassword": password,
        "promo_code": promo_code or "",
        "source": None
    }
    try:
        r = requests.post(f"{BASE_URL}/h5/taskBase/biz3/register",
                          headers=HEADERS_BASE, json=payload, timeout=15)
        res = clean_json_response(r.text)
        return res.get("code") == 0, res
    except Exception as e:
        logging.error(f"Register API error: {e}")
        return False, {"error": "Failed to call register API"}

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
            # We TRY to update Supabase, but if it fails, the frontend still has the UUID
            try:
                save_bot_accounts(user_id, [{"id": account_id, "uuid": uuid_val}], update=True)
            except: pass 

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
        # PRIORITY: Get UUID from the frontend request payload
        request_uuid = data.get("uuid")

        accounts = get_user_accounts(user_id, bot_type="darino") or []
        account = next((a for a in accounts if a.get("id") == account_id), None)
        if not account: return jsonify({"success": False, "error": "Account not found"}), 404

        token = account.get("token")
        # FALLBACK: Use DB uuid only if request didn't send one
        final_uuid = request_uuid or account.get("uuid")

        if not token or not final_uuid:
            return jsonify({"success": False, "error": "Binding session missing"}), 400

        scan_res = scan_result(final_uuid, token)
        if scan_res.get("code") == 0:
            try:
                save_bot_accounts(user_id, [{"id": account_id, "status": "bound"}], update=True)
            except: pass
            return jsonify({"success": True, "message": "Bound!"})

        return jsonify({"success": False, "message": scan_res.get("msg", "Pending...")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
