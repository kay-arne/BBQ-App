import os
import secrets
from flask import Flask, request, jsonify, render_template, url_for, redirect, flash, session
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps, lru_cache
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import re
import logging
import threading
import queue
import time
from contextlib import contextmanager
import html
from markupsafe import Markup

# Laad omgevingsvariabelen
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configure file upload
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Generate a secure secret key if not provided
secret_key = os.getenv('SECRET_KEY')
if not secret_key or secret_key == 'your_very_secure_secret_key_here_change_this_in_production':
    secret_key = secrets.token_hex(32)
    print("WARNING: Using generated secret key. Set SECRET_KEY in .env for production!")

app.config['SECRET_KEY'] = secret_key
app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('SESSION_LIFETIME', 1800))

# Performance optimizations
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache for static files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Add ProxyFix for better handling behind reverse proxies
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Make configuration functions available in templates
@app.template_global()
def get_config_value(key, default=None):
    """Get configuration value for use in templates"""
    return get_config(key, default)

@app.template_global()
def render_main_content():
    """Render the main content with dynamic placeholders"""
    content = get_config('main_content', '')
    bbq_details = get_cached_bbq_details()
    
    # Get additional variables from config
    price_per_adult = get_config_value('price_per_adult', str(bbq_details['price_per_adult']))
    price_per_child = get_config_value('price_per_child', '12')
    contact_phone = get_config_value('bbq_contact_phone', bbq_details['contact_kay_phone'])
    
    # Replace placeholders with actual values
    content = content.replace('{date}', bbq_details['date'])
    content = content.replace('{location}', bbq_details['location'])
    content = content.replace('{price}', f"{float(price_per_adult):.2f}")
    content = content.replace('{price_adult}', f"{float(price_per_adult):.2f}")
    content = content.replace('{price_child}', f"{float(price_per_child):.2f}")
    content = content.replace('{deadline}', bbq_details['deadline'])
    content = content.replace('{contact_phone}', contact_phone)
    
    # Return as safe HTML (Markup)
    return Markup(content)

# E-mail configuratie
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
ORGANIZER_EMAIL = os.getenv('ORGANIZER_EMAIL')

# Bunq.me basis URL
BUNQ_ME_BASE_URL = os.getenv('BUNQ_ME_BASE_URL', "https://bunq.me/buurtBBQ")

# BBQ details from environment variables
BBQ_DETAILS = {
    "price_per_adult": float(os.getenv('BBQ_PRICE_PER_ADULT', 25.00)),
    "date": os.getenv('BBQ_DATE', "zaterdag 15 juni"),
    "location": os.getenv('BBQ_LOCATION', "het buurthuis"),
    "deadline": os.getenv('BBQ_DEADLINE', "10 juni"),
    "contact_kay_phone": os.getenv('BBQ_CONTACT_PHONE', "06-12345678")
}

# Database setup - Fixed path
DATABASE = os.getenv('DATABASE_PATH', 'bbq.db')

