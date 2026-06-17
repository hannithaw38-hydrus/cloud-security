# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE = 'users.db'
    LOG_FILE = 'logs/app.log'
    LOG_MAX_BYTES = 10240
    LOG_BACKUP_COUNT = 5
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_WINDOW = 300