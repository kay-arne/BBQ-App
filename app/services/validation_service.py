"""
Input validation service
"""

import re
import logging

logger = logging.getLogger(__name__)

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


