# app.py
from flask import Flask, request, jsonify
from supabase_client import supabase  # your existing Supabase client
from darino import register, login, request_phone_code, scan_result
import uuid, datetime
import jwt
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- Helper: extract user_id from JWT token ---
def get_user_id_from_token(auth_header):
    if not auth_header:
        logging.warning("Authorization header missing")
        return None
    try:
        token = auth_header.split(" ")[1]  # Bearer <token>
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("user_id")  # match your token payload
        if not user_id:
            logging.warning("user_id not found in token")
        return user_id
    except Exception as e:
        logging.error(f"Token decode error: {e}")
        return None

# --- Helper function to save account in Supabase ---
def save_account_to_db(user_id, bot_type, email, password, promo_code):
    if not user_id:
        logging.error("Cannot save account without user_id")
        return False, "Missing user_id"

    data = {
        "user_id": user_id,
        "bot_type": bot_type,
        "email": email,
        "password": password,
        "promo_code": promo_code,
        "status": "not_bound",
        "metadata": {},
        "created_at": datetime.datetime.utcnow()
    }
    res = supabase.table("bot_accounts").insert(data).execute()
    if res.error:
        logging.error(f"Supabase insert error: {res.error}")
        return False, res.error
    logging.info(f"Account saved: {email}")
    return True, res.data[0]

# --- Endpoint: Create Darino accounts ---
@app.route("/bot/darino/create", methods=["POST"])
def create_accounts():
    # Step 1: Extract user_id from Authorization token
    user_id = get_user_id_from_token(request.headers.get("Authorization"))
    if not user_id:
        return jsonify({"success": False, "error": "Invalid or missing Authorization token"}), 401

    # Step 2: Parse payload
    payload = request.get_json()
    promo_code = payload.get("promo_code", "")
    count = int(payload.get("count", 1))

    created_accounts = []
    success_count = 0

    for _ in range(count):
        email = f"user{uuid.uuid4().hex[:8]}@example.com"
        password = uuid.uuid4().hex[:10]

        ok, result = register(email, password, promo_code)
        account_entry = {
            "email": email,
            "password": password,
            "promo_code": promo_code,
            "status": "not_bound",
            "created_at": datetime.datetime.utcnow(),
            "error": None
        }

        if ok:
            saved, db_result = save_account_to_db(user_id, "darino", email, password, promo_code)
            if saved:
                success_count += 1
            else:
                account_entry["error"] = str(db_result)
        else:
            account_entry["error"] = result

        created_accounts.append(account_entry)

    return jsonify({
        "success": True,
        "created": success_count,
        "accounts": created_accounts
    })

# --- Endpoint: Fetch existing Darino accounts ---
@app.route("/bot/darino/accounts", methods=["GET"])
def get_accounts():
    user_id = get_user_id_from_token(request.headers.get("Authorization"))
    if not user_id:
        return jsonify({"success": False, "error": "Invalid or missing Authorization token"}), 401

    res = supabase.table("bot_accounts").select("*").eq("user_id", user_id).eq("bot_type", "darino").execute()
    if res.error:
        logging.error(f"Error fetching accounts: {res.error}")
        return jsonify({"success": False, "error": str(res.error)}), 500

    accounts = []
    for row in res.data:
        accounts.append({
            "id": row["id"],
            "email": row["email"],
            "password": row["password"],
            "promo_code": row.get("promo_code"),
            "status": row["status"],
            "created_at": row["created_at"]
        })

    return jsonify({"success": True, "accounts": accounts})

# --- Endpoint: Bind account ---
@app.route("/bot/darino/bind", methods=["POST"])
def bind_account():
    user_id = get_user_id_from_token(request.headers.get("Authorization"))
    if not user_id:
        return jsonify({"success": False, "error": "Invalid or missing Authorization token"}), 401

    payload = request.get_json()
    account_id = payload.get("account_id")
    phone = payload.get("phone")

    if not account_id or not phone:
        return jsonify({"success": False, "error": "Missing account_id or phone"}), 400

    # Fetch account from Supabase
    res = supabase.table("bot_accounts").select("*").eq("id", account_id).eq("user_id", user_id).execute()
    if res.error or not res.data:
        return jsonify({"success": False, "error": "Account not found or not owned by user"}), 404

    account = res.data[0]
    login_res = login(account["email"], account["password"])
    token = login_res.get("data", {}).get("token")
    uuid_val = login_res.get("data", {}).get("uuid")

    if not token or not uuid_val:
        return jsonify({"success": False, "error": "Login failed"}), 500

    code_res = request_phone_code(uuid_val, phone, token)
    if code_res.get("code") != 0:
        return jsonify({"success": False, "error": code_res}), 500

    scan_res = scan_result(uuid_val, token)
    if scan_res.get("code") == 0:
        update_res = supabase.table("bot_accounts").update({
            "status": "bound",
            "metadata": scan_res
        }).eq("id", account_id).execute()
        if update_res.error:
            logging.error(f"Error updating account: {update_res.error}")
            return jsonify({"success": False, "error": str(update_res.error)}), 500

        return jsonify({"success": True, "message": "Account bound successfully!"})
    else:
        return jsonify({"success": False, "error": "Scan failed or not completed"}), 500


if __name__ == "__main__":
    app.run(debug=True)
