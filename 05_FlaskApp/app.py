# app.py
import logging
import sqlite3
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import init_db, get_user_by_username, get_user_by_id

# ── App Setup ──
app = Flask(__name__)
app.config.from_object(Config)

# ── Logging Setup ──
def setup_logging():
    os.makedirs('logs', exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_BACKUP_COUNT']
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

setup_logging()

# ── Flask-Login Setup ──
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# ── Helpers ──
def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def log_event(event_type, username, ip, extra=''):
    message = f"{event_type} | user={username} | ip={ip}"
    if extra:
        message += f" | {extra}"
    if event_type in ('LOGIN_FAILURE', 'UNAUTHORIZED_ACCESS', 'BLOCKED'):
        app.logger.warning(message)
    else:
        app.logger.info(message)

# ── Routes ──
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        ip = get_client_ip()
        user = get_user_by_username(username)

        if user and user.check_password(password):
            login_user(user)
            log_event('LOGIN_SUCCESS', username, ip)
            flash(f'Welcome back, {username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            log_event('LOGIN_FAILURE', username, ip, 'Invalid credentials')
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    ip = get_client_ip()
    log_event('PAGE_ACCESS', current_user.username, ip, 'dashboard')
    return render_template('dashboard.html', user=current_user)


@app.route('/admin')
@login_required
def admin():
    ip = get_client_ip()
    if not current_user.is_admin():
        log_event('UNAUTHORIZED_ACCESS', current_user.username, ip, 'attempted admin access')
        abort(403)

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role FROM users')
    users = cursor.fetchall()
    conn.close()

    log_event('PAGE_ACCESS', current_user.username, ip, 'admin panel')
    return render_template('admin.html', users=users)


@app.route('/logout')
@login_required
def logout():
    ip = get_client_ip()
    username = current_user.username
    logout_user()
    log_event('LOGOUT', username, ip)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.errorhandler(403)
def forbidden(e):
    return render_template('login.html',
        error="Access denied. You don't have permission."), 403


@app.errorhandler(404)
def not_found(e):
    ip = get_client_ip()
    log_event('404_NOT_FOUND', 'anonymous', ip, f'path={request.path}')
    return render_template('login.html', error="Page not found."), 404


# ── Run ──
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)