# Database connection pool
class DatabasePool:
    def __init__(self, database_path, max_connections=10):
        self.database_path = database_path
        self.max_connections = max_connections
        self.connections = queue.Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool"""
        for _ in range(self.max_connections):
            conn = sqlite3.connect(self.database_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode for better concurrency
            conn.execute('PRAGMA synchronous=NORMAL')  # Balance between safety and speed
            conn.execute('PRAGMA cache_size=10000')  # Increase cache size
            conn.execute('PRAGMA temp_store=MEMORY')  # Store temp tables in memory
            self.connections.put(conn)
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            conn = self.connections.get(timeout=5)
            yield conn
        finally:
            if conn:
                self.connections.put(conn)
    
    def close_all(self):
        """Close all connections in the pool"""
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                conn.close()
            except queue.Empty:
                break

# Initialize database pool
db_pool = DatabasePool(DATABASE)

# Asynchronous email queue
class EmailQueue:
    def __init__(self):
        self.email_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._email_worker, daemon=True)
        self.worker_thread.start()
    
    def _email_worker(self):
        """Background worker for sending emails"""
        while True:
            try:
                email_data = self.email_queue.get(timeout=1)
                if email_data is None:  # Shutdown signal
                    break
                self._send_email_sync(email_data)
                self.email_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in email worker: {e}")
    
    def _send_email_sync(self, email_data):
        """Synchronous email sending (moved from original function)"""
        to_email, subject, body_html, is_html = email_data
        
        if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
            logger.warning("E-mail configuratie onvolledig. E-mail kan niet worden verstuurd.")
            return False
        if not to_email:
            logger.warning("Geen e-mailadres opgegeven, e-mail kan niet worden verstuurd.")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg['From'] = SMTP_USERNAME
            msg['To'] = to_email
            msg['Subject'] = subject

            if is_html:
                msg.attach(MIMEText(body_html, 'html'))
            else:
                msg.attach(MIMEText(body_html, 'plain'))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            logger.info(f"E-mail succesvol verstuurd naar {to_email}")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error(f"SMTP Authenticatie fout: Controleer gebruikersnaam en wachtwoord/app-wachtwoord voor {SMTP_USERNAME}.")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP Verbindingsfout met {SMTP_SERVER}:{SMTP_PORT}: {e}. Controleer server en poort.")
            return False
        except Exception as e:
            logger.error(f"Algemene fout bij versturen e-mail naar {to_email}: {e}")
            return False
    
    def send_email_async(self, to_email, subject, body_html, is_html=True):
        """Add email to queue for asynchronous sending"""
        self.email_queue.put((to_email, subject, body_html, is_html))
        logger.info(f"E-mail toegevoegd aan wachtrij voor {to_email}")

# Initialize email queue
email_queue = EmailQueue()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bbq_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Input validation functions
def validate_registration_data(data):
    """Validate registration form data"""
    errors = []
    
    # Name validation
    name = data.get('name', '').strip()
    if not name:
        errors.append('Naam is verplicht')
    elif len(name) < 2:
        errors.append('Naam moet minimaal 2 karakters bevatten')
    elif len(name) > 100:
        errors.append('Naam mag maximaal 100 karakters bevatten')
    elif not re.match(r'^[a-zA-Z\s\-\.]+$', name):
        errors.append('Naam mag alleen letters, spaties, streepjes en punten bevatten')
    
    # House number validation
    house_number = data.get('houseNumber', '').strip()
    house_number_regex = r"^\d+[a-zA-Z]?$"
    if not house_number:
        errors.append('Huisnummer is verplicht')
    elif not re.match(house_number_regex, house_number):
        errors.append('Ongeldig huisnummer. Voer enkel cijfers en optioneel één letter (bijv. 46 of 46a) in.')
    
    # Email validation (optional)
    email = data.get('email', '').strip()
    if email:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            errors.append('Ongeldig e-mailadres formaat')
        elif len(email) > 254:
            errors.append('E-mailadres is te lang')
    
    # Adults validation
    try:
        persons_adults = int(data.get('personsAdults', 0))
        if persons_adults < 1:
            errors.append('Aantal volwassenen moet minimaal 1 zijn')
        elif persons_adults > 20:
            errors.append('Aantal volwassenen mag maximaal 20 zijn')
    except (ValueError, TypeError):
        errors.append('Ongeldig aantal volwassenen')
    
    # Children validation
    try:
        persons_children = int(data.get('personsChildren', 0))
        if persons_children < 0:
            errors.append('Aantal kinderen kan niet negatief zijn')
        elif persons_children > 20:
            errors.append('Aantal kinderen mag maximaal 20 zijn')
    except (ValueError, TypeError):
        errors.append('Ongeldig aantal kinderen')
    
    # Allergies/notes validation
    allergies_notes = data.get('allergiesNotes', '').strip()
    if len(allergies_notes) > 500:
        errors.append('Opmerkingen mogen maximaal 500 karakters bevatten')
    
    return errors

# Configuration management functions
def get_config(key, default=None):
    """Get a configuration value from the database"""
    with db_pool.get_connection() as conn:
        try:
            cursor = conn.execute('SELECT value FROM config WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else default
        except sqlite3.Error as e:
            logger.error(f"Error getting config {key}: {e}")
            return default

def set_config(key, value, description=None, category='general'):
    """Set a configuration value in the database"""
    with db_pool.get_connection() as conn:
        try:
            # If description is not provided, fetch the existing one
            if description is None:
                cursor = conn.execute('SELECT description FROM config WHERE key = ?', (key,))
                result = cursor.fetchone()
                if result:
                    description = result[0]

            conn.execute('''
                INSERT OR REPLACE INTO config (key, value, description, category, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, value, description, category))
            conn.commit()
            logger.info(f"Configuration updated: {key} = {value}")
        except sqlite3.Error as e:
            logger.error(f"Error setting config {key}: {e}")

def update_config_value(key, value):
    """Update only the value of a configuration setting, preserving category and description"""
    with db_pool.get_connection() as conn:
        try:
            conn.execute('''
                UPDATE config SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = ?
            ''', (value, key))
            conn.commit()
            logger.info(f"Configuration value updated: {key} = {value}")
        except sqlite3.Error as e:
            logger.error(f"Error updating config value {key}: {e}")

def get_all_config():
    """Get all configuration settings grouped by category"""
    with db_pool.get_connection() as conn:
        try:
            cursor = conn.execute('SELECT * FROM config ORDER BY category, key')
            configs = {}
            for row in cursor.fetchall():
                category = row['category']
                if category not in configs:
                    configs[category] = []
                configs[category].append(dict(row))
            return configs
        except sqlite3.Error as e:
            logger.error(f"Error getting all config: {e}")
            return {}

def cleanup_old_config():
    """Remove old configuration fields that are no longer used"""
    old_fields = ['welcome_text', 'description_text']
    
    with db_pool.get_connection() as conn:
        cursor = conn.cursor()
        for field in old_fields:
            cursor.execute("DELETE FROM config WHERE key = ?", (field,))
            if cursor.rowcount > 0:
                logger.info(f"Removed old configuration field: {field}")
        conn.commit()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def initialize_default_config():
    """Initialize default configuration values"""
    # Clean up old fields first
    cleanup_old_config()
    
    defaults = {
        'app_title': ('BBQ-App', 'Titel van de applicatie', 'general'),
        'bbq_date': ('zaterdag 15 juni', 'Datum van de BBQ', 'bbq'),
        'bbq_location': ('het buurthuis', 'Locatie van de BBQ', 'bbq'),
        'bbq_deadline': ('10 juni', 'Deadline voor aanmelding', 'bbq'),
        'bbq_contact_phone': ('06-12345678', 'Contact telefoonnummer', 'bbq'),
        'main_content': ('<h2>🎉 Welkom bij ons jaarlijkse buurtfeest!</h2><p><strong>Beste buurtgenoten,</strong></p><p>Hartelijk welkom op het digitale aanmeldformulier voor ons jaarlijkse tuinfeest met BBQ. Dit jaar houden we ons feest op <strong>{date}</strong>. We zijn voor ons feest welkom bij <strong>{location}</strong>. De inloop is vanaf <strong>16.00 uur.</strong></p><p>De kosten voor de BBQ bedragen <strong>€{price} per volwassene</strong>. Alles is inbegrepen: een complete BBQ, op- en afbouw tuinfeest, schoonmaak BBQ\'s, koffie, thee en overige (non) alcoholische dranken. Thuiswonende kinderen mogen gratis mee. Wel vragen we u vriendelijk om op te geven of en hoeveel kinderen er meekomen.</p><p>Met dit formulier kunt u zich direct aanmelden. Na het invullen en verzenden van dit formulier wordt u automatisch doorverwezen naar een betaalpagina waar u de verschuldigde kosten direct kunt voldoen.</p><p>Meldt u zich alstublieft <strong>uiterlijk {deadline}</strong> aan via dit formulier. We hopen u allemaal te zien op <strong>{date}</strong>!</p><p>Met hartelijke groet,</p><p><strong>Het organisatieteam</strong></p>', 'Hoofdinhoud van de aanmeldpagina (HTML)', 'content'),
        'smtp_server': (SMTP_SERVER or '', 'SMTP server voor e-mail', 'email'),
        'smtp_port': (str(SMTP_PORT), 'SMTP poort', 'email'),
        'smtp_username': (SMTP_USERNAME or '', 'SMTP gebruikersnaam', 'email'),
        'smtp_password': (SMTP_PASSWORD or '', 'SMTP wachtwoord', 'email'),
        'organizer_email': (ORGANIZER_EMAIL or '', 'E-mailadres van de organisator', 'email'),
        'hero_image': ('bbq_achtergrond.png', 'Hero afbeelding', 'content'),
        'primary_color': ('#FF8C00', 'Primaire kleur van de applicatie', 'appearance'),
        'secondary_color': ('#FF6B35', 'Secundaire kleur van de applicatie', 'appearance'),
        'hero_title': ('WELKOM BIJ ONZE JAARLIJKSE BUURT BBQ', 'Hero titel op de hoofdpagina', 'content'),
        'hero_subtitle': ('Geniet van heerlijk eten, gezellige sfeer en ontmoet je buren tijdens ons jaarlijkse buurtfeest.', 'Hero ondertitel op de hoofdpagina', 'content'),
        'benefit_1_title': ('HEERLIJK VLEES', 'Titel van voordeel 1', 'benefits'),
        'benefit_1_description': ('Geniet van premium vlees dat perfect bereid wordt door onze ervaren BBQ-chefs.', 'Beschrijving van voordeel 1', 'benefits'),
        'benefit_1_icon': ('🍖', 'Icoon van voordeel 1', 'benefits'),
        'benefit_2_title': ('BUURTGEVOEL', 'Titel van voordeel 2', 'benefits'),
        'benefit_2_description': ('Ontmoet je buren en bouw nieuwe vriendschappen in een gezellige sfeer.', 'Beschrijving van voordeel 2', 'benefits'),
        'benefit_2_icon': ('👥', 'Icoon van voordeel 2', 'benefits'),
        'benefit_3_title': ('GEZELLIGHEID', 'Titel van voordeel 3', 'benefits'),
        'benefit_3_description': ('Een ontspannen avond met lekker eten, drankjes en gezellige gesprekken.', 'Beschrijving van voordeel 3', 'benefits'),
        'benefit_3_icon': ('🎉', 'Icoon van voordeel 3', 'benefits'),
        'benefit_4_title': ('GOEDE PRIJS', 'Titel van voordeel 4', 'benefits'),
        'benefit_4_description': ('Alles inclusief voor een eerlijke prijs - geen verborgen kosten.', 'Beschrijving van voordeel 4', 'benefits'),
        'benefit_4_icon': ('💰', 'Icoon van voordeel 4', 'benefits'),
        'price_per_adult': ('25', 'Prijs per volwassene in euro', 'variables'),
        'price_per_child': ('12', 'Prijs per kind in euro', 'variables'),
        'payment_method': ('none', 'Betaalmethode (none, bunq)', 'payment'),
        'bunq_me_link': ('', 'Bunq.me betaallink', 'payment'),
        'no_payment_message': ('Uw aanmelding is succesvol ontvangen! Wij nemen binnenkort contact met u op voor de betaling.', 'Bericht bij geen betalingsintegratie', 'payment')
    }
    
    for key, (value, description, category) in defaults.items():
        if get_config(key) is None:
            set_config(key, value, description, category)
        else:
            # Only update category if it's 'general' (default) and should be something else
            with db_pool.get_connection() as conn:
                try:
                    cursor = conn.execute('SELECT category FROM config WHERE key = ?', (key,))
                    result = cursor.fetchone()
                    if result and result[0] == 'general' and category != 'general':
                        conn.execute('UPDATE config SET category = ? WHERE key = ?', (category, key))
                        conn.commit()
                        logger.info(f"Updated category for {key} from general to {category}")
                except sqlite3.Error as e:
                    logger.error(f"Error updating category for {key}: {e}")

# Admin user management functions
def get_all_admins():
    """Get all admin users"""
    with db_pool.get_connection() as conn:
        try:
            cursor = conn.execute('SELECT id, username, email, created_at, is_active FROM users ORDER BY created_at')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting admins: {e}")
            return []

def create_admin(username, password, email=None):
    """Create a new admin user"""
    with db_pool.get_connection() as conn:
        try:
            # Check if username already exists (case-insensitive)
            cursor = conn.execute('SELECT COUNT(*) FROM users WHERE LOWER(username) = LOWER(?)', (username,))
            if cursor.fetchone()[0] > 0:
                return False, "Gebruikersnaam bestaat al"
            
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            conn.execute('''
                INSERT INTO users (username, password_hash, email, created_at, is_active)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
            ''', (username, hashed_password, email))
            conn.commit()
            logger.info(f"New admin user created: {username}")
            return True, "Admin gebruiker succesvol aangemaakt"
        except sqlite3.Error as e:
            logger.error(f"Error creating admin {username}: {e}")
            return False, f"Fout bij aanmaken admin: {e}"

def update_admin_password(admin_id, new_password):
    """Update admin user password"""
    with db_pool.get_connection() as conn:
        try:
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (hashed_password, admin_id))
            conn.commit()
            logger.info(f"Password updated for admin ID: {admin_id}")
            return True, "Wachtwoord succesvol bijgewerkt"
        except sqlite3.Error as e:
            logger.error(f"Error updating admin password: {e}")
            return False, f"Fout bij bijwerken wachtwoord: {e}"

def delete_admin(admin_id):
    """Delete an admin user (soft delete by setting is_active to 0)"""
    with db_pool.get_connection() as conn:
        try:
            # Don't allow deleting the last admin
            cursor = conn.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            active_count = cursor.fetchone()[0]
            if active_count <= 1:
                return False, "Kan de laatste admin gebruiker niet verwijderen"
            
            conn.execute('UPDATE users SET is_active = 0 WHERE id = ?', (admin_id,))
            conn.commit()
            logger.info(f"Admin user deactivated: {admin_id}")
            return True, "Admin gebruiker succesvol verwijderd"
        except sqlite3.Error as e:
            logger.error(f"Error deleting admin: {e}")
            return False, f"Fout bij verwijderen admin: {e}"

# Caching for frequently accessed data
@lru_cache(maxsize=128)
def get_cached_bbq_details():
    """Cache BBQ details from configuration"""
    return {
        "price_per_adult": float(get_config('price_per_adult', 25.00)),
        "date": get_config('bbq_date', "zaterdag 15 juni"),
        "location": get_config('bbq_location', "het buurthuis"),
        "deadline": get_config('bbq_deadline', "10 juni"),
        "contact_kay_phone": get_config('bbq_contact_phone', "06-12345678")
    }

def get_db_connection():
    """Legacy function - use db_pool.get_connection() instead"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database verbindingsfout: {e}")
        return None

