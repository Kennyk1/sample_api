from supabase import create_client, Client
import logging

# ================== SUPABASE CONFIG ==================

SUPABASE_URL = "https://vvkvowtrzmekbdresegf.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2a3Zvd3Ryem1la2JkcmVzZWdmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3MDQyMzIsImV4cCI6MjA4MjI4MDIzMn0.ge6YMn01wM_oEm1wT4tx1mUBxwXqUHiKZIQdCIC1-OM"

supabase: Client = None


def init_supabase():
    global supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        if not supabase:
            raise RuntimeError("Supabase client is None")
        logging.info("Supabase initialized successfully")
    except Exception as e:
        logging.critical("Supabase init failed", exc_info=True)
        raise RuntimeError("App cannot start without Supabase")


init_supabase()

# ================== AUTH ==================

def supabase_auth_sign_up(email: str, password: str):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if not res.user:
            return {"error": "Signup failed"}
        return {"user": res.user}
    except Exception as e:
        logging.exception("Signup error")
        return {"error": str(e)}


def supabase_auth_sign_in(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if not res.user:
            return {"error": "Invalid credentials"}
        return {"user": res.user}
    except Exception as e:
        logging.exception("Signin error")
        return {"error": str(e)}

# ================== USER PROFILE ==================

def insert_user_profile(user_id, email, referral_code, bio="", avatar_url=""):
    try:
        res = supabase.table("users").insert({
            "id": user_id,
            "email": email,
            "referral_code": referral_code,
            "bio": bio,
            "avatar_url": avatar_url
        }).execute()
        return {"data": res.data}
    except Exception as e:
        logging.exception("Insert profile error")
        return {"error": str(e)}


def get_user_by_email(email):
    try:
        res = supabase.table("users").select("*").eq("email", email).single().execute()
        return res.data
    except Exception:
        return None


def get_user_by_id(user_id):
    try:
        res = supabase.table("users").select("*").eq("id", user_id).single().execute()
        return res.data
    except Exception:
        return None


def update_user_profile(user_id, bio=None, avatar_url=None):
    """
    supabase-py v2 safe update
    """
    try:
        update_data = {}

        if bio is not None:
            update_data["bio"] = bio
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url

        if not update_data:
            return {"error": "No fields to update"}

        res = (
            supabase
            .table("users")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )

        # v2 success check
        if res.data is None:
            return {"error": "Update failed"}

        return {"data": res.data}

    except Exception as e:
        logging.exception("Update user profile error")
        return {"error": str(e)}

# ================== DASHBOARD & BOTS ==================

def get_all_bots():
    try:
        res = supabase.table("bots").select("*").eq("is_active", True).execute()
        return res.data or []
    except Exception:
        return []


def get_user_stats(user_id):
    try:
        total = supabase.table("bot_accounts") \
            .select("*", count="exact") \
            .eq("user_id", user_id) \
            .execute()

        success = supabase.table("bot_accounts") \
            .select("*", count="exact") \
            .eq("user_id", user_id) \
            .eq("status", "bound") \
            .execute()

        return {
            "total_accounts": total.count or 0,
            "success_accounts": success.count or 0
        }
    except Exception:
        return {"total_accounts": 0, "success_accounts": 0}

# ================== CHAT & SEARCH ==================

def search_users_by_handle(query):
    try:
        clean_handle = query.replace("@", "").strip()
        res = (
            supabase
            .table("users")
            .select("id, email, avatar_url, bio")
            .ilike("email", f"{clean_handle}@%")
            .execute()
        )

        for user in res.data or []:
            user["username"] = user["email"].split("@")[0]

        return res.data or []
    except Exception:
        return []


def send_message(sender_id, recipient_id, content, msg_type="text", file_url=None):
    try:
        payload = {
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "content": content,
            "msg_type": msg_type,
            "file_url": file_url
        }
        res = supabase.table("messages").insert(payload).execute()
        return res.data
    except Exception:
        return None


def get_chat_history(user_id, partner_id):
    try:
        res = (
            supabase
            .table("messages")
            .select("*")
            .or_(
                f"and(sender_id.eq.{user_id},recipient_id.eq.{partner_id}),"
                f"and(sender_id.eq.{partner_id},recipient_id.eq.{user_id})"
            )
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

# ================== STORAGE ==================

def upload_file(bucket_name, file_path, file_body, content_type):
    try:
        supabase.storage.from_(bucket_name).upload(
            file_path,
            file_body,
            {
                "content-type": content_type,
                "upsert": True
            }
        )

        return supabase.storage.from_(bucket_name).get_public_url(file_path)

    except Exception as e:
        logging.exception("Storage upload failed")
        return None

# ================== BOT ACCOUNTS ==================

def save_bot_accounts(user_id, accounts, update=False):
    try:
        if not update:
            rows = [{
                "user_id": user_id,
                "bot_type": a.get("bot_type"),
                "email": a.get("email"),
                "password": a.get("password"),
                "promo_code": a.get("promo_code"),
                "status": a.get("status", "not_bound"),
                "metadata": a.get("metadata", {})
            } for a in accounts]

            res = supabase.table("bot_accounts").insert(rows).execute()
            return len(res.data or [])

        else:
            count = 0
            for acc in accounts:
                rid = acc.pop("id", None)
                if not rid:
                    continue

                res = (
                    supabase
                    .table("bot_accounts")
                    .update(acc)
                    .eq("id", rid)
                    .eq("user_id", user_id)
                    .execute()
                )

                if res.data:
                    count += 1

            return count

    except Exception as e:
        logging.exception("Save bot accounts error")
        return 0


def get_user_accounts(user_id, bot_type=None, limit=50, offset=0):
    try:
        q = supabase.table("bot_accounts").select("*").eq("user_id", user_id)
        if bot_type:
            q = q.eq("bot_type", bot_type)

        res = q.order("created_at", desc=True).limit(limit).offset(offset).execute()
        return res.data or []
    except Exception:
        return []
