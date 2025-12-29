from supabase import create_client, Client
import logging
import os

# Supabase credentials - use environment variables in production!
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vvkvowtrzmekbdresegf.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2a3Zvd3Ryem1la2JkcmVzZWdmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3MDQyMzIsImV4cCI6MjA4MjI4MDIzMn0.ge6YMn01wM_oEm1wT4tx1mUBxwXqUHiKZIQdCIC1-OM")  # Use service role key for admin ops

supabase: Client = None

def init_supabase():
    global supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        logging.warning("Supabase credentials not found. Database features disabled.")
        return None
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Supabase client initialized successfully")
        return supabase
    except Exception as e:
        logging.error(f"Failed to initialize Supabase: {e}")
        return None

init_supabase()

# ============= AUTH FUNCTIONS =============

def supabase_auth_sign_up(email, password):
    """Sign up user using Supabase Auth"""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.get("error"):
            return {"error": response["error"]["message"]}
        return {"user": response.get("user")}
    except Exception as e:
        logging.error(f"Error in supabase_auth_sign_up: {e}", exc_info=True)
        return {"error": str(e)}

def insert_user_profile(user_id, email, referral_code):
    """Insert user profile data in users table"""
    try:
        result = supabase.table("users").insert({
            "id": user_id,
            "email": email,
            "referral_code": referral_code
        }).execute()
        if result.error:
            return {"error": result.error.message}
        return {"data": result.data}
    except Exception as e:
        logging.error(f"Error in insert_user_profile: {e}", exc_info=True)
        return {"error": str(e)}

def supabase_auth_sign_in(email, password):
    """Sign in user using Supabase Auth"""
    try:
        response = supabase.auth.sign_in({"email": email, "password": password})
        if response.get("error"):
            return {"error": response["error"]["message"]}
        return {"user": response.get("user")}
    except Exception as e:
        logging.error(f"Error in supabase_auth_sign_in: {e}", exc_info=True)
        return {"error": str(e)}

def get_user_by_email(email):
    """Get user profile by email from users table"""
    try:
        result = supabase.table("users").select("*").eq("email", email).single().execute()
        if result.error:
            logging.error(f"Error getting user by email: {result.error.message}")
            return None
        return result.data
    except Exception as e:
        logging.error(f"Exception in get_user_by_email: {e}", exc_info=True)
        return None

def get_user_by_id(user_id):
    """Get user profile by ID from users table"""
    try:
        result = supabase.table("users").select("*").eq("id", user_id).single().execute()
        if result.error:
            logging.error(f"Error getting user by id: {result.error.message}")
            return None
        return result.data
    except Exception as e:
        logging.error(f"Exception in get_user_by_id: {e}", exc_info=True)
        return None

# ============= OTHER EXISTING FUNCTIONS =============

def save_bot_accounts(user_id, accounts):
    try:
        db_accounts = []
        for acc in accounts:
            db_accounts.append({
                'user_id': user_id,
                'bot_type': acc.get('bot_type'),
                'email': acc.get('email'),
                'password': acc.get('password'),
                'promo_code': acc.get('promo_code'),
                'status': acc.get('status'),
                'metadata': {
                    'token': acc.get('token'),
                    'registration_link': acc.get('registration_link'),
                    'error': acc.get('error')
                }
            })
        result = supabase.table('bot_accounts').insert(db_accounts).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        logging.error(f"Error saving bot accounts: {e}", exc_info=True)
        return 0

def get_user_accounts(user_id, bot_type=None, limit=50, offset=0):
    try:
        query = supabase.table('bot_accounts').select('*').eq('user_id', user_id)
        if bot_type:
            query = query.eq('bot_type', bot_type)
        result = query.order('created_at', desc=True).limit(limit).offset(offset).execute()
        return result.data if result.data else []
    except Exception as e:
        logging.error(f"Error getting user accounts: {e}", exc_info=True)
        return []

def get_user_stats(user_id):
    try:
        total = supabase.table('bot_accounts').select('*', count='exact').eq('user_id', user_id).execute()
        success = supabase.table('bot_accounts').select('*', count='exact').eq('user_id', user_id).eq('status', 'success').execute()
        defi = supabase.table('bot_accounts').select('*', count='exact').eq('user_id', user_id).eq('bot_type', 'defi').execute()
        darino = supabase.table('bot_accounts').select('*', count='exact').eq('user_id', user_id).eq('bot_type', 'darino').execute()
        return {
            'total_accounts': total.count if total else 0,
            'success_accounts': success.count if success else 0,
            'accounts_by_bot': {
                'defi': defi.count if defi else 0,
                'darino': darino.count if darino else 0
            }
        }
    except Exception as e:
        logging.error(f"Error getting user stats: {e}", exc_info=True)
        return {
            'total_accounts': 0,
            'success_accounts': 0,
            'accounts_by_bot': {}
        }

def get_all_bots():
    try:
        result = supabase.table('bots').select('*').eq('is_active', True).execute()
        return result.data if result.data else []
    except Exception as e:
        logging.error(f"Error getting bots: {e}", exc_info=True)
        return []
