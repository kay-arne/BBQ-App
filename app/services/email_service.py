"""
Email service for sending notifications
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import Config

logger = logging.getLogger(__name__)

def send_email(to_email, subject, body_html, is_html=True):
    """Send email notification"""
    if not all([Config.SMTP_SERVER, Config.SMTP_PORT, Config.SMTP_USERNAME, Config.SMTP_PASSWORD]):
        logger.warning("E-mail configuratie onvolledig. E-mail kan niet worden verstuurd.")
        return False
    if not to_email:
        logger.warning("Geen e-mailadres opgegeven, e-mail kan niet worden verstuurd.")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = Config.SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject

        if is_html:
            msg.attach(MIMEText(body_html, 'html'))
        else:
            msg.attach(MIMEText(body_html, 'plain'))

        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"E-mail succesvol verstuurd naar {to_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(f"SMTP Authenticatie fout: Controleer gebruikersnaam en wachtwoord/app-wachtwoord voor {Config.SMTP_USERNAME}.")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP Verbindingsfout met {Config.SMTP_SERVER}:{Config.SMTP_PORT}: {e}. Controleer server en poort.")
        return False
    except Exception as e:
        logger.error(f"Algemene fout bij versturen e-mail naar {to_email}: {e}")
        return False

def send_registration_confirmation(name, house_number, email, persons_adults, persons_children, total_amount):
    """Send registration confirmation email to user"""
    if not email:
        return False
        
    subject = "Bevestiging aanmelding Buurt BBQ"
    body = f"""
    <html>
    <body>
        <p>Beste {name} (Kamperweg {house_number}),</p>
        <p>Hartelijk dank voor je aanmelding voor de Buurt BBQ!</p>
        <p>Je hebt je aangemeld voor <strong>{persons_adults} volwassene(n)</strong> en <strong>{persons_children} kind(eren)</strong>.</p>
        <p>Het totaalbedrag voor de volwassenen is <strong>€{total_amount:.2f}</strong>.</p>
        <p>Uw aanmelding en betaling worden nu door ons geverifieerd. Zodra alles in orde is, ontvangt u een aparte e-mail met een definitieve bevestiging.</p>
        <p>Datum BBQ: {Config.BBQ_DETAILS["date"]}. Locatie: {Config.BBQ_DETAILS["location"]}.</p>
        <p>Uiterste opgavedatum: {Config.BBQ_DETAILS["deadline"]}.</p>
        <p>We kijken ernaar uit u te zien!</p>
        <p>Met hartelijke groet,</p>
        <p>Bestuur buurt Kamperweg</p>
    </body>
    </html>
    """
    return send_email(email, subject, body)

def send_organizer_notification(name, house_number, email, persons_adults, persons_children, 
                               allergies_notes, total_amount, payment_url, registration_id):
    """Send notification email to organizer"""
    if not Config.ORGANIZER_EMAIL:
        return False
        
    subject = f"NIEUWE BBQ AANMELDING: {name} (Kamperweg {house_number})"
    body = f"""
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
                <td>Kamperweg {house_number}</td>
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
                <td><strong>Betalingsstatus (initieel):</strong></td>
                <td>Pending (via Bunq.me)</td>
            </tr>
            <tr>
                <td><strong>Bunq.me Link:</strong></td>
                <td><a href="{payment_url}">{payment_url}</a></td>
            </tr>
            <tr>
                <td><strong>Interne Registratie ID:</strong></td>
                <td>{registration_id}</td>
            </tr>
        </table>
        
        <p>Controleer de betaling handmatig in je Bunq app en werk de status bij in het admin-paneel.</p>
        
        <p>Met vriendelijke groet,</p>
        <p>Je BBQ Aanmeld Applicatie</p>
    </body>
    </html>
    """
    return send_email(Config.ORGANIZER_EMAIL, subject, body)

def send_payment_confirmation(name, house_number, email, persons_adults, persons_children, total_amount):
    """Send payment confirmation email to user"""
    if not email:
        return False
        
    subject = "Bevestiging betaling Buurt BBQ verwerkt"
    body = f"""
    <html>
    <body>
        <p>Beste {name} (Kamperweg {house_number}),</p>
        <p>Goed nieuws! Uw betaling van <strong>€{total_amount:.2f}</strong> voor de Buurt BBQ is zojuist door de organisatie <strong>verwerkt en bevestigd</strong>.</p>
        <p>U bent nu officieel aangemeld voor {persons_adults} volwassene(n) en {persons_children} kind(eren).</p>
        <p>Wij kijken ernaar uit u te zien op ons tuinfeest op <strong>{Config.BBQ_DETAILS["date"]}</strong>!</p>
        <p>Met vriendelijke groet,</p>
        <p>Bestuur buurt Kamperweg</p>
    </body>
    </html>
    """
    return send_email(email, subject, body)


