# Edu App Roo

Applicazione educativa per la gestione di studenti, quiz, percorsi e ricompense.

Backend sviluppato in Django e Django REST Framework.
Frontend sviluppati in Vue.js 3 (Composition API, TypeScript, Pinia, Tailwind CSS).

## Setup e Avvio

### 1. Esecuzione Locale (Sviluppo)

#### Prerequisiti

*   Python 3.10+
*   Node.js 18+ e npm
*   PostgreSQL Server in esecuzione

#### Backend (Django)

1.  **Clonare il repository:**
    ```bash
    git clone <URL_REPOSITORY>
    cd edu_app_roo
    ```
2.  **Creare e attivare un ambiente virtuale Python:**
    ```bash
    python -m venv .venv
    # Windows PowerShell:
    .venv\Scripts\Activate.ps1
    # Linux/macOS:
    # source .venv/bin/activate
    ```
3.  **Installare le dipendenze Python:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configurare il Database:**
    *   Assicurati che il tuo server PostgreSQL sia in esecuzione.
    *   Crea un database (es. `edu_app_db`).
    *   Crea un file `.env` nella root del progetto copiando `.env.local` (se esiste) o creandolo da zero.
    *   Modifica il file `.env` con le tue credenziali PostgreSQL:
        ```dotenv
        DATABASE_URL=postgres://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB_NAME>
        # Esempio:
        # DATABASE_URL=postgres://postgres:admin@localhost:5432/edu_app_db

        # Opzionale: Credenziali per il superutente iniziale (usato da Docker o comando manuale)
        DJANGO_SUPERUSER_USERNAME=admin
        DJANGO_SUPERUSER_PASSWORD=admin
        DJANGO_SUPERUSER_EMAIL=admin@example.com
        ```
5.  **Applicare le migrazioni del database:**
    ```bash
    python manage.py migrate
    ```
6.  **Creare un superutente (Admin Django):**
    ```bash
    python manage.py createsuperuser
    ```
    (Segui le istruzioni a schermo. Puoi usare le credenziali definite in `.env` se preferisci).
7.  **(Opzionale) Popolare con dati di test:**
    ```bash
    python manage.py seed_test_data
    ```
8.  **Avviare il server di sviluppo Django:**
    ```bash
    python manage.py runserver
    ```
    Il backend sarà accessibile su `http://127.0.0.1:8000/`.

#### Frontend Studente (Vue.js)

1.  **Navigare nella directory:**
    ```bash
    cd frontend-student
    ```
2.  **Installare le dipendenze Node.js:**
    ```bash
    npm install
    ```
3.  **Avviare il server di sviluppo Vue:**
    ```bash
    npm run dev
    ```
    Il frontend studente sarà accessibile su `http://localhost:5175/` (o la porta indicata nel terminale).

#### Frontend Docente (Vue.js)

1.  **Navigare nella directory:**
    ```bash
    cd frontend-teacher
    ```
2.  **Installare le dipendenze Node.js:**
    ```bash
    npm install
    ```
3.  **Avviare il server di sviluppo Vue:**
    ```bash
    npm run dev
    ```
    Il frontend docente sarà accessibile su `http://localhost:5174/` (o la porta indicata nel terminale).

### 2. Esecuzione con Docker Compose (Alternativa)

#### Prerequisiti

*   Docker e Docker Compose installati.

#### Avvio

1.  **Creare il file `.env.docker`:** Copia `.env.example` (se esiste) o crealo manualmente nella root del progetto. Assicurati che contenga le variabili necessarie, in particolare:
    ```dotenv
    # Impostazioni Database (Docker Compose userà queste per il servizio 'db')
    POSTGRES_DB=edu_app_db
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=admin # Scegli una password sicura

    # URL Database per Django (deve puntare al nome del servizio db)
    DATABASE_URL=postgres://postgres:admin@db:5432/edu_app_db

    # Credenziali Superutente Django (verranno usate all'avvio del container web)
    DJANGO_SUPERUSER_USERNAME=admin
    DJANGO_SUPERUSER_PASSWORD=admin # Usa la stessa password sicura scelta sopra o un'altra
    DJANGO_SUPERUSER_EMAIL=admin@example.com

    # Impostazioni Django per Docker
    DJANGO_SECRET_KEY=la-tua-secret-key-per-docker # Genera una chiave sicura
    DJANGO_DEBUG=True # O False per un ambiente più simile alla produzione
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 # Aggiungi altri host se necessario
    CORS_ALLOWED_ORIGINS=http://localhost:5174,http://localhost:5175 # Permetti accesso dai frontend
    ```
    **Nota:** Il `DJANGO_SECRET_KEY` dovrebbe essere una stringa casuale e sicura. Puoi generarne una con Django (`python manage.py shell -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`).

2.  **Build e Avvio dei Container:**
    ```bash
    docker-compose --env-file .env.docker up --build -d
    ```
    *   `--env-file .env.docker`: Specifica il file di variabili d'ambiente da usare.
    *   `up`: Crea e avvia i container.
    *   `--build`: Forza la ricostruzione delle immagini se i Dockerfile sono cambiati.
    *   `-d`: Esegue i container in background (detached mode).

3.  **Accesso ai Servizi:**
    *   **Backend Django:** `http://localhost:8000/`
    *   **Frontend Docente:** `http://localhost:5174/`
    *   **Frontend Studente:** `http://localhost:5175/`
    *   **Interfaccia Admin:** `http://localhost:8000/admin/` (usa le credenziali definite in `.env.docker`)

#### Comandi Utili Docker Compose

*   **Vedere i log:** `docker-compose logs -f [nome_servizio]` (es. `docker-compose logs -f web`)
*   **Fermare i container:** `docker-compose down`
*   **Eseguire comandi nel container web (es. migrate, createsuperuser manualmente):**
    ```bash
    docker-compose exec web python manage.py <comando>
    # Esempio:
    # docker-compose exec web python manage.py migrate
    # docker-compose exec web python manage.py seed_test_data
    ```

*(Aggiungere ulteriori dettagli su configurazione, API, ecc. in seguito)*