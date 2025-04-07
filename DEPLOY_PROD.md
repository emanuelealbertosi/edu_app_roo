# Istruzioni per il Deployment in Produzione (Ubuntu Server)

Questo documento descrive i passaggi per effettuare il deployment dell'applicazione Edu App Roo su un server Ubuntu utilizzando Docker e Docker Compose, basandosi sulla configurazione funzionante al 7 Aprile 2025.

## Prerequisiti

*   Server Ubuntu con Docker e Docker Compose (V1 o V2 plugin) installati.
*   Accesso SSH al server.
*   Immagini Docker aggiornate per `backend`, `frontend-student`, `frontend-teacher` pushate su Docker Hub (repository: `albertosiemanuele/...`).
*   Repository Git clonato sul server o un modo per copiare i file necessari.

## File Necessari sul Server

Assicurati che i seguenti file siano presenti nella directory di deployment scelta sul server (es. `/root/edu_app_deployment/`):

1.  `deploy_env_only.sh`: Lo script che gestisce la creazione del file `.env.prod` e l'avvio dei container. **Assicurati che sia la versione più recente dal repository locale.**
2.  `docker-compose.prod.static.yml`: Il file Docker Compose statico che definisce i servizi. **Assicurati che sia la versione più recente dal repository locale.**

## Procedura di Deployment

1.  **Connettiti al server Ubuntu** tramite SSH.

2.  **Naviga alla directory di deployment:**
    ```bash
    cd /root/edu_app_deployment # O il percorso corretto
    ```

3.  **Assicurati che lo script sia eseguibile:**
    ```bash
    chmod +x deploy_env_only.sh
    ```

4.  **Esegui lo script di deployment:**
    ```bash
    ./deploy_env_only.sh
    ```
    *   Lo script ti chiederà interattivamente di inserire le variabili d'ambiente necessarie (IP del server, credenziali DB, SECRET_KEY, ecc.). Inserisci valori sicuri per la produzione.
    *   Lo script creerà/sovrascriverà il file `.env.prod`.
    *   Lo script fermerà e rimuoverà eventuali container precedenti.
    *   Lo script forzerà il pull delle immagini più recenti da Docker Hub (`--pull always`).
    *   Lo script avvierà i nuovi container in background usando `docker-compose.prod.static.yml` e le variabili da `.env.prod`.

5.  **Verifica l'avvio dei container:**
    ```bash
    docker ps
    ```
    Dovresti vedere i container `db`, `backend`, `frontend-student`, `frontend-teacher` in stato "Up".

6.  **Controlla i log (se necessario):**
    ```bash
    docker compose -f docker-compose.prod.static.yml logs -f
    ```
    Verifica che non ci siano errori, in particolare nel backend riguardo alla connessione al database e alle migrazioni.

7.  **Accedi alle applicazioni:**
    *   Backend Admin: `http://<SERVER_IP>:8000/admin/`
    *   Frontend Docente: `http://<SERVER_IP>:5174/`
    *   Frontend Studente: `http://<SERVER_IP>:5175/`
    (Sostituisci `<SERVER_IP>` con l'IP pubblico del tuo server).

## Note Aggiuntive

*   Questo script rimuove il volume del database (`postgres_data`) ad ogni esecuzione (`docker compose down -v`). Questo garantisce uno stato pulito ma **cancella tutti i dati del database** ad ogni deployment. Se hai bisogno di persistere i dati tra i deployment, rimuovi l'opzione `-v` dal comando `down` nello script `deploy_env_only.sh`.
*   Assicurati che le porte `8000`, `5174`, `5175` siano aperte nel firewall del tuo server Ubuntu, se attivo.
*   La `SECRET_KEY` viene generata automaticamente dallo script se non ne fornisci una, ma è buona norma generarne una forte e conservarla in modo sicuro.