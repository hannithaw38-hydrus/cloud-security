# models.py
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password_hash, role):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'


def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]

    if count == 0:
        default_users = [
            ('admin', generate_password_hash('Admin@1234'), 'admin'),
            ('alice', generate_password_hash('Alice@5678'), 'user'),
            ('bob',   generate_password_hash('Bob@9999'),   'user'),
        ]
        cursor.executemany(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            default_users
        )
        print("[+] Default users created:")
        print("    admin / Admin@1234 (admin)")
        print("    alice / Alice@5678 (user)")
        print("    bob   / Bob@9999   (user)")

    conn.commit()
    conn.close()


def get_user_by_username(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, username, password_hash, role FROM users WHERE username = ?',
        (username,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(id=row[0], username=row[1], password_hash=row[2], role=row[3])
    return None


def get_user_by_id(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, username, password_hash, role FROM users WHERE id = ?',
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(id=row[0], username=row[1], password_hash=row[2], role=row[3])
    return None