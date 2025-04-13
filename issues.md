# Riepilogo Problema: Reverse Proxy Nginx per Applicazioni Frontend/Backend

**Obiettivo:**
Configurare un reverse proxy Nginx (esterno) per accedere a:
- Frontend Studenti (Vue/Vite SPA) tramite `http://217.154.2.9/studenti/`
- Frontend Docenti (Vue/Vite SPA) tramite `http://217.154.2.9/docenti/`
- Backend Admin (Django) tramite `http://217.154.2.9/admin/`
- API Backend tramite `http://217.154.2.9/api/`

**Stato Iniziale Sessione (12/04/2025):**
- Accedendo a `/studenti/` o `/docenti/` si ottiene l'errore `ERR_TOO_MANY_REDIRECTS` nel browser.
- `/admin/` e `/api/` presumibilmente funzionanti.

**Azioni Intraprese (Sessione 12/04/2025):**
1.  **Modifica Nginx Esterno (`nginx.conf`):**
    *   Rimosse direttive `rewrite` e `try_files` dai blocchi `location /studenti/` e `/docenti/`.
    *   Modificato `proxy_pass` per usare il nome del servizio e la porta interna Docker, senza slash finale (es. `proxy_pass http://frontend-teacher:80;`), per inoltrare l'URI completo.
2.  **Modifica Nginx Interno (`frontend-student/nginx.conf`):**
    *   Aggiunta regola `rewrite ^/studenti/(.*)$ /$1 break;` per gestire il prefisso internamente prima di `try_files`.
3.  **Modifica Nginx Interno (`frontend-teacher/nginx.conf`):**
    *   Tentativo 1: Aggiunta regola `rewrite ^/docenti/(.*)$ /$1 break;`. Risultato: `/docenti/` reindirizzava a `/studenti/`.
    *   Tentativo 2: Sostituita `rewrite` con `location /docenti/ { alias /usr/share/nginx/html/; try_files $uri $uri/ /docenti/index.html; }`. Risultato: Nessun cambiamento, redirect a `/studenti/` persisteva.
4.  **Diagnostica Log:**
    *   Log `frontend-teacher` (tramite `docker compose logs`) non mostravano accessi HTTP, solo avvio Nginx.
    *   Aggiunto logging esplicito (`access_log /dev/stdout; error_log /dev/stderr;`) a `frontend-teacher/nginx.conf`. Risultato: Ancora nessun log di accesso visibile dopo rebuild/restart.
    *   Aggiunto logging `notice` e header `X-Debug-Proxy` a `nginx.conf` (esterno) nel blocco `/docenti/`.
    *   Verifica Browser + Log `nginx-proxy`: L'header `X-Debug-Proxy` **non** era presente nella risposta a `/docenti/`. I log di `nginx-proxy` mostravano solo richieste a `/studenti/` (probabilmente post-redirect), **nessuna evidenza** che la richiesta originale a `/docenti/` fosse stata processata dal blocco `location /docenti/`.

**Stato Attuale (Fine Sessione 12/04/2025):**
- L'errore `ERR_TOO_MANY_REDIRECTS` sembra risolto.
- Accedendo a `http://217.154.2.9/studenti/` si ottiene (probabilmente) l'applicazione studenti (log mostrano 304).
- Accedendo a `http://217.154.2.9/docenti/` si viene **reindirizzati** a `/studenti/`.
- L'analisi indica che le richieste a `/docenti/` **non** vengono correttamente catturate dal blocco `location /docenti/` nel proxy Nginx esterno (`nginx.conf`). Cadono invece nel blocco generico `location / { return 301 /studenti/; }`.
- La causa esatta per cui il blocco `location /docenti/` non viene attivato non è stata identificata.

**Componenti e Configurazioni Chiave (Stato Attuale):**
- **Nginx Proxy Esterno (`nginx.conf`):** Usa `proxy_pass http://service:80;` per i frontend. Ha `error_log notice` e header debug in `/docenti/` (ma non viene raggiunto).
- **Frontend Containers (`frontend-student`, `frontend-teacher`):** Usano Nginx interno.
    - `frontend-student/nginx.conf`: Usa `rewrite ^/studenti/` + `try_files`.
    - `frontend-teacher/nginx.conf`: Usa `location /docenti/ { alias ...; try_files ...; }` e log su stdout/stderr.
- **Vite Config:** `base: '/studenti/'` e `base: '/docenti/'` confermate corrette.
- **Docker Compose (`docker-compose.prod.static.yml`):** Definisce i servizi.
- **Script di Deploy (`deploy_env_only.sh`):** Usato per il deploy.

**Prossimi Passi Suggeriti (per nuova sessione):**
1.  **Riesaminare `nginx.conf` (esterno):** Ispezionare attentamente la sintassi, l'ordine delle `location`, possibili conflitti o caratteri invisibili. Considerare l'uso di `location ~ ^/docenti/` per forzare la corrispondenza regex.
2.  **Verificare Mount Volumi (`docker-compose.prod.static.yml`):** Assicurarsi che il servizio `nginx-proxy` monti `nginx.conf` dalla posizione corretta (`./nginx.conf:/etc/nginx/nginx.conf` o simile).
3.  **Semplificare `nginx.conf` (esterno):** Commentare temporaneamente altre `location` (es. `/`, `/studenti`, `/admin`) per isolare il comportamento del blocco `/docenti/`.
4.  **Analizzare Log `nginx-proxy` (livello `debug`):** Se necessario, aumentare ulteriormente il livello di log in `nginx.conf` (`error_log /dev/stderr debug;`) per ottenere dettagli massimi sull'elaborazione delle richieste e sulla selezione della `location`.

---

## Risoluzione (13/04/2025)

Il problema è stato risolto seguendo questi passaggi:

1.  **Modifica Nginx Esterno (`nginx.conf`):** Aggiunto il modificatore `^~` alla `location /docenti/` (`location ^~ /docenti/ { ... }`) per garantire che questa location avesse la priorità sulla location generica `/`.
2.  **Modifica Nginx Interno (`frontend-teacher/nginx.conf`):** Rimosso il blocco `location ~ ^/docenti/assets/ { ... }` che era ridondante e potenzialmente conflittuale. La gestione degli assets è stata affidata al blocco `location /docenti/ { alias ...; try_files ...; }`.
3.  **Identificazione Causa Finale:** Dopo l'applicazione delle modifiche lato server, il problema persisteva su alcuni browser (Edge) ma non su altri (Firefox). Questo ha indicato un problema di **caching del browser**. Il browser Edge aveva memorizzato in cache il vecchio redirect 301 e continuava ad applicarlo.
4.  **Soluzione:** Pulire completamente la cache del browser (o usare una finestra InPrivate/Incognito) ha risolto il problema residuo.

**Stato Finale:** Il reverse proxy Nginx ora instrada correttamente le richieste a `/studenti/`, `/docenti/`, `/admin/` e `/api/` ai rispettivi servizi backend/frontend. L'applicazione docenti è accessibile e carica correttamente le sue risorse. Questo issue è considerato **chiuso**.