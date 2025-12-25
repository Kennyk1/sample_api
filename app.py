from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import hashlib
import time
import random
import string
import logging
from datetime import datetime
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app)

# ============= CONFIGURATION =============
API_URL = "https://api.defiproducts.vip/api/user/register?lang=en"
REGISTRATION_LINK = "https://defiproducts.vip/?code="

# ============= API HEADERS =============
HEADERS_BASE = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
    'Accept': "application/json, text/plain, */*",
    'Content-Type': "application/json",
    'sec-ch-ua-platform': '"Android"',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': "?1",
    'dnt': "1",
    'st-lang': "en",
    'origin': "https://defiproducts.vip",
    'sec-fetch-site': "same-site",
    'sec-fetch-mode': "cors",
    'sec-fetch-dest': "empty",
    'referer': "https://defiproducts.vip/",
    'accept-language': "en-US,en;q=0.9",
    'priority': "u=1, i"
}

# ============= DATA STORAGE =============
user_accounts = {}  # {user_id: [accounts]}

# ============= UTILITY FUNCTIONS =============

def generate_email():
    """Generate random email address"""
    names = ["crypto", "defi", "trader", "invest", "finance", "digital", "block", "chain", "smart", "token"]
    name = random.choice(names)
    digits = ''.join(random.choices(string.digits, k=6))
    return f"{name}{digits}@gmail.com"

def generate_password():
    """Generate a secure password and return both plain and hashed"""
    chars = string.ascii_letters + string.digits
    password = ''.join(random.choices(chars, k=10))
    hashed = hashlib.md5(password.encode()).hexdigest()
    return password, hashed

def generate_st_ttgn():
    """Generate st-ttgn header value"""
    return hashlib.md5(str(time.time()).encode()).hexdigest()

def generate_st_ctime():
    """Generate st-ctime header value (timestamp in milliseconds)"""
    return str(int(time.time() * 1000))

def generate_user_id():
    """Generate unique user ID"""
    return 'USER-' + str(int(time.time())) + '-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def save_data():
    """Save user data to file"""
    try:
        with open('user_accounts.json', 'w') as f:
            json.dump(user_accounts, f, indent=2)
        logging.info("Data saved successfully")
    except Exception as e:
        logging.error(f"Error saving data: {e}")

def load_data():
    """Load user data from file"""
    global user_accounts
    try:
        if os.path.exists('user_accounts.json'):
            with open('user_accounts.json', 'r') as f:
                user_accounts = json.load(f)
            logging.info(f"Data loaded successfully - {len(user_accounts)} users")
    except Exception as e:
        logging.error(f"Error loading data: {e}")

# ============= API FUNCTIONS =============

def register_defi_account(email: str, password_plain: str, password_hash: str, referral_code: str):
    """Register a new DeFi Products account"""
    
    payload = {
        "account": email,
        "pwd": password_hash,
        "user_type": 1,
        "code": referral_code,
        "safety_pwd": password_hash,
        "ws": "",
        "te": "",
        "email_code": "",
        "user_email": email
    }
    
    headers = HEADERS_BASE.copy()
    headers['st-ctime'] = generate_st_ctime()
    headers['st-ttgn'] = generate_st_ttgn()
    
    try:
        logging.info(f"Registering account: {email} with referral: {referral_code}")
        
        response = requests.post(
            API_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=20
        )
        
        logging.info(f"Response status: {response.status_code}")
        result = response.json()
        
        success = result.get('status') == 200 and result.get('msg') == 'register success'
        
        return success, result
        
    except Exception as e:
        logging.error(f"Registration error: {e}")
        return False, {"error": str(e)}

# ============= FLASK ROUTES =============

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "FXC Bot Looters API",
        "platform": "DeFi Products",
        "endpoints": {
            "/": "API status",
            "/create-accounts": "Create multiple accounts (POST)",
            "/get-accounts": "Get user accounts (POST)",
            "/stats": "Get statistics"
        }
    })

@app.route("/create-accounts", methods=["POST"])
def create_accounts():
    """Create multiple accounts with promo code"""
    try:
        data = request.json
        promo_code = data.get("promo_code")
        count = data.get("count", 1)
        user_id = data.get("user_id")  # Optional: if user wants to use existing ID
        
        # Validate promo code
        if not promo_code:
            return jsonify({
                "success": False,
                "error": "Promo code is required"
            }), 400
        
        # Validate promo code format (6 digits)
        if not promo_code.isdigit() or len(promo_code) != 6:
            return jsonify({
                "success": False,
                "error": "Promo code must be exactly 6 digits"
            }), 400
        
        # Validate count
        if not isinstance(count, int) or count < 1 or count > 50:
            return jsonify({
                "success": False,
                "error": "Count must be between 1 and 50"
            }), 400
        
        # Generate new user ID if not provided
        if not user_id:
            user_id = generate_user_id()
        
        # Initialize user account list
        if user_id not in user_accounts:
            user_accounts[user_id] = []
        
        created_accounts = []
        failed_accounts = []
        
        # Create accounts
        for i in range(count):
            email = generate_email()
            password_plain, password_hash = generate_password()
            
            # Register account
            success, response = register_defi_account(email, password_plain, password_hash, promo_code)
            
            account_data = {
                "email": email,
                "password": password_plain,
                "promo_code": promo_code,
                "created_at": datetime.now().isoformat(),
                "status": "success" if success else "failed",
                "registration_link": f"{REGISTRATION_LINK}{promo_code}"
            }
            
            if success:
                account_data["token"] = response.get('data', {}).get('token', 'N/A')
                created_accounts.append(account_data)
                user_accounts[user_id].append(account_data)
            else:
                account_data["error"] = response.get('msg', response.get('error', 'Unknown error'))
                failed_accounts.append(account_data)
            
            # Small delay between requests
            if i < count - 1:
                time.sleep(1)
        
        # Save data
        save_data()
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "created": len(created_accounts),
            "failed": len(failed_accounts),
            "accounts": created_accounts,
            "failed_accounts": failed_accounts,
            "message": f"Successfully created {len(created_accounts)} out of {count} accounts"
        })
        
    except Exception as e:
        logging.error(f"Error in create_accounts: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/get-accounts", methods=["POST"])
def get_accounts():
    """Get all accounts for a user ID"""
    try:
        data = request.json
        user_id = data.get("user_id")
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "User ID is required"
            }), 400
        
        if user_id not in user_accounts:
            return jsonify({
                "success": False,
                "error": "User ID not found"
            }), 404
        
        accounts = user_accounts[user_id]
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "total_accounts": len(accounts),
            "accounts": accounts
        })
        
    except Exception as e:
        logging.error(f"Error in get_accounts: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/stats", methods=["GET"])
def get_stats():
    """Get overall statistics"""
    try:
        total_users = len(user_accounts)
        total_accounts = sum(len(accounts) for accounts in user_accounts.values())
        
        return jsonify({
            "success": True,
            "total_users": total_users,
            "total_accounts": total_accounts,
            "platform": "DeFi Products"
        })
        
    except Exception as e:
        logging.error(f"Error in get_stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============= MAIN =============

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 FXC BOT LOOTERS - FLASK API")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Platform: DeFi Products")
    print("=" * 60)
    
    # Load saved data
    load_data()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
