from flask import Flask, render_template, request, jsonify, session, redirect
from flask_session import Session
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = "secret"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DB = "database.db"


# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        input TEXT,
        mode TEXT,
        output TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------- AUTH ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (data["username"], data["password"]))

    user = c.fetchone()
    conn.close()

    if user:
        session["user"] = data["username"]
        return jsonify({"success": True})

    return jsonify({"error": "invalid"}), 401


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (data["username"], data["password"]))
        conn.commit()
    except:
        return jsonify({"error": "exists"}), 400

    conn.close()
    return jsonify({"success": True})


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- DASHBOARD ----------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")


# ---------------- AI (MOCK) ----------------
def fake_ai(text, mode):
    return f"[{mode.upper()} RESULT]\n\n{text[::-1]}"


@app.route("/generate", methods=["POST"])
def generate():
    user = session["user"]
    data = request.json

    result = fake_ai(data["text"], data["mode"])

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO history (username, input, mode, output)
    VALUES (?, ?, ?, ?)
    """, (user, data["text"], data["mode"], result))

    conn.commit()
    conn.close()

    return jsonify({"result": result})


@app.route("/history")
def history():
    user = session["user"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    SELECT input, mode, output
    FROM history
    WHERE username=?
    ORDER BY id DESC
    """, (user,))

    data = c.fetchall()
    conn.close()

    return jsonify([
        {"input": d[0], "mode": d[1], "output": d[2]}
        for d in data
    ])


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)