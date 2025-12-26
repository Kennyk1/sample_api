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
# These will be separate files you create
from bots.defi import defi_bp
from bots.darino import darino_bp
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp

# ============= REGISTER BLUEPRINTS =============
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(defi_bp, url_prefix='/bot/defi')
app.register_blueprint(darino_bp, url_prefix='/bot/darino')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

# ============= MAIN ROUTES =============

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "FXC Bot Looters Platform",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "signup": "/auth/signup (POST)",
                "login": "/auth/login (POST)",
                "profile": "/auth/profile (GET)"
            },
            "bots": {
                "defi": "/bot/defi/* (DeFi Products Bot)",
                "darino": "/bot/darino/* (Darino Bot)"
            },
            "dashboard": {
                "stats": "/dashboard/stats (GET)",
                "bots": "/dashboard/bots (GET)",
                "accounts": "/dashboard/accounts (GET)"
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
    print("🚀 FXC BOT LOOTERS PLATFORM")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
