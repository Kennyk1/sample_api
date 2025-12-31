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
    if phone.startswith("+"):
        phone = phone.replace("+", "")
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
@darino_bp.route("/info")
def info():
    return jsonify({"bot_name": "Darino", "bot_type": "darino", "website": "https://darino.vip"})

# -------- CREATE ACCOUNTS --------
@darino_bp.route("/create", methods=["POST"])
def create_accounts():
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.json or {}
        promo_code = data.get("promo_code", "")
        count = int(data.get("count", 1))

        created, failed = [], []

        for _ in range(count):
            email = generate_email()
            password = generate_password()

            ok, res = register_darino_account(email, password, promo_code)
            acc = {"email": email, "password": password, "promo_code": promo_code,
                   "status": "not_bound", "bot_type": "darino", "created_at": datetime.utcnow().isoformat()}

            if ok:
                login_res = darino_login(email, password)
                token = login_res.get("data", {}).get("token")
                if token:
                    acc["token"] = token
                    created.append(acc)
                else:
                    acc["error"] = "Login token missing"
                    failed.append(acc)
            else:
                acc["error"] = res
                failed.append(acc)
            time.sleep(1)

        if created:
            save_bot_accounts(user_id, created)

        return jsonify({"success": True, "created": len(created),
                        "failed": len(failed), "accounts": created, "failed_accounts": failed})
    except Exception as e:
        logging.exception("Create accounts failed")
        return jsonify({"success": False, "error": "Internal server error"}), 500

# -------- GET ACCOUNTS --------
@darino_bp.route("/accounts", methods=["GET"])
def get_accounts():
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        accounts = get_user_accounts(user_id, bot_type="darino") or []
        return jsonify({"success": True, "accounts": accounts})
    except Exception as e:
        logging.exception("Get accounts failed")
        return jsonify({"success": False, "error": "Internal server error"}), 500

# -------- REQUEST BIND CODE --------
@darino_bp.route("/bind", methods=["POST"])
def bind_request_code():
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.json or {}
        account_id = data.get("account_id")
        phone = data.get("phone")
        if not account_id or not phone:
            return jsonify({"success": False, "error": "Missing account_id or phone"}), 400

        accounts = get_user_accounts(user_id, bot_type="darino") or []
        account = next((a for a in accounts if a.get("id") == account_id), None)
        if not account:
            return jsonify({"success": False, "error": "Account not found"}), 404

        # Ensure email/password exist
        if not account.get("email") or not account.get("password"):
            return jsonify({"success": False, "error": "Account missing email or password"}), 400

        # Ensure token exists
        token = account.get("token")
        if not token:
            login_res = darino_login(account["email"], account["password"])
            token = login_res.get("data", {}).get("token")
            if not token:
                return jsonify({"success": False, "error": "Login failed"}), 500

        # Generate UUID and request phone code
        uuid_val = generate_uuid()
        phone_res = request_phone_code(uuid_val, phone, token)
        if phone_res.get("code") != 0:
            return jsonify({"success": False, "error": phone_res.get("msg", "Unknown error")}), 400

        # Save UUID without overwriting other fields
        update_data = account.copy()
        update_data["uuid"] = uuid_val
        save_bot_accounts(user_id, [update_data], update=True)

        return jsonify({
            "success": True,
            "message": "Code requested. Enter it in WhatsApp",
            "uuid": uuid_val,
            "phone_code": phone_res.get("data", {}).get("phone_code")
        })

    except Exception as e:
        logging.exception("Bind request failed")
        return jsonify({"success": False, "error": "Internal server error"}), 500

# -------- CHECK BIND STATUS --------
@darino_bp.route("/bind/status", methods=["POST"])
def bind_check_status():
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.json or {}
        account_id = data.get("account_id")
        if not account_id:
            return jsonify({"success": False, "error": "Missing account_id"}), 400

        accounts = get_user_accounts(user_id, bot_type="darino") or []
        account = next((a for a in accounts if a.get("id") == account_id), None)
        if not account:
            return jsonify({"success": False, "error": "Account not found"}), 404

        token = account.get("token")
        uuid_val = account.get("uuid")
        if not token or not uuid_val:
            return jsonify({"success": False, "error": "Binding not started"}), 400

        scan_res = scan_result(uuid_val, token)
        if scan_res.get("code") == 0:
            # Update account as bound
            update_data = account.copy()
            update_data["status"] = "bound"
            update_data["metadata"] = scan_res
            save_bot_accounts(user_id, [update_data], update=True)
            return jsonify({"success": True, "message": "Account bound successfully", "data": scan_res.get("data")})

        return jsonify({"success": False, "message": scan_res.get("msg", "Scan not completed yet")})

    except Exception as e:
        logging.exception("Bind check failed")
        return jsonify({"success": False, "error": "Internal server error"}), 500
        @darino_bp.route("/test_update")
def test_update():
    return jsonify({"success": True, "message": "Updated code is running!"})
