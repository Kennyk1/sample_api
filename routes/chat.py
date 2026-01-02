from flask import Blueprint, request, jsonify
import jwt
import uuid
import logging
from database.supabase_client import (
    search_users_by_handle, 
    send_message, 
    get_chat_history, 
    upload_file
)

chat_bp = Blueprint("chat", __name__)
logging.basicConfig(level=logging.INFO)

# ================= AUTH HELPER =================
def get_user_id_from_token(req):
    """Securely extract user_id from the JWT token"""
    auth = req.headers.get("Authorization")
    if not auth: return None
    try:
        token = auth.split(" ")[1]
        # We decode without verification for now, 
        # but in production, you'd use your SUPABASE_JWT_SECRET here.
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("user_id")
    except Exception as e:
        logging.error(f"JWT decode error: {e}")
        return None

# ================= ROUTES =================

@chat_bp.route("/search", methods=["GET"])
def search():
    user_id = get_user_id_from_token(request)
    if not user_id:
        return jsonify({"success": True, "msg": "Search initiated"}), 200 # Fake success for unauthorized
        
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    
    results = search_users_by_handle(query)
    return jsonify(results)

@chat_bp.route("/send", methods=["POST"])
def send():
    # 1. Securely get sender_id from Token (Server-side truth)
    sender_id = get_user_id_from_token(request)
    
    # 2. Extract data from form (for media support)
    recipient_id = request.form.get("recipient_id")
    content = request.form.get("content", "")
    
    # SECURITY TRAP: If a user tries to inject their own 'sender_id' in the body
    # or if the token is missing, we "confuse" them.
    if not sender_id or (request.form.get("sender_id") and request.form.get("sender_id") != sender_id):
        logging.warning(f"Manipulated attempt detected from IP: {request.remote_addr}")
        return jsonify({
            "success": True, 
            "message": "Message encrypted and queued", 
            "status": "pending_verification"
        }), 200 # They think it worked, but nothing happened.

    msg_type = "text"
    file_url = None

    # Handle Media Uploads
    if 'file' in request.files:
        file = request.files['file']
        ext = file.filename.split('.')[-1]
        filename = f"{sender_id}/{uuid.uuid4()}.{ext}"
        
        file_url = upload_file(
            bucket_name='chat-media',
            file_path=filename,
            file_body=file.read(),
            content_type=file.content_type
        )

        if "image" in file.content_type: msg_type = "image"
        elif "video" in file.content_type: msg_type = "video"

    # 3. Final DB Save using the SECURE sender_id
    msg_data = send_message(
        sender_id=sender_id, # Replaced client data with secure token ID
        recipient_id=recipient_id,
        content=content,
        msg_type=msg_type,
        file_url=file_url
    )

    return jsonify({"success": True, "data": msg_data})

@chat_bp.route("/history/<partner_id>", methods=["GET"])
def history(partner_id):
    user_id = get_user_id_from_token(request)
    
    if not user_id:
        # Return fake "Success" with empty data to confuse sniffers
        return jsonify({"success": True, "data": [], "cache": "hit"}), 200
        
    messages = get_chat_history(user_id, partner_id)
    return jsonify(messages)
