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
    get_user_by_id,
    update_user_profile  # You need to implement this in your DB client
)

auth_bp = Blueprint("auth", __name__)

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "e9b1c2d3f4a56789b0cdef1234567890abcdef1234567890abcdef1234567890"
)

# ================== UTILITY FUNCTIONS ==================

def generate_referral_code():
    """Generate unique 8-character referral code"""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_token(user_id, email):
    """Create JWT token for your API"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    """Verify JWT token"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def get_auth_payload():
    """Helper to extract and verify token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    return verify_token(token)

# ================== ROUTES ==================

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Register new user using Supabase Auth, then insert profile"""
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        # Validate inputs
        if not email or not password:
            return jsonify(success=False, error="Email and password are required"), 400

        if len(password) < 6:
            return jsonify(success=False, error="Password must be at least 6 characters"), 400

        # 1. Create user in Supabase Auth
        auth_result = supabase_auth_sign_up(email, password)
        if "error" in auth_result:
            return jsonify(success=False, error=auth_result["error"]), 400

        user = auth_result.get("user")

        if not user or not getattr(user, "id", None):
            logging.error(f"Supabase signup returned invalid user: {auth_result}")
            return jsonify(success=False, error="Failed to create user"), 500

        user_id = user.id

        # 2. Insert user profile with initial empty bio and avatar_url
        referral_code = generate_referral_code()
        profile_result = insert_user_profile(user_id, email, referral_code, bio="", avatar_url="")

        if "error" in profile_result:
            logging.error(f"Profile insert failed: {profile_result['error']}")
            return jsonify(success=False, error=profile_result["error"]), 500

        # 3. Issue JWT
        token = create_token(user_id, email)

        return jsonify(
            success=True,
            message="Account created successfully",
            user={
                "id": user_id,
                "email": email,
                "referral_code": referral_code
            },
            token=token
        ), 201

    except Exception as e:
        logging.exception("Exception during signup")
        return jsonify(success=False, error="Internal server error"), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login user via Supabase Auth"""
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify(success=False, error="Email and password are required"), 400

        # 1. Sign in via Supabase
        auth_result = supabase_auth_sign_in(email, password)
        if "error" in auth_result:
            return jsonify(success=False, error="Invalid credentials"), 401

        user = auth_result.get("user")

        if not user or not getattr(user, "id", None):
            return jsonify(success=False, error="Invalid credentials"), 401

        user_id = user.id

        # 2. Get profile
        profile = get_user_by_id(user_id)
        if not profile:
            return jsonify(success=False, error="User profile not found"), 404

        # 3. Issue JWT
        token = create_token(user_id, email)

        return jsonify(
            success=True,
            message="Login successful",
            user={
                "id": user_id,
                "email": email,
                "referral_code": profile.get("referral_code", "")
            },
            token=token
        )

    except Exception as e:
        logging.exception("Exception during login")
        return jsonify(success=False, error="Internal server error"), 500


@auth_bp.route("/profile", methods=["GET"])
def get_profile():
    """Get authenticated user's profile"""
    try:
        payload = get_auth_payload()
        if not payload:
            return jsonify(success=False, error="Invalid or expired token"), 401

        user = get_user_by_id(payload["user_id"])
        if not user:
            return jsonify(success=False, error="User not found"), 404

        return jsonify(
            success=True,
            user={
                "id": user["id"],
                "email": user["email"],
                "referral_code": user.get("referral_code", ""),
                "bio": user.get("bio", ""),
                "avatar_url": user.get("avatar_url", "")
            }
        )

    except Exception as e:
        logging.exception("Exception during get_profile")
        return jsonify(success=False, error="Internal server error"), 500


