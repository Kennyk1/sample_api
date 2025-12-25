from flask import Flask, request, jsonify
from flask_cors import CORS
from darino import register, login, request_phone_code, scan_result
from storage import save_account, log_action

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return {
        "status": "online",
        "service": "Darino API Bridge"
    }

@app.route("/create-account", methods=["POST"])
def create_account():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    promo = data.get("promo_code")

    if not email or not password:
        return {"error": "Missing fields"}, 400

    success, result = register(email, password, promo)

    if not success:
        return {"success": False, "error": result}, 400

    save_account({
        "email": email,
        "password": password,
        "promo": promo
    })

    return {
        "success": True,
        "data": result
    }

@app.route("/login", methods=["POST"])
def login_route():
    data = request.json
    return jsonify(login(data["email"], data["password"]))

@app.route("/phone-code", methods=["POST"])
def phone_code():
    return jsonify(request_phone_code(**request.json))

@app.route("/scan-result", methods=["POST"])
def scan():
    return jsonify(scan_result(**request.json))

if __name__ == "__main__":
    app.run()
