from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
from pathlib import Path
import sqlite3

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Helps Flask behave correctly behind Railway's proxy / HTTPS termination
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


# =========================
# DATABASE
# =========================
def ensure_database_directory():
    db_path = Path(app.config["DATABASE"])
    if db_path.parent and str(db_path.parent) not in ("", "."):
        db_path.parent.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    ensure_database_directory()
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            input_text TEXT NOT NULL,
            mode TEXT NOT NULL,
            output_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


# =========================
# HELPERS
# =========================
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "message": "You must log in first."
                }), 401
            return redirect(url_for("login_page"))
        return view_func(*args, **kwargs)
    return wrapper


def get_current_user():
    if "user_id" not in session:
        return None

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (session["user_id"],)
    )
    user = cur.fetchone()
    conn.close()
    return user


def normalize_spacing(text):
    return " ".join(text.strip().split())


def smart_capitalize(text):
    if not text:
        return text
    return text[0].upper() + text[1:]


def basic_writing_fix(text):
    fixed = text.strip()

    replacements = {
        " i ": " I ",
        " im ": " I'm ",
        " dont ": " don't ",
        " cant ": " can't ",
        " doesnt ": " doesn't ",
        " didnt ": " didn't ",
        " isnt ": " isn't ",
        " wasnt ": " wasn't ",
        " werent ": " weren't ",
        " ive ": " I've ",
        " id ": " I'd ",
        " ill ": " I'll ",
        " u ": " you ",
        " ur ": " your ",
        " pls ": " please ",
        " thx ": " thanks ",
        " wsa ": " was ",
        "teh": "the"
    }

    padded = f" {fixed.lower()} "
    for old, new in replacements.items():
        padded = padded.replace(old, new)

    fixed = normalize_spacing(padded)

    if fixed:
        fixed = smart_capitalize(fixed)
        if fixed[-1] not in ".!?":
            fixed += "."

    return fixed


def generate_mock_ai(text, mode):
    clean_text = text.strip()

    if mode == "email":
        return (
            "Subject: Professional Follow-Up\n\n"
            "Hello,\n\n"
            f"{clean_text}\n\n"
            "Please let me know if you need anything else.\n\n"
            "Best regards,"
        )

    if mode == "reply":
        return (
            "Hello,\n\n"
            "Thank you for your message.\n\n"
            f"Regarding your request: {clean_text}\n\n"
            "I appreciate your time and will follow up shortly.\n\n"
            "Best regards,"
        )

    if mode == "improve":
        improved = basic_writing_fix(clean_text)
        return (
            "Improved Version:\n\n"
            f"{improved}\n\n"
            "This version is cleaner, more polished, and easier to read."
        )

    if mode == "text":
        corrected = basic_writing_fix(clean_text)
        return (
            "Writing Fix:\n\n"
            f"{corrected}\n\n"
            "Checked for spelling, grammar, and clarity."
        )

    return (
        "Generated Text:\n\n"
        f"{clean_text}"
    )


# =========================
# HEALTHCHECK
# =========================
@app.route("/health")
def health():
    return jsonify({
        "success": True,
        "status": "ok"
    }), 200


# =========================
# PAGE ROUTES
# =========================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login_page"))


@app.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/register")
def register_page():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    username = user["username"] if user else "User"
    return render_template("index.html", username=username)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# =========================
# API ROUTES
# =========================
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received."
        }), 400

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required."
        }), 400

    if len(username) < 3:
        return jsonify({
            "success": False,
            "message": "Username must be at least 3 characters."
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters."
        }), 400

    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()

        cur.execute(
            "SELECT id, username FROM users WHERE username = ?",
            (username,)
        )
        user = cur.fetchone()

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "redirect": url_for("dashboard")
        }), 200

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "This username already exists."
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }), 500

    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received."
        }), 400

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required."
        }), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,)
    )
    user = cur.fetchone()
    conn.close()

    if not user:
        return jsonify({
            "success": False,
            "message": "Username not found."
        }), 404

    if not check_password_hash(user["password_hash"], password):
        return jsonify({
            "success": False,
            "message": "Incorrect password."
        }), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "redirect": url_for("dashboard")
    }), 200


@app.route("/api/generate", methods=["POST"])
@login_required
def api_generate():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received."
        }), 400

    text = str(data.get("text", "")).strip()
    mode = str(data.get("mode", "text")).strip().lower()

    allowed_modes = {"email", "text", "reply", "improve"}

    if mode not in allowed_modes:
        return jsonify({
            "success": False,
            "message": "Invalid mode selected."
        }), 400

    if not text:
        return jsonify({
            "success": False,
            "message": "Please enter some text first."
        }), 400

    result = generate_mock_ai(text, mode)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO history (user_id, input_text, mode, output_text)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], text, mode, result))
        conn.commit()

        return jsonify({
            "success": True,
            "result": result
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Could not save history: {str(e)}"
        }), 500

    finally:
        conn.close()


@app.route("/api/history", methods=["GET"])
@login_required
def api_history():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, input_text, mode, output_text, created_at
        FROM history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
    """, (session["user_id"],))

    rows = cur.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "id": row["id"],
            "input_text": row["input_text"],
            "mode": row["mode"],
            "output_text": row["output_text"],
            "created_at": row["created_at"]
        })

    return jsonify({
        "success": True,
        "history": history
    }), 200


@app.route("/api/check-session", methods=["GET"])
def api_check_session():
    if "user_id" in session:
        return jsonify({
            "success": True,
            "logged_in": True,
            "username": session.get("username", "")
        }), 200

    return jsonify({
        "success": True,
        "logged_in": False
    }), 200


# =========================
# STARTUP
# =========================
init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=app.config["PORT"],
        debug=app.config["DEBUG"]
    )