@auth_bp.route("/profile", methods=["PUT"])
def update_profile():
    """Allow authenticated user to update bio and avatar_url"""
    try:
        payload = get_auth_payload()
        if not payload:
            return jsonify(success=False, error="Invalid or expired token"), 401

        data = request.get_json() or {}
        bio = data.get("bio")
        avatar_url = data.get("avatar_url")

        # Validate inputs (optional, e.g. max length)
        if bio is not None and not isinstance(bio, str):
            return jsonify(success=False, error="Bio must be a string"), 400
        if avatar_url is not None and not isinstance(avatar_url, str):
            return jsonify(success=False, error="Avatar URL must be a string"), 400

        # Update profile in DB
        update_result = update_user_profile(payload["user_id"], bio=bio, avatar_url=avatar_url)
        if "error" in update_result:
            logging.error(f"Profile update failed: {update_result['error']}")
            return jsonify(success=False, error=update_result["error"]), 500

        return jsonify(success=True, message="Profile updated successfully")

    except Exception as e:
        logging.exception("Exception during update_profile")
        return jsonify(success=False, error="Internal server error"), 500


@auth_bp.route("/verify", methods=["POST"])
def verify():
    """Verify JWT token"""
    try:
        data = request.get_json() or {}
        token = data.get("token", "")

        payload = verify_token(token)
        if not payload:
            return jsonify(success=False, error="Invalid or expired token"), 401

        return jsonify(
            success=True,
            valid=True,
            user_id=payload["user_id"],
            email=payload["email"]
        )

    except Exception as e:
        logging.exception("Exception during verify")
        return jsonify(success=False, error="Internal server error"), 500

@auth_bp.route("/profile/avatar", methods=["POST"])
def upload_avatar():
    """
    Upload a new avatar image for the authenticated user.
    Expects multipart/form-data with 'avatar' file.
    Returns JSON with new avatar_url on success.
    """
    try:
        # Verify JWT token from Authorization header
        payload = get_auth_payload()
        if not payload:
            return jsonify(success=False, error="Invalid or expired token"), 401

        user_id = payload["user_id"]

        # Check if file is present in request
        if "avatar" not in request.files:
            return jsonify(success=False, error="No avatar file provided"), 400

        avatar_file = request.files["avatar"]

        # Optional: validate file type and size here
        allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
        filename = avatar_file.filename.lower()
        if not ('.' in filename and filename.rsplit('.', 1)[1] in allowed_extensions):
            return jsonify(success=False, error="Unsupported file type"), 400

        # Build file path for storage: e.g. avatars/<user_id>.<ext>
        file_ext = filename.rsplit('.', 1)[1]
        file_path = f"avatars/{user_id}.{file_ext}"

        # Read file bytes
        file_bytes = avatar_file.read()

        # Upload file to Supabase Storage (bucket name 'avatars' assumed)
        public_url = upload_file("avatars", file_path, file_bytes, avatar_file.content_type)

        if not public_url:
            return jsonify(success=False, error="Failed to upload avatar"), 500

        # Update user's avatar_url in database
        update_result = update_user_profile(user_id, avatar_url=public_url)
        if "error" in update_result:
            current_app.logger.error(f"Failed to update avatar_url: {update_result['error']}")
            return jsonify(success=False, error="Failed to update profile avatar"), 500

        return jsonify(success=True, avatar_url=public_url)

    except Exception as e:
        current_app.logger.exception("Exception during avatar upload")
        return jsonify(success=False, error="Internal server error"), 500


@auth_bp.route("/userprofile/<user_id>", methods=["GET"])
def get_userprofile(user_id):
    """
    Public endpoint to get minimal user info for chat or other services.
    Requires valid token but returns only public info (email, avatar_url, bio, username).
    """
    try:
        payload = get_auth_payload()
        if not payload:
            return jsonify(success=False, error="Invalid or expired token"), 401

        user = get_user_by_id(user_id)
        if not user:
            return jsonify(success=False, error="User not found"), 404

        return jsonify({
            "success": True,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "avatar_url": user.get("avatar_url", ""),
                "bio": user.get("bio", ""),
                "username": user["email"].split("@")[0]
            }
        })

    except Exception as e:
        logging.exception("Exception during get_userprofile")
        return jsonify(success=False, error="Internal server error"), 500
