#!/bin/sh

# Attendi che il database sia pronto (opzionale ma consigliato)
# Questo richiede netcat (nc), che potrebbe dover essere aggiunto al Dockerfile
# echo "Waiting for postgres..."
# while ! nc -z db 5432; do
#   sleep 0.1
# done
# echo "PostgreSQL started"

# Esegui le migrazioni del database
echo "Applying database migrations..."
python manage.py migrate --noinput

# Raccogli i file statici (anche se serviti da Nginx, è buona pratica)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput --clear

# Crea il superutente iniziale se le variabili d'ambiente sono impostate
# e l'utente non esiste già.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating initial superuser..."
    python manage.py create_initial_superuser
else
    echo "Superuser environment variables not set, skipping superuser creation."
fi

# Avvia Gunicorn
echo "Starting Gunicorn..."
# Nota: Assicurati che 'config.wsgi:application' sia il percorso corretto per il tuo file wsgi.py
# Puoi regolare il numero di workers (-w) in base alle risorse del tuo server
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3