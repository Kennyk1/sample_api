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
        if not supabase: raise RuntimeError("Supabase client is None")
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
            "referral_code": referral_code,
            "avatar_url": None,
            "bio": "Hey there! I'm using FXC Bot."
        }).execute()
        return {"data": res.data}
    except Exception as e:
        logging.error(f"Insert profile error: {e}")
        return {"error": str(e)}

def get_user_by_id(user_id):
    try:
        res = supabase.table("users").select("*").eq("id", user_id).single().execute()
        return res.data
    except: return None

# ================== CHAT & USER SEARCH ==================

def search_users_by_handle(query):
    """
    Search users by EXACT handle (email prefix).
    If user types @kennyfavour11, it finds kennyfavour11@gmail.com
    """
    try:
        clean_handle = query.replace("@", "").strip()
        # Using ilike with @ prefix ensures we don't get partial matches like 'kenny' finding 'kenny2'
        res = supabase.table("users").select("id, email, avatar_url, bio")\
            .ilike("email", f"{clean_handle}@%").execute()
        
        for user in res.data:
            user['username'] = user['email'].split('@')[0]
        return res.data
    except Exception as e:
        logging.error(f"User search error: {e}")
        return []

def get_saved_contacts(owner_id, query):
    """Search within the user's private saved contacts list"""
    try:
        res = supabase.table("contacts")\
            .select("saved_name, contact_user_id, users(email, avatar_url, bio)")\
            .eq("owner_id", owner_id)\
            .ilike("saved_name", f"%{query}%").execute()
        return res.data
    except Exception as e:
        logging.error(f"Contact search error: {e}")
        return []

def add_contact(owner_id, contact_user_id, saved_name):
    """Save a user to your personal contacts list with a nickname"""
    try:
        res = supabase.table("contacts").insert({
            "owner_id": owner_id,
            "contact_user_id": contact_user_id,
            "saved_name": saved_name
        }).execute()
        return res.data
    except Exception as e:
        logging.error(f"Add contact error: {e}")
        return None

def send_message(sender_id, recipient_id, content, msg_type="text", file_url=None):
    """Sends a message (text, photo, or video)"""
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
    except Exception as e:
        logging.error(f"Send message error: {e}")
        return None

def get_chat_history(user_id, partner_id):
    """Fetches full conversation history between two users"""
    try:
        res = supabase.table("messages").select("*")\
            .or_(f"and(sender_id.eq.{user_id},recipient_id.eq.{partner_id}),and(sender_id.eq.{partner_id},recipient_id.eq.{user_id})")\
            .order("created_at", desc=False).execute()
        return res.data
    except Exception as e:
        logging.error(f"Fetch chat error: {e}")
        return []

# ================== STORAGE (PHOTOS/VIDEOS/AVATARS) ==================

def upload_file(bucket_name, file_path, file_body, content_type):
    """Uploads media to storage and returns the public URL"""
    try:
        supabase.storage.from_(bucket_name).upload(file_path, file_body, {
            "content-type": content_type,
            "upsert": "true" # Overwrite if same path (good for updating profile pics)
        })
        url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        return url
    except Exception as e:
        logging.error(f"Upload error: {e}")
        return None

# ================== BOT ACCOUNTS ==================
def save_bot_accounts(user_id, accounts, update=False):
    try:
        if not update:
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
            updated_count = 0
            for acc in accounts:
                if "id" not in acc: continue
                row_id = acc.pop("id")
                res = supabase.table("bot_accounts").update(acc).eq("id", row_id).eq("user_id", user_id).execute()
                if res.data: updated_count += 1
            return updated_count
    except Exception as e:
        logging.error(f"Save/Update bot accounts error: {e}")
        return 0

def get_user_accounts(user_id, bot_type=None):
    try:
        q = supabase.table("bot_accounts").select("*").eq("user_id", user_id)
        if bot_type: q = q.eq("bot_type", bot_type)
        res = q.order("created_at", desc=True).execute()
        return res.data or []
    except: return []
