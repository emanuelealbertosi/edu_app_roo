#!/bin/bash

# Script interattivo per il deployment dell'applicazione Edu App Roo su Ubuntu usando Docker
# Chiede sempre le variabili, sovrascrive .env.prod e avvia i container usando env_file.
# Rimuove il volume del DB ad ogni esecuzione per garantire uno stato pulito.

# --- Variabili Configurabili (Immagini Docker Hub) ---
DOCKERHUB_USERNAME="albertosiemanuele" # Il tuo username Docker Hub
BACKEND_IMAGE="${DOCKERHUB_USERNAME}/edu-app-backend:latest"
STUDENT_FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/edu-app-frontend-student:latest"
TEACHER_FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/edu-app-frontend-teacher:latest"
DB_IMAGE="postgres:15-alpine"
PROJECT_DIR="edu_app_deployment"

# --- Funzioni Helper ---
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_dependency() {
    if ! command_exists "$1"; then
        echo "Errore: '$1' non trovato. Per favore, installalo prima di eseguire questo script."
        if [ "$1" == "docker" ]; then
            echo "Puoi installare Docker seguendo la guida ufficiale: https://docs.docker.com/engine/install/ubuntu/"
        elif [ "$1" == "docker-compose" ] || [ "$1" == "docker compose" ]; then
             echo "Puoi installare Docker Compose seguendo la guida ufficiale: https://docs.docker.com/compose/install/"
             echo "Nota: Potrebbe essere necessario installare 'docker-compose-plugin' se usi Docker Desktop o versioni recenti."
        fi
        exit 1
    fi
}

generate_secret_key() {
    # Metodo più robusto e comune su Linux
    if command_exists openssl; then
        openssl rand -base64 48
    elif [ -e /dev/urandom ]; then
         head /dev/urandom | tr -dc A-Za-z0-9 | head -c 50 ; echo ''
    else
        # Fallback molto semplice se tutto il resto fallisce
        date +%s | sha256sum | base64 | head -c 50 ; echo ''
        echo "Attenzione: Chiave segreta generata con metodo di fallback meno sicuro."
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

# --- Creazione Directory ---
echo "Creazione della directory di progetto '$PROJECT_DIR' (se non esiste)..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1 # Entra nella directory o esci se fallisce

# --- Raccolta Interattiva delle Variabili d'Ambiente ---
echo "---------------------------------------------------------------------"
echo "Configurazione delle variabili d'ambiente per la produzione (.env.prod)"
echo "Premi Invio per usare i valori predefiniti suggeriti tra parentesi."
echo "ATTENZIONE: Usa password FORTI e UNICHE per il database e l'admin!"
echo "---------------------------------------------------------------------"

# Indirizzo IP del Server
read -p "Inserisci l'indirizzo IP pubblico di questo server Ubuntu: " SERVER_IP
if [ -z "$SERVER_IP" ]; then
    echo "Errore: L'indirizzo IP del server è necessario per configurare CORS e ALLOWED_HOSTS."
    exit 1
fi

# Database
read -p "Nome database PostgreSQL [edu_app_prod_db]: " POSTGRES_DB_VAR # Usiamo _VAR per evitare conflitti
POSTGRES_DB_VAR=${POSTGRES_DB_VAR:-edu_app_prod_db}

read -p "Utente database PostgreSQL [prod_user]: " POSTGRES_USER_VAR # Usiamo _VAR
POSTGRES_USER_VAR=${POSTGRES_USER_VAR:-prod_user}

read -sp "Password database PostgreSQL (NESSUN DEFAULT - OBBLIGATORIA!): " POSTGRES_PASSWORD_VAR # Usiamo _VAR
echo # Aggiunge newline dopo input password
if [ -z "$POSTGRES_PASSWORD_VAR" ]; then
    echo "Errore: La password del database è obbligatoria."
    exit 1
fi

# Django Settings
# Genera una chiave segreta di default
echo "Generazione SECRET_KEY..."
DEFAULT_SECRET_KEY=$(generate_secret_key)
read -p "Django SECRET_KEY [Generata automaticamente]: " SECRET_KEY_VAR # Usiamo _VAR
SECRET_KEY_VAR=${SECRET_KEY_VAR:-$DEFAULT_SECRET_KEY}

# DEBUG deve essere False in produzione
DEBUG_VAR=False # Usiamo _VAR
echo "DEBUG impostato a: $DEBUG_VAR (non modificabile per produzione)"

# Suggerisci ALLOWED_HOSTS con l'IP fornito e '*'
DEFAULT_ALLOWED_HOSTS="*,${SERVER_IP}"
read -p "Host/Domini permessi per Django (separati da virgola) [Default: ${DEFAULT_ALLOWED_HOSTS}]: " DJANGO_ALLOWED_HOSTS_VAR # Usiamo _VAR
DJANGO_ALLOWED_HOSTS_VAR=${DJANGO_ALLOWED_HOSTS_VAR:-${DEFAULT_ALLOWED_HOSTS}}

# Suggerisci CORS_ALLOWED_ORIGINS con l'IP fornito
DEFAULT_CORS_ORIGINS="http://${SERVER_IP}:5174,http://${SERVER_IP}:5175"
echo "Configurazione CORS: Verranno usati gli URL basati sull'IP fornito."
echo "Se userai domini e HTTPS in futuro, dovrai aggiornare questo valore manualmente nel file .env.prod."
read -p "Origini CORS permesse (separati da virgola) [Default: ${DEFAULT_CORS_ORIGINS}]: " CORS_ALLOWED_ORIGINS_VAR # Usiamo _VAR
CORS_ALLOWED_ORIGINS_VAR=${CORS_ALLOWED_ORIGINS_VAR:-${DEFAULT_CORS_ORIGINS}}

# Superuser
read -p "Username Superuser Django [admin_prod]: " DJANGO_SUPERUSER_USERNAME_VAR # Usiamo _VAR
DJANGO_SUPERUSER_USERNAME_VAR=${DJANGO_SUPERUSER_USERNAME_VAR:-admin_prod}

read -p "Email Superuser Django [admin@example.com]: " DJANGO_SUPERUSER_EMAIL_VAR # Usiamo _VAR
DJANGO_SUPERUSER_EMAIL_VAR=${DJANGO_SUPERUSER_EMAIL_VAR:-admin@example.com}

read -sp "Password Superuser Django (NESSUN DEFAULT - OBBLIGATORIA!): " DJANGO_SUPERUSER_PASSWORD_VAR # Usiamo _VAR
echo # Aggiunge newline dopo input password
if [ -z "$DJANGO_SUPERUSER_PASSWORD_VAR" ]; then
    echo "Errore: La password del superuser è obbligatoria."
    exit 1
fi

# --- Creazione File .env.prod (Sovrascrive se esiste) ---
echo "Creazione/Sovrascrittura del file '.env.prod' con i valori forniti..."
cat << EOF > .env.prod
# File generato automaticamente dallo script deploy_on_ubuntu.sh
# Data: $(date)

# --- Database Configuration ---
POSTGRES_DB=${POSTGRES_DB_VAR}
POSTGRES_USER=${POSTGRES_USER_VAR}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD_VAR}

