# Piano di Integrazione Menu Frontend

**Versione:** 1.2
**Data:** 22 Maggio 2025 (Ulteriormente Aggiornato)
**Autore:** Roo (Architect AI)

## 1. Obiettivo Principale

Modificare i menu delle applicazioni frontend esistenti, `frontend-student` e `frontend-teacher`, per incorporare funzionalità specifiche ospitate sull'applicazione `frontend-lessons`. L'integrazione avverrà tramite `<iframe>`, permettendo al menu e al layout dell'applicazione "host" (`frontend-student` o `frontend-teacher`) di rimanere visibili mentre il contenuto di `frontend-lessons` viene visualizzato in un frame.

Le tre applicazioni (`frontend-student`, `frontend-teacher`, `frontend-lessons`) rimarranno separate dal punto di vista del codice sorgente e del deployment, ma saranno servite da percorsi distinti sotto lo stesso dominio principale (es. `vostrodominio.com/studenti/`, `vostrodominio.com/docenti/`, `vostrodominio.com/lezioni/`). La sessione utente sarà condivisa e mantenuta tramite un meccanismo di Single Sign-On (SSO) basato su token JWT memorizzati in `localStorage`.

Le funzionalità relative ai "Percorsi" (Pathways) sono escluse da questa integrazione. Le dashboard esistenti di `frontend-student` e `frontend-teacher` rimarranno i punti di ingresso principali per i rispettivi ruoli.

## 2. Prerequisiti e Azioni Correttive Infrastrutturali

### 2.1. Configurazione Infrastrutturale Esistente e da Allineare

*   Le applicazioni `frontend-student`, `frontend-teacher`, e `frontend-lessons` sono attualmente servite da Nginx (gestito tramite Docker Compose) su percorsi distinti dello stesso dominio principale.
    *   `frontend-student` è servito da `/studenti/` (come da `frontend-student/vite.config.ts`).
    *   `frontend-lessons` è servito da `/lezioni/` (come da `frontend-lessons/vite.config.ts` per la build di produzione, ma accessibile direttamente su una porta diversa in sviluppo, es. `http://localhost:5173`).
    *   `frontend-teacher` è servito da `/docenti/` (come da `nginx.conf`).

*   **Azione Correttiva 1: Aggiornare `frontend-teacher/vite.config.ts`**
    *   **File da modificare:** [`frontend-teacher/vite.config.ts`](frontend-teacher/vite.config.ts)
    *   **Modifica:** Assicurare che la proprietà `base` sia configurata a `'/docenti/'` per le build di produzione.
    *   **Stato:** COMPLETATO.

*   **Azione Correttiva 2: Rivedere e Semplificare le `location` Nginx per `frontend-teacher`**
    *   **File da modificare:** [`nginx.conf`](nginx.conf)
    *   **Modifica:** Rimosse le `location` Nginx superflue per `/assets/`, `/landing`, e `/dashboard` relative a `frontend-teacher`.
    *   **Stato:** COMPLETATO.

*   **Azione Correttiva 3: Aggiornare la Home Page di `frontend-teacher`**
    *   **File da modificare:** [`frontend-teacher/src/router/index.ts`](frontend-teacher/src/router/index.ts)
    *   **Modifica:**
        *   Rimossa la rotta `/landing`.
        *   Impostata la rotta `/` (root) per puntare a `DashboardView.vue` e richiedere autenticazione.
        *   Aggiornate tutte le guardie di navigazione e i redirect interni per puntare alla `dashboard` invece che a `/landing`.
    *   **Stato:** COMPLETATO.

### 2.2. Meccanismo di Single Sign-On (SSO)

