#!/bin/bash

# Script interattivo per il deployment dell'applicazione Edu App Roo su Ubuntu usando Docker

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
    # Prova a usare python3 se disponibile, altrimenti python
    if command_exists python3; then
        python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
    elif command_exists python; then
        python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
    else
        # Fallback a un metodo meno sicuro se Python non è disponibile
        head /dev/urandom | tr -dc A-Za-z0-9 | head -c 50
        echo "" # Aggiunge newline
        echo "Attenzione: Chiave segreta generata con metodo meno sicuro. Installa Python per una chiave migliore."
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

# Database
read -p "Nome database PostgreSQL [edu_app_prod_db]: " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-edu_app_prod_db}

read -p "Utente database PostgreSQL [prod_user]: " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-prod_user}

read -sp "Password database PostgreSQL (NESSUN DEFAULT - OBBLIGATORIA!): " POSTGRES_PASSWORD
echo # Aggiunge newline dopo input password
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "Errore: La password del database è obbligatoria."
    exit 1
fi

# Django Settings
# Genera una chiave segreta di default
DEFAULT_SECRET_KEY=$(generate_secret_key)
read -p "Django SECRET_KEY [Generata automaticamente]: " SECRET_KEY
SECRET_KEY=${SECRET_KEY:-$DEFAULT_SECRET_KEY}

# DEBUG deve essere False in produzione
DEBUG=False
echo "DEBUG impostato a: $DEBUG (non modificabile per produzione)"

read -p "Host/Domini permessi per Django (separati da virgola) [Default: * (permetti tutti)]: " DJANGO_ALLOWED_HOSTS
DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS:-*}

# Nota sulla sicurezza di CORS
echo "Configurazione CORS: Specificare gli URL completi dei frontend permessi (es. https://mio-studente.com,https://mio-docente.com)."
echo "Lasciando vuoto si useranno i default per localhost (http://localhost:5174,http://localhost:5175), NON ADATTO a produzione reale senza reverse proxy."
read -p "Origini CORS permesse (separati da virgola) [Default: localhost ports]: " CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS:-"http://localhost:5174,http://localhost:5175"}

# Superuser
read -p "Username Superuser Django [admin_prod]: " DJANGO_SUPERUSER_USERNAME
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin_prod}

read -p "Email Superuser Django [admin@example.com]: " DJANGO_SUPERUSER_EMAIL
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}

read -sp "Password Superuser Django (NESSUN DEFAULT - OBBLIGATORIA!): " DJANGO_SUPERUSER_PASSWORD
echo # Aggiunge newline dopo input password
if [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Errore: La password del superuser è obbligatoria."
    exit 1
fi

# --- Creazione File .env.prod ---
echo "Creazione del file '.env.prod' con i valori forniti..."
cat << EOF > .env.prod
# File generato automaticamente dallo script deploy_on_ubuntu.sh
# Data: $(date)

# --- Database Configuration ---
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# --- Django Settings ---
SECRET_KEY='${SECRET_KEY}' # Apici singoli per gestire caratteri speciali
DEBUG=${DEBUG}
DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS}
CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}

# --- Superuser Credentials ---
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}
EOF

echo "File '.env.prod' creato con successo."

# --- Creazione File docker-compose.prod.yml (se non esiste) ---
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Creazione del file 'docker-compose.prod.yml'..."
    # Usiamo \${VAR} per evitare l'espansione immediata delle variabili nello script
    cat << 'EOF' > docker-compose.prod.yml
services:
  db:
    image: postgres:15-alpine # Usa variabile definita nello script o immagine diretta
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - .env.prod
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${POSTGRES_USER} -d \${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  backend:
    image: albertosiemanuele/edu-app-backend:latest # Usa variabile definita nello script o immagine diretta
    ports:
      - "8000:8000"
    env_file:
      - .env.prod
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG}
      - DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
      - DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME}
      - DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL}
      - DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  frontend-student:
    image: albertosiemanuele/edu-app-frontend-student:latest # Usa variabile definita nello script o immagine diretta
    ports:
      - "5175:80"
    depends_on:
      - backend
    restart: unless-stopped

  frontend-teacher:
    image: albertosiemanuele/edu-app-frontend-teacher:latest # Usa variabile definita nello script o immagine diretta
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


# --- Avvio dei Container ---
echo "Tentativo di pull delle immagini più recenti da Docker Hub..."
$COMPOSE_CMD -f docker-compose.prod.yml pull

echo "Avvio dei container Docker in background (potrebbe richiedere tempo)..."
$COMPOSE_CMD -f docker-compose.prod.yml --env-file .env.prod up -d --force-recreate

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
echo "  - Username: ${DJANGO_SUPERUSER_USERNAME}" # Legge variabile dallo script
echo "  - Password: (quella inserita durante l'esecuzione dello script)"
echo ""
echo "Comandi utili:"
echo "  - Vedere i log: $COMPOSE_CMD -f docker-compose.prod.yml logs -f"
echo "  - Fermare i servizi: cd $PROJECT_DIR && $COMPOSE_CMD -f docker-compose.prod.yml down"
echo "  - Riavviare i servizi: cd $PROJECT_DIR && $COMPOSE_CMD -f docker-compose.prod.yml restart"
echo "---------------------------------------------------------------------"

exit 0