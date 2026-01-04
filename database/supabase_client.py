from supabase import create_client, Client
import logging
import os

# ================== SUPABASE CONFIG ==================
SUPABASE_URL = "https://vvkvowtrzmekbdresegf.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2a3Zvd3Ryem1la2JkcmVzZWdmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3MDQyMzIsImV4cCI6MjA4MjI4MDIzMn0.ge6YMn01wM_oEm1wT4tx1mUBxwXqUHiKZIQdCIC1-OM"
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Add this to Render env vars

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

# ================== USER PROFILE (FIXED) ==================
def insert_user_profile(user_id, email, referral_code, bio="Hey there! I'm using FXC Bot.", avatar_url=""):
    try:
        res = supabase.table("users").insert({
            "id": user_id, 
            "email": email, 
            "referral_code": referral_code,
            "bio": bio,
            "avatar_url": avatar_url
        }).execute()
        if res.error:
            return {"error": str(res.error)}
        return {"data": res.data}
    except Exception as e:
        logging.error(f"Insert profile error: {e}")
        return {"error": str(e)}

def get_user_by_email(email):
    try:
        res = supabase.table("users").select("*").eq("email", email).single().execute()
        if res.error:
            return None
        return res.data
    except: 
        return None

def get_user_by_id(user_id):
    try:
        res = supabase.table("users").select("*").eq("id", user_id).single().execute()
        if res.error:
            return None
        return res.data
    except: 
        return None

def update_user_profile(user_id, bio=None, avatar_url=None):
    """
    Update user's bio and/or avatar_url.
    FIXED: Proper Supabase APIResponse handling
    Returns: {"success": True} or {"error": "message"}
    """
    try:
        update_data = {}
        if bio is not None:
            update_data["bio"] = bio
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url

        if not update_data:
            return {"success": True}  # No changes needed

        res = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        # FIXED: Check .error attribute, not dict key
        if hasattr(res, 'error') and res.error:
            logging.error(f"Profile update error: {res.error}")
            return {"error": str(res.error)}
            
        if hasattr(res, 'data') and res.data:
            return {"success": True, "data": res.data}
        else:
            return {"success": True}  # Empty data is OK for updates
            
    except Exception as e:
        logging.error(f"Update user profile error: {e}")
        return {"error": f"Database error: {str(e)}"}

# ================== STORAGE (FIXED) ==================
def upload_file(bucket_name, file_path, file_bytes, content_type):
    """
    FIXED: Proper error handling and return public URL
    """
    try:
        # Upload file
        upload_res = supabase.storage.from_(bucket_name).upload(file_path, file_bytes, {
            "content-type": content_type,
            "upsert": True
        })
        
        if hasattr(upload_res, 'error') and upload_res.error:
            logging.error(f"Storage upload error: {upload_res.error}")
            return None
        
        # Get public URL
        url_res = supabase.storage.from_(bucket_name).get_public_url(file_path)
        return url_res
        
    except Exception as e:
        logging.error(f"Upload file error: {e}")
        return None

# ================== DASHBOARD & BOTS ==================
def get_all_bots():
    try:
        res = supabase.table("bots").select("*").eq("is_active", True).execute()
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

# ================== CHAT & SEARCH ==================
def search_users_by_handle(query):
    try:
        clean_handle = query.replace("@", "").strip()
        res = supabase.table("users").select("id, email, avatar_url, bio")\
            .ilike("email", f"{clean_handle}@%").execute()
        for user in res.data:
            user['username'] = user['email'].split('@')[0]
        return res.data
    except: return []

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
    except: return None

def get_chat_history(user_id, partner_id):
    try:
        res = supabase.table("messages").select("*")\
            .or_(f"and(sender_id.eq.{user_id},recipient_id.eq.{partner_id}),and(sender_id.eq.{partner_id},recipient_id.eq.{user_id})")\
            .order("created_at", desc=False).execute()
        return res.data
    except: return []

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
                if "id" not in acc: continue
                rid = acc.pop("id")
                res = supabase.table("bot_accounts").update(acc).eq("id", rid).eq("user_id", user_id).execute()
                if res.data: count += 1
            return count
    except Exception as e:
        logging.error(f"Save bot accounts error: {e}")
        return 0

def get_user_accounts(user_id, bot_type=None, limit=50, offset=0):
    try:
        q = supabase.table("bot_accounts").select("*").eq("user_id", user_id)
        if bot_type: q = q.eq("bot_type", bot_type)
        res = q.order("created_at", desc=True).limit(limit).offset(offset).execute()
        return res.data or []
    except: return []
