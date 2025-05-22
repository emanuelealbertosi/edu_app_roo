# Piano di Integrazione Menu Frontend

**Versione:** 1.1
**Data:** 22 Maggio 2025 (Aggiornato)
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
    *   **Stato:** COMPLETATO.
3.  **Creazione Componenti Vista Embedding (in `frontend-teacher/src/views/embedded/`):**
    *   Creati componenti (`EmbeddedTeacherSubjectsView.vue`, `EmbeddedTeacherTopicsView.vue`, ecc.) ognuno con un `<iframe>`.
    *   L'attributo `src` di ogni iframe è impostato all'URL corretto di `frontend-lessons` con `?embedded=true` (es. `{VITE_LESSONS_APP_URL}/materie?embedded=true`).
    *   **Stato:** COMPLETATO.
4.  **Aggiornamento Router ([`frontend-teacher/src/router/index.ts`](frontend-teacher/src/router/index.ts)):**
    *   Aggiunte nuove rotte (es. `/gestione/materie`, `name: 'EmbeddedTeacherSubjects'`) per i componenti embedded.
    *   **Stato:** COMPLETATO.

### 3.3. Modifiche a `frontend-lessons` per Supporto Embedding

1.  **Nascondere Menu in Modalità Embedded ([`frontend-lessons/src/App.vue`](frontend-lessons/src/App.vue)):**
    *   Aggiunta logica per leggere il query parameter `embedded` dall'URL.
    *   L'header e la sidebar di `frontend-lessons` sono nascosti se `embedded=true`.
    *   **Stato:** COMPLETATO.
2.  **Persistenza del Query Parameter `embedded` ([`frontend-lessons/src/router/index.ts`](frontend-lessons/src/router/index.ts)):**
    *   Modificata la guardia `router.beforeEach` per aggiungere `embedded=true` alla query della rotta di destinazione se la navigazione proviene da una rotta già embedded.
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
    *   Verificare che `frontend-lessons` funzioni correttamente (con i suoi menu) se acceduta direttamente.
6.  **Verifica Esperienza Utente con `<iframe>`:**
    *   Valutare scrolling, altezza iframe, coerenza visiva.

## 5. Considerazioni Aggiuntive

*   **Variabili d'Ambiente:** Cruciale configurare `VITE_LESSONS_APP_URL` in `frontend-student` e `frontend-teacher` (es. `http://localhost:5173` per sviluppo `frontend-lessons`).
*   **Gestione Cache:** Invalidare cache del browser dopo il deploy.
*   **Styling e Altezza `<iframe>`:** L'altezza è statica. Considerare soluzioni dinamiche (es. `iframe-resizer`, `postMessage`) per miglioramenti futuri.
*   **Comunicazione tra Frame:** Usare `window.postMessage()` se necessaria comunicazione complessa.
*   **Sicurezza `<iframe>`:** Valutare attributi `sandbox` e `allow`.
*   **Alternative Future a `<iframe>`:** Per maggiore integrazione, considerare architetture Micro-Frontend (MFE).

Questo piano aggiornato riflette l'approccio di integrazione tramite `<iframe>` per mantenere il layout dell'applicazione host.