from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# Initialize Flask
app = Flask(__name__)
CORS(app)

# ============= CONFIGURATION =============
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SUPABASE_URL'] = os.environ.get('SUPABASE_URL', '')
app.config['SUPABASE_KEY'] = os.environ.get('SUPABASE_KEY', '')

# ============= IMPORT BLUEPRINTS =============
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from routes.chat import chat_bp         # New: Chat System
from bots.darino import darino_bp
from bots.lavend import lavend_bp       # New: Lavend Bot
from bots.defi import defi_bp

# === FUTURE EXAMPLES (Add files for these as you grow) ===
# from bots.gold_rush import gold_bp    # Example 1: New Bot
# from routes.admin import admin_bp     # Example 2: Admin Panel
# from routes.market import market_bp   # Example 3: User Marketplace
# from routes.wallet import wallet_bp   # Example 4: Internal Wallet
# from routes.tasks import tasks_bp     # Example 5: Global Task Manager

# ============= REGISTER BLUEPRINTS =============
# CORE SYSTEMS
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(chat_bp, url_prefix='/chat')       # Endpoints: /chat/send, /chat/history

# BOT SYSTEMS
app.register_blueprint(defi_bp, url_prefix='/bot/defi')
app.register_blueprint(darino_bp, url_prefix='/bot/darino')
app.register_blueprint(lavend_bp, url_prefix='/bot/lavend') # Endpoints: /bot/lavend/bind

# ============= MAIN ROUTES =============

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "FXC Bot Looters Platform",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "endpoints": {
            "core": {
                "auth": "/auth/*",
                "dashboard": "/dashboard/*",
                "chat": "/chat/* (Social & Multimedia Messaging)"
            },
            "bots": {
                "darino": "/bot/darino/*",
                "lavend": "/bot/lavend/* (New Bot)",
                "defi": "/bot/defi/*"
            },
            "examples": {
                "future_bot": "/bot/gold_rush",
                "marketplace": "/market",
                "admin": "/admin"
            }
        }
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ============= MAIN =============

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 FXC BOT LOOTERS PLATFORM - MULTI-BOT CORE")
    print("=" * 60)
    print(f"📡 Chat System: ACTIVE")
    print(f"🤖 Lavend Bot: READY")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
