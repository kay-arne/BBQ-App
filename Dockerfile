# Gebruik een officiële Python runtime als basisimage
FROM --platform=linux/amd64 python:3.9-slim-buster

# Stel de werkmap in de container in
WORKDIR /app

# Kopieer de requirements.txt en installeer afhankelijkheden
# Dit is een geoptimaliseerde stap om de Docker build cache te benutten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van je applicatiecode naar de container
COPY . .

# Stel omgevingsvariabelen in (voor Flask en Gunicorn)
# FLASK_APP is nodig voor Flask, maar Gunicorn start direct app.py
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=0

# Poort waarop Gunicorn zal luisteren
EXPOSE 5000

# Commando om de applicatie te starten met Gunicorn
# 'app:app' verwijst naar het 'app' object in 'app.py'
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]