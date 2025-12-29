from flask import Blueprint, request, jsonify
import hashlib
import uuid
import jwt
import random
import string
from datetime import datetime, timedelta
import os
import logging

from database.supabase_client import create_user, get_user_by_email, get_user_by_id

auth_bp = Blueprint('auth', __name__)

SECRET_KEY = os.environ.get('SECRET_KEY', 'e9b1c2d3f4a56789b0cdef1234567890abcdef1234567890abcdef1234567890')

# ============= UTILITY FUNCTIONS =============

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_referral_code():
    """Generate unique 8-character referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_token(user_id, email):
    """Create JWT token"""
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
    """Register new user"""
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
        
        # Check if user exists in Supabase
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({"success": False, "error": "Email already registered"}), 400
        
        # Create user
        password_hash = hash_password(password)
        referral_code = generate_referral_code()
        
        user = create_user(email, password_hash, referral_code)
        
        # Handle create_user error response
        if not user:
            logging.error("create_user returned None without error details")
            return jsonify({"success": False, "error": "Failed to create user"}), 500
        
        if isinstance(user, dict) and "error" in user:
            logging.error(f"Supabase user creation error: {user['error']}")
            return jsonify({"success": False, "error": user["error"]}), 500
        
        # Create token
        token = create_token(user['id'], email)
        
        return jsonify({
            "success": True,
            "message": "Account created successfully",
            "user": {
                "id": user['id'],
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
    """Login user"""
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
        
        password_hash = hash_password(password)
        
        # Check user in Supabase
        user = get_user_by_email(email)
        if not user or user.get('password_hash') != password_hash:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        # Create token
        token = create_token(user['id'], email)
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "email": email,
                "referral_code": user.get('referral_code', '')
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
        # Get token from header
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
        
        # Fetch user from Supabase
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