def init_db():
    """Initialize database with optimized tables and indexes"""
    with db_pool.get_connection() as conn:
        try:
            # Table for registrations with optimized structure
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
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Table for configuration settings
            conn.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    description TEXT,
                    category TEXT DEFAULT 'general',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better query performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_registrations_payment_status ON registrations(payment_status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_registrations_registered_at ON registrations(registered_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_registrations_email ON registrations(email)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            
            conn.commit()
            logger.info("Database en tabellen gecontroleerd/aangemaakt met optimalisaties.")

        except sqlite3.Error as e:
            logger.error(f"Fout bij aanmaken database tabellen: {e}")
            raise

# BELANGRIJK: Roep init_db() aan bij het opstarten van de applicatie
with app.app_context():
    init_db()
    # Initialize default configuration
    initialize_default_config()
    # Voeg een standaard admin gebruiker toe als deze nog niet bestaat
    with db_pool.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('admin',))
        if cursor.fetchone()[0] == 0:
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('admin', hashed_password))
            conn.commit()
            logger.info("Standaard admin gebruiker 'admin' aangemaakt. Wachtwoord is in .env of 'admin123'.")
            logger.warning("Verander 'admin123' in een sterk wachtwoord in je .env bestand!")


# Decorator om routes te beveiligen
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('U moet inloggen om deze pagina te bekijken.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Functie om e-mail te versturen (now asynchronous)
def send_email(to_email, subject, body_html, is_html=True):
    """Send email asynchronously using the email queue"""
    email_queue.send_email_async(to_email, subject, body_html, is_html)
    return True  # Always return True since it's queued

@app.route('/')
def index():
    # Use cached BBQ details for better performance
    return render_template('index.html', bbq_details=get_cached_bbq_details())

@app.route('/success')
def success_page():
    return render_template('success.html')

# Login pagina
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        with db_pool.get_connection() as conn:
            # Case-insensitive username lookup
            user = conn.execute('SELECT * FROM users WHERE LOWER(username) = LOWER(?)', (username,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['logged_in'] = True
            flash('Succesvol ingelogd!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'error')
    return render_template('login.html')

# Logout functie
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('U bent uitgelogd.', 'info')
    return redirect(url_for('login'))

# Configuration management routes
@app.route('/admin/config')
@login_required
def admin_config():
    """Admin configuration page"""
    configs = get_all_config()
    admins = get_all_admins()
    return render_template('admin_config.html', configs=configs, admins=admins)

@app.route('/admin/config/update', methods=['POST'])
@login_required
def update_config():
    """Update configuration settings"""
    try:
        active_tab = request.form.get('active_tab', 'variables')

        # Map tabs to their corresponding configuration categories
        tab_to_category_map = {
            'variables': ['general', 'bbq', 'variables'],
            'content': ['content'],
            'benefits': ['benefits'],
            'style': ['appearance'],
            'payment': ['payment'],
            'email': ['email']
        }

        # Create a mapping from config key to its category for efficient lookup
        all_configs = get_all_config()
        key_to_category_map = {
            setting['key']: setting['category']
            for category_settings in all_configs.values()
            for setting in category_settings
        }

        # Handle file upload for the 'content' tab
        if active_tab == 'content' and 'hero_image' in request.files:
            file = request.files['hero_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                # Use set_config to preserve description and category for new uploads
                set_config('hero_image', f'uploads/{filename}', description='Hero afbeelding', category='content')
                flash('Hero afbeelding succesvol geüpload!', 'success')

        # Process and save only the form fields relevant to the active tab
        categories_to_update = tab_to_category_map.get(active_tab, [])
        for key, value in request.form.items():
            if key.startswith('config_'):
                config_key = key[7:]  # Remove 'config_' prefix
                if key_to_category_map.get(config_key) in categories_to_update:
                    update_config_value(config_key, value)
        
        flash('Configuratie succesvol bijgewerkt!', 'success')
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        flash('Fout bij bijwerken configuratie.', 'error')
        active_tab = 'variables' # Fallback to default tab on error
    
    return redirect(url_for('admin_config') + f'#{active_tab}')


@app.route('/admin/config/reset-style', methods=['POST'])
@login_required
def reset_style_config():
    """Reset only style-related configuration to default values"""
    try:
        # Get default style configuration only
        default_style_config = {
            'primary_color': '#FF8C00',
            'secondary_color': '#FF6B35'
        }
        
        # Reset only style configuration values
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            for key, value in default_style_config.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO config (key, value, description, category, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (key, value, f'Default style value for {key}', 'appearance', datetime.now()))
            conn.commit()
        
        flash('Stijl instellingen succesvol gereset naar standaardwaarden!', 'success')
    except Exception as e:
        logger.error(f"Error resetting style config: {e}")
        flash('Fout bij resetten stijl instellingen.', 'error')
    
    return redirect(url_for('admin_config'))

# Admin user management routes
@app.route('/admin/users/create', methods=['POST'])
@login_required
def create_admin_user():
    """Create new admin user"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    email = request.form.get('email', '').strip()
    
    if not username or not password:
        flash('Gebruikersnaam en wachtwoord zijn verplicht.', 'error')
        return redirect(url_for('admin_config') + '#users')
    
    success, message = create_admin(username, password, email)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_config') + '#users')

@app.route('/admin/users/update_password/<int:admin_id>', methods=['POST'])
@login_required
def update_admin_user_password(admin_id):
    """Update admin user password"""
    new_password = request.form.get('new_password', '')
    
    if not new_password:
        flash('Nieuw wachtwoord is verplicht.', 'error')
        return redirect(url_for('admin_config') + '#users')
    
    success, message = update_admin_password(admin_id, new_password)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_config') + '#users')

@app.route('/admin/users/delete/<int:admin_id>', methods=['POST'])
@login_required
def delete_admin_user(admin_id):
    """Delete admin user"""
    success, message = delete_admin(admin_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_config') + '#users')


@app.route('/api/register', methods=['POST'])
@csrf.exempt
def register_and_pay():
    data = request.json
    
    # Validate input data
    validation_errors = validate_registration_data(data)
    if validation_errors:
        error_message = '; '.join(validation_errors)
        logger.warning(f"Registration validation failed: {error_message}")
        return jsonify({'message': error_message}), 400
    
    # Extract validated data
    name = data.get('name').strip()
    house_number = data.get('houseNumber').strip()
    email = data.get('email', '').strip()
    persons_adults = int(data.get('personsAdults'))
    persons_children = int(data.get('personsChildren', 0))
    allergies_notes = data.get('allergiesNotes', '').strip()
    
    # Get prices and payment method from database configuration
    price_per_adult = float(get_config_value('price_per_adult', '15'))
    price_per_child = float(get_config_value('price_per_child', '8'))
    total_amount = (persons_adults * price_per_adult) + (persons_children * price_per_child)
    payment_method = get_config_value('payment_method', 'none')
    bunq_me_link = get_config_value('bunq_me_link', '')
    no_payment_message = get_config_value('no_payment_message', 'Uw aanmelding is succesvol ontvangen! Wij nemen binnenkort contact met u op voor de betaling.')

    payment_url = ""
    payment_status = "pending"
    
    try:
        # Generate payment URL based on payment method
        if payment_method == 'bunq' and bunq_me_link:
            description = f"BBQ {name} - Huisnr: {house_number}"
            payment_url = f"{bunq_me_link}/{total_amount:.2f}/{description.replace(' ', '%20')}"
        elif payment_method == 'none':
            payment_url = ""
            payment_status = "no_payment_required"

        with db_pool.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO registrations (name, house_number, email, persons_adults, persons_children, allergies_notes, total_amount, bunq_me_url, payment_status, paid_amount) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (name, house_number, email, persons_adults, persons_children, allergies_notes, total_amount, payment_url, payment_status, 0.0)
                )
                registration_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Aanmelding opgeslagen met ID: {registration_id} voor {name} (Huisnummer {house_number})")
                flash('Aanmelding succesvol opgeslagen.', 'success')

                # --- E-mails versturen ---
                if email:
                    subject_user = "Bevestiging aanmelding Buurt BBQ"
                    
                    # Different email content based on payment method
                    if payment_method == 'bunq' and payment_url:
                        payment_info = f"<p>Het totaalbedrag is <strong>€{total_amount:.2f}</strong>. U kunt betalen via de volgende link: <a href='{payment_url}'>Klik hier om te betalen</a></p>"
                        payment_status_text = "Uw aanmelding en betaling worden nu door ons geverifieerd."
                    else:
                        payment_info = f"<p>Het totaalbedrag is <strong>€{total_amount:.2f}</strong>.</p><p>{no_payment_message}</p>"
                        payment_status_text = "Uw aanmelding is succesvol ontvangen."
                    
                    # Get all config values for email
                    bbq_date = get_config_value('bbq_date', 'zaterdag 15 juni')
                    bbq_location = get_config_value('bbq_location', 'het buurthuis')
                    bbq_deadline = get_config_value('bbq_deadline', '10 juni')
                    bbq_contact = get_config_value('bbq_contact_phone', '06-12345678')
                    
                    body_user = f"""
                    <html>
                    <body>
                        <p>Beste {name} (Huisnummer {house_number}),</p>
                        <p>Hartelijk dank voor je aanmelding voor de Buurt BBQ!</p>
                        <p>Je hebt je aangemeld voor <strong>{persons_adults} volwassene(n)</strong> en <strong>{persons_children} kind(eren)</strong>.</p>
                        {payment_info}
                        <p>{payment_status_text}</p>
                        <p>Datum BBQ: {bbq_date}. Locatie: {bbq_location}.</p>
                        <p>Uiterste opgavedatum: {bbq_deadline}.</p>
                        <p>Voor vragen kunt u contact opnemen via {bbq_contact}.</p>
                        <p>We kijken ernaar uit u te zien!</p>
                        <p>Met hartelijke groet,</p>
                        <p>Het organisatieteam</p>
                    </body>
                    </html>
                    """
                    if not send_email(email, subject_user, body_user):
                        flash(f'Fout bij versturen bevestigingsmail naar {email}.', 'error')

                # E-mail naar de organisator met tabeloverzicht
                subject_organizer = f"NIEUWE BBQ AANMELDING: {name} (Huisnummer {house_number})"
                
                # Different organizer email content based on payment method
                if payment_method == 'bunq' and payment_url:
                    payment_status_text = "Pending (via Bunq.me)"
                    payment_link_text = f"<a href='{payment_url}'>{payment_url}</a>"
                    payment_instructions = "<p>Controleer de betaling handmatig in je Bunq app en werk de status bij in het admin-paneel.</p>"
                else:
                    payment_status_text = "Geen betalingsintegratie"
                    payment_link_text = "N.V.T."
                    payment_instructions = "<p>Neem contact op met de deelnemer voor de betaling.</p>"
                
                body_organizer = f"""
                <html>
                <head>
                    <style>
                        table {{ width: 100%; border-collapse: collapse; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        .highlight {{ background-color: #e6ffe6; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <p>Beste beheerder,</p>
                    <p>Er is een <strong>nieuwe aanmelding</strong> voor de Buurt BBQ ontvangen via het online formulier.</p>
                    
                    <table>
                        <tr>
                            <th>Details</th>
                            <th>Waarde</th>
                        </tr>
                        <tr>
                            <td><strong>Naam:</strong></td>
                            <td>{name}</td>
                        </tr>
                        <tr>
                            <td><strong>Adres:</strong></td>
                            <td>Huisnummer {house_number}</td>
                        </tr>
                        <tr>
                            <td><strong>E-mail:</strong></td>
                            <td>{email if email else 'N.V.T. (niet opgegeven)'}</td>
                        </tr>
                        <tr>
                            <td><strong>Aantal volwassenen:</strong></td>
                            <td>{persons_adults}</td>
                        </tr>
                        <tr>
                            <td><strong>Aantal kinderen:</strong></td>
                            <td>{persons_children}</td>
                        </tr>
                        <tr>
                            <td><strong>Allergieën/Opmerkingen:</strong></td>
                            <td>{allergies_notes if allergies_notes else 'Geen specifieke opmerkingen'}</td>
                        </tr>
                        <tr class="highlight">
                            <td><strong>Totaal verschuldigd:</strong></td>
                            <td>€{total_amount:.2f}</td>
                        </tr>
                        <tr>
                            <td><strong>Betalingsstatus:</strong></td>
                            <td>{payment_status_text}</td>
                        </tr>
                        <tr>
                            <td><strong>Betaallink:</strong></td>
                            <td>{payment_link_text}</td>
                        </tr>
                        <tr>
                            <td><strong>Datum aanmelding:</strong></td>
                            <td>{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</td>
                        </tr>
                        <tr>
                            <td><strong>Interne Registratie ID:</strong></td>
                            <td>{registration_id}</td>
                        </tr>
                    </table>
                    
                    {payment_instructions}
                    <p><a href="{request.url_root}admin">Ga naar het BBQ Admin Paneel</a></p>
                    
                    <p>Met vriendelijke groet,</p>
                    <p>Je BBQ Aanmeld Applicatie</p>
                </body>
                </html>
                """
                if not send_email(ORGANIZER_EMAIL, subject_organizer, body_organizer):
                    flash(f'Fout bij versturen notificatiemail naar {ORGANIZER_EMAIL}.', 'error')

                # Return different response based on payment method
                if payment_method == 'bunq' and payment_url:
                    return jsonify({
                        'message': 'Aanmelding succesvol! Je wordt nu doorgestuurd naar de betaalpagina.',
                        'paymentUrl': payment_url,
                        'registrationId': registration_id,
                        'paymentMethod': 'bunq'
                    })
                else:
                    return jsonify({
                        'message': no_payment_message,
                        'registrationId': registration_id,
                        'paymentMethod': 'none'
                    })

            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Database fout bij opslaan aanmelding: {e}")
                flash(f'Databasefout bij aanmelding: {e}.', 'error')
                return jsonify({'message': f'Fout bij opslaan aanmelding: {e}'}), 500

    except Exception as e:
        logger.error(f"Algemene fout bij aanmelding: {e}")
        flash(f'Er is een onverwachte fout opgetreden: {e}.', 'error')
        return jsonify({'message': f'Er is een onverwachte fout opgetreden: {e}'}), 500

# Beveilig de admin_dashboard route met @login_required
@app.route('/admin')
@login_required
def admin_dashboard():
    registrations = []
    total_persons = 0
    total_adults = 0
    total_children = 0
    total_due_amount = 0.0
    total_paid_amount = 0.0
    
    # Use cached BBQ details for better performance
    bbq_details = get_cached_bbq_details()
    
    with db_pool.get_connection() as conn:
        try:
            registrations = conn.execute('SELECT * FROM registrations ORDER BY registered_at DESC').fetchall()
            
            for reg in registrations:
                total_adults += reg['persons_adults']
                total_children += reg['persons_children']
                total_persons = total_adults + total_children
                total_due_amount += reg['total_amount']
                total_paid_amount += reg['paid_amount']

        except sqlite3.Error as e:
            flash(f"Fout bij ophalen aanmeldingen: {e}", 'error')
            logger.error(f"Fout bij ophalen aanmeldingen: {e}")
    
    return render_template(
        'admin.html', 
        registrations=registrations,
        total_persons=total_persons,
        total_adults=total_adults,
        total_children=total_children,
        total_due_amount=total_due_amount,
        total_paid_amount=total_paid_amount,
        bbq_details=bbq_details
    )

# De route /admin/update_settings is verwijderd

# Beveilig de API route voor details (optioneel, maar aanbevolen)
@app.route('/api/registration/<int:reg_id>', methods=['GET'])
@login_required
def get_registration_details(reg_id):
    with db_pool.get_connection() as conn:
        try:
            registration = conn.execute('SELECT * FROM registrations WHERE id = ?', (reg_id,)).fetchone()
            if registration:
                return jsonify(dict(registration)), 200
            else:
                return jsonify({'message': 'Aanmelding niet gevonden.'}), 404
        except sqlite3.Error as e:
            logger.error(f"Fout bij ophalen registratie details: {e}")
            return jsonify({'message': 'Fout bij ophalen details.'}), 500

# Beveilig de admin acties (add, update, delete)
@app.route('/admin/add_registration', methods=['POST'])
@login_required
def add_registration():
    name = request.form['name']
    house_number = request.form.get('house_number', '')
    email = request.form.get('email', '')
    persons_adults = int(request.form['persons_adults'])
    persons_children = int(request.form.get('persons_children', 0))
    allergies_notes = request.form.get('allergies_notes', '')
    total_amount = float(request.form['total_amount'])
    payment_status = request.form.get('payment_status', 'pending')
    bunq_me_url = request.form.get('bunq_me_url', '')

    initial_paid_amount = 0.0
    if payment_status == 'paid':
        initial_paid_amount = total_amount

    with db_pool.get_connection() as conn:
        try:
            conn.execute(
                '''INSERT INTO registrations (name, house_number, email, persons_adults, persons_children, allergies_notes, total_amount, bunq_me_url, payment_status, paid_amount) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, house_number, email, persons_adults, persons_children, allergies_notes, total_amount, bunq_me_url, payment_status, initial_paid_amount)
            )
            conn.commit()
            flash("Aanmelding succesvol toegevoegd.", 'success')
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Fout bij toevoegen aanmelding: {e}", 'error')
            logger.error(f"Fout bij toevoegen aanmelding: {e}")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_status/<int:reg_id>', methods=['POST'])
@login_required
def update_registration_status(reg_id):
    new_status = request.form['status']
    
    with db_pool.get_connection() as conn:
        try:
            current_reg = conn.execute('SELECT * FROM registrations WHERE id = ?', (reg_id,)).fetchone()
            if not current_reg:
                flash("Aanmelding niet gevonden.", 'info')
                return redirect(url_for('admin_dashboard'))
            
            total_amount_for_reg = current_reg['total_amount']
            current_email = current_reg['email']
            current_name = current_reg['name']
            
            paid_amount_to_set = 0.0
            if new_status == 'paid':
                paid_amount_to_set = total_amount_for_reg

            conn.execute(
                'UPDATE registrations SET payment_status = ?, paid_amount = ? WHERE id = ?', 
                (new_status, paid_amount_to_set, reg_id)
            )
            conn.commit()

            if conn.total_changes > 0:
                flash("Status en betaald bedrag succesvol bijgewerkt.", 'success')
                
                if new_status == 'paid' and current_email:
                    bbq_details = get_cached_bbq_details()
                    subject_paid = "Bevestiging betaling Buurt BBQ verwerkt"
                    # Get config values for payment confirmation email
                    bbq_date = get_config_value('bbq_date', bbq_details["date"])
                    bbq_location = get_config_value('bbq_location', 'het buurthuis')
                    bbq_contact = get_config_value('bbq_contact_phone', '06-12345678')
                    
                    body_paid = f"""
                    <html>
                    <body>
                        <p>Beste {current_name} (Huisnummer {current_reg['house_number']}),</p>
                        <p>Goed nieuws! Uw betaling van <strong>€{total_amount_for_reg:.2f}</strong> voor de Buurt BBQ is zojuist door de organisatie <strong>verwerkt en bevestigd</strong>.</p>
                        <p>U bent nu officieel aangemeld voor {current_reg['persons_adults']} volwassene(n) en {current_reg['persons_children']} kind(eren).</p>
                        <p>Wij kijken ernaar uit u te zien op ons tuinfeest op <strong>{bbq_date}</strong> bij <strong>{bbq_location}</strong>!</p>
                        <p>Voor vragen kunt u contact opnemen via {bbq_contact}.</p>
                        <p>Met vriendelijke groet,</p>
                        <p>Het organisatieteam</p>
                    </body>
                    </html>
                    """
                    if not send_email(current_email, subject_paid, body_paid):
                        flash(f'Fout bij versturen van de betalingsbevestiging naar {current_email}.', 'error')

            else:
                flash("Aanmelding niet gevonden of status/bedrag was al hetzelfde.", 'info')
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Fout bij bijwerken status: {e}", 'error')
            logger.error(f"Fout bij bijwerken status: {e}")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_registration/<int:reg_id>', methods=['POST'])
@login_required
def delete_registration(reg_id):
    with db_pool.get_connection() as conn:
        try:
            conn.execute('DELETE FROM registrations WHERE id = ?', (reg_id,))
            conn.commit()
            if conn.total_changes > 0:
                flash("Aanmelding succesvol verwijderd.", 'success')
            else:
                flash("Aanmelding niet gevonden.", 'info')
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Fout bij verwijderen aanmelding: {e}", 'error')
            logger.error(f"Fout bij verwijderen aanmelding: {e}")

    return redirect(url_for('admin_dashboard'))


# Graceful shutdown handler
import atexit
import signal

def cleanup():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down application...")
    db_pool.close_all()
    email_queue.email_queue.put(None)  # Signal email worker to stop
    logger.info("Cleanup completed.")

atexit.register(cleanup)

# Handle SIGTERM and SIGINT for graceful shutdown
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    cleanup()
    exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    logger.info("Starting BBQ application with performance optimizations...")
    app.run(debug=True, port=3000, threaded=True)