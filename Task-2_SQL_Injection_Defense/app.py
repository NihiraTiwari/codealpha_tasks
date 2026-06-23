import os
import sqlite3
from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

app = Flask(__name__)
DB_NAME = "secure_user_vault.db"

# A secure 32-byte encryption key for AES-256
ENCRYPTION_KEY = b'C0deAlphaCloudSecurityKey2026!!!' 
BLOCK_SIZE = 16

def encrypt_data(plain_text):
    """Encrypts sensitive info using AES-256 (CBC mode) before database entry."""
    iv = os.urandom(BLOCK_SIZE)
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plain_text.encode('utf-8'), BLOCK_SIZE))
    return (iv + ciphertext).hex()

def decrypt_data(hex_data):
    """Decrypts protected database entries back to human-readable strings."""
    raw_data = bytes.fromhex(hex_data)
    iv = raw_data[:BLOCK_SIZE]
    ciphertext = raw_data[BLOCK_SIZE:]
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), BLOCK_SIZE).decode('utf-8')

def init_secure_db():
    """Initializes a local database containing a structured user asset vault."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS secure_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            encrypted_password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400
        
    encrypted_pw = encrypt_data(password)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Parameterized query blocks SQL injection attempts
        cursor.execute("INSERT INTO secure_users (username, encrypted_password) VALUES (?, ?)", (username, encrypted_pw))
        conn.commit()
        return jsonify({"status": "Success", "message": "Account created. Data encrypted using AES-256."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists."}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    input_password = data.get('password')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # PARAMETERIZED PROTECTION: Separates SQL query code logic from data variables safely
    cursor.execute("SELECT encrypted_password FROM secure_users WHERE username = ?", (username,))
    record = cursor.fetchone()
    conn.close()
    
    if record:
        stored_encrypted_pw = record[0]
        decrypted_pw = decrypt_data(stored_encrypted_pw)
        
        if input_password == decrypted_pw:
            return jsonify({"status": "Access Granted", "message": "Secure authentication handshake complete."}), 200
            
    return jsonify({"status": "Access Denied", "message": "Invalid credentials or malicious input signature detected."}), 401

if __name__ == '__main__':
    init_secure_db()
    app.run(debug=True, port=5001)