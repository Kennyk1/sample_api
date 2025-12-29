from flask import Blueprint, request, jsonify
import logging

from database.supabase_client import get_all_bots, get_user_stats, get_user_accounts, get_user_by_id
from auth.routes import verify_token  # adjust import path if needed

dashboard_bp = Blueprint('dashboard', __name__)

def get_user_id_from_auth_header(auth_header):
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    if not payload:
        return None
    return payload.get('user_id')

@dashboard_bp.route("/bots", methods=["GET"])
def get_bots():
    try:
        bots = get_all_bots()
        return jsonify({
            "success": True,
            "bots": bots,
            "total": len(bots)
        })
    except Exception as e:
        logging.error(f"Error in get_bots: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@dashboard_bp.route("/stats", methods=["GET"])
def get_stats():
    try:
        user_id = get_user_id_from_auth_header(request.headers.get('Authorization'))
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        
        stats = get_user_stats(user_id)
        
        # You can add success_rate and total_bots_used calculations here if needed
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logging.error(f"Error in get_stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@dashboard_bp.route("/accounts", methods=["GET"])
def get_all_accounts():
    try:
        user_id = get_user_id_from_auth_header(request.headers.get('Authorization'))
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        
        bot_type = request.args.get('bot_type', None)
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        accounts = get_user_accounts(user_id, bot_type=bot_type, limit=limit, offset=offset)
        
        return jsonify({
            "success": True,
            "accounts": accounts,
            "total": len(accounts),
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        logging.error(f"Error in get_all_accounts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@dashboard_bp.route("/referral", methods=["GET"])
def get_referral_info():
    try:
        user_id = get_user_id_from_auth_header(request.headers.get('Authorization'))
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        referral_code = user.get('referral_code', '')
        referral_link = f"https://fxcbotlooters.com/signup?ref={referral_code}"
        
        # TODO: You can implement counting referrals if you have that data
        
        referral_info = {
            "referral_code": referral_code,
            "referral_link": referral_link,
            "total_referrals": 0,  # placeholder
            "active_referrals": 0  # placeholder
        }
        
        return jsonify({
            "success": True,
            "referral": referral_info
        })
    except Exception as e:
        logging.error(f"Error in get_referral_info: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@dashboard_bp.route("/search", methods=["GET"])
def search_bots():
    try:
        query = request.args.get('q', '').lower()
        category = request.args.get('category', None)
        
        bots = get_all_bots()
        
        if query:
            bots = [bot for bot in bots if query in bot.get('name', '').lower()]
        
        if category:
            bots = [bot for bot in bots if bot.get('category', '').lower() == category.lower()]
        
        return jsonify({
            "success": True,
            "results": bots,
            "total": len(bots),
            "query": query,
            "category": category
        })
    except Exception as e:
        logging.error(f"Error in search_bots: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
