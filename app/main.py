import os
import sys
import datetime
import threading
import json
import re
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.scanner import scan_website
from lib.analyzer import analyze_endpoints, llm as analyzer_llm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    scans = db.relationship('Scan', backref='user', lazy=True)

    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_url = db.Column(db.String(200), nullable=False)
    max_pages = db.Column(db.Integer, default=20)
    tests_run = db.Column(db.String(100), default='sql,xss')
    status = db.Column(db.String(20), default='pending')
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    results = db.Column(db.Text, nullable=True)

@login_manager.user_loader
def load_user(user_id): return db.session.get(User, int(user_id))

# --- Chatbot AI Engine ---
def get_chatbot_response(user_message):
    if not analyzer_llm:
        return "The local AI model is not loaded. Please follow the instructions in INSTRUCTIONS.md."

    # Use the LLM to understand the user's intent
    prompt = f"""[INST] You are the brain of a cybersecurity chatbot. A user sent you a message.
    Your job is to understand their intent and extract relevant information.
    The user's message is: "{user_message}"

    Possible intents are: 'start_scan', 'ask_question', 'show_history', 'greet', 'unknown'.
    If the intent is 'start_scan', you must extract the 'url' and optionally the number of 'pages'.

    Respond with a single line of JSON. For example:
    {{"intent": "start_scan", "url": "http://example.com", "pages": 10}}
    {{"intent": "ask_question", "question": "What is SQL injection?"}}
    {{"intent": "show_history"}}
    {{"intent": "greet"}} [/INST]
    """

    try:
        output = analyzer_llm(prompt, max_tokens=128, stop=["[INST]"], temperature=0.1)
        response_text = output["choices"][0]["text"]
        parsed_json = json.loads(response_text)
        intent = parsed_json.get("intent")

        if intent == "start_scan":
            url = parsed_json.get("url")
            if not url: return "You asked me to start a scan, but did not provide a URL."
            pages = parsed_json.get("pages", 10)

            new_scan = Scan(target_url=url, max_pages=pages, tests_run="sql,xss", user_id=current_user.id)
            db.session.add(new_scan); db.session.commit()
            threading.Thread(target=run_scan_in_background, args=(app.app_context(), new_scan.id)).start()
            return f"Scan started for {url} (ID: {new_scan.id}). I'll let you know when it's done. You can also ask for the results of a scan by its ID."

        elif intent == "show_history":
            scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.timestamp.desc()).limit(5).all()
            if not scans: return "You have no previous scans."
            response = "Here are your 5 most recent scans:\n"
            for s in scans:
                response += f"- ID: {s.id}, URL: {s.target_url}, Status: {s.status}\n"
            return response

        elif intent == "ask_question":
            question = parsed_json.get("question", user_message)
            answer_prompt = f"[INST] As a cybersecurity expert, answer the following question in a helpful and concise way: {question} [/INST]"
            answer_output = analyzer_llm(answer_prompt, max_tokens=512, stop=["[INST]"])
            return answer_output["choices"][0]["text"].strip()

        elif intent == "greet":
            return "Hello! How can I help you with your web security needs today?"

        else: # unknown
            return "I'm sorry, I'm not sure how to help with that. You can ask me to scan a website, or ask a question about web security."

    except Exception as e:
        print(f"Error in chatbot response generation: {e}")
        return "I'm sorry, I had a problem processing your request."

def run_scan_in_background(app_context, scan_id):
    with app_context:
        scan = db.session.get(Scan, scan_id)
        if not scan: return
        scan.status = 'running'; db.session.commit()
        try:
            endpoints = scan_website(scan.target_url, scan.max_pages)
            vulnerabilities = analyze_endpoints(endpoints, scan.tests_run.split(','))
            scan.results = json.dumps(vulnerabilities)
            scan.status = 'completed'
        except Exception as e:
            scan.status = 'failed'; scan.results = json.dumps([{"error": str(e)}])
        db.session.commit()
        # In a real-world app, we'd use WebSockets or another method to push this notification.
        print(f"Scan {scan.id} for {scan.target_url} is complete!")

# --- Routes ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('chat'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user, remember=True); return redirect(url_for('chat'))
        else: flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('chat'))
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists')
        else:
            new_user = User(username=request.form['username'])
            new_user.set_password(request.form['password'])
            db.session.add(new_user); db.session.commit()
            login_user(new_user); return redirect(url_for('chat'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    user_message = request.json['message']

    # Check for a specific command to get scan results
    match = re.match(r"show me scan (\d+)", user_message.lower())
    if match:
        scan_id = int(match.group(1))
        scan = db.session.get(Scan, scan_id)
        if not scan or scan.user_id != current_user.id:
            response = "Sorry, I can't find that scan or you don't have permission to view it."
        elif scan.status != 'completed':
            response = f"Scan {scan.id} is still in progress (status: {scan.status}). Please check back later."
        else:
            vulnerabilities = json.loads(scan.results)
            if not vulnerabilities:
                response = f"Scan {scan.id} for {scan.target_url} completed with no vulnerabilities found."
            else:
                response = f"Results for scan {scan.id} ({scan.target_url}):\n\n"
                for vuln in vulnerabilities:
                    response += f"--- VULNERABILITY: {vuln['type']} ---\n"
                    response += f"URL: {vuln['url']}\n"
                    response += f"Confidence: {vuln['confidence']}\n\n"
                    response += f"Explanation: {vuln['explanation']}\n\n"
                    response += f"Impact: {vuln['impact']}\n\n"
                    response += f"Remediation: {vuln['remediation']}\n\n"
    else:
        response = get_chatbot_response(user_message)

    return jsonify({'response': response})

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=8080)
