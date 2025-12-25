from flask import Blueprint, request, jsonify
import requests
import json
import hashlib
import time
import random
import string
import logging
from datetime import datetime

defi_bp = Blueprint('defi', __name__)

# ============= CONFIGURATION =============
API_URL = "https://api.defiproducts.vip/api/user/register?lang=en"
REGISTRATION_LINK = "https://defiproducts.vip/?code="

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

# ============= UTILITY FUNCTIONS =============

def generate_email():
    names = ["crypto", "defi", "trader", "invest", "finance", "digital", "block", "chain", "smart", "token"]
    name = random.choice(names)
    digits = ''.join(random.choices(string.digits, k=6))
    return f"{name}{digits}@gmail.com"

def generate_password():
    chars = string.ascii_letters + string.digits
    password = ''.join(random.choices(chars, k=10))
    hashed = hashlib.md5(password.encode()).hexdigest()
    return password, hashed

def generate_st_ttgn():
    return hashlib.md5(str(time.time()).encode()).hexdigest()

def generate_st_ctime():
    return str(int(time.time() * 1000))

def register_defi_account(email, password_plain, password_hash, referral_code):
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
        response = requests.post(API_URL, data=json.dumps(payload), headers=headers, timeout=20)
        result = response.json()
        success = result.get('status') == 200 and result.get('msg') == 'register success'
        return success, result
    except Exception as e:
        logging.error(f"DeFi Registration error: {e}")
        return False, {"error": str(e)}

# ============= ROUTES =============

@defi_bp.route("/info")
def info():
    return jsonify({
        "bot_name": "DeFi Products",
        "bot_type": "defi",
        "description": "Automated account creation for DeFi Products platform",
        "website": "https://defiproducts.vip",
        "requires_promo": True,
        "promo_format": "6 digits"
    })

@defi_bp.route("/create", methods=["POST"])
def create_accounts():
    """Create DeFi accounts - requires authentication"""
    try:
        data = request.json
        promo_code = data.get("promo_code")
        count = data.get("count", 1)
        user_id = data.get("user_id")  # From auth token
        
        # Validate promo code
        if not promo_code or not promo_code.isdigit() or len(promo_code) != 6:
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
        
        created_accounts = []
        failed_accounts = []
        
        # Create accounts
        for i in range(count):
            email = generate_email()
            password_plain, password_hash = generate_password()
            
            success, response = register_defi_account(email, password_plain, password_hash, promo_code)
            
            account_data = {
                "email": email,
                "password": password_plain,
                "promo_code": promo_code,
                "created_at": datetime.now().isoformat(),
                "status": "success" if success else "failed",
                "registration_link": f"{REGISTRATION_LINK}{promo_code}",
                "bot_type": "defi"
            }
            
            if success:
                account_data["token"] = response.get('data', {}).get('token', 'N/A')
                created_accounts.append(account_data)
            else:
                account_data["error"] = response.get('msg', response.get('error', 'Unknown error'))
                failed_accounts.append(account_data)
            
            # Delay between requests
            if i < count - 1:
                time.sleep(1)
        
        # TODO: Save to Supabase database
        # save_accounts_to_db(user_id, created_accounts)
        
        return jsonify({
            "success": True,
            "bot_type": "defi",
            "created": len(created_accounts),
            "failed": len(failed_accounts),
            "accounts": created_accounts,
            "failed_accounts": failed_accounts,
            "message": f"Successfully created {len(created_accounts)} out of {count} accounts"
        })
        
    except Exception as e:
        logging.error(f"Error in DeFi create_accounts: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@defi_bp.route("/accounts", methods=["GET"])
def get_accounts():
    """Get user's DeFi accounts - requires authentication"""
    try:
        # TODO: Get user_id from auth token
        # user_id = get_user_from_token(request.headers.get('Authorization'))
        
        # TODO: Fetch from Supabase
        # accounts = fetch_user_accounts_from_db(user_id, bot_type='defi')
        
        return jsonify({
            "success": True,
            "bot_type": "defi",
            "accounts": []  # Will be populated from database
        })
        
    except Exception as e:
        logging.error(f"Error in DeFi get_accounts: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
