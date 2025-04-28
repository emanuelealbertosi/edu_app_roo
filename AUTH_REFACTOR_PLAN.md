# Piano di Refactoring Autenticazione

**Nota:** Tutti i comandi CLI in questo piano assumono l'uso di **PowerShell**.

Questo documento descrive il piano per modificare il sistema di autenticazione dell'applicazione educativa per allinearlo allo schema fornito e gestire login separati per Studenti e Docenti/Admin.

## 1. Obiettivo

Implementare un flusso di login che:
1.  Presenti pagine di login separate per Docente/Admin (username/password) e Studente (codice/PIN).
2.  Chiami endpoint API distinti per i due tipi di login.
3.  Utilizzi uno store Pinia condiviso (`sharedAuth.ts`) per centralizzare lo stato di autenticazione (token, dati utente essenziali, ruolo).
4.  Dopo il login, reindirizzi l'utente a una pagina "hub" (`/landing`, gestita da `frontend-teacher`).
5.  La `LandingView` mostri link (tag `<a>`) alle sezioni appropriate (`frontend-student`, `frontend-teacher`, `frontend-lessons`) in base al ruolo letto dallo store condiviso.
6.  Le applicazioni `frontend-student`, `frontend-teacher`, e `frontend-lessons` utilizzino lo store condiviso per la logica dipendente dall'autenticazione e dal ruolo.

## 2. Endpoint API Identificati

*   **Login Docente/Admin:** `POST /api/auth/token/` (Richiede: `username`, `password`. Restituisce: JWT standard)
*   **Login Studente:** `POST /api/auth/student/login/` (Richiede: `student_code`, `pin`. Restituisce: JWT con claim `is_student: True` e dati studente)
*   **Recupero Dati Utente (Docente/Admin):** `GET /api/admin/users/me/` (Richiede: JWT Docente/Admin valido. Restituisce: Dati utente incluso il ruolo)

## 3. Piano Dettagliato (Revisionato)

*   **Fase 1: Analisi Backend Autenticazione (Completata)**
    *   Identificati i due distinti endpoint di login e i dati che restituiscono.

*   **Fase 2: Creazione Store Condiviso (Completata)**
    *   Creato `frontend-teacher/src/stores/sharedAuth.ts` con stato (user, accessToken, refreshToken, loading, error) e azioni (setAuthData, clearAuthData, setLoading, setError).
    *   Copiato `sharedAuth.ts` in `frontend-student/src/stores/` e `frontend-lessons/src/stores/`.

*   **Fase 3: Integrazione Store Condiviso (Completata)**
    *   Modificato `frontend-teacher/src/stores/auth.ts` (rinominato `authTeacher`) per usare `sharedAuthStore`, delegare stato/azioni comuni, e mappare `TeacherUser` a `SharedUser`.
    *   Modificato `frontend-student/src/stores/auth.ts` (rinominato `authStudent`) per usare `sharedAuthStore`, delegare stato/azioni comuni, e mappare `StudentData` a `SharedUser` (aggiungendo `role: 'STUDENT'`).
    *   Modificato `frontend-student/src/views/GroupTokenRegistrationView.vue` per usare `sharedAuthStore.setAuthData` dopo la registrazione.
    *   Modificato `frontend-lessons/src/App.vue` per usare `sharedAuthStore` per la logica condizionale (v-if) e logout.
    *   Modificato `frontend-lessons/src/router/index.ts` per usare `sharedAuthStore` nella navigation guard `beforeEach`.

*   **Fase 4: Creazione Pagina `LandingView` e Routing (Completata)**
    1.  Creato il componente `frontend-teacher/src/views/LandingView.vue`.
    2.  Aggiunta la rotta `/landing` nel router di `frontend-teacher`.
    3.  Il componente `LandingView` legge ruolo/utente da `sharedAuthStore` e mostra link condizionali (usando tag `<a>` con `href`) alle altre applicazioni.

*   **Fase 5: Aggiornamento Redirect Post-Login (Completata)**
    *   Modificato `frontend-teacher/src/views/LoginView.vue` per reindirizzare a `/landing` (usando `router.push({ name: 'landing' })`).
    *   Modificato `frontend-student/src/views/LoginView.vue` per reindirizzare a `/landing` (usando `window.location.href = '/landing';`).
    *   Modificato `frontend-student/src/views/GroupTokenRegistrationView.vue` per reindirizzare a `/landing` (usando `window.location.href = '/landing';`).

*   **Fase 6: Modifica Pagina Iniziale Statica (Completata)**
    *   Modificato `index.html` nella root per mostrare logo e un singolo pulsante "Accedi" che punta a `/landing`.

