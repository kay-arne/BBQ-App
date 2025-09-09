"""
Admin routes (protected pages)
"""

import logging
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, url_for, redirect, flash, session
from werkzeug.security import check_password_hash
from app.models.database import get_db_connection
from app.services.email_service import send_payment_confirmation
from app.config import Config

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def login_required(f):
    """Decorator to require login for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('U moet inloggen om deze pagina te bekijken.', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['logged_in'] = True
            flash('Succesvol ingelogd!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'error')
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('logged_in', None)
    flash('U bent uitgelogd.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard"""
    conn = get_db_connection()
    registrations = []
    total_persons = 0
    total_adults = 0
    total_children = 0
    total_due_amount = 0.0
    total_paid_amount = 0.0
    
    if conn:
        try:
            registrations = conn.execute('SELECT * FROM registrations ORDER BY registered_at DESC').fetchall()
            
            for reg in registrations:
                total_adults += reg['persons_adults']
                total_children += reg['persons_children']
                total_persons = total_adults + total_children
                total_due_amount += reg['total_amount']
                total_paid_amount += reg['paid_amount']

        except Exception as e:
            flash(f"Fout bij ophalen aanmeldingen: {e}", 'error')
            logger.error(f"Fout bij ophalen aanmeldingen: {e}")
        finally:
            conn.close()
    else:
        flash("Geen databaseverbinding. Kan aanmeldingen niet ophalen.", 'error')
    
    return render_template(
        'admin.html', 
        registrations=registrations,
        total_persons=total_persons,
        total_adults=total_adults,
        total_children=total_children,
        total_due_amount=total_due_amount,
        total_paid_amount=total_paid_amount,
        bbq_details=Config.BBQ_DETAILS
    )

@admin_bp.route('/add_registration', methods=['POST'])
@login_required
def add_registration():
    """Add manual registration"""
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

    conn = get_db_connection()
    if not conn:
        flash('Database fout: Kan geen verbinding maken.', 'error')
        return redirect(url_for('admin.dashboard'))

    try:
        conn.execute(
            '''INSERT INTO registrations (name, house_number, email, persons_adults, persons_children, allergies_notes, total_amount, bunq_me_url, payment_status, paid_amount) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name, house_number, email, persons_adults, persons_children, allergies_notes, total_amount, bunq_me_url, payment_status, initial_paid_amount)
        )
        conn.commit()
        flash("Aanmelding succesvol toegevoegd.", 'success')
    except Exception as e:
        conn.rollback()
        flash(f"Fout bij toevoegen aanmelding: {e}", 'error')
        logger.error(f"Fout bij toevoegen aanmelding: {e}")
    finally:
        conn.close()

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/update_status/<int:reg_id>', methods=['POST'])
@login_required
def update_registration_status(reg_id):
    """Update registration payment status"""
    new_status = request.form['status']
    
    conn = get_db_connection()
    if not conn:
        flash('Database fout: Kan geen verbinding maken.', 'error')
        return redirect(url_for('admin.dashboard'))

    try:
        current_reg = conn.execute('SELECT * FROM registrations WHERE id = ?', (reg_id,)).fetchone()
        if not current_reg:
            flash("Aanmelding niet gevonden.", 'info')
            conn.close()
            return redirect(url_for('admin.dashboard'))
        
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
            
            # Send payment confirmation email
            if new_status == 'paid' and current_email:
                if not send_payment_confirmation(current_name, current_reg['house_number'], current_email, 
                                               current_reg['persons_adults'], current_reg['persons_children'], 
                                               total_amount_for_reg):
                    flash(f'Fout bij versturen van de betalingsbevestiging naar {current_email}.', 'error')
        else:
            flash("Aanmelding niet gevonden of status/bedrag was al hetzelfde.", 'info')
    except Exception as e:
        conn.rollback()
        flash(f"Fout bij bijwerken status: {e}", 'error')
        logger.error(f"Fout bij bijwerken status: {e}")
    finally:
        conn.close()

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_registration/<int:reg_id>', methods=['POST'])
@login_required
def delete_registration(reg_id):
    """Delete registration"""
    conn = get_db_connection()
    if not conn:
        flash('Database fout: Kan geen verbinding maken.', 'error')
        return redirect(url_for('admin.dashboard'))

    try:
        conn.execute('DELETE FROM registrations WHERE id = ?', (reg_id,))
        conn.commit()
        if conn.total_changes > 0:
            flash("Aanmelding succesvol verwijderd.", 'success')
        else:
            flash("Aanmelding niet gevonden.", 'info')
    except Exception as e:
        conn.rollback()
        flash(f"Fout bij verwijderen aanmelding: {e}", 'error')
        logger.error(f"Fout bij verwijderen aanmelding: {e}")
    finally:
        conn.close()

    return redirect(url_for('admin.dashboard'))