*   **Stato Attuale:** Meccanismo di SSO basato su token JWT.
*   **Azione di Verifica/Consolidamento:**
    1.  **Gestione Token JWT via `localStorage`:** I token JWT (Access e Refresh) sono gestiti dai client frontend e memorizzati in `localStorage`. Poiché tutte e tre le applicazioni operano sotto lo stesso dominio principale, `localStorage` è condiviso, permettendo il Single Sign-On.
        *   **Verifica Frontend:** Verificato che ogni applicazione frontend utilizzi un interceptor Axios per leggere il token da `localStorage` (tramite `sharedAuthStore` o direttamente) e allegarlo all'header `Authorization` delle richieste API.
        *   **Stato:** COMPLETATO.
    2.  **Logica di Consumo Sessione e Validazione Token in `frontend-lessons`:**
        *   **All'avvio dell'app ([`frontend-lessons/src/main.ts`](frontend-lessons/src/main.ts)):** `frontend-lessons` ora chiama `checkInitialAuth` dallo store `auth` per caricare lo stato di autenticazione.
            *   **Stato:** COMPLETATO.
        *   **Validazione Token, Popolamento Store, Gestione Token Non Valido/Assente:** La logica esistente negli store `auth.ts` e `sharedAuth.ts` di `frontend-lessons` gestisce questi aspetti.
        *   **Stato:** Confermato.

## 3. Fase di Implementazione: Modifiche ai Frontend (Approccio `<iframe>`)

L'integrazione delle funzionalità di `frontend-lessons` avverrà incorporando le sue pagine tramite `<iframe>` all'interno di `frontend-student` e `frontend-teacher`.

### 3.1. Modifiche a `frontend-student`

1.  **Percorsi di Destinazione in `frontend-lessons`:**
    *   Lezioni Assegnate: `{VITE_LESSONS_APP_URL}/lezioni-assegnate` (es. `http://localhost:5173/lezioni-assegnate` in sviluppo).
2.  **Aggiornamento Menu ([`frontend-student/src/App.vue`](frontend-student/src/App.vue)):**
    *   Il link "Le Mie Lezioni" usa `<router-link>` puntando alla rotta interna `EmbeddedLessons`.
    *   Il link "I Miei Corsi (Lessons)" è stato rimosso.
    *   **Stato:** COMPLETATO.
3.  **Creazione Componente Vista Embedding ([`frontend-student/src/views/EmbeddedLessonsView.vue`](frontend-student/src/views/EmbeddedLessonsView.vue)):**
    *   Creato componente con `<iframe>`. L'attributo `src` è impostato a `{VITE_LESSONS_APP_URL}/lezioni-assegnate?embedded=true`.
    *   **Stato:** COMPLETATO.
4.  **Aggiornamento Router ([`frontend-student/src/router/index.ts`](frontend-student/src/router/index.ts)):**
    *   Aggiunta rotta `/visualizza-lezioni` (`name: 'EmbeddedLessons'`) per `EmbeddedLessonsView.vue`.
    *   **Stato:** COMPLETATO.

### 3.2. Modifiche a `frontend-teacher`

