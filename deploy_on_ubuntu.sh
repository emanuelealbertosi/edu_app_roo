# aggiornamento 11:28
#!/bin/bash

# Script interattivo per il deployment dell'applicazione Edu App Roo su Ubuntu usando Docker
# Chiede sempre le variabili, crea/sovrascrive .env.prod e docker-compose.prod.yml,
# e avvia i container usando env_file esplicito.
# Rimuove il volume del DB ad ogni esecuzione per garantire uno stato pulito.

# --- Variabili Configurabili (Immagini Docker Hub) ---
DOCKERHUB_USERNAME="albertosiemanuele" # Il tuo username Docker Hub
BACKEND_IMAGE="${DOCKERHUB_USERNAME}/edu-app-backend:latest"
STUDENT_FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/edu-app-frontend-student:latest"
TEACHER_FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/edu-app-frontend-teacher:latest"
DB_IMAGE="postgres:15-alpine"
PROJECT_DIR_NAME="edu_app_deployment" # Nome della directory
# Ottieni il percorso assoluto della directory dello script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR="${SCRIPT_DIR}/${PROJECT_DIR_NAME}" # Percorso assoluto della directory di deployment

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
echo "Creazione della directory di progetto '$PROJECT_DIR_NAME' (se non esiste)..."
# Crea la directory relativa alla posizione dello script, non alla CWD
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1 # Entra nella directory o esci se fallisce
echo "Directory di lavoro corrente: $(pwd)"


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
ENV_FILE_PATH="${PROJECT_DIR}/.env.prod" # Percorso assoluto
echo "Creazione/Sovrascrittura del file '${ENV_FILE_PATH}' con i valori forniti..."
cat << EOF > "${ENV_FILE_PATH}"
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

# Costruisci DATABASE_URL
DATABASE_URL_VAR="postgres://${POSTGRES_USER_VAR}:${POSTGRES_PASSWORD_VAR}@db:5432/${POSTGRES_DB_VAR}"
DATABASE_URL=${DATABASE_URL_VAR}

# --- Superuser Credentials ---
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME_VAR}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL_VAR}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD_VAR}
EOF

echo "File '${ENV_FILE_PATH}' creato/aggiornato con successo."

# --- Creazione File docker-compose.prod.yml da Template ---
TEMPLATE_FILE_PATH="${SCRIPT_DIR}/docker-compose.prod.yml.template" # Percorso del template
COMPOSE_FILE_PATH="${PROJECT_DIR}/docker-compose.prod.yml" # Percorso del file finale

if [ ! -f "$TEMPLATE_FILE_PATH" ]; then
    echo "Errore: File template '${TEMPLATE_FILE_PATH}' non trovato!"
    exit 1
fi

echo "Copia del template in '${COMPOSE_FILE_PATH}'..."
cp "$TEMPLATE_FILE_PATH" "$COMPOSE_FILE_PATH"

echo "Sostituzione dei segnaposto in '${COMPOSE_FILE_PATH}'..."

# Funzione helper per escape di caratteri speciali per sed
escape_sed() {
  echo "$1" | sed -e 's/[]\/$*.^[]/\\&/g'
}

# Applica le sostituzioni usando sed -i (modifica diretta)
# Usiamo | come delimitatore per sed per evitare conflitti con / nelle URL o password
sed -i "s|__POSTGRES_DB__|$(escape_sed "${POSTGRES_DB_VAR}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__POSTGRES_USER__|$(escape_sed "${POSTGRES_USER_VAR}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__POSTGRES_PASSWORD__|$(escape_sed "${POSTGRES_PASSWORD_VAR}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__BACKEND_IMAGE__|$(escape_sed "${BACKEND_IMAGE}")|g" "$COMPOSE_FILE_PATH"
# Assicuriamoci che DATABASE_URL_VAR sia definita PRIMA di usarla qui
DATABASE_URL_VAR="postgres://${POSTGRES_USER_VAR}:${POSTGRES_PASSWORD_VAR}@db:5432/${POSTGRES_DB_VAR}"
sed -i "s|__DATABASE_URL__|$(escape_sed "${DATABASE_URL_VAR}")|g" "$COMPOSE_FILE_PATH"
# Inseriamo il valore escapato all'interno delle doppie virgolette nel template
SECRET_KEY_ESCAPED=$(escape_sed "${SECRET_KEY_VAR}")
sed -i "s|\"__SECRET_KEY__\"|\"${SECRET_KEY_ESCAPED}\"|g" "$COMPOSE_FILE_PATH"
sed -i "s|__DEBUG__|$(escape_sed "${DEBUG_VAR}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__DJANGO_ALLOWED_HOSTS__|$(escape_sed "${DJANGO_ALLOWED_HOSTS_VAR}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__CORS_ALLOWED_ORIGINS__|$(escape_sed "${CORS_ALLOWED_ORIGINS_VAR}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__DJANGO_SUPERUSER_USERNAME__|$(escape_sed "${DJANGO_SUPERUSER_USERNAME_VAR}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__DJANGO_SUPERUSER_EMAIL__|$(escape_sed "${DJANGO_SUPERUSER_EMAIL_VAR}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__DJANGO_SUPERUSER_PASSWORD__|$(escape_sed "${DJANGO_SUPERUSER_PASSWORD_VAR}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__STUDENT_FRONTEND_IMAGE__|$(escape_sed "${STUDENT_FRONTEND_IMAGE}")|g" "$COMPOSE_FILE_PATH"
sed -i "s|__TEACHER_FRONTEND_IMAGE__|$(escape_sed "${TEACHER_FRONTEND_IMAGE}")|g" "$COMPOSE_FILE_PATH"

echo "File '${COMPOSE_FILE_PATH}' generato e aggiornato con i valori reali."


# --- Fermare e Rimuovere Vecchi Container/Volumi ---
echo "Fermare e rimuovere eventuali container e volumi precedenti..."
# Usiamo -f con il percorso assoluto per sicurezza
$COMPOSE_CMD -f "${COMPOSE_FILE_PATH}" down --remove-orphans # Rimosso -v per preservare il volume del DB

# --- Avvio dei Container ---
echo "Tentativo di pull delle immagini più recenti da Docker Hub..."
$COMPOSE_CMD -f "${COMPOSE_FILE_PATH}" pull

echo "Avvio dei container Docker in background (potrebbe richiedere tempo)..."
# Usiamo il compose file appena modificato con i valori reali
$COMPOSE_CMD -f "${COMPOSE_FILE_PATH}" up -d --force-recreate

echo "Attesa di 10 secondi per permettere al backend di avviarsi completamente..."
sleep 10
echo "Esecuzione delle migrazioni Django..."
$COMPOSE_CMD -f "${COMPOSE_FILE_PATH}" exec backend python manage.py migrate --noinput
echo "Migrazioni Django completate."

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
echo "  - Vedere i log: $COMPOSE_CMD -f ${COMPOSE_FILE_PATH} logs -f"
echo "  - Fermare i servizi: cd ${PROJECT_DIR} && $COMPOSE_CMD -f ${COMPOSE_FILE_PATH} down"
echo "  - Riavviare i servizi: cd ${PROJECT_DIR} && $COMPOSE_CMD -f ${COMPOSE_FILE_PATH} restart"
echo "---------------------------------------------------------------------"

exit 0