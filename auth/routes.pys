from flask import Blueprint, request, jsonify
import random
import string
from datetime import datetime, timedelta
import os
import logging
import jwt

from database.supabase_client import (
    supabase_auth_sign_up,
    insert_user_profile,
    supabase_auth_sign_in,
    get_user_by_id
)

auth_bp = Blueprint('auth', __name__)

SECRET_KEY = os.environ.get('SECRET_KEY', 'e9b1c2d3f4a56789b0cdef1234567890abcdef1234567890abcdef1234567890')

# ============= UTILITY FUNCTIONS =============

def generate_referral_code():
    """Generate unique 8-character referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_token(user_id, email):
    """Create JWT token for your API (optional if you want your own tokens)"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ============= ROUTES =============

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Register new user using Supabase Auth, then insert profile"""
    try:
        data = request.json
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        # Validate inputs
        if not email or not password:
            return jsonify({
                "success": False,
                "error": "Email and password are required"
            }), 400
        
        if len(password) < 6:
            return jsonify({
                "success": False,
                "error": "Password must be at least 6 characters"
            }), 400
        
        # 1. Create user in Supabase Auth
        auth_result = supabase_auth_sign_up(email, password)
        if "error" in auth_result:
            return jsonify({"success": False, "error": auth_result["error"]}), 400
        
        user = auth_result.get("user")
        if not user or "id" not in user:
            logging.error(f"Supabase Auth signup failed: {auth_result}")
            return jsonify({"success": False, "error": "Failed to create user in auth system"}), 500
        
        user_id = user["id"]
        
        # 2. Insert user profile info in your users table
        referral_code = generate_referral_code()
        profile_result = insert_user_profile(user_id, email, referral_code)
        if "error" in profile_result:
            logging.error(f"Failed to insert user profile: {profile_result['error']}")
            # Optional: consider deleting the Supabase Auth user here to avoid orphaned auth users
            return jsonify({"success": False, "error": profile_result["error"]}), 500
        
        # 3. Create your own JWT token if needed (or use Supabase access token)
        token = create_token(user_id, email)
        
        return jsonify({
            "success": True,
            "message": "Account created successfully",
            "user": {
                "id": user_id,
                "email": email,
                "referral_code": referral_code
            },
            "token": token
        }), 201
        
    except Exception as e:
        logging.exception("Exception during signup")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    """Login user via Supabase Auth"""
    try:
        data = request.json
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({
                "success": False,
                "error": "Email and password are required"
            }), 400
        
        # 1. Sign in via Supabase Auth
        auth_result = supabase_auth_sign_in(email, password)
        if "error" in auth_result:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        user = auth_result.get("user")
        if not user or "id" not in user:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        user_id = user["id"]
        
        # 2. Fetch user profile from your users table
        profile = get_user_by_id(user_id)
        if not profile:
            return jsonify({"success": False, "error": "User profile not found"}), 404
        
        # 3. Create your own JWT token if needed (or use Supabase session token)
        token = create_token(user_id, email)
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user_id,
                "email": email,
                "referral_code": profile.get("referral_code", "")
            },
            "token": token
        })
        
    except Exception as e:
        logging.exception("Exception during login")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@auth_bp.route("/profile", methods=["GET"])
def get_profile():
    """Get user profile - requires authentication"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "error": "No token provided"
            }), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        
        if not payload:
            return jsonify({
                "success": False,
                "error": "Invalid or expired token"
            }), 401
        
        user = get_user_by_id(payload['user_id'])
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "referral_code": user.get('referral_code', '')
            }
        })
        
    except Exception as e:
        logging.exception("Exception during get_profile")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@auth_bp.route("/verify", methods=["POST"])
def verify():
    """Verify JWT token"""
    try:
        data = request.json
        token = data.get("token", "")
        
        payload = verify_token(token)
        
        if not payload:
            return jsonify({
                "success": False,
                "error": "Invalid or expired token"
            }), 401
        
        return jsonify({
            "success": True,
            "valid": True,
            "user_id": payload['user_id'],
            "email": payload['email']
        })
        
    except Exception as e:
        logging.exception("Exception during verify")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
