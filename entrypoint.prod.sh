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

# Raccogli i file statici nella directory STATIC_ROOT
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Crea il superutente iniziale se le variabili d'ambiente sono impostate
# e l'utente non esiste già.
# Leggiamo le variabili direttamente (dovrebbero essere state esportate da 'source')
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating initial superuser..."
    python manage.py create_initial_superuser
else
    echo "Superuser environment variables not set or not loaded, skipping superuser creation."
fi

# Ensure media files are readable by other services (like Nginx in frontend)
echo "Setting permissions for media files..."
# o+rX: give read permission to files/dirs, execute permission only to dirs for 'others'
chmod -R o+rX /app/mediafiles || echo "Warning: Failed to set permissions on /app/mediafiles"

# Avvia Gunicorn con ottimizzazioni per server con risorse limitate
echo "Starting Gunicorn with optimizations for low memory server..."
# Ottimizzazioni per server con 1GB di RAM:
# - 1 worker per ridurre l'utilizzo di memoria
# - timeout aumentato a 180s per dare più tempo alle richieste di completarsi
# - max-requests per riavviare i worker periodicamente ed evitare memory leak
# - worker-class gevent per gestire meglio le connessioni concorrenti con meno memoria
# - log-level warning per ridurre la verbosità dei log
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --timeout 180 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --worker-class gevent \
    --log-level warning