#!/bin/bash

# Script per il deployment dell'applicazione Edu App Roo su Ubuntu usando Docker

# --- Variabili Configurabili ---
PROJECT_DIR="edu_app_deployment"
DOCKERHUB_USERNAME="albertosiemanuele" # Il tuo username Docker Hub
# Immagini Docker Hub
BACKEND_IMAGE="${DOCKERHUB_USERNAME}/edu-app-backend:latest"
STUDENT_FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/edu-app-frontend-student:latest"
TEACHER_FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/edu-app-frontend-teacher:latest"
DB_IMAGE="postgres:15-alpine"

# --- Funzioni Helper ---
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_dependency() {
    if ! command_exists "$1"; then
        echo "Errore: '$1' non trovato. Per favore, installalo prima di eseguire questo script."
        if [ "$1" == "docker" ]; then
            echo "Puoi installare Docker seguendo la guida ufficiale: https://docs.docker.com/engine/install/ubuntu/"
        elif [ "$1" == "docker-compose" ]; then
            echo "Puoi installare Docker Compose seguendo la guida ufficiale: https://docs.docker.com/compose/install/"
            echo "Nota: Potrebbe essere necessario installare 'docker-compose-plugin' se usi Docker Desktop o versioni recenti."
        fi
        exit 1
    fi
}

# --- Controllo Dipendenze ---
echo "Controllo delle dipendenze..."
check_dependency "docker"
# Docker Compose V2 usa 'docker compose', V1 usa 'docker-compose'
if command_exists "docker-compose"; then
    COMPOSE_CMD="docker-compose"
elif command_exists "docker" && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "Errore: Docker Compose (V1 'docker-compose' o V2 plugin 'docker compose') non trovato."
    echo "Per favore, installalo seguendo la guida ufficiale: https://docs.docker.com/compose/install/"
    exit 1
fi
echo "Dipendenze trovate ($COMPOSE_CMD)."

# --- Creazione Directory e File ---
echo "Creazione della directory di progetto '$PROJECT_DIR'..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1 # Entra nella directory o esci se fallisce