*   **Fase 7: Verifica Configurazione Docker/Nginx (Completata)**
    *   Analizzare `docker-compose.prod.yml`, `docker-compose.local-prod-test.yml`, `docker-compose.prod.static.yml`.
    *   Analizzare `nginx.conf`.
    *   Identificare e applicare modifiche necessarie a `nginx.conf` per supportare il nuovo routing (es. gestione `/landing`, nome servizio backend).

*   **Fase 8: Gestione Logout (Parzialmente Completata)**
    *   Le azioni di logout negli store specifici (`authTeacher`, `authStudent`) e in `frontend-lessons/App.vue` ora chiamano `sharedAuth.clearAuthData()` e reindirizzano alla root (`/`) tramite `window.location.href`.

## 4. Passi Svolti Dettagliati

1.  Analizzato `design_document.md` e schema immagine.
2.  Proposto piano iniziale.
3.  Chiariti requisiti su pagina intermedia e login differenziato.
4.  Analizzato `apps/users/views.py` per identificare `StudentLoginView`.
5.  Analizzato `config/urls.py` e `apps/users/urls.py` per identificare endpoint API (`/api/auth/token/` e `/api/auth/student/login/`).
6.  Proposto piano rivisto con store condiviso e landing page.
7.  Creato branch Git `singlesignon`.
8.  Creato store condiviso `frontend-teacher/src/stores/sharedAuth.ts`.
9.  Integrato store condiviso in `frontend-teacher/src/stores/auth.ts`.
10. Integrato store condiviso in `frontend-student/src/stores/auth.ts`.
11. Integrato store condiviso in `frontend-student/src/views/GroupTokenRegistrationView.vue`.
12. Copiato `sharedAuth.ts` in `frontend-student/src/stores/`.
13. Aggiornati percorsi import in `frontend-student/src/stores/auth.ts` e `frontend-student/src/views/GroupTokenRegistrationView.vue`.
14. Creato componente `frontend-teacher/src/views/LandingView.vue`.
15. Corretti link esterni in `LandingView.vue` (usando `<a>` invece di `<router-link>`).
16. Aggiunta rotta `/landing` a `frontend-teacher/src/router/index.ts`.
17. Aggiornato redirect post-login in `frontend-teacher/src/views/LoginView.vue`.
18. Aggiornato redirect post-login in `frontend-student/src/views/LoginView.vue`.
19. Aggiornato redirect post-registrazione in `frontend-student/src/views/GroupTokenRegistrationView.vue`.
20. Copiato `sharedAuth.ts` in `frontend-lessons/src/stores/`.
21. Integrato store condiviso in `frontend-lessons/src/App.vue`.
22. Integrato store condiviso in `frontend-lessons/src/router/index.ts`.
23. Verificato assenza di link `<router-link>`/`router.push` verso `frontend-lessons` da altre app.
24. Modificato `index.html` root come richiesto.
25. Analizzato `docker-compose.prod.yml` e `nginx.conf`.
26. Modificato `nginx.conf` per correggere nome servizio backend e aggiungere gestione `/` e `/landing`.
27. Corretto nome servizio backend in `nginx.conf` da `web` a `backend` (verifica post-modifica precedente).
28. Modificati `vite.config.ts` di `frontend-student`, `frontend-teacher`, `frontend-lessons` per usare `base` URL condizionale (percorso specifico in build, `/` in dev) per risolvere problemi di routing locale.
29. Corretto nome rotta in `frontend-teacher/LandingView.vue` da `Dashboard` a `dashboard` per risolvere errore `No match for...`.
30. Corretta posizione commento HTML in `frontend-teacher/LandingView.vue` per risolvere errore `InvalidCharacterError`.
31. Corretta chiamata in `frontend-student/DashboardView.vue` da `authStore.checkAuth()` (inesistente) a `authStore.isAuthenticated` per risolvere `TypeError`.
32. Aggiunta funzione `fetchCurrentStudent` a `frontend-student/src/api/auth.ts` per recuperare dati studente autenticato (assumendo endpoint `/api/auth/student/me/`).
33. Aggiunta azione `initializeAuth` a `frontend-student/src/stores/auth.ts` per popolare lo stato utente all'avvio tramite `fetchCurrentStudent`.
34. Modificato `frontend-student/src/main.ts` per chiamare `initializeAuth` prima del mount dell'app.
35. Modificata view `StudentProtectedTestView` in `apps/users/views.py` (associata a `/student/test-auth/`) per restituire dati studente completi invece del solo ID, risolvendo il blocco dell'inizializzazione in `frontend-student`.

## 5. Diagramma del Flusso (Aggiornato)

