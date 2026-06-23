import hashlib
import time
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_NAME = "bus_pass_system.db"

def generate_pass_signature(passenger_name, route_id, expiry_timestamp):
    """Generates a secure, unalterable validation hash for the digital pass."""
    secret_salt = "CodeAlpha_BusSecure_2026_Salt!!!"
    raw_string = f"{passenger_name}-{route_id}-{expiry_timestamp}-{secret_salt}"
    return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_passes (
            pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_name TEXT NOT NULL,
            route_id TEXT NOT NULL,
            expiry_time REAL NOT NULL,
            signature TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/issue_pass', methods=['POST'])
def issue_pass():
    data = request.get_json()
    name = data.get('passenger_name')
    route = data.get('route_id')
    valid_days = data.get('valid_days', 30)
    
    if not name or not route:
        return jsonify({"error": "Missing required passenger or route details."}), 400
        
    expiry = time.time() + (valid_days * 86400)
    pass_hash = generate_pass_signature(name, route, expiry)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO bus_passes (passenger_name, route_id, expiry_time, signature) VALUES (?, ?, ?, ?)",
            (name, route, expiry, pass_hash)
        )
        conn.commit()
        return jsonify({
            "status": "Pass Issued Successfully",
            "passenger_name": name,
            "route_id": route,
            "digital_signature_token": pass_hash,
            "valid_until_timestamp": expiry
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Pass duplicate security signature exception triggered."}), 400
    finally:
        conn.close()

@app.route('/verify_pass', methods=['POST'])
def verify_pass():
    data = request.get_json()
    name = data.get('passenger_name')
    route = data.get('route_id')
    expiry = data.get('expiry_time')
    provided_signature = data.get('signature')
    
    expected_signature = generate_pass_signature(name, route, expiry)
    
    if expected_signature != provided_signature:
        return jsonify({"status": "INVALID_PASS", "message": "Warning: Fraudulent or altered security token detected!"}), 401
        
    if time.time() > expiry:
        return jsonify({"status": "EXPIRED_PASS", "message": "This digital pass has expired."}), 410
        
    return jsonify({"status": "VALID_PASS", "message": f"Pass verified for route {route}. Access allowed."}), 200

if __name__ == '__main__':
    init_db()
    # Running on port 5002 to keep all tasks independent
    app.run(debug=True, port=5002)