import os
from supabase import create_client, Client
import logging

# Get credentials from environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# Initialize Supabase client
supabase: Client = None

def init_supabase():
    """Initialize Supabase client"""
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

# Initialize on import
init_supabase()

# ============= DATABASE HELPER FUNCTIONS =============

def create_user(email, password_hash, referral_code):
    """Create new user in database"""
    try:
        data = {
            'email': email,
            'password_hash': password_hash,
            'referral_code': referral_code
        }
        result = supabase.table('users').insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return None

def get_user_by_email(email):
    """Get user by email"""
    try:
        result = supabase.table('users').select('*').eq('email', email).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logging.error(f"Error getting user: {e}")
        return None

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logging.error(f"Error getting user: {e}")
        return None

def save_bot_accounts(user_id, accounts):
    """Save bot accounts to database"""
    try:
        # Prepare accounts for insertion
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
        logging.error(f"Error saving bot accounts: {e}")
        return 0

def get_user_accounts(user_id, bot_type=None, limit=50, offset=0):
    """Get user's bot accounts"""
    try:
        query = supabase.table('bot_accounts').select('*').eq('user_id', user_id)
        
        if bot_type:
            query = query.eq('bot_type', bot_type)
        
        result = query.order('created_at', desc=True).limit(limit).offset(offset).execute()
        return result.data if result.data else []
    except Exception as e:
        logging.error(f"Error getting user accounts: {e}")
        return []

def get_user_stats(user_id):
    """Get user statistics"""
    try:
        # Total accounts
        total = supabase.table('bot_accounts').select('*', count='exact').eq('user_id', user_id).execute()
        
        # Success accounts
        success = supabase.table('bot_accounts').select('*', count='exact').eq('user_id', user_id).eq('status', 'success').execute()
        
        # Accounts by bot type
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
        logging.error(f"Error getting user stats: {e}")
        return {
            'total_accounts': 0,
            'success_accounts': 0,
            'accounts_by_bot': {}
        }

def get_all_bots():
    """Get all active bots"""
    try:
        result = supabase.table('bots').select('*').eq('is_active', True).execute()
        return result.data if result.data else []
    except Exception as e:
        logging.error(f"Error getting bots: {e}")
        return []