```mermaid
graph TD
    A[Pagina Iniziale /index.html] --> B(Click 'Accedi');
    B --> C[/landing];
    C -- Richiesta a Nginx --> D{Nginx Proxy};
    D -- Inoltra a frontend-teacher --> E(App: frontend-teacher);
    E -- Router carica LandingView --> F[Componente: LandingView];
    F -- Legge sharedAuth --> G{Utente Autenticato?};
    G -- No --> H(Guardia Router frontend-teacher);
    H -- Redirect a Login --> I[/login/docente-admin]; % O altra login di default
    I -- Richiesta a Nginx --> D;
    D -- Inoltra a frontend-lessons? --> J(App: frontend-lessons); % Assumendo /login/* vada qui
    J -- Router carica Login Docente --> K[Vista Login Docente/Admin];
    K -- Inserisce User/Pass --> L(Chiama POST /api/auth/token/);
    L -- Richiesta a Nginx --> D;
    D -- Inoltra a backend --> M(Servizio: web);
    M -- Risponde OK (JWT) --> D;
    D -- Risposta a frontend-lessons --> K;
    K -- authTeacher.login --> N(authTeacher: fetchUserProfile);
    N -- Chiama GET /api/admin/users/me/ --> L; % Riutilizza chiamata API
    M -- Risponde con UserData --> D;
    D -- Risposta a frontend-lessons --> N;
    N -- sharedAuth.setAuthData --> O(Store Condiviso Aggiornato);
    K -- Redirect a /landing --> C; % Ritorna a /landing

    G -- Sì --> P{Ruolo?};
    P -- Studente --> Q[Link /studenti/...];
    P -- Studente --> R[Link /lezioni/studente];
    P -- Docente/Admin --> S[Link /docenti/...];
    P -- Docente/Admin --> T[Link /lezioni/docente];
    Q -- Click (href) --> U[/studenti/...];
    R -- Click (href) --> V[/lezioni/studente];
    S -- Click (href) --> W[/docenti/...];
    T -- Click (href) --> X[/lezioni/docente];

    U -- Richiesta a Nginx --> D;
    D -- Inoltra a frontend-student --> Y(App: frontend-student);
    V -- Richiesta a Nginx --> D;
    D -- Inoltra a frontend-lessons --> J;
    W -- Richiesta a Nginx --> D;
    D -- Inoltra a frontend-teacher --> E;
    X -- Richiesta a Nginx --> D;
    D -- Inoltra a frontend-lessons --> J;

    subgraph Login Studente
        Z[/login/studente];
        Z -- Richiesta a Nginx --> D;
        D -- Inoltra a frontend-lessons? --> J;
        J -- Router carica Login Studente --> AA[Vista Login Studente];
        AA -- Inserisce Codice/PIN --> BB(Chiama POST /api/auth/student/login/);
        BB -- Richiesta a Nginx --> D;
        D -- Inoltra a backend --> M;
        M -- Risponde OK (JWT + StudentData) --> D;
        D -- Risposta a frontend-lessons --> AA;
        AA -- authStudent.login --> CC(Mappa a SharedUser);
        CC -- sharedAuth.setAuthData --> O;
        AA -- Redirect a /landing --> C;
    end

    subgraph Logout
        F -- Click Logout --> DD(sharedAuth.clearAuthData);
        Y -- Click Logout --> DD;
        E -- Click Logout --> DD;
        J -- Click Logout --> DD;
        DD --> EE(window.location.href = '/');
        EE --> A;
    end
36. Debug errore 404 su `/landing`: Verificato `index.html` (OK), `nginx.conf` (OK), `frontend-teacher/router/index.ts` (OK).
37. Analizzati log Docker (`nginx-proxy`, `frontend-teacher`): Identificato errore 404 proveniente da Nginx interno a `frontend-teacher` a causa di configurazione SPA mancante (`try_files` non applicato a `/landing`).
38. Modificato `frontend-teacher/nginx.conf` per aggiungere `location / { try_files $uri $uri/ /index.html; }` e servire correttamente la SPA dalla root.
39. Debug pagina bianca e errori MIME su `/landing`: Identificato problema con `base: '/docenti/'` in `frontend-teacher/vite.config.ts` che causava richieste asset errate (`/docenti/assets/...`).
40. Modificato `frontend-teacher/vite.config.ts` per usare `base: '/'`.
41. Debug errori MIME residui su `/landing` (richieste `/assets/...`): Identificato problema con proxy Nginx esterno (`nginx.conf` root) che non inoltrava `/assets/` a `frontend-teacher`, ma li cercava nella sua root.
42. Modificato `nginx.conf` (root) per aggiungere `location /assets/ { proxy_pass http://frontend-teacher:80; }` prima della `location /` generica.
43. Debug pagina bianca su `/lezioni/docente`: Identificato problema di stato Pinia non condiviso/persistito tra `frontend-teacher` e `frontend-lessons`.
44. Installato `pinia-plugin-persistedstate` tramite npm nelle directory `frontend-teacher`, `frontend-lessons`, `frontend-student`.
45. Configurato `pinia-plugin-persistedstate` importandolo e usandolo con `createPinia()` nei file `main.ts` delle tre app frontend.
46. Abilitata persistenza aggiungendo `{ persist: true }` come secondo argomento di `defineStore` nei file `sharedAuth.ts` delle tre app frontend.
47. Debug errore 401 (Unauthorized) su chiamata API da `/lezioni/docente`: Identificato uso chiave `localStorage` errata (`accessToken` invece di `shared_access_token`) nell'interceptor Axios in `frontend-lessons/src/services/api.ts`.
48. Corretta chiave `localStorage` in `frontend-lessons/src/services/api.ts` a `shared_access_token`.
49. Debug pagina bianca iniziale (senza errori console) su `/lezioni/docente`: Identificata mancanza di una rotta corrispondente a `/docente` (risultato della riscrittura Nginx interna) nel router di `frontend-lessons`.
50. Aggiunta rotta `{ path: '/docente', name: 'teacher-landing', component: () => import('../views/TeacherLessonListView.vue'), meta: { requiresAuth: true, roles: ['Docente', 'Teacher', 'TEACHER'] } }` a `frontend-lessons/src/router/index.ts`.
51. Debug login studente (caricamento infinito): Analizzato `frontend-student/stores/auth.ts` (`initializeAuth`) e `sharedAuth.ts`. Identificato che la condizione `!sharedAuth.user` in `initializeAuth` era falsa a causa della persistenza Pinia che ripristinava sia token che utente.
52. Corretto `frontend-student/stores/sharedAuth.ts`: Rimosso accesso manuale a `localStorage` per token, affidandosi a `pinia-plugin-persistedstate`.
53. Corretto `frontend-student/router/index.ts`: Modificate guardie `beforeEach` e `beforeEnter` per usare `sharedAuth.isAuthenticated` (dallo store Pinia) invece di `AuthService.isAuthenticated`.
54. Debug login studente (redirect a login/dashboard docente): Identificato che la guardia `beforeEach` in `frontend-teacher/router/index.ts` usava lo store specifico del docente (`authTeacher`) invece di `sharedAuth`.
55. Corretto `frontend-teacher/router/index.ts`: Modificata guardia `beforeEach` per usare `sharedAuth`, permettere accesso a `/landing` a tutti gli utenti autenticati e limitare le altre rotte protette a 'TEACHER'/'ADMIN'. Corretto errore TS `Cannot find name 'SharedUser'`.
56. Debug `DOMException: String contains an invalid character` su `/landing`: Corretta posizione commento HTML in `frontend-teacher/views/LandingView.vue`.
57. Debug sidebar docente visibile su `/landing`: Modificato `frontend-teacher/App.vue` per usare `sharedAuth.isAuthenticated` e aggiunto controllo `route.name !== 'landing'` per nascondere sidebar/header su quella rotta specifica.
58. Modificato `frontend-teacher/views/LandingView.vue` per usare layout a card per i link ai portali, ispirandosi all'immagine fornita.
59. Corretto errore CSS (parentesi graffa extra) in `frontend-teacher/views/LandingView.vue`.
60. Corretto errore 401 (Unauthorized) su chiamate API da `frontend-lessons` come studente: Modificato interceptor Axios in `frontend-lessons/src/services/api.ts` per leggere il token dallo stato persistito di `sharedAuth` in `localStorage`.
61. Modificato `index.html` per far puntare il pulsante "Accedi" a `/studenti/login` come default.
62. Verificato che `frontend-student/src/views/LoginView.vue` contenesse già il link a `/docenti/login`.
63. Corretto routing per login docente: Modificato `path` della rotta `login` in `frontend-teacher/src/router/index.ts` da `/login` a `/docenti/login`.
64. Modificato `index.html` per mostrare due pulsanti di accesso separati ("Accedi come Studente" e "Accedi come Docente") con stili distinti.
65. Nascosta temporaneamente l'opzione "Template Percorso" in `frontend-teacher/src/views/AssignmentView.vue` aggiungendo `v-if="false"`.
66. Aggiunto montaggio volume per `logo.png` in `/usr/share/nginx/html/logo.png` nel servizio `nginx-proxy` dei file `docker-compose.prod.yml`, `docker-compose.prod.static.yml`, `docker-compose.local-prod-test.yml` per renderlo accessibile a `index.html`.
67. Modificati link "Portale Lezioni" in `frontend-teacher/views/LandingView.vue` per puntare a `/lezioni/dashboard` per entrambi i ruoli.
68. Verificato che la rotta `/dashboard` in `frontend-lessons/src/router/index.ts` fosse già esistente e accessibile a tutti gli utenti autenticati.
69. Semplificato `frontend-lessons/src/views/DashboardView.vue` rimuovendo la visualizzazione del ruolo e la sezione "Azioni Rapide".