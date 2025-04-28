# Piano di Refactoring Autenticazione

**Nota:** Tutti i comandi CLI in questo piano assumono l'uso di **PowerShell**.

Questo documento descrive il piano per modificare il sistema di autenticazione dell'applicazione educativa per allinearlo allo schema fornito e gestire login separati per Studenti e Docenti/Admin.

## 1. Obiettivo

Implementare un flusso di login che:
1.  Presenti un form unificato o con selezione per login Docente/Admin (username/password) e Studente (codice/PIN).
2.  Chiami endpoint API distinti per i due tipi di login.
3.  Dopo il login, reindirizzi l'utente a una pagina "hub" (`LandingView`).
4.  La `LandingView` mostri link alle sezioni appropriate (`frontend-student`, `frontend-teacher`, `frontend-lessons`) in base al ruolo dell'utente.
5.  Il componente `frontend-lessons` si adatti al contesto del ruolo (Studente o Docente/Admin), preferibilmente usando Pinia per la gestione dello stato.

## 2. Endpoint API Identificati

*   **Login Docente/Admin:** `POST /api/auth/token/` (Richiede: `username`, `password`. Restituisce: JWT standard)
*   **Login Studente:** `POST /api/auth/student/login/` (Richiede: `student_code`, `pin`. Restituisce: JWT con claim `is_student: True` e dati studente)
*   **Recupero Dati Utente (Docente/Admin):** `GET /api/admin/users/me/` (Richiede: JWT Docente/Admin valido. Restituisce: Dati utente incluso il ruolo)

## 3. Piano Dettagliato

*   **Fase 1: Analisi Backend Autenticazione (Completata)**
    *   Identificati i due distinti endpoint di login e i dati che restituiscono.

*   **Fase 2: Modifica/Creazione Form di Login Frontend**
    *   Creare/adattare il form Vue.js per permettere all'utente di scegliere se loggarsi come Docente/Admin (username/password) o Studente (codice/PIN).
    *   Il form chiamerà l'endpoint API corretto (`/api/auth/token/` o `/api/auth/student/login/`) in base alla scelta e ai dati inseriti.

*   **Fase 3: Implementazione Logica Post-Login Frontend**
    1.  Dopo una risposta API di successo da *uno qualsiasi* dei due endpoint:
    2.  Ottenere il token JWT.
    3.  Ispezionare il payload del token per il claim `is_student`.
    4.  Se `is_student` è `True`, salvare il ruolo "Studente" nello store Pinia.
    5.  Altrimenti, chiamare `GET /api/admin/users/me/` per ottenere i dati dell'utente (incluso il ruolo "Docente" o "Admin") e salvarli nello store Pinia.
    6.  Salvare il token JWT nello store Pinia (o `localStorage`).
    7.  Reindirizzare l'utente alla nuova pagina `LandingView` (es. `/landing`).

*   **Fase 4: Creazione Pagina `LandingView` (Frontend)**
    1.  Creare il componente `LandingView.vue`.
    2.  Aggiungere la rotta `/landing` nel router Vue.
    3.  Nel componente, leggere il ruolo dallo store Pinia.
    4.  Mostrare condizionalmente i link/schede:
        *   Studente: Link a `frontend-student` (es. `/student/dashboard`) e `frontend-lessons` (es. `/lessons/student`).
        *   Docente/Admin: Link a `frontend-teacher` (es. `/teacher/dashboard`) e `frontend-lessons` (es. `/lessons/teacher`).

*   **Fase 5: Adeguamento `frontend-lessons`**
    1.  Definire le rotte (es. `/lessons/student`, `/lessons/teacher`).
    2.  Il componente `frontend-lessons` userà **Pinia** per ottenere il contesto del ruolo e adattare la visualizzazione/funzionalità.

*   **Fase 6: Gestione Logout**
    1.  Implementare la logica di logout (rimozione token/dati utente dallo store, redirect alla pagina di login iniziale) accessibile da tutte le sezioni post-login (`LandingView`, `frontend-student`, `frontend-teacher`, `frontend-lessons`).

## 4. Diagramma del Flusso

```mermaid
graph TD
    A[Pagina Iniziale / Login Form] --> B{Utente sceglie tipo login?};
    B -- Docente/Admin --> C(Inserisce User/Pass);
    B -- Studente --> D(Inserisce Codice/PIN);
    C --> E(Frontend chiama POST /api/auth/token/);
    D --> F(Frontend chiama POST /api/auth/student/login/);
    E --> G{Backend risponde OK?};
    F --> G;
    G -- Sì (JWT) --> H{Frontend: Ispeziona JWT};
    H -- Claim 'is_student' presente? --> I(Salva Ruolo='Studente' in Store);
    H -- Claim 'is_student' assente --> J(Frontend chiama GET /api/admin/users/me/);
    J -- Backend risponde con dati utente --> K(Salva Ruolo='Docente/Admin' in Store);
    I --> L(Salva JWT in Store);
    K --> L;
    L --> M(Frontend: Redirect a /landing);
    G -- No --> A;
    M --> N(Pagina LandingView);
    N -- Legge Ruolo da Store --> O{Mostra Link/Schede};
    O -- Ruolo Studente --> P[Link a frontend-student (/student/...)];
    O -- Ruolo Studente --> Q[Link a frontend-lessons (/lessons/student)];
    O -- Ruolo Docente/Admin --> R[Link a frontend-teacher (/teacher/...)];
    O -- Ruolo Docente/Admin --> S[Link a frontend-lessons (/lessons/teacher)];
    P -- Click --> T(App: frontend-student);
    Q -- Click --> U(App: frontend-lessons [contesto=student]);
    R -- Click --> V(App: frontend-teacher);
    S -- Click --> W(App: frontend-lessons [contesto=teacher]);
    T -- Logout --> X{Frontend: Logica Logout};
    U -- Logout --> X;
    V -- Logout --> X;
    W -- Logout --> X;
    X -- Token Rimosso & Redirect --> A;