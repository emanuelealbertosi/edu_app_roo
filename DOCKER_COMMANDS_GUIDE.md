# Guida ai Comandi Docker per l'Ambiente di Sviluppo Locale

Questa guida fornisce i comandi Docker per buildare (con tag specifici), eseguire e gestire i servizi dell'applicazione, inclusi i passaggi per pushare le immagini su Docker Hub.

**Informazioni Chiave:**
*   **File Docker Compose per Esecuzione:** `docker-compose.local-prod-test.yml`
*   **File Environment Associato:** `.env.localprod` (assicurati che sia presente nella root del progetto e configurato correttamente)
*   **Username Docker Hub:** `albertosiemanuele`

**Servizi Principali e Contesti di Build:**
*   **Backend (`backend`):**
    *   Contesto: `.` (directory principale del progetto)
    *   Dockerfile: `Dockerfile` (nella directory principale)
*   **Frontend Studente (`frontend-student`):**
    *   Contesto: `./frontend-student`
    *   Dockerfile: `frontend-student/Dockerfile`
*   **Frontend Docente (`frontend-teacher`):**
    *   Contesto: `./frontend-teacher`
    *   Dockerfile: `frontend-teacher/Dockerfile`
*   **Frontend Lezioni (`frontend-lessons`):**
    *   Contesto: `./frontend-lessons`
    *   Dockerfile: `frontend-lessons/Dockerfile`

---

## 1. Build dei Servizi con Tag Specifico (Usando `docker build`)

Questo metodo builda le immagini direttamente con il tuo username Docker Hub e un tag specifico. Sostituisci `tuo_tag_specifico` con il tag desiderato (es. `v1.0.0`, `latest`, `feature-xyz`).

*   **Build Backend:**
    ```bash
    docker build -t albertosiemanuele/backend:tuo_tag_specifico .
    ```
*   **Build Frontend Studente:**
    ```bash
    docker build -t albertosiemanuele/frontend-student:tuo_tag_specifico ./frontend-student
    ```
*   **Build Frontend Docente:**
    ```bash
    docker build -t albertosiemanuele/frontend-teacher:tuo_tag_specifico ./frontend-teacher
    ```
*   **Build Frontend Lezioni:**
    ```bash
    docker build -t albertosiemanuele/frontend-lessons:tuo_tag_specifico ./frontend-lessons
    ```

---

## 2. Esecuzione dei Servizi (Usando `docker compose up`)

Per avviare i servizi utilizzando `docker compose up` e far sì che utilizzi le immagini che hai appena buildato e taggato specificamente nella Sezione 1:

**NOTA MOLTO IMPORTANTE:**
Il file `docker-compose.local-prod-test.yml` **deve essere aggiornato** per fare riferimento a queste immagini con nome e tag specifici. Per ogni servizio (`backend`, `frontend-student`, `frontend-teacher`, `frontend-lessons`), dovrai aggiungere o modificare la direttiva `image:` nel file `docker-compose.local-prod-test.yml` affinché corrisponda esattamente al nome e tag che hai usato nel comando `docker build`.

**Esempio di modifica per il servizio `backend` in `docker-compose.local-prod-test.yml`:**
```yaml
services:
  backend:
    # Rimuovi o commenta la sezione 'build:' se l'immagine è sempre pre-buildata,
    # oppure lasciala se vuoi che Compose possa buildare se l'immagine non esiste.
    # build:
    #   context: .
    #   dockerfile: Dockerfile
    image: albertosiemanuele/backend:tuo_tag_specifico # <-- AGGIORNA QUESTA RIGA
    env_file:
      - .env.localprod
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - media_data:/app/mediafiles
      - static_data:/app/staticfiles
    restart: unless-stopped
  # ... configura similarmente gli altri servizi frontend ...
```
Se la direttiva `image:` non è presente o non corrisponde al tag che hai usato per buildare, `docker compose up` potrebbe:
    a) Tentare di buildare nuovamente le immagini usando la sezione `build:` e assegnando nomi predefiniti (es. `edu_app_roo-backend:latest`).
    b) Non trovare l'immagine specificata se hai rimosso la sezione `build:`.

Una volta che il file `docker-compose.local-prod-test.yml` è stato aggiornato per puntare alle immagini corrette:

### Avvio di Tutti i Servizi
*   In background (detached mode):
    ```bash
    docker compose -f docker-compose.local-prod-test.yml --env-file .env.localprod up -d
    ```
*   In foreground (per visualizzare i log in tempo reale):
    ```bash
    docker compose -f docker-compose.local-prod-test.yml --env-file .env.localprod up
    ```

### Riavvio di Tutti i Servizi
*   Se i servizi sono già in esecuzione:
    ```bash
    docker compose -f docker-compose.local-prod-test.yml --env-file .env.localprod restart
    ```
*   Alternativa (Stop e poi Start):
    ```bash
    docker compose -f docker-compose.local-prod-test.yml --env-file .env.localprod stop
    docker compose -f docker-compose.local-prod-test.yml --env-file .env.localprod start
    ```

### Avvio Singolo di un Servizio (e sue dipendenze)
*   **Avvio Backend:**
    ```bash
    docker compose -f docker-compose.local-prod-test.yml --env-file .env.localprod up -d backend
    ```
*   *(Similmente per `frontend-student`, `frontend-teacher` e `frontend-lessons`)*

---

## 3. Push delle Immagini su Docker Hub

Dopo aver buildato le immagini con il tuo username e tag specifici (come nella Sezione 1):

### Passo 3.1: Login a Docker Hub
Se non hai già effettuato l'accesso:
```bash
docker login
```
Ti verranno chiesti username e password.

### Passo 3.2: Pushare le Immagini Taggate
Assicurati che `tuo_tag_specifico` sia lo stesso usato nei comandi `docker build -t`.
```bash
docker push albertosiemanuele/backend:tuo_tag_specifico
docker push albertosiemanuele/frontend-student:tuo_tag_specifico
docker push albertosiemanuele/frontend-teacher:tuo_tag_specifico
docker push albertosiemanuele/frontend-lessons:tuo_tag_specifico
```

---

## Note Aggiuntive

*   **File `.env.localprod`:** Questo file è cruciale per la configurazione dei tuoi servizi. Assicurati che sia presente e corretto.
*   **Visualizzare i Log:**
    ```bash
    docker compose -f docker-compose.local-prod-test.yml logs -f nome_servizio
    # Esempio: docker compose -f docker-compose.local-prod-test.yml logs -f backend
    ```
    Per i log di tutti i servizi:
    ```bash
    docker compose -f docker-compose.local-prod-test.yml logs -f
    ```

---

## Diagramma Architetturale Semplificato
(Il diagramma rimane concettualmente lo stesso, ma i nomi delle immagini usate da `docker compose up` dipenderanno dalle modifiche apportate al file compose come descritto nella Sezione 2.)

```mermaid
graph TD
    subgraph Docker Environment (local-prod-test)
        direction LR
        U[Utente/Browser] --> NP[nginx-proxy:80]

        NP ----> BE[backend]
        NP ----> FS[frontend-student]
        NP ----> FT[frontend-teacher]
        NP ----> FL[frontend-lessons]

        BE ----> DB[db (PostgreSQL)]

        subgraph Volumes Persistenti
            direction TB
            PV[postgres_data]
            MD[media_data]
            SD[static_data]
        end

        DB -- archivia dati in --> PV
        BE -- usa/archivia --> MD
        BE -- usa/archivia --> SD
        FS -- accede a --> MD
        FT -- accede a --> MD
        FL -- accede a --> MD
        NP -- serve files da --> MD
        NP -- serve files da --> SD
    end