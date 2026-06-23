import hashlib
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_NAME = "cloud_storage.db"

def init_db():
    """Initializes the database and creates a table with a unique hash index."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            data_hash TEXT NOT NULL UNIQUE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def generate_hash(text):
    """Normalizes the string and computes a SHA-256 hash to find true duplicates."""
    normalized_text = text.strip().lower()
    return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

@app.route('/upload', methods=['POST'])
def upload_data():
    req_data = request.get_json()
    
    if not req_data or 'content' not in req_data:
        return jsonify({"error": "Missing 'content' field"}), 400
    
    raw_content = req_data['content']
    content_hash = generate_hash(raw_content)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Validate and insert data
        cursor.execute("INSERT INTO data_records (content, data_hash) VALUES (?, ?)", 
                       (raw_content, content_hash))
        conn.commit()
        return jsonify({
            "status": "Success",
            "message": "Unique data entry verified and appended successfully.",
            "hash": content_hash
        }), 201
        
    except sqlite3.IntegrityError:
        # Prevent duplicates from being added
        return jsonify({
            "status": "Rejected",
            "message": "Data redundancy removal system flagged this record as a duplicate entry.",
            "hash": content_hash
        }), 409
        
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)