1.  **Percorsi di Destinazione in `frontend-lessons` (per Docenti):**
    *   Materie: `{VITE_LESSONS_APP_URL}/materie`
    *   Argomenti: `{VITE_LESSONS_APP_URL}/argomenti`
    *   Lezioni: `{VITE_LESSONS_APP_URL}/lezioni-docente`
    *   Corsi: `{VITE_LESSONS_APP_URL}/courses`
    *   UDA: `{VITE_LESSONS_APP_URL}/udas`
    *   (dove `VITE_LESSONS_APP_URL` è l'URL base di `frontend-lessons`, es. `http://localhost:5173` in sviluppo).
2.  **Aggiornamento Menu ([`frontend-teacher/src/App.vue`](frontend-teacher/src/App.vue)):**
    *   I link per "Gestione Didattica" usano `<router-link>` puntando a nuove rotte interne (es. `name: 'EmbeddedTeacherSubjects'`).
    *   Il testo dell'intestazione della sezione è "Gestione Didattica".
    *   Gli URL dei link sono stati corretti per puntare direttamente ai path specifici di `frontend-lessons`.
    *   Le icone per le voci "Materie", "Argomenti", "Lezioni", "Corsi", "UDA" sono state aggiornate con icone tematiche più specifiche (`TagIcon`, `LightBulbIcon`, `AcademicCapIcon`, `FolderIcon`, `PuzzlePieceIcon` rispettivamente).
    *   **Stato:** COMPLETATO.
3.  **Creazione Componenti Vista Embedding (in `frontend-teacher/src/views/embedded/`):**
    *   Creati componenti (`EmbeddedTeacherSubjectsView.vue`, `EmbeddedTeacherTopicsView.vue`, ecc.) ognuno con un `<iframe>`.
    *   L'attributo `src` di ogni iframe è impostato all'URL corretto di `frontend-lessons` con `?embedded=true` (es. `{VITE_LESSONS_APP_URL}/materie?embedded=true`).
    *   **Stato:** COMPLETATO.
4.  **Aggiornamento Router ([`frontend-teacher/src/router/index.ts`](frontend-teacher/src/router/index.ts)):**
    *   Aggiunte nuove rotte (es. `/gestione/materie`, `name: 'EmbeddedTeacherSubjects'`) per i componenti embedded.
    *   **Stato:** COMPLETATO.

### 3.3. Modifiche a `frontend-lessons` per Supporto Embedding

1.  **Rimozione Menu e Header da `frontend-lessons` e Modifiche alla Dashboard ([`frontend-lessons/src/App.vue`](frontend-lessons/src/App.vue), [`frontend-lessons/src/views/DashboardView.vue`](frontend-lessons/src/views/DashboardView.vue)):**
    *   Il menu laterale (sidebar) e l'header sono stati completamente rimossi da [`frontend-lessons/src/App.vue`](frontend-lessons/src/App.vue) per eliminare il "flash" del menu quando l'applicazione è caricata in un iframe.
    *   I link di navigazione precedentemente presenti nel menu laterale sono stati aggiunti alla [`frontend-lessons/src/views/DashboardView.vue`](frontend-lessons/src/views/DashboardView.vue), con visibilità basata sul ruolo dell'utente.
    *   Un pulsante di "Logout" è stato aggiunto alla [`DashboardView.vue`](frontend-lessons/src/views/DashboardView.vue) per permettere il logout quando si accede a `frontend-lessons` direttamente (es. per debug).
    *   **Stato:** COMPLETATO.
2.  **Persistenza del Query Parameter `embedded` ([`frontend-lessons/src/router/index.ts`](frontend-lessons/src/router/index.ts)):**
    *   Modificata la guardia `router.beforeEach` per aggiungere `embedded=true` alla query della rotta di destinazione se la navigazione proviene da una rotta già embedded. Questo comportamento rimane cruciale.
    *   **Stato:** COMPLETATO.
3.  **Rimozione Padding in Modalità Embedded ([`frontend-lessons/src/App.vue`](frontend-lessons/src/App.vue)):**
    *   Il padding attorno all'elemento `<main>` in [`frontend-lessons/src/App.vue`](frontend-lessons/src/App.vue) è stato reso condizionale. Viene rimosso quando il query parameter `embedded` è `true`, per migliorare l'integrazione visiva del contenuto dell'iframe.
    *   **Stato:** COMPLETATO.

## 4. Test e Verifica

1.  **Test Azioni Correttive Infrastrutturali:**
    *   Verificare accesso a `frontend-teacher` su `/docenti/` e funzionamento corretto.
    *   Verificare che la home di `frontend-teacher` sia la dashboard.
2.  **Test Funzionalità SSO e Embedding:**
    *   **Studente:** Login in `frontend-student`, navigare a "Le Mie Lezioni". Verificare caricamento `<iframe>` da `frontend-lessons`, autenticazione SSO, e assenza menu di `frontend-lessons`.
    *   **Docente:** Login in `frontend-teacher`, navigare alle sezioni "Gestione Didattica". Verificare caricamento `<iframe>` da `frontend-lessons`, autenticazione SSO, e assenza menu di `frontend-lessons`.
3.  **Test Navigazione e Routing (Embedding):**
    *   Verificare che i link nei menu host puntino alle viste `<iframe>` corrette.
    *   Verificare che gli `<iframe>` carichino gli URL corretti da `frontend-lessons` con `?embedded=true`.
    *   Testare navigazione *interna* a `frontend-lessons` nell'iframe: `?embedded=true` deve persistere e i menu di `frontend-lessons` rimanere nascosti.
4.  **Test Permessi e Ruoli in `frontend-lessons` (embedded):**
    *   Assicurare che i permessi basati sul ruolo siano applicati correttamente.
5.  **Test di Regressione:**
    *   Verificare funzionalità esistenti in `frontend-student` e `frontend-teacher`.
    *   Verificare che `frontend-lessons` funzioni correttamente se acceduta direttamente, inclusa la navigazione tramite i link nella dashboard e la funzionalità di logout.
6.  **Verifica Esperienza Utente con `<iframe>`:**
    *   Valutare scrolling, altezza iframe, coerenza visiva.
    *   Verificare l'assenza di padding attorno al contenuto di `frontend-lessons` quando visualizzato nell'iframe (modalità embedded).

## 5. Considerazioni Aggiuntive

*   **Variabili d'Ambiente:** Cruciale configurare `VITE_LESSONS_APP_URL` in `frontend-student` e `frontend-teacher` (es. `http://localhost:5173` per sviluppo `frontend-lessons`).
*   **Gestione Cache:** Invalidare cache del browser dopo il deploy.
*   **Styling e Altezza `<iframe>`:** L'altezza è statica. Considerare soluzioni dinamiche (es. `iframe-resizer`, `postMessage`) per miglioramenti futuri.
*   **Comunicazione tra Frame:** Usare `window.postMessage()` se necessaria comunicazione complessa.
*   **Sicurezza `<iframe>`:** Valutare attributi `sandbox` e `allow`.
*   **Alternative Future a `<iframe>`:** Per maggiore integrazione, considerare architetture Micro-Frontend (MFE).

Questo piano aggiornato riflette l'approccio di integrazione tramite `<iframe>` per mantenere il layout dell'applicazione host.
## 6. Debug e Risoluzione Problemi SSO (Post-Integrazione)

Durante i test successivi all'integrazione iniziale, è emerso un problema specifico relativo al Single Sign-On (SSO) quando uno studente, dopo essersi autenticato in `frontend-student` e aver navigato alle lezioni (caricate da `frontend-lessons` in un iframe), effettuava un logout e un nuovo login in `frontend-student`. Al successivo accesso alla sezione delle lezioni, `frontend-lessons` non riconosceva il nuovo stato di autenticazione, risultando in errori (es. "Given token not valid for any token type" durante tentativi di refresh del token) o in un reindirizzamento alla pagina di login errata (quella per docenti/admin) all'interno dell'iframe.

### 6.1. Causa Principale Identificata (Iterativa)

L'indagine ha rivelato una catena di problemi:

1.  **Inizialmente**: Si sospettava un problema nella logica di refresh del token o nella gestione del ruolo utente in `frontend-lessons`.
2.  **Successivamente**: È emerso che gli interceptor Axios configurati in `frontend-lessons/src/services/apiClient.ts` non venivano eseguiti, probabilmente a causa di problemi di caching di Vite o HMR che servivano una versione obsoleta del modulo all'iframe. Un workaround che prevedeva la creazione di un'istanza Axios locale con interceptor duplicati in `frontend-lessons/src/stores/lessons.ts` ha confermato che gli interceptor funzionavano se eseguiti.
3.  **Poi**: Il problema si è spostato sulla lettura di `localStorage` da parte di `frontend-lessons`, che trovava dati nulli nonostante `frontend-student` sembrasse aggiornare correttamente il suo store Pinia.
4.  **Infine (Causa Attuale)**: È stato scoperto che `pinia-plugin-persistedstate` in `frontend-student` non stava scrivendo correttamente lo stato aggiornato dello `sharedAuthStore` (in particolare l'oggetto `user`) in `localStorage`. Anche dopo aver corretto la configurazione `paths` del plugin, `localStorage` rimaneva con dati nulli per `user` e `accessToken` dopo un login, come verificato leggendo `localStorage` direttamente da `frontend-student`. Successivamente, si è determinato che, anche con una scrittura manuale in `localStorage` da `frontend-student`, l'iframe `frontend-lessons` non vedeva queste modifiche in modo tempestivo o affidabile.

La causa principale definitiva è una **mancata o ritardata sincronizzazione dello stato di `localStorage` tra l'applicazione host (`frontend-student`) e l'applicazione caricata nell'iframe (`frontend-lessons`)**. `frontend-lessons` legge una versione di `localStorage` che non riflette gli aggiornamenti più recenti effettuati da `frontend-student`.

### 6.2. Indagini e Tentativi di Correzione Dettagliati

Il processo di debug ha incluso i seguenti passaggi principali:

1.  **Analisi della Logica di Autenticazione in `frontend-lessons`**:
    *   Verifica e robustezza delle funzioni `checkInitialAuth` e `refreshTokenAction`.
    *   Aggiunta di tentativi di idratazione manuale da `localStorage` in `checkInitialAuth`, incluso un secondo tentativo con ritardo.

2.  **Verifica degli Interceptor Axios**:
    *   Aggiunta di interceptor di risposta in `frontend-lessons/src/services/apiClient.ts`.
    *   Diagnosi della mancata esecuzione di tale modulo e workaround con istanza Axios locale in `frontend-lessons/src/stores/lessons.ts`.

3.  **Analisi della Persistenza Pinia in `frontend-student`**:
    *   Correzione della configurazione `paths` per `pinia-plugin-persistedstate` in `frontend-student/src/stores/sharedAuth.ts` per includere `user`.
    *   Semplificazione a `persist: true` per escludere errori di configurazione `paths`.
    *   Aggiunta di log per verificare il contenuto di `localStorage` subito dopo le operazioni di scrittura da `frontend-student`.

4.  **Implementazione di Scrittura Manuale in `localStorage` da `frontend-student`**:
    *   Modificate le azioni `setAuthData` e `clearAuthData` in `frontend-student/src/stores/sharedAuth.ts` per scrivere/pulire manualmente `localStorage` (chiave `sharedAuth`), bypassando `pinia-plugin-persistedstate` per la scrittura. Questo ha confermato che `frontend-student` scriveva correttamente i dati.

### 6.3. Soluzione Attualmente in Corso di Verifica: Comunicazione Esplicita Host -> Iframe tramite `postMessage`

Data l'inaffidabilità della sincronizzazione di `localStorage` tra l'host e l'iframe, si è implementato un meccanismo di comunicazione esplicita:

1.  **Invio Messaggio da Host (`frontend-student`):**
    *   Le azioni `setAuthData` e `clearAuthData` in `frontend-student/src/stores/sharedAuth.ts` sono state modificate per:
        *   Continuare ad aggiornare manualmente `localStorage`.
        *   Ottenere un riferimento all'iframe (assumendo un ID come `lessons-iframe`).
        *   Utilizzare `iframe.contentWindow.postMessage()` per inviare un messaggio a `frontend-lessons`.
        *   Il messaggio per l'aggiornamento include `{ type: 'AUTH_STATE_UPDATED', payload: stateToPersist }` (dove `stateToPersist` contiene `user`, `accessToken`, `refreshToken`, ecc.).
        *   Il messaggio per la pulizia è `{ type: 'AUTH_STATE_CLEARED' }`.
    *   L'origine target per `postMessage` è specificata per sicurezza (derivata da `VITE_LESSONS_APP_URL` di `frontend-student`).

2.  **Ricezione Messaggio nell'Iframe (`frontend-lessons`):**
    *   Il file `frontend-lessons/src/main.ts` è stato modificato per aggiungere un `window.addEventListener('message', ...)`.
    *   Quando viene ricevuto un messaggio di tipo `AUTH_STATE_UPDATED` (e l'origine è verificata), `frontend-lessons` usa il `payload` per chiamare `setAuthData` sul suo `sharedAuthStore`.
    *   Quando viene ricevuto `AUTH_STATE_CLEARED`, chiama `clearAuthData`.
    *   Dopo l'aggiornamento dello store, viene richiamata `authStore.checkInitialAuth()` per riesaminare lo stato di autenticazione e, se necessario, gestire i reindirizzamenti (es. se l'utente è ora autenticato ma si trova su una pagina di login).

Questo approccio mira a garantire che `frontend-lessons` sia notificato direttamente e aggiorni il suo stato di autenticazione in modo affidabile quando l'autenticazione cambia in `frontend-student`. La verifica di questa soluzione è l'attività corrente.