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
                token = login_res.get("data", {}).get("token") if login_res.get("data") else None
                if token:
                    acc["token"] = token
                    created.append(acc)
                else:
                    acc["error"] = "Login token missing"
                    failed.append(acc)
            else:
                acc["error"] = res
                failed.append(acc)
            time.sleep(0.5)

        if created:
            save_bot_accounts(user_id, created)

        return jsonify({"success": True, "created": len(created), "accounts": created})
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

# -------- REQUEST BIND CODE (Database-Free Version) --------
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

        # Get accounts to find the credentials
        accounts = get_user_accounts(user_id, bot_type="darino") or []
        account = next((a for a in accounts if a.get("id") == account_id), None)
        
        if not account:
            return jsonify({"success": False, "error": "Account not found"}), 404

        token = account.get("token")
        if not token:
            login_res = darino_login(account["email"], account["password"])
            token = login_res.get("data", {}).get("token") if login_res.get("data") else None

        # Generate the session UUID
        uuid_val = generate_uuid()
        
        # Call Darino API
        phone_res = request_phone_code(uuid_val, phone, token)

        if phone_res.get("code") == 0:
            # We return the uuid and phone_code to the frontend.
            # We don't save to Supabase here to avoid the Render crash.
            return jsonify({
                "success": True,
                "uuid": uuid_val,
                "phone_code": phone_res.get("data", {}).get("phone_code", "77777777")
            })
        else:
            return jsonify({"success": False, "error": phone_res.get("msg", "API Error")}), 400

    except Exception as e:
        logging.exception("Bind request failed")
        return jsonify({"success": False, "error": str(e)}), 500

# -------- CHECK BIND STATUS (Database-Free Version) --------
@darino_bp.route("/bind/status", methods=["POST"])
def bind_check_status():
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.json or {}
        account_id = data.get("account_id")
        uuid_val = data.get("uuid") # The frontend passes this back to us

        if not uuid_val:
            return jsonify({"success": False, "error": "No session UUID provided"}), 400

        accounts = get_user_accounts(user_id, bot_type="darino") or []
        account = next((a for a in accounts if a.get("id") == account_id), None)
        
        if not account:
            return jsonify({"success": False, "error": "Account not found"}), 404

        token = account.get("token")
        
        # Check Darino API directly using the UUID provided by the frontend
        scan_res = scan_result(uuid_val, token)
        
        if scan_res.get("code") == 0:
            # ONLY update status to bound if it actually succeeded
            # This is a simple update that shouldn't crash
            try:
                save_bot_accounts(user_id, [{"id": account_id, "status": "bound", "bound_phone": "Linked"}], update=True)
            except:
                pass 
            return jsonify({"success": True, "message": "Success!"})

        return jsonify({"success": False, "message": scan_res.get("msg", "Waiting for scan...")})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
        

# -------- CHECK BIND STATUS --------
@darino_bp.route("/bind/status", methods=["POST"])
def bind_check_status():
    try:
        user_id = get_user_id_from_token(request)
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.json or {}
        account_id = data.get("account_id")
        # UUID provided by frontend if DB didn't save it
        uuid_val = data.get("uuid") 

        accounts = get_user_accounts(user_id, bot_type="darino") or []
        account = next((a for a in accounts if a.get("id") == account_id), None)
        
        if not account:
            return jsonify({"success": False, "error": "Account not found"}), 404

        token = account.get("token")
        # Use UUID from request if the DB one is missing
        uuid_val = uuid_val or account.get("uuid")

        if not token or not uuid_val:
            return jsonify({"success": False, "error": "Binding session missing"}), 400

        scan_res = scan_result(uuid_val, token)
        
        if scan_res.get("code") == 0:
            # Update status to bound
            try:
                save_bot_accounts(user_id, [{"id": account_id, "status": "bound"}], update=True)
            except:
                pass
            return jsonify({"success": True, "message": "Bound!", "data": scan_res.get("data")})

        return jsonify({"success": False, "message": scan_res.get("msg", "Pending...")})

    except Exception as e:
        logging.exception("Bind status failed")
        return jsonify({"success": False, "error": "Internal server error"}), 500
