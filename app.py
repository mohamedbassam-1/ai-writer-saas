import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from dotenv import load_dotenv
from google import genai

# Load environment variables from your secret .env file
load_dotenv()

app = Flask(__name__)
# Replace this fallback string with a long random key inside your .env file
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-saas-key-12345")

# Initialize the Gemini Client using the modern official google-genai SDK module
# It automatically picks up GEMINI_API_KEY from your environment variables
try:
    client = genai.Client()
except Exception as e:
    print(f"Configuration Warning: Gemini Client initialization failed. Error: {e}")
    client = None

# Mock database tracking for session evaluation testing
USERS = {"aaaaaa": "password123"}

@app.route('/')
def index():
    if "username" not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', username=session["username"])

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ==========================================
# 🔐 AUTHENTICATION API ENDPOINTS
# ==========================================
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if username in USERS and USERS[username] == password:
        session["username"] = username
        return jsonify({"success": True, "redirect": url_for('index')})
    
    return jsonify({"success": False, "message": "Invalid username or password credentials."})

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password fields cannot be blank."})
    
    if username in USERS:
        return jsonify({"success": False, "message": "This username is already taken."})
    
    # Register user profile mapping
    USERS[username] = password
    session["username"] = username
    return jsonify({"success": True, "redirect": url_for('index')})


# ==========================================
# 🤖 GENERATIVE AI PIPELINE
# ==========================================
@app.route('/api/generate', methods=['POST'])
def api_generate():
    if "username" not in session:
        return jsonify({"success": False, "message": "Unauthorized access workspace session context."}), 401

    data = request.get_json() or {}
    user_input = data.get("text", "").strip()
    selected_mode = data.get("mode", "email")

    if not user_input:
        return jsonify({"success": False, "message": "Please supply text context before hitting generate."})

    if not client:
        return jsonify({"success": False, "message": "Gemini API client not initialized. Check your .env setup."})

    # Strict system instruction prompt mapping matching your exact frontend button modes!
    mode_instructions = {
        "email": "You are an expert executive assistant. Turn the following rough notes into a professional, clear, and high-converting email draft.",
        "text": "You are a professional editor. Review the following text, fix all grammatical errors, structural flaws, and spelling typos, while keeping the original meaning.",
        "reply": "You are a corporate communications manager. Analyze the incoming message context provided and write a polite, smart, and professional reply draft.",
        "improve": "You are an award-winning copywriter. Rewrite the following text to dramatically elevate its vocabulary, impact, clarity, and overall flow."
    }

    # Fallback to standard email builder if tracking variable contains code slip ups
    system_instruction = mode_instructions.get(selected_mode, mode_instructions["email"])

    try:
        # Generate raw response output via standard live gemini-2.5-flash configuration
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_input,
            config={'system_instruction': system_instruction}
        )
        
        return jsonify({
            "success": True, 
            "result": response.text
        })

    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Gemini Generation Error: {str(e)}"
        })

# Dynamic stub layout handling history canvas sync values
@app.route('/api/history', methods=['POST', 'GET'])
def api_history():
    return jsonify({"success": True, "history": []})

if __name__ == '__main__':
    app.run(debug=True)