from flask import Blueprint, request, jsonify
import hashlib
import uuid
import jwt
import random
import string
from datetime import datetime, timedelta
import os

auth_bp = Blueprint('auth', __name__)

# TODO: Replace with actual Supabase connection
# from database.supabase_client import supabase

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-')

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
        
        # TODO: Check if user exists in Supabase
        # existing_user = supabase.table('users').select('*').eq('email', email).execute()
        # if existing_user.data:
        #     return jsonify({"success": False, "error": "Email already registered"}), 400
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        referral_code = generate_referral_code()
        
        # TODO: Insert into Supabase
        # user_data = {
        #     'id': user_id,
        #     'email': email,
        #     'password_hash': password_hash,
        #     'referral_code': referral_code,
        #     'created_at': datetime.now().isoformat()
        # }
        # supabase.table('users').insert(user_data).execute()
        
        # Create token
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
        
        # TODO: Check user in Supabase
        # user = supabase.table('users').select('*').eq('email', email).eq('password_hash', password_hash).execute()
        # if not user.data:
        #     return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        # Mock user data (replace with actual database query)
        user_data = {
            'id': str(uuid.uuid4()),
            'email': email,
            'referral_code': 'ABC12345'
        }
        
        # Create token
        token = create_token(user_data['id'], email)
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user_data['id'],
                "email": email,
                "referral_code": user_data['referral_code']
            },
            "token": token
        })
        
    except Exception as e:
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
        
        # TODO: Fetch user from Supabase
        # user = supabase.table('users').select('*').eq('id', payload['user_id']).execute()
        # if not user.data:
        #     return jsonify({"success": False, "error": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "user": {
                "id": payload['user_id'],
                "email": payload['email'],
                "referral_code": "ABC12345"  # From database
            }
        })
        
    except Exception as e:
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
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
