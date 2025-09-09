"""
API routes
"""

import logging
from flask import Blueprint, request, jsonify, flash, current_app
from flask_wtf.csrf import exempt
from app.models.database import get_db_connection
from app.services.validation_service import validate_registration_data
from app.services.email_service import send_registration_confirmation, send_organizer_notification
from app.config import Config

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/register', methods=['POST'])
@exempt
def register_and_pay():
    """Handle registration and payment URL generation"""
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
    total_amount = persons_adults * Config.BBQ_DETAILS["price_per_adult"]

    payment_url = ""
    try:
        description = f"BBQ {name} - Huisnr: {house_number}"
        payment_url = f"{Config.BUNQ_ME_BASE_URL}/{total_amount:.2f}/{description.replace(' ', '%20')}"

        conn = get_db_connection()
        if not conn:
            flash('Database fout: Kan geen verbinding maken.', 'error')
            return jsonify({'message': 'Fout bij opslaan aanmelding (database).'}), 500

        try:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO registrations (name, house_number, email, persons_adults, persons_children, allergies_notes, total_amount, bunq_me_url, payment_status, paid_amount) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, house_number, email, persons_adults, persons_children, allergies_notes, total_amount, payment_url, 'pending', 0.0)
            )
            registration_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Aanmelding opgeslagen met ID: {registration_id} voor {name} (Kamperweg {house_number})")
            flash('Aanmelding succesvol opgeslagen.', 'success')

            # Send emails
            if email:
                if not send_registration_confirmation(name, house_number, email, persons_adults, persons_children, total_amount):
                    flash(f'Fout bij versturen bevestigingsmail naar {email}.', 'error')

            if not send_organizer_notification(name, house_number, email, persons_adults, persons_children, 
                                             allergies_notes, total_amount, payment_url, registration_id):
                flash(f'Fout bij versturen notificatiemail naar {Config.ORGANIZER_EMAIL}.', 'error')

            return jsonify({
                'message': 'Aanmelding succesvol! Je wordt nu doorgestuurd naar de betaalpagina.',
                'paymentUrl': payment_url,
                'registrationId': registration_id
            })

        except Exception as e:
            conn.rollback()
            logger.error(f"Database fout bij opslaan aanmelding: {e}")
            flash(f'Databasefout bij aanmelding: {e}.', 'error')
            return jsonify({'message': f'Fout bij opslaan aanmelding: {e}'}), 500
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Algemene fout bij aanmelding: {e}")
        flash(f'Er is een onverwachte fout opgetreden: {e}.', 'error')
        return jsonify({'message': f'Er is een onverwachte fout opgetreden: {e}'}), 500

@api_bp.route('/registration/<int:reg_id>', methods=['GET'])
@exempt
def get_registration_details(reg_id):
    """Get registration details by ID"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database fout: Kan geen verbinding maken.'}), 500
    try:
        registration = conn.execute('SELECT * FROM registrations WHERE id = ?', (reg_id,)).fetchone()
        if registration:
            return jsonify(dict(registration)), 200
        else:
            return jsonify({'message': 'Aanmelding niet gevonden.'}), 404
    except Exception as e:
        logger.error(f"Fout bij ophalen registratie details: {e}")
        return jsonify({'message': 'Fout bij ophalen details.'}), 500
    finally:
        conn.close()
