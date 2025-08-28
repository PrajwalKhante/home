import os
import sys
import datetime
import threading
import json
import io
import csv
from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.scanner import scan_website
from lib.analyzer import analyze_endpoints

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Background Scan Function
def run_scan_in_background(app_context, scan_id):
    with app_context:
        scan = db.session.get(Scan, scan_id)
        if not scan: return
        print(f"Starting background scan for {scan.target_url}")
        scan.status = 'running'; db.session.commit()
        try:
            endpoints = scan_website(scan.target_url, scan.max_pages)
            tests = scan.tests_run.split(',')
            vulnerabilities = analyze_endpoints(endpoints, tests)
            scan.results = json.dumps(vulnerabilities)
            scan.status = 'completed'
        except Exception as e:
            print(f"Error during scan: {e}"); scan.status = 'failed'
            scan.results = json.dumps([{"error": str(e)}])
        db.session.commit()
        print(f"Scan {scan.id} finished with status: {scan.status}")

# Routes
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        else: flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists')
        else:
            new_user = User(username=request.form['username'])
            new_user.set_password(request.form['password'])
            db.session.add(new_user); db.session.commit()
            login_user(new_user)
            return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        new_scan = Scan(target_url=request.form['url'], max_pages=int(request.form['max_pages']),
                        tests_run=",".join(request.form.getlist('tests')), user_id=current_user.id)
        db.session.add(new_scan); db.session.commit()
        threading.Thread(target=run_scan_in_background, args=(app.app_context(), new_scan.id)).start()
        flash(f'Scan started for {new_scan.target_url}. Results will appear here when complete.')
        return redirect(url_for('dashboard'))
    scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.timestamp.desc()).all()
    return render_template('dashboard.html', scans=scans)

@app.route('/scan/<int:scan_id>')
@login_required
def scan_results(scan_id):
    scan = db.session.get(Scan, scan_id)
    if not scan or scan.user_id != current_user.id:
        flash("Scan not found or you don't have permission to view it.")
        return redirect(url_for('dashboard'))

    vulnerabilities = json.loads(scan.results) if scan.results else []
    return render_template('results.html', scan=scan, vulnerabilities=vulnerabilities)

@app.route('/scan/<int:scan_id>/download')
@login_required
def download_report(scan_id):
    scan = db.session.get(Scan, scan_id)
    if not scan or scan.user_id != current_user.id:
        flash("Scan not found or you don't have permission to view it.")
        return redirect(url_for('dashboard'))

    vulnerabilities = json.loads(scan.results) if scan.results else []
    if not vulnerabilities:
        flash("No vulnerabilities to report for this scan.")
        return redirect(url_for('scan_results', scan_id=scan_id))

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=vulnerabilities[0].keys())
    writer.writeheader()
    writer.writerows(vulnerabilities)

    mem_file = io.BytesIO()
    mem_file.write(output.getvalue().encode('utf-8'))
    mem_file.seek(0)

    return send_file(mem_file, as_attachment=True, download_name=f'scan_{scan_id}_report.csv', mimetype='text/csv')

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=8080)
