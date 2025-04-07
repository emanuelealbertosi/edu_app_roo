#!/bin/bash

# Script interattivo per creare .env.prod e avviare Docker Compose
# usando un file docker-compose.prod.static.yml preesistente.

# --- Variabili Configurabili ---
PROJECT_DIR_NAME="edu_app_deployment" # Nome della directory
# Ottieni il percorso assoluto della directory dello script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR="${SCRIPT_DIR}/${PROJECT_DIR_NAME}" # Percorso assoluto della directory di deployment
COMPOSE_FILE_NAME="docker-compose.prod.static.yml" # Nome del file compose statico
COMPOSE_FILE_PATH="${PROJECT_DIR}/${COMPOSE_FILE_NAME}"
ENV_FILE_PATH="${PROJECT_DIR}/.env.prod"

# --- Funzioni Helper ---
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_dependency() {
    if ! command_exists "$1"; then
        echo "Errore: '$1' non trovato. Per favore, installalo prima di eseguire questo script."
        exit 1
    fi
}

generate_secret_key() {
    if command_exists openssl; then
        openssl rand -base64 48
    elif [ -e /dev/urandom ]; then
         head /dev/urandom | tr -dc A-Za-z0-9 | head -c 50 ; echo ''
    else
        date +%s | sha256sum | base64 | head -c 50 ; echo ''
        echo "Attenzione: Chiave segreta generata con metodo di fallback meno sicuro."
    fi
}

# --- Controllo Dipendenze ---
echo "Controllo delle dipendenze..."
check_dependency "docker"
if command_exists "docker-compose"; then
    COMPOSE_CMD="docker-compose"
elif command_exists "docker" && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "Errore: Docker Compose non trovato."
    exit 1
fi
echo "Dipendenze trovate ($COMPOSE_CMD)."

# --- Creazione Directory ---
echo "Assicurarsi che la directory di progetto '$PROJECT_DIR_NAME' esista..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1
echo "Directory di lavoro corrente: $(pwd)"

# --- Verifica Esistenza File Compose Statico ---
if [ ! -f "$COMPOSE_FILE_PATH" ]; then
    echo "Errore: File Docker Compose statico '${COMPOSE_FILE_NAME}' non trovato in $(pwd)."
    echo "Per favore, copia il file '${COMPOSE_FILE_NAME}' in questa directory prima di eseguire lo script."
    exit 1
fi
echo "File Docker Compose statico trovato: ${COMPOSE_FILE_PATH}"

# --- Raccolta Interattiva delle Variabili d'Ambiente ---
echo "---------------------------------------------------------------------"
echo "Configurazione delle variabili d'ambiente per la produzione (.env.prod)"
echo "Premi Invio per usare i valori predefiniti suggeriti tra parentesi."
echo "ATTENZIONE: Usa password FORTI e UNICHE per il database e l'admin!"
echo "---------------------------------------------------------------------"

# Indirizzo IP del Server
read -p "Inserisci l'indirizzo IP pubblico di questo server Ubuntu: " SERVER_IP
if [ -z "$SERVER_IP" ]; then
    echo "Errore: L'indirizzo IP del server è necessario."
    exit 1
fi

# Database
read -p "Nome database PostgreSQL [edu_app_prod_db]: " POSTGRES_DB_VAR
POSTGRES_DB_VAR=${POSTGRES_DB_VAR:-edu_app_prod_db}

read -p "Utente database PostgreSQL [prod_user]: " POSTGRES_USER_VAR
POSTGRES_USER_VAR=${POSTGRES_USER_VAR:-prod_user}

read -sp "Password database PostgreSQL (NESSUN DEFAULT - OBBLIGATORIA!): " POSTGRES_PASSWORD_VAR
echo
if [ -z "$POSTGRES_PASSWORD_VAR" ]; then
    echo "Errore: La password del database è obbligatoria."
    exit 1
fi

# Django Settings
echo "Generazione SECRET_KEY..."
DEFAULT_SECRET_KEY=$(generate_secret_key)
read -p "Django SECRET_KEY [Generata automaticamente]: " SECRET_KEY_VAR
SECRET_KEY_VAR=${SECRET_KEY_VAR:-$DEFAULT_SECRET_KEY}

DEBUG_VAR=False
echo "DEBUG impostato a: $DEBUG_VAR"

DEFAULT_ALLOWED_HOSTS="*,${SERVER_IP}"
read -p "Host/Domini permessi per Django (separati da virgola) [${DEFAULT_ALLOWED_HOSTS}]: " DJANGO_ALLOWED_HOSTS_VAR
DJANGO_ALLOWED_HOSTS_VAR=${DJANGO_ALLOWED_HOSTS_VAR:-${DEFAULT_ALLOWED_HOSTS}}

