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

### 3. Deployment (Produzione con Docker)

Questa sezione descrive come eseguire l'applicazione su un server utilizzando le immagini Docker pre-compilate disponibili su Docker Hub e il file `docker-compose.prod.yml`.

#### Prerequisiti

*   Docker e Docker Compose installati sul server.
*   Accesso al server tramite SSH o terminale.

#### Passaggi

1.  **Clonare il repository sul server:**
    ```bash
    git clone <URL_REPOSITORY>
    cd edu_app_roo
    ```
2.  **Creare e Configurare `.env.prod`:**
    *   Crea un file chiamato `.env.prod` nella directory principale del progetto (`edu_app_roo`).
    *   Copia il contenuto di esempio da `.env.prod.example` (se esiste) o definisci le seguenti variabili:
        ```dotenv
        # =========================================
        # === VARIABILI AMBIENTE DI PRODUZIONE ===
        # =========================================
        # ATTENZIONE: Modificare questi valori con segreti reali prima del deployment!

        # --- Database Configuration ---
        POSTGRES_DB=edu_app_prod_db # Nome del database di produzione
        POSTGRES_USER=prod_user     # Utente database di produzione
        # Cambiare questa password con una forte e sicura!
        POSTGRES_PASSWORD=changeme_prod_password

        # --- Django Settings ---
        # Generare una nuova SECRET_KEY per la produzione! Esempio: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
        SECRET_KEY='changeme_replace_with_a_real_production_secret_key'
        # Impostare DEBUG a False in produzione per sicurezza e performance!
        DEBUG=False
        # Impostare gli host permessi (es. il dominio del tuo server, indirizzo IP)
        DJANGO_ALLOWED_HOSTS=tuo_dominio.com,www.tuo_dominio.com,indirizzo_ip_server
        # Impostare gli origin CORS permessi (es. i domini dei tuoi frontend in produzione)
        CORS_ALLOWED_ORIGINS=https://frontend-studente.tuo_dominio.com,https://frontend-docente.tuo_dominio.com

        # --- Superuser Credentials (per lo script di inizializzazione) ---
        # Scegliere username e email desiderati per l'admin iniziale
        DJANGO_SUPERUSER_USERNAME=admin_prod
        DJANGO_SUPERUSER_EMAIL=admin@tuo_dominio.com
        # Cambiare questa password con una forte e sicura!
        DJANGO_SUPERUSER_PASSWORD=changeme_admin_prod_password
        ```
    *   **IMPORTANTE:** Sostituisci i valori `changeme_...` e `tuo_dominio.com`/`indirizzo_ip_server` con i tuoi valori reali e sicuri per la produzione.

3.  **(Opzionale) Login a Docker Hub (se le immagini sono private):**
    Se i repository su Docker Hub sono privati, dovrai fare il login:
    ```bash
    docker login -u tuo_username_dockerhub
    ```

4.  **Avviare i Container di Produzione:**
    Utilizza il file `docker-compose.prod.yml` e il file `.env.prod` per avviare i servizi:
    ```bash
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
    ```
    *   `-f docker-compose.prod.yml`: Specifica di usare il file Compose di produzione.
    *   `--env-file .env.prod`: Specifica il file di variabili d'ambiente di produzione.
    *   `up`: Scarica le immagini (se non presenti localmente), crea e avvia i container.
    *   `-d`: Esegue i container in background.

    Docker Compose scaricherà automaticamente le immagini specificate (`albertosiemanuele/edu-app-...:latest`) da Docker Hub. Lo script `entrypoint.prod.sh` all'interno del container `backend` eseguirà le migrazioni e creerà il superutente iniziale (se configurato in `.env.prod`).

5.  **Accesso ai Servizi (Tramite Reverse Proxy Nginx):**
    L'applicazione è configurata per essere accessibile tramite un reverse proxy Nginx sulla porta 80 del server (es. `217.154.2.9`):
    *   **Frontend Studente:** `http://217.154.2.9/studenti/`
    *   **Frontend Docente:** `http://217.154.2.9/docenti/`
    *   **Interfaccia Admin:** `http://217.154.2.9/admin/` (usa le credenziali definite in `.env.prod`)
    *   **API Backend:** `http://217.154.2.9/api/`

#### Gestione dei Container di Produzione

*   **Vedere i log:**
    ```bash
    docker-compose -f docker-compose.prod.yml logs -f [nome_servizio]
    # Esempio: docker-compose -f docker-compose.prod.yml logs -f backend
    ```
*   **Fermare i container:**
    ```bash
    docker-compose -f docker-compose.prod.yml down
    ```
*   **Riavviare i container:**
    ```bash
    docker-compose -f docker-compose.prod.yml restart [nome_servizio]
    ```
*   **Eseguire comandi nel container backend:**
    ```bash
    docker-compose -f docker-compose.prod.yml exec backend <comando>
    # Esempio: docker-compose -f docker-compose.prod.yml exec backend python manage.py shell
    ```

## Comandi Utili Docker

### Build e Tag Immagini come `latest`

Esegui questi comandi dalla directory principale del progetto per buildare le immagini e taggarle come `latest` per Docker Hub.

```bash
# Build e tag Backend
docker build -t albertosiemanuele/edu-app-backend:latest . -f Dockerfile

# Build e tag Frontend Studente
docker build -t albertosiemanuele/edu-app-frontend-student:latest ./frontend-student -f ./frontend-student/Dockerfile

# Build e tag Frontend Docente
docker build -t albertosiemanuele/edu-app-frontend-teacher:latest ./frontend-teacher -f ./frontend-teacher/Dockerfile
```

### Push Immagini `latest` su Docker Hub

Assicurati di essere loggato (`docker login`).

```bash
# Push Backend
docker push albertosiemanuele/edu-app-backend:latest

# Push Frontend Studente
docker push albertosiemanuele/edu-app-frontend-student:latest

# Push Frontend Docente
docker push albertosiemanuele/edu-app-frontend-teacher:latest
```

### Cancellare Manualmente File Media nel Container Backend

Questo comando cancellerà **tutti** i file nella directory `/app/mediafiles/` all'interno del container `backend` in esecuzione. **Usare con estrema cautela.**

```bash
# Trova il nome esatto del container con 'docker ps' se necessario
docker exec edu_app_roo-backend-1 rm -rf /app/mediafiles/*
```
    ```