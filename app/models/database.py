"""
Database models and connection management
"""

import sqlite3
import logging
from flask import current_app
from werkzeug.security import generate_password_hash
from app.config import Config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    conn = None
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database verbindingsfout: {e}")
        return None

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    if conn:
        try:
            # Table for registrations
            conn.execute('''
                CREATE TABLE IF NOT EXISTS registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    house_number TEXT,
                    email TEXT,
                    persons_adults INTEGER NOT NULL,
                    persons_children INTEGER DEFAULT 0,
                    allergies_notes TEXT,
                    total_amount REAL NOT NULL,
                    bunq_me_url TEXT,
                    payment_status TEXT DEFAULT 'pending',
                    paid_amount REAL DEFAULT 0.0,
                    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table for users (admin login)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            logger.info("Database en tabellen gecontroleerd/aangemaakt.")
            
            # Create default admin user if it doesn't exist
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('admin',))
            if cursor.fetchone()[0] == 0:
                admin_password = Config.ADMIN_PASSWORD
                hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('admin', hashed_password))
                conn.commit()
                logger.info("Standaard admin gebruiker 'admin' aangemaakt. Wachtwoord is in .env of 'admin123'.")
                logger.warning("Verander 'admin123' in een sterk wachtwoord in je .env bestand!")

        except sqlite3.Error as e:
            logger.error(f"Fout bij aanmaken database tabellen: {e}")
        finally:
            conn.close()
    else:
        logger.error("Geen database connectie, kan tabellen niet aanmaken.")