DEFAULT_CORS_ORIGINS="http://${SERVER_IP}:5174,http://${SERVER_IP}:5175"
read -p "Origini CORS permesse (separati da virgola) [${DEFAULT_CORS_ORIGINS}]: " CORS_ALLOWED_ORIGINS_VAR
CORS_ALLOWED_ORIGINS_VAR=${CORS_ALLOWED_ORIGINS_VAR:-${DEFAULT_CORS_ORIGINS}}

# Superuser
read -p "Username Superuser Django [admin_prod]: " DJANGO_SUPERUSER_USERNAME_VAR
DJANGO_SUPERUSER_USERNAME_VAR=${DJANGO_SUPERUSER_USERNAME_VAR:-admin_prod}

read -p "Email Superuser Django [admin@example.com]: " DJANGO_SUPERUSER_EMAIL_VAR
DJANGO_SUPERUSER_EMAIL_VAR=${DJANGO_SUPERUSER_EMAIL_VAR:-admin@example.com}

read -sp "Password Superuser Django (NESSUN DEFAULT - OBBLIGATORIA!): " DJANGO_SUPERUSER_PASSWORD_VAR
echo
if [ -z "$DJANGO_SUPERUSER_PASSWORD_VAR" ]; then
    echo "Errore: La password del superuser è obbligatoria."
    exit 1
fi

# --- Creazione File .env.prod (Sovrascrive se esiste) ---
echo "Creazione/Sovrascrittura del file '${ENV_FILE_PATH}'..."
# Costruisci DATABASE_URL DENTRO lo script, prima di scrivere il file .env
DATABASE_URL_VAR="postgres://${POSTGRES_USER_VAR}:${POSTGRES_PASSWORD_VAR}@db:5432/${POSTGRES_DB_VAR}"

cat << EOF > "${ENV_FILE_PATH}"
# File generato automaticamente dallo script deploy_env_only.sh
# Data: $(date)

# --- Database Configuration ---
POSTGRES_DB=${POSTGRES_DB_VAR}
POSTGRES_USER=${POSTGRES_USER_VAR}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD_VAR}

# --- Django Settings ---
# NOTA: DATABASE_URL viene letta da Django/dj-database-url
DATABASE_URL=${DATABASE_URL_VAR}
SECRET_KEY='${SECRET_KEY_VAR}' # Usiamo apici singoli per sicurezza
DEBUG=${DEBUG_VAR}
DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS_VAR}
CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS_VAR}

# --- Superuser Credentials (usate da entrypoint.prod.sh) ---
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME_VAR}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL_VAR}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD_VAR}
EOF

echo "File '${ENV_FILE_PATH}' creato/aggiornato con successo."

# --- Fermare e Rimuovere Vecchi Container/Volumi ---
echo "Fermare e rimuovere eventuali container e volumi precedenti associati a ${COMPOSE_FILE_NAME}..."
$COMPOSE_CMD -f "${COMPOSE_FILE_PATH}" down -v --remove-orphans

# --- Avvio dei Container ---
echo "Tentativo di pull delle immagini più recenti da Docker Hub..."
# Usiamo il file statico per il pull
$COMPOSE_CMD -f "${COMPOSE_FILE_PATH}" pull

echo "Avvio dei container Docker usando ${COMPOSE_FILE_NAME} e ${ENV_FILE_PATH} (forzando il pull)..."
# Usiamo il file statico, specifichiamo --env-file e aggiungiamo --pull always
$COMPOSE_CMD -f "${COMPOSE_FILE_PATH}" --env-file "${ENV_FILE_PATH}" up -d --force-recreate --pull always

echo "---------------------------------------------------------------------"
echo "Deployment avviato!"
echo "I container dovrebbero essere in esecuzione."
echo ""
echo "Puoi accedere ai servizi (potrebbe richiedere qualche istante per l'avvio completo):"
echo "  - Backend Django (Admin): http://${SERVER_IP}:8000/admin/"
echo "  - Frontend Docente:       http://${SERVER_IP}:5174/"
echo "  - Frontend Studente:      http://${SERVER_IP}:5175/"
echo ""
echo "Credenziali Admin (definite durante l'esecuzione dello script):"
echo "  - Username: ${DJANGO_SUPERUSER_USERNAME_VAR}"
echo "  - Password: (quella inserita durante l'esecuzione dello script)"
echo ""
echo "Comandi utili:"
echo "  - Vedere i log: $COMPOSE_CMD -f ${COMPOSE_FILE_PATH} logs -f"
echo "  - Fermare i servizi: cd ${PROJECT_DIR} && $COMPOSE_CMD -f ${COMPOSE_FILE_PATH} down"
echo "  - Riavviare i servizi: cd ${PROJECT_DIR} && $COMPOSE_CMD -f ${COMPOSE_FILE_PATH} restart"
echo "---------------------------------------------------------------------"

exit 0