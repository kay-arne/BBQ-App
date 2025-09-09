# 🔥 Kamperweg BBQ App

Een moderne webapplicatie voor het beheren van BBQ evenementen en aanmeldingen voor de Kamperweg buurt.

## ✨ Features

- **Aanmeldformulier**: Gebruikers kunnen zich aanmelden voor BBQ evenementen
- **Admin Dashboard**: Beheer aanmeldingen, gebruikers en configuratie
- **Dynamische Configuratie**: Pas kleuren, content en instellingen aan via de admin interface
- **Gebruikersbeheer**: Maak en beheer admin gebruikers
- **E-mail Notificaties**: Automatische bevestigingsmails
- **Responsive Design**: Werkt op alle apparaten

## 🚀 Installatie

### Vereisten
- Python 3.9+
- pip

### Setup
1. Clone de repository:
```bash
git clone <repository-url>
cd kamperweg-bbq-app
```

2. Maak een virtuele omgeving:
```bash
python -m venv venv
source venv/bin/activate  # Op Windows: venv\Scripts\activate
```

3. Installeer dependencies:
```bash
pip install -r requirements.txt
```

4. Maak een `.env` bestand:
```bash
cp config.example .env
```

5. Vul de `.env` bestand in met je instellingen:
```
SECRET_KEY=your-secret-key-here
ADMIN_PASSWORD=your-admin-password
SMTP_SERVER=your-smtp-server
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-password
```

6. Start de applicatie:
```bash
python app.py
```

De applicatie is nu beschikbaar op `http://localhost:3000`

## 📁 Project Structuur

```
kamperweg-bbq-app/
├── app/                    # Flask applicatie structuur
│   ├── models/            # Database modellen
│   ├── routes/            # Route handlers
│   ├── services/          # Business logic
│   └── utils/             # Utility functies
├── static/                # Statische bestanden (CSS, JS, afbeeldingen)
├── templates/             # HTML templates
├── app.py                 # Hoofdapplicatie
├── requirements.txt       # Python dependencies
└── README.md             # Dit bestand
```

## 🔧 Configuratie

De applicatie heeft een uitgebreide configuratie interface waar je kunt aanpassen:

- **Variabelen**: BBQ datum, locatie, prijzen
- **Content**: Hoofdtekst en beschrijvingen
- **Stijl**: Kleuren en achtergrondafbeeldingen
- **E-mail**: SMTP instellingen
- **Gebruikers**: Admin gebruikersbeheer

## 🎨 Customisatie

De applicatie ondersteunt volledige customisatie via de admin interface:

- **Kleuren**: Pas primaire en secundaire kleuren aan
- **Achtergrond**: Upload eigen achtergrondafbeeldingen
- **Content**: Bewerk alle teksten via de WYSIWYG editor
- **Variabelen**: Stel datums, prijzen en locaties in

## 🔐 Beveiliging

- CSRF bescherming op alle formulieren
- Wachtwoord hashing met PBKDF2
- Case-insensitive login
- Session management

## 📱 Responsive Design

De applicatie is volledig responsive en werkt optimaal op:
- Desktop computers
- Tablets
- Smartphones

## 🚀 Deployment

Voor productie deployment:

1. Gebruik een productie WSGI server (bijv. Gunicorn)
2. Configureer een reverse proxy (bijv. Nginx)
3. Stel productie environment variabelen in
4. Gebruik een productie database (PostgreSQL)

## 📝 Licentie

Dit project is ontwikkeld voor de Kamperweg buurt.

## 🤝 Bijdragen

Voor vragen of suggesties, neem contact op met de ontwikkelaar.

---

**Ontwikkeld met ❤️ voor de Kamperweg buurt**