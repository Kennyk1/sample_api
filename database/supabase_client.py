from supabase import create_client, Client
import logging

# ================== SUPABASE CONFIG ==================

SUPABASE_URL = "https://vvkvowtrzmekbdresegf.supabase.co"

SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2a3Zvd3Ryem1la2JkcmVzZWdmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3MDQyMzIsImV4cCI6MjA4MjI4MDIzMn0.ge6YMn01wM_oEm1wT4tx1mUBxwXqUHiKZIQdCIC1-OM"

# ================== CLIENT ==================

supabase: Client = None


def init_supabase():
    global supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

        if not supabase:
            raise RuntimeError("Supabase client is None")

        logging.info("Supabase initialized successfully")

    except Exception as e:
        logging.critical(f"Supabase init failed: {e}", exc_info=True)
        raise RuntimeError("App cannot start without Supabase")


init_supabase()

# ================== AUTH ==================

def supabase_auth_sign_up(email: str, password: str):
    if not supabase:
        return {"error": "Supabase not initialized"}

    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if not res.user:
            return {"error": "Signup failed"}

        return {"user": res.user}

    except Exception as e:
        logging.error(f"Signup error: {e}", exc_info=True)
        return {"error": str(e)}


def supabase_auth_sign_in(email: str, password: str):
    if not supabase:
        return {"error": "Supabase not initialized"}

    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not res.user:
            return {"error": "Invalid credentials"}

        return {"user": res.user}

    except Exception as e:
        logging.error(f"Signin error: {e}", exc_info=True)
        return {"error": str(e)}

# ================== USER PROFILE ==================

def insert_user_profile(user_id, email, referral_code):
    try:
        res = supabase.table("users").insert({
            "id": user_id,
            "email": email,
            "referral_code": referral_code
        }).execute()

        return {"data": res.data}

    except Exception as e:
        logging.error(f"Insert profile error: {e}", exc_info=True)
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

# ================== BOT ACCOUNTS ==================

def save_bot_accounts(user_id, accounts):
    try:
        rows = [{
            "user_id": user_id,
            "bot_type": acc.get("bot_type"),
            "email": acc.get("email"),
            "password": acc.get("password"),
            "promo_code": acc.get("promo_code"),
            "status": acc.get("status"),
            "metadata": acc.get("metadata", {})
        } for acc in accounts]

        res = supabase.table("bot_accounts").insert(rows).execute()
        return len(res.data or [])

    except Exception as e:
        logging.error(f"Save bot accounts error: {e}", exc_info=True)
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

def get_user_stats(user_id):
    try:
        total = supabase.table("bot_accounts").select("*", count="exact").eq("user_id", user_id).execute()
        success = supabase.table("bot_accounts").select("*", count="exact").eq("user_id", user_id).eq("status", "success").execute()

        return {
            "total_accounts": total.count or 0,
            "success_accounts": success.count or 0
        }

    except Exception:
        return {"total_accounts": 0, "success_accounts": 0}

def get_all_bots():
    try:
        res = supabase.table("bots").select("*").eq("is_active", True).execute()
        return res.data or []
    except Exception:
        return []
