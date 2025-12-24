from flask import Flask, jsonify
from flask_cors import CORS  # <-- import CORS

app = Flask(__name__)
CORS(app)  # <-- enable CORS for all routes

@app.route('/')
def home():
    return jsonify({"message": "Hello from Render API!"})

@app.route('/ping')
def ping():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
