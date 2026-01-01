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
    if not supabase: return {"error": "Supabase not initialized"}
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if not res.user: return {"error": "Signup failed"}
        return {"user": res.user}
    except Exception as e:
        logging.error(f"Signup error: {e}")
        return {"error": str(e)}

def supabase_auth_sign_in(email: str, password: str):
    if not supabase: return {"error": "Supabase not initialized"}
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if not res.user: return {"error": "Invalid credentials"}
        return {"user": res.user}
    except Exception as e:
        logging.error(f"Signin error: {e}")
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
        logging.error(f"Insert profile error: {e}")
        return {"error": str(e)}

def get_user_by_email(email):
    try:
        res = supabase.table("users").select("*").eq("email", email).single().execute()
        return res.data
    except: return None

def get_user_by_id(user_id):
    try:
        res = supabase.table("users").select("*").eq("id", user_id).single().execute()
        return res.data
    except: return None

# ================== BOT ACCOUNTS ==================

def save_bot_accounts(user_id, accounts, update=False):
    """
    Handles both inserting and updating accounts.
    If update=True, looks for 'id' in the account dict to target the row.
    """
    try:
        if not update:
            # Standard Insert Logic
            rows = [{
                "user_id": user_id,
                "bot_type": acc.get("bot_type"),
                "email": acc.get("email"),
                "password": acc.get("password"),
                "promo_code": acc.get("promo_code"),
                "status": acc.get("status", "not_bound"),
                "metadata": acc.get("metadata", {})
            } for acc in accounts]
            res = supabase.table("bot_accounts").insert(rows).execute()
            return len(res.data or [])
        else:
            # Update Logic: Targets specific row by 'id'
            updated_count = 0
            for acc in accounts:
                if "id" not in acc: continue
                
                row_id = acc.pop("id") # Extract ID to use in .eq()
                # Update the remaining fields (status, uuid, etc)
                res = supabase.table("bot_accounts") \
                    .update(acc) \
                    .eq("id", row_id) \
                    .eq("user_id", user_id) \
                    .execute()
                if res.data: updated_count += 1
            return updated_count

    except Exception as e:
        logging.error(f"Save/Update bot accounts error: {e}", exc_info=True)
        return 0

def get_user_accounts(user_id, bot_type=None, limit=50, offset=0):
    try:
        q = supabase.table("bot_accounts").select("*").eq("user_id", user_id)
        if bot_type: q = q.eq("bot_type", bot_type)
        res = q.order("created_at", desc=True).limit(limit).offset(offset).execute()
        return res.data or []
    except: return []

def get_user_stats(user_id):
    try:
        total = supabase.table("bot_accounts").select("*", count="exact").eq("user_id", user_id).execute()
        success = supabase.table("bot_accounts").select("*", count="exact").eq("user_id", user_id).eq("status", "bound").execute()
        return {
            "total_accounts": total.count or 0,
            "success_accounts": success.count or 0
        }
    except: return {"total_accounts": 0, "success_accounts": 0}

def get_all_bots():
    try:
        res = supabase.table("bots").select("*").eq("is_active", True).execute()
        return res.data or []
    except: return []