echo "Creazione del file 'docker-compose.prod.yml'..."
cat << EOF > docker-compose.prod.yml
services:
  db:
    image: ${DB_IMAGE}
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - .env.prod # Carica variabili d'ambiente specifiche per la produzione
    environment:
      # Assicurati che queste variabili siano definite nel tuo .env.prod
      - POSTGRES_DB=\${POSTGRES_DB}
      - POSTGRES_USER=\${POSTGRES_USER}
      - POSTGRES_PASSWORD=\${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${POSTGRES_USER} -d \${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped # Riavvia il DB se si ferma inaspettatamente

  backend: # Rinominato da 'web' per chiarezza
    image: ${BACKEND_IMAGE} # Usa l'immagine da Docker Hub
    ports:
      - "8000:8000" # Mappa la porta di Gunicorn
    env_file:
      - .env.prod # Carica variabili d'ambiente specifiche per la produzione
    environment:
      # Assicurati che queste variabili siano definite nel tuo .env.prod
      - SECRET_KEY=\${SECRET_KEY}
      - DEBUG=\${DEBUG} # Dovrebbe essere False in produzione
      - DATABASE_URL=postgres://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@db:5432/\${POSTGRES_DB}
      - DJANGO_ALLOWED_HOSTS=\${DJANGO_ALLOWED_HOSTS} # Configura gli host permessi per la produzione
      - CORS_ALLOWED_ORIGINS=\${CORS_ALLOWED_ORIGINS} # Configura gli origin permessi per la produzione
      # Credenziali Superuser per lo script di entrypoint
      - DJANGO_SUPERUSER_USERNAME=\${DJANGO_SUPERUSER_USERNAME}
      - DJANGO_SUPERUSER_EMAIL=\${DJANGO_SUPERUSER_EMAIL}
      - DJANGO_SUPERUSER_PASSWORD=\${DJANGO_SUPERUSER_PASSWORD}
    depends_on:
      db:
        condition: service_healthy # Attende che il DB sia pronto
    restart: unless-stopped # Riavvia il backend se si ferma inaspettatamente

  frontend-student:
    image: ${STUDENT_FRONTEND_IMAGE} # Usa l'immagine da Docker Hub
    ports:
      - "5175:80" # Mappa la porta di Nginx
    depends_on:
      - backend # Dipende dal backend
    restart: unless-stopped

  frontend-teacher:
    image: ${TEACHER_FRONTEND_IMAGE} # Usa l'immagine da Docker Hub
    ports:
      - "5174:80" # Mappa la porta di Nginx
    depends_on:
      - backend # Dipende dal backend
    restart: unless-stopped

volumes:
  postgres_data: # Volume nominato per persistere i dati del database
EOF

echo "Creazione del file template '.env.prod.template'..."
# Nota: Usiamo \${VAR} per evitare l'espansione immediata delle variabili nello script
cat << 'EOF' > .env.prod.template
# =========================================
# === VARIABILI AMBIENTE DI PRODUZIONE ===
# =========================================
# ATTENZIONE: Copia questo file in .env.prod e modifica i valori
#             con segreti reali prima di avviare i container!

# --- Database Configuration ---
POSTGRES_DB=edu_app_prod_db
POSTGRES_USER=prod_user
# Cambiare questa password con una forte e sicura!
POSTGRES_PASSWORD=changeme_prod_password

# --- Django Settings ---
# Generare una nuova SECRET_KEY per la produzione! Esempio: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY='changeme_replace_with_a_real_production_secret_key'
# Impostare DEBUG a False in produzione per sicurezza e performance!
DEBUG=False
# Impostare gli host permessi (es. il dominio del tuo server, indirizzo IP)
# Esempio: DJANGO_ALLOWED_HOSTS=tuodominio.com,www.tuodominio.com,192.168.1.100
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 # Modifica con i tuoi host/domini reali!
# Impostare gli origin CORS permessi (es. i domini dei tuoi frontend in produzione)
# Esempio: CORS_ALLOWED_ORIGINS=https://studente.tuodominio.com,https://docente.tuodominio.com
CORS_ALLOWED_ORIGINS=http://localhost:5175,http://localhost:5174 # Modifica con i tuoi URL reali!

# --- Superuser Credentials (per lo script di inizializzazione) ---
# Scegliere username e email desiderati per l'admin iniziale
DJANGO_SUPERUSER_USERNAME=admin_prod
DJANGO_SUPERUSER_EMAIL=admin@example.com # Modifica con una email valida
# Cambiare questa password con una forte e sicura!
DJANGO_SUPERUSER_PASSWORD=changeme_admin_prod_password
EOF

# --- Istruzioni per l'utente ---
if [ ! -f ".env.prod" ]; then
    echo "Copiato '.env.prod.template' in '.env.prod'."
    cp .env.prod.template .env.prod
    echo "---------------------------------------------------------------------"
    echo "IMPORTANTE: Modifica il file '.env.prod' ora con i tuoi valori reali!"
    echo "            In particolare, imposta password sicure e configura"
    echo "            DJANGO_ALLOWED_HOSTS e CORS_ALLOWED_ORIGINS."
    echo "---------------------------------------------------------------------"
    read -p "Premi Invio dopo aver modificato e salvato il file .env.prod..."
else
    echo "File '.env.prod' già esistente. Assicurati che sia configurato correttamente."
    read -p "Premi Invio per continuare..."
fi

# --- Avvio dei Container ---
echo "Tentativo di pull delle immagini più recenti da Docker Hub..."
$COMPOSE_CMD -f docker-compose.prod.yml pull

echo "Avvio dei container Docker in background..."
$COMPOSE_CMD -f docker-compose.prod.yml --env-file .env.prod up -d

echo "---------------------------------------------------------------------"
echo "Deployment completato!"
echo "I container dovrebbero essere in esecuzione."
echo ""
echo "Puoi accedere ai servizi (potrebbe richiedere qualche istante per l'avvio completo):"
echo "  - Backend Django (Admin): http://<IP_SERVER_O_DOMINIO>:8000/admin/"
echo "  - Frontend Docente:       http://<IP_SERVER_O_DOMINIO>:5174/"
echo "  - Frontend Studente:      http://<IP_SERVER_O_DOMINIO>:5175/"
echo ""
echo "Credenziali Admin (definite in .env.prod):"
echo "  - Username: \$(grep DJANGO_SUPERUSER_USERNAME .env.prod | cut -d '=' -f2)"
echo "  - Password: \$(grep DJANGO_SUPERUSER_PASSWORD .env.prod | cut -d '=' -f2)"
echo ""
echo "Comandi utili:"
echo "  - Vedere i log: $COMPOSE_CMD -f docker-compose.prod.yml logs -f"
echo "  - Fermare i servizi: cd $PROJECT_DIR && $COMPOSE_CMD -f docker-compose.prod.yml down"
echo "  - Riavviare i servizi: cd $PROJECT_DIR && $COMPOSE_CMD -f docker-compose.prod.yml restart"
echo "---------------------------------------------------------------------"

exit 0