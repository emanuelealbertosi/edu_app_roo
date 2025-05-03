# Usa un'immagine Python ufficiale come immagine base
FROM python:3.11-slim

# Imposta variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Imposta la directory di lavoro nel container
WORKDIR /app

# Installa le dipendenze di sistema necessarie per psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    # Pulisci apt cache
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get install -y --no-install-recommends cron nano \
    # Pulisci apt cache
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Copia il file dei requisiti nella directory di lavoro
COPY requirements.txt /app/

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia lo script di entrypoint
COPY entrypoint.prod.sh /app/entrypoint.prod.sh
# Assicurati che sia eseguibile (anche se lo abbiamo fatto sull'host, è buona norma ripeterlo)
RUN chmod +x /app/entrypoint.prod.sh

# Copia il resto del codice dell'applicazione nella directory di lavoro
COPY . /app/

# Configura Cron
COPY crontab.txt /etc/cron.d/django-cron
RUN chmod 0644 /etc/cron.d/django-cron \
    && crontab /etc/cron.d/django-cron \
    # Crea directory e file di log per cron
    && mkdir -p /app/logs \
    && touch /app/logs/cron.log \
    && chmod 666 /app/logs/cron.log

# Crea la directory per i file temporanei di upload (non nel volume) e imposta permessi ampi per debug
RUN mkdir -p /app/tmp_uploads_non_volume && chmod -R 777 /app/tmp_uploads_non_volume

# Esponi la porta su cui Gunicorn sarà in ascolto
EXPOSE 8000

# Imposta lo script di entrypoint come comando di avvio del container
ENTRYPOINT ["/app/entrypoint.prod.sh"]