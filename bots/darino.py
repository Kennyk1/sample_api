from flask import Blueprint, request, jsonify
import requests
import json
import logging
from datetime import datetime
import random
import string
import time

darino_bp = Blueprint('darino', __name__)

# ============= CONFIGURATION =============
BASE_URL = "https://api.darino.vip"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "origin": "https://darino.vip"
}

# ============= UTILITY FUNCTIONS =============

def generate_email():
    names = ["darino", "crypto", "trader", "invest", "digital"]
    name = random.choice(names)
    digits = ''.join(random.choices(string.digits, k=6))
    return f"{name}{digits}@gmail.com"

def generate_password():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=10))

def register_darino_account(email, password, promo_code):
    """Register account on Darino platform"""
    payload = {
        "email": email,
        "password": password,
        "confirmPassword": password,
        "promo_code": promo_code or "",
        "source": None  # Add this field
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/h5/taskBase/biz3/register",
            headers=HEADERS,
            data=json.dumps(payload),
            timeout=15
        )
        
        # Clean JSON response
        text = response.text
        if "{" in text:
            text = text[text.find("{"):]
        if "}" in text:
            text = text[:text.rfind("}")+1]
        
        result = json.loads(text)
        success = result.get("code") == 0
        
        return success, result
        
    except Exception as e:
        logging.error(f"Darino registration error: {e}")
        return False, {"error": str(e)}

# ============= ROUTES =============

@darino_bp.route("/info")
def info():
    return jsonify({
        "bot_name": "Darino",
        "bot_type": "darino",
        "description": "Automated account creation for Darino platform",
        "website": "https://darino.vip",
        "requires_promo": False,
        "promo_format": "Optional"
    })

@darino_bp.route("/create", methods=["POST"])
def create_accounts():
    """Create Darino accounts - requires authentication"""
    try:
        data = request.json
        promo_code = data.get("promo_code", "")
        count = data.get("count", 1)
        user_id = data.get("user_id")  # From auth token
        
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
            password = generate_password()
            
            success, response = register_darino_account(email, password, promo_code)
            
            account_data = {
                "email": email,
                "password": password,
                "promo_code": promo_code,
                "created_at": datetime.now().isoformat(),
                "status": "success" if success else "failed",
                "bot_type": "darino"
            }
            
            if success:
                # Try to login to get token
                login_result = darino_login(email, password)
                account_data["token"] = login_result.get('data', {}).get('token', 'N/A')
                created_accounts.append(account_data)
            else:
                account_data["error"] = response.get('msg', response.get('error', 'Unknown error'))
                failed_accounts.append(account_data)
            
            # Delay between requests
            if i < count - 1:
                time.sleep(1.5)
        
        # TODO: Save to Supabase database
        # save_accounts_to_db(user_id, created_accounts)
        
        return jsonify({
            "success": True,
            "bot_type": "darino",
            "created": len(created_accounts),
            "failed": len(failed_accounts),
            "accounts": created_accounts,
            "failed_accounts": failed_accounts,
            "message": f"Successfully created {len(created_accounts)} out of {count} accounts"
        })
        
    except Exception as e:
        logging.error(f"Error in Darino create_accounts: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@darino_bp.route("/accounts", methods=["GET"])
def get_accounts():
    """Get user's Darino accounts - requires authentication"""
    try:
        # TODO: Get user_id from auth token
        # user_id = get_user_from_token(request.headers.get('Authorization'))
        
        # TODO: Fetch from Supabase
        # accounts = fetch_user_accounts_from_db(user_id, bot_type='darino')
        
        return jsonify({
            "success": True,
            "bot_type": "darino",
            "accounts": []  # Will be populated from database
        })
        
    except Exception as e:
        logging.error(f"Error in Darino get_accounts: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
