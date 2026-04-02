import os
import subprocess
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Security Setup
PASSWORD_FILE = "admin_pwd.txt"
DEFAULT_HASH = generate_password_hash("admin123")

def get_stored_pwd():
    if not os.path.exists(PASSWORD_FILE):
        return DEFAULT_HASH
    with open(PASSWORD_FILE, "r") as f:
        return f.read().strip()

@app.route('/')
def index():
    if 'logged_in' in session:
        return render_template('index.html')
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if check_password_hash(get_stored_pwd(), password):
        session['logged_in'] = True
        return redirect(url_for('index'))
    return "Invalid Password! <a href='/'>Try again</a>"

@app.route('/toggle_alarm', methods=['POST'])
def toggle_alarm():
    if 'logged_in' not in session: 
        return jsonify({"error": "Unauthorized"}), 401
    
    action = request.json.get("action")
    
    # FIX: Always stop existing media before starting/stopping to clear the buffer
    subprocess.run(["termux-media-player", "stop"])
    
    if action == "ON":
        # Optional: Set volume to max (0-15)
        subprocess.run(["termux-volume", "music", "15"])
        # Play in background loop
        subprocess.Popen(["termux-media-player", "play", "--loop", "alarm.mp3"])
        status = "Alarm Started"
    else:
        status = "Alarm Stopped"
        
    return jsonify({"status": "success", "message": status})

@app.route('/update_pwd', methods=['POST'])
def update_pwd():
    if 'logged_in' not in session: return jsonify({"error": "Unauthorized"}), 401
    new_pwd = request.json.get('new_password')
    if len(new_pwd) < 4: return jsonify({"error": "Password too short"}), 400
    
    with open(PASSWORD_FILE, "w") as f:
        f.write(generate_password_hash(new_pwd))
    return jsonify({"status": "Password Updated Successfully!"})

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Ensure camera static folder exists (optional)
    if not os.path.exists('static'): os.makedirs('static')
    app.run(host='0.0.0.0', port=5000)
