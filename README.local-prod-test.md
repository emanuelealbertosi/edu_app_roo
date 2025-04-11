# Eseguire l'Ambiente di Test Locale Simile alla Produzione

Questo documento descrive come avviare un ambiente Docker locale che simula la configurazione di produzione (`DEBUG=False`, Nginx per servire i file statici/media), utilizzando immagini buildate localmente.

## Prerequisiti

*   Docker installato e funzionante.
*   Docker Compose (v1 o v2) installato.

## Configurazione

1.  **Crea il file `.env.localprod`**:
    *   Nella directory principale del progetto, crea un file chiamato `.env.localprod`.
    *   Popola questo file con le variabili d'ambiente necessarie. Puoi usare il seguente template come base, **assicurandoti di usare password sicure e una `SECRET_KEY` unica**:

    ```dotenv
    # .env.localprod

    # --- Database Configuration ---
    POSTGRES_DB=edu_app_local_prod_db
    POSTGRES_USER=local_user
    POSTGRES_PASSWORD=local_password # Usa una password sicura

    # --- Django Settings ---
    # DATABASE_URL sarà costruito da Django/dj-database-url usando le variabili sopra
    DATABASE_URL=postgres://local_user:local_password@db:5432/edu_app_local_prod_db
    SECRET_KEY='una_chiave_segreta_molto_sicura_per_il_test_locale' # Generane una nuova se preferisci
    DEBUG=False # Importante per testare il serving media come in produzione
    DJANGO_ALLOWED_HOSTS=*,localhost,127.0.0.1
    CORS_ALLOWED_ORIGINS=http://localhost:5174,http://localhost:5175,http://127.0.0.1:5174,http://127.0.0.1:5175

    # --- Superuser Credentials (opzionale per test, ma utile) ---
    DJANGO_SUPERUSER_USERNAME=admin_local_prod
    DJANGO_SUPERUSER_EMAIL=admin_local@example.com
    DJANGO_SUPERUSER_PASSWORD=admin_password # Usa una password sicura

    # --- Docker Settings (non usata direttamente da questo compose, ma per coerenza) ---
    DOCKER_VERSION=local-test
    ```

2.  **Verifica `docker-compose.local-prod-test.yml`**:
    *   Assicurati che il file `docker-compose.local-prod-test.yml` esista nella directory principale e contenga la configurazione corretta per buildare le immagini localmente e usare i volumi `_local_prod`.

## Comandi

Esegui i seguenti comandi nel terminale, dalla directory principale del progetto:

1.  **(Opzionale) Pulizia Ambiente Precedente**: Se hai già eseguito questo ambiente in precedenza, puoi fermare i container e rimuovere i volumi per partire da uno stato pulito:
    ```bash
    docker-compose -f docker-compose.local-prod-test.yml down --volumes --remove-orphans
    ```

2.  **Build Immagini**: Costruisce le immagini Docker per backend e frontend localmente:
    ```bash
    docker-compose -f docker-compose.local-prod-test.yml build
    ```
    *(Questo passaggio è necessario solo la prima volta o dopo aver modificato i file sorgente o i Dockerfile).*

3.  **Avvio Ambiente**: Avvia tutti i container in background, usando le variabili definite in `.env.localprod`:
    ```bash
    docker-compose -f docker-compose.local-prod-test.yml --env-file .env.localprod up -d
    ```

## Accesso ai Servizi

Una volta avviato l'ambiente, i servizi saranno accessibili ai seguenti indirizzi:

*   **Backend Django (Admin)**: `http://localhost:8000/admin/`
*   **Frontend Docente**: `http://localhost:5174/`
*   **Frontend Studente**: `http://localhost:5175/`
*   **Media Files (Esempio)**: `http://localhost:5175/media/badges/nome_file.png` (o porta 5174)

*(Nota: Se le porte 5174 o 5175 sono già in uso sulla tua macchina, dovrai modificare la sezione `ports` nel file `docker-compose.local-prod-test.yml` e aggiornare gli URL di accesso di conseguenza).*

## Credenziali Admin

Le credenziali per l'utente superuser creato automaticamente (se le variabili sono impostate in `.env.localprod`) sono:

*   **Username**: Il valore di `DJANGO_SUPERUSER_USERNAME` in `.env.localprod` (default: `admin_local_prod`)
*   **Password**: Il valore di `DJANGO_SUPERUSER_PASSWORD` in `.env.localprod` (default: `admin_password_sicura` - **cambiala!**)

Usa queste credenziali per accedere all'interfaccia di amministrazione su `http://localhost:8000/admin/`.

## Debug e Gestione

*   **Vedere i Log**:
    ```bash
    # Log di tutti i servizi
    docker-compose -f docker-compose.local-prod-test.yml logs -f

    # Log di un servizio specifico (es. backend)
    docker-compose -f docker-compose.local-prod-test.yml logs -f backend
    ```

*   **Fermare l'Ambiente**:
    ```bash
    docker-compose -f docker-compose.local-prod-test.yml down
    ```

*   **Fermare e Rimuovere Volumi**: (Attenzione: questo cancellerà i dati del database e i file media locali)
    ```bash
    docker-compose -f docker-compose.local-prod-test.yml down --volumes