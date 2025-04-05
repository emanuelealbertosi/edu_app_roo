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

# Copia lo script di entrypoint
COPY entrypoint.prod.sh /app/entrypoint.prod.sh
# Assicurati che sia eseguibile (anche se lo abbiamo fatto sull'host, è buona norma ripeterlo)
RUN chmod +x /app/entrypoint.prod.sh

# Copia il resto del codice dell'applicazione nella directory di lavoro
COPY . /app/

# Esponi la porta su cui Gunicorn sarà in ascolto
EXPOSE 8000

# Imposta lo script di entrypoint come comando di avvio del container
ENTRYPOINT ["/app/entrypoint.prod.sh"]