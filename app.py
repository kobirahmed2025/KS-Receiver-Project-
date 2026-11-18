from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from telethon import TelegramClient
import os

app = Flask(__name__)
CORS(app)

# আপনার Telethon API credentials
API_ID = 20676547
API_HASH = "73ee3c17f64c2cef18f436d2386b9f0f"
SESSION_FOLDER = "sessions"
os.makedirs(SESSION_FOLDER, exist_ok=True)

# টেম্পোরারি স্টোরেজ (ক্লায়েন্ট ও ফোন হ্যাশ মনে রাখার জন্য)
active_sessions = {}

# ১. ওটিপি পাঠানোর এপিআই
@app.route("/api/send-otp", methods=["POST"])
async def send_otp():
    data = request.get_json()
    phone = data.get("phone")

    if not phone:
        return jsonify({"success": False, "message": "Phone number is required."}), 400

    # সেশন ফাইল পাথ
    session_path = os.path.join(SESSION_FOLDER, phone.replace("+", ""))
    client = TelegramClient(session_path, API_ID, API_HASH)

    try:
        await client.connect()
        # টেলিগ্রামে কোড পাঠানোর রিকোয়েস্ট
        sent = await client.send_code_request(phone)
        
        # ক্লায়েন্ট এবং ফোন কোড হ্যাশ সেভ করে রাখা
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

# ২. ওটিপি ভেরিফাই ও লগইন করার এপিআই
@app.route("/api/verify-otp", methods=["POST"])
async def verify_otp():
    data = request.get_json()
    phone = data.get("phone")
    code = data.get("code")

    if not phone or not code:
        return jsonify({"success": False, "message": "Phone and code are required."}), 400

    session_data = active_sessions.get(phone)
    if not session_data:
        return jsonify({"success": False, "message": "Session not found. Request OTP first."}), 400

    client = session_data["client"]
    phone_code_hash = session_data["phone_code_hash"]

    try:
        # টেলিগ্রাম কোড দিয়ে সাইন ইন করা
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        
        # সফলভাবে লগইন হলে সেশন সেভ হয়ে যাবে
        client.session.save()
        await client.disconnect()
        
        # মেমোরি থেকে মুছে ফেলা
        del active_sessions[phone]

        return jsonify({
            "success": True, 
            "message": "Login successful! Session created."
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
