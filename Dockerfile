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
    && rm -rf /var/lib/apt/lists/*

# Copia il file dei requisiti nella directory di lavoro
COPY requirements.txt /app/

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice dell'applicazione nella directory di lavoro
COPY . /app/

# Esponi la porta su cui Gunicorn (o il server di sviluppo) sarà in ascolto
EXPOSE 8000

# Comando per eseguire l'applicazione (usiamo il server di sviluppo per ora,
# per produzione si dovrebbe usare Gunicorn o uWSGI)
# Assicurati che le migrazioni siano applicate all'avvio o separatamente
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]