# --- Django Settings ---
SECRET_KEY='${SECRET_KEY_VAR}' # Apici singoli per gestire caratteri speciali
DEBUG=${DEBUG_VAR}
DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS_VAR}
CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS_VAR}

# --- Superuser Credentials ---
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME_VAR}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL_VAR}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD_VAR}
EOF

echo "File '.env.prod' creato/aggiornato con successo."

# --- Creazione File docker-compose.prod.yml (se non esiste) ---
# Assicurati che il file docker-compose.prod.yml sia presente o crealo
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Creazione del file 'docker-compose.prod.yml'..."
    cat <<-EOF > docker-compose.prod.yml
services:
  db:
    image: ${DB_IMAGE}
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - .env.prod
    # La sezione environment qui è ridondante ma non dannosa
    environment:
      - POSTGRES_DB=\${POSTGRES_DB}
      - POSTGRES_USER=\${POSTGRES_USER}
      - POSTGRES_PASSWORD=\${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  backend:
    image: ${BACKEND_IMAGE}
    ports:
      - "8000:8000"
    env_file:
      - .env.prod # Usa .env.prod per caricare le variabili
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  frontend-student:
    image: ${STUDENT_FRONTEND_IMAGE}
    ports:
      - "5175:80"
    depends_on:
      - backend
    restart: unless-stopped

  frontend-teacher:
    image: ${TEACHER_FRONTEND_IMAGE}
    ports:
      - "5174:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
EOF
    echo "File 'docker-compose.prod.yml' creato."
else
    echo "File 'docker-compose.prod.yml' già esistente, non sovrascritto."
fi

# --- Fermare e Rimuovere Vecchi Container/Volumi ---
echo "Fermare e rimuovere eventuali container e volumi precedenti..."
$COMPOSE_CMD -f docker-compose.prod.yml down -v --remove-orphans

# --- Avvio dei Container ---
echo "Tentativo di pull delle immagini più recenti da Docker Hub..."
$COMPOSE_CMD -f docker-compose.prod.yml pull

echo "Avvio dei container Docker in background (potrebbe richiedere tempo)..."
# Usa --env-file per passare esplicitamente il file .env.prod
$COMPOSE_CMD -f docker-compose.prod.yml --env-file .env.prod up -d --force-recreate

echo "---------------------------------------------------------------------"
echo "Deployment completato!"
echo "I container dovrebbero essere in esecuzione."
echo ""
echo "Puoi accedere ai servizi (potrebbe richiedere qualche istante per l'avvio completo):"
echo "  - Backend Django (Admin): http://${SERVER_IP}:8000/admin/"
echo "  - Frontend Docente:       http://${SERVER_IP}:5174/"
echo "  - Frontend Studente:      http://${SERVER_IP}:5175/"
echo ""
echo "Credenziali Admin (definite durante l'esecuzione dello script):"
echo "  - Username: ${DJANGO_SUPERUSER_USERNAME_VAR}" # Legge variabile dallo script
echo "  - Password: (quella inserita durante l'esecuzione dello script)"
echo ""
echo "Comandi utili:"
echo "  - Vedere i log: $COMPOSE_CMD -f docker-compose.prod.yml logs -f"
echo "  - Fermare i servizi: cd $PROJECT_DIR && $COMPOSE_CMD -f docker-compose.prod.yml down"
echo "  - Riavviare i servizi: cd $PROJECT_DIR && $COMPOSE_CMD -f docker-compose.prod.yml restart"
echo "---------------------------------------------------------------------"

exit 0