# app.py
from flask import Flask, request, jsonify
from supabase_client import supabase  # your existing Supabase client
from darino import register, login, request_phone_code, scan_result
import uuid, datetime

app = Flask(__name__)

# --- Helper function to save account in Supabase ---
def save_account_to_db(user_id, bot_type, email, password, promo_code):
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
        return False, res.error
    return True, res.data[0]

# --- Endpoint: Create Darino accounts ---
@app.route("/bot/darino/create", methods=["POST"])
def create_accounts():
    payload = request.get_json()
    promo_code = payload.get("promo_code", "")
    count = int(payload.get("count", 1))
    user_id = payload.get("user_id")  # assume frontend sends this or get from session

    created_accounts = []
    success_count = 0

    for _ in range(count):
        # generate a random email and password
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
            # save to Supabase
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
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Missing user_id"}), 400

    res = supabase.table("bot_accounts").select("*").eq("user_id", user_id).eq("bot_type", "darino").execute()
    if res.error:
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
    payload = request.get_json()
    account_id = payload.get("account_id")
    phone = payload.get("phone")

    if not account_id or not phone:
        return jsonify({"success": False, "error": "Missing account_id or phone"}), 400

    # Fetch account from Supabase
    res = supabase.table("bot_accounts").select("*").eq("id", account_id).execute()
    if res.error or not res.data:
        return jsonify({"success": False, "error": "Account not found"}), 404

    account = res.data[0]
    # Login first
    login_res = login(account["email"], account["password"])
    token = login_res.get("data", {}).get("token")
    uuid_val = login_res.get("data", {}).get("uuid")  # adjust based on Darino API

    if not token or not uuid_val:
        return jsonify({"success": False, "error": "Login failed"}), 500

    # Request phone code
    code_res = request_phone_code(uuid_val, phone, token)

    if code_res.get("code") != 0:
        return jsonify({"success": False, "error": code_res}), 500

    # Simulate waiting for user to type "done" in frontend
    scan_res = scan_result(uuid_val, token)

    if scan_res.get("code") == 0:
        # Update Supabase
        update_res = supabase.table("bot_accounts").update({
            "status": "bound",
            "metadata": scan_res
        }).eq("id", account_id).execute()
        if update_res.error:
            return jsonify({"success": False, "error": str(update_res.error)}), 500

        return jsonify({"success": True, "message": "Account bound successfully!"})

    else:
        return jsonify({"success": False, "error": "Scan failed or not completed"}), 500


if __name__ == "__main__":
    app.run(debug=True)
