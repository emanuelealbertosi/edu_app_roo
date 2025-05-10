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
    docker build -t albertosiemanuele/edu-app-backend:tuo_tag_specifico .
    ```
*   **Build Frontend Studente:**
    ```bash
    docker build -t albertosiemanuele/edu-app-frontend-student:tuo_tag_specifico ./frontend-student
    ```
*   **Build Frontend Docente:**
    ```bash
    docker build -t albertosiemanuele/edu-app-frontend-teacher:tuo_tag_specifico ./frontend-teacher
    ```
*   **Build Frontend Lezioni:**
    ```bash
    docker build -t albertosiemanuele/edu-app-frontend-lessons:tuo_tag_specifico ./frontend-lessons
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
    image: albertosiemanuele/edu-app-backend:tuo_tag_specifico # <-- AGGIORNA QUESTA RIGA
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
docker push albertosiemanuele/edu-app-backend:tuo_tag_specifico
docker push albertosiemanuele/edu-app-frontend-student:tuo_tag_specifico
docker push albertosiemanuele/edu-app-frontend-teacher:tuo_tag_specifico
docker push albertosiemanuele/edu-app-frontend-lessons:tuo_tag_specifico
```

---

## 4. Operazioni Comuni sui Container

Questi comandi presuppongono che i tuoi servizi siano definiti nel file `docker-compose.local-prod-test.yml` e che tu stia operando dalla directory principale del progetto.

### Eseguire Migrazioni Django (sul container `backend`)

Per eseguire le migrazioni del database Django (es. `python manage.py migrate`) all'interno del container del backend in esecuzione:

```bash
docker compose -f docker-compose.local-prod-test.yml exec backend python manage.py migrate
```

*   `docker compose exec [NOME_SERVIZIO] [COMANDO]`: Esegue un comando all'interno di un container specifico già in esecuzione.
*   `backend`: È il nome del tuo servizio backend come definito nel file `docker-compose.local-prod-test.yml`.
*   `python manage.py migrate`: È il comando Django per applicare le migrazioni.

Se hai bisogno di creare nuove migrazioni (es. `python manage.py makemigrations nome_app`), il comando sarebbe:
```bash
docker compose -f docker-compose.local-prod-test.yml exec backend python manage.py makemigrations nome_tua_app
```
Sostituisci `nome_tua_app` con il nome dell'app Django per cui vuoi creare le migrazioni.

### Visualizzare i Log del Backend

*   Per visualizzare i log del backend in tempo reale e seguirli (utile per il debug):
    ```bash
    docker compose -f docker-compose.local-prod-test.yml logs -f backend
    ```
*   Per visualizzare tutti i log storici del backend:
    ```bash
    docker compose -f docker-compose.local-prod-test.yml logs backend
    ```

### Pulizia del Sistema Docker (Prune)

Questi comandi aiutano a liberare spazio su disco rimuovendo risorse Docker non utilizzate.

*   **Rimuovere tutti i container fermati, le reti non utilizzate, le immagini "dangling" (senza tag) e la cache di build:**
    ```bash
    docker system prune
    ```
    Ti verrà chiesta una conferma.

*   **Rimuovere TUTTE le immagini non utilizzate (non solo quelle dangling):**
    Attenzione: questo comando è più aggressivo e rimuoverà tutte le immagini che non sono attualmente associate a un container.
    ```bash
    docker image prune -a
    ```
    Ti verrà chiesta una conferma.

*   **Pulizia completa del sistema Docker ESCLUSI I VOLUMI:**
    Il comando più semplice e sicuro per rimuovere container fermati, reti non utilizzate, tutte le immagini non utilizzate (non solo dangling) e la cache di build, **senza toccare i volumi** è:
    ```bash
    docker system prune -a
    ```
    Docker chiederà conferma e specificherà che i volumi non verranno rimossi a meno che non si usi il flag `--volumes`.

**Importante sui Volumi:**
I comandi `docker system prune` e `docker image prune` di default **non** rimuovono i volumi Docker. Per rimuovere anche i volumi non utilizzati (cosa che di solito **NON vuoi fare** a meno che tu non sia sicuro, perché perderesti dati persistenti come quelli del database), dovresti aggiungere il flag `--volumes` a `docker system prune`. La tua richiesta era specificamente di *non* toccare i volumi, quindi i comandi sopra sono sicuri in tal senso.

---

## 5. Note Aggiuntive

*   **File `.env.localprod`:** Questo file è cruciale per la configurazione dei tuoi servizi. Assicurati che sia presente e corretto.
*   La sezione precedente sui log è stata integrata nella Sezione 4.

---

## 6. Diagramma Architetturale Semplificato
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