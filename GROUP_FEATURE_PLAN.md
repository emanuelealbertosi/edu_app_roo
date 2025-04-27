# Piano di Progettazione: Funzionalità Gruppi di Studenti

**Versione:** 1.1 (Aggiornamento del 24 Aprile 2025)

**Obiettivo:** Introdurre la possibilità per i Docenti di creare Gruppi, assegnare Studenti ai Gruppi, generare link di registrazione specifici per Gruppo e gestire assegnazioni (Quiz, Percorsi, **Lezioni**, disponibilità Ricompense) e revoche a livello di Gruppo.

---

## 1. Modifiche allo Schema del Database

Introdurremo due nuove tabelle principali: `STUDENT_GROUP` e `STUDENT_GROUP_MEMBERSHIP`. Aggiorneremo anche le relazioni per le assegnazioni.

```mermaid
erDiagram
    USER ||--o{ STUDENT : "è_docente_di"
    USER ||--o{ QUIZ_TEMPLATE : "creato_da (Admin)"
    USER ||--o{ QUIZ : "creato_da (Docente)"
    USER ||--o{ PATHWAY : "creato_da (Docente)"
    USER ||--o{ LESSON : "creato_da (Docente)" # NUOVA RELAZIONE (se modello Lesson esiste)
    USER ||--o{ REWARD_TEMPLATE : "creato_da (Admin/Docente)"
    USER ||--o{ REWARD : "creato_da (Docente)"
    USER ||--o{ REWARD_PURCHASE : "consegnato_da"
    USER ||--o{ STUDENT_GROUP : "creato_da (Docente)" # NUOVA RELAZIONE

    STUDENT ||--o{ QUIZ_ATTEMPT : "svolge"
    STUDENT ||--o{ PATHWAY_PROGRESS : "progredisce_in"
    STUDENT ||--o{ WALLET : "possiede"
    STUDENT ||--o{ REWARD_PURCHASE : "acquista"
    STUDENT }|..|{ REWARD : "disponibile_per (specifico)"
    STUDENT ||--|{ STUDENT_GROUP_MEMBERSHIP : "appartiene_a" # NUOVA RELAZIONE

    WALLET ||--o{ POINT_TRANSACTION : "ha_transazioni"

    QUIZ_TEMPLATE ||--o{ QUESTION_TEMPLATE : "contiene"
    QUIZ ||--o{ QUESTION : "contiene"
    QUIZ ||--o{ QUIZ_ATTEMPT : "ha_tentativi"
    QUIZ ||--|{ QUIZ_ASSIGNMENT : "è_assegnato_via" # NUOVA TABELLA/RELAZIONE

    QUESTION_TEMPLATE ||--o{ ANSWER_OPTION_TEMPLATE : "ha_opzioni"
    QUESTION ||--o{ ANSWER_OPTION : "ha_opzioni"
    QUESTION ||--o{ STUDENT_ANSWER : "ha_risposte"

    QUIZ_ATTEMPT ||--o{ STUDENT_ANSWER : "contiene"

    PATHWAY ||--o{ PATHWAY_QUIZ : "contiene"
    PATHWAY ||--o{ PATHWAY_PROGRESS : "ha_progressi"
    PATHWAY ||--|{ PATHWAY_ASSIGNMENT : "è_assegnato_via" # NUOVA TABELLA/RELAZIONE
    QUIZ ||--|{ PATHWAY_QUIZ : "fa_parte_di"

    LESSON ||--|{ LESSON_ASSIGNMENT : "è_assegnato_via" # NUOVA TABELLA/RELAZIONE

    REWARD_TEMPLATE ||--o{ REWARD : "è_template_per"
    REWARD ||--o{ REWARD_PURCHASE : "è_acquistata_in"
    REWARD }|..|{ REWARD_AVAILABILITY : "ha_disponibilità" # NUOVA TABELLA/RELAZIONE (Sostituisce REWARD_STUDENT_SPECIFIC_AVAILABILITY)

    STUDENT_GROUP ||--|{ STUDENT_GROUP_MEMBERSHIP : "ha_membri" # NUOVA RELAZIONE
    STUDENT_GROUP ||--|{ QUIZ_ASSIGNMENT : "assegnato_a_gruppo" # NUOVA RELAZIONE
    STUDENT_GROUP ||--|{ PATHWAY_ASSIGNMENT : "assegnato_a_gruppo" # NUOVA RELAZIONE
    STUDENT_GROUP ||--|{ LESSON_ASSIGNMENT : "assegnato_a_gruppo" # NUOVA RELAZIONE
    STUDENT_GROUP ||--|{ REWARD_AVAILABILITY : "disponibile_per_gruppo" # NUOVA RELAZIONE

    STUDENT ||--|{ QUIZ_ASSIGNMENT : "assegnato_a_studente" # NUOVA RELAZIONE
    STUDENT ||--|{ PATHWAY_ASSIGNMENT : "assegnato_a_studente" # NUOVA RELAZIONE
    STUDENT ||--|{ LESSON_ASSIGNMENT : "assegnato_a_studente" # NUOVA RELAZIONE
    STUDENT ||--|{ REWARD_AVAILABILITY : "disponibile_per_studente" # NUOVA RELAZIONE


    USER {
        int id PK
        string username UK
        string password_hash
        string email UK
        string first_name
        string last_name
        string role FK ("Admin", "Docente")
        datetime date_joined
        bool is_active
    }

    STUDENT {
        int id PK
        int user_id FK "Docente associato"
        string first_name
        string last_name
        string unique_identifier "Codice o username studente"
        datetime created_at
        bool is_active
        # Rimuovere FK diretta a gruppo se si usa tabella membership
    }

    STUDENT_GROUP { # NUOVA TABELLA
        int id PK
        int teacher_id FK "Docente proprietario"
        string name
        string description NULL
        string registration_token UK NULL "Token univoco per auto-registrazione"
        datetime created_at
        bool is_active DEFAULT true
    }

    STUDENT_GROUP_MEMBERSHIP { # NUOVA TABELLA
        int id PK
        int group_id FK
        int student_id FK
        datetime joined_at
        UNIQUE (group_id, student_id)
    }

    QUIZ_ASSIGNMENT { # NUOVA TABELLA (o simile)
        int id PK
        int quiz_id FK
        int student_id FK NULL
        int group_id FK NULL
        datetime assigned_at
        CHECK (student_id IS NOT NULL OR group_id IS NOT NULL) # Assicura che sia assegnato a uno dei due
    }

    PATHWAY_ASSIGNMENT { # NUOVA TABELLA (o simile)
        int id PK
        int pathway_id FK
        int student_id FK NULL
        int group_id FK NULL
        datetime assigned_at
        CHECK (student_id IS NOT NULL OR group_id IS NOT NULL)
    }

    LESSON { # NUOVA TABELLA (o esistente)
        int id PK
        int teacher_id FK
        string title
        # ... altri campi della lezione ...
    }

    LESSON_ASSIGNMENT { # NUOVA TABELLA
        int id PK
        int lesson_id FK
        int student_id FK NULL
        int group_id FK NULL
        datetime assigned_at
        CHECK (student_id IS NOT NULL OR group_id IS NOT NULL)
    }

    REWARD_AVAILABILITY { # NUOVA TABELLA (Sostituisce REWARD_STUDENT_SPECIFIC_AVAILABILITY)
        int id PK
        int reward_id FK
        int student_id FK NULL
        int group_id FK NULL
        datetime made_available_at
        CHECK (student_id IS NOT NULL OR group_id IS NOT NULL)
    }

    # ... altre tabelle come definite nel documento originale ...
    # QUIZ, PATHWAY, REWARD, etc. rimangono simili ma le relazioni
    # di assegnazione/disponibilità puntano alle nuove tabelle ponte.
    # Rimuovere REWARD_STUDENT_SPECIFIC_AVAILABILITY
```

**Note sulle Modifiche allo Schema:**

1.  **`STUDENT_GROUP`**: Tabella per definire i gruppi, associati a un docente. Include un `registration_token` opzionale e univoco.
2.  **`STUDENT_GROUP_MEMBERSHIP`**: Tabella ponte Many-to-Many tra `STUDENT_GROUP` e `STUDENT`.
3.  **Tabelle di Assegnazione/Disponibilità (`QUIZ_ASSIGNMENT`, `PATHWAY_ASSIGNMENT`, `LESSON_ASSIGNMENT`, `REWARD_AVAILABILITY`)**: Queste tabelle servono a tracciare a *chi* (studente singolo o gruppo) è stato assegnato un quiz/percorso/lezione o resa disponibile una ricompensa. Sostituiscono l'approccio precedente.
4.  **`REWARD.availability_type`**: Da valutare se mantenerlo o basarsi solo sulla presenza di record in `REWARD_AVAILABILITY`.

---

## 2. Modifiche ai Modelli Django (`apps/`)

1.  **`apps/users/models.py`**: Probabilmente nessuna modifica diretta a `Student`.
2.  **Nuova App `apps/groups/models.py` (o integrare)**:
    *   `StudentGroup(models.Model)`: Campi `teacher`, `name`, `description`, `registration_token`, `created_at`, `is_active`, `students` (M2M through `StudentGroupMembership`).
    *   `StudentGroupMembership(models.Model)`: Campi `group`, `student`, `joined_at`. `unique_together`.
3.  **`apps/education/models.py`**:
    *   `QuizAssignment(models.Model)`: Campi `quiz`, `student` (nullable), `group` (nullable), `assigned_at`. Constraint `CHECK`.
    *   `PathwayAssignment(models.Model)`: Simile a `QuizAssignment` con FK a `Pathway`.
    *   `LessonAssignment(models.Model)`: Simile a `QuizAssignment` con FK a `Lesson` (da definire in `apps/lessons` o `apps/education`).
4.  **`apps/lessons/models.py` (o `apps/education`)**:
    *   Definire il modello `Lesson` se non esiste già.
    *   Definire il modello `LessonAssignment`.
5.  **`apps/rewards/models.py`**:
    *   `RewardAvailability(models.Model)`: Campi `reward`, `student` (nullable), `group` (nullable), `made_available_at`. Constraint `CHECK`.
    *   Rimuovere `RewardStudentSpecificAvailability`.
    *   Aggiornare `Reward` per usare `RewardAvailability`.

---

## 3. Modifiche alle API REST (Endpoint DRF)

*   **Gestione Gruppi (Docente):** CRUD per gruppi, gestione membri (`/api/groups/...`, `/api/groups/{id}/students/...`), generazione/eliminazione token (`/api/groups/{id}/...-token/`).
*   **Registrazione Studente via Token (Pubblico?):** `POST /api/auth/register-by-token/`.
*   **Assegnazione a Gruppi (Docente):** Nuovi endpoint per assegnare/revocare quiz, percorsi, lezioni, disponibilità ricompense a gruppi (`/api/quizzes/{id}/assign-to-group/`, `/api/lessons/{id}/assign-to-group/`, `/api/rewards/{id}/make-available-to-group/`, etc.).
*   **Endpoint Esistenti (Aggiornamenti):** La logica di visualizzazione studente (`/api/student/...`) deve considerare l'appartenenza ai gruppi per tutti gli elementi assegnabili. Gli endpoint di assegnazione individuale devono usare le nuove tabelle ponte.

---

## 4. Logica di Business Principale

1.  **Creazione Gruppo/Gestione Membri:** Operazioni CRUD standard sui nuovi modelli.
2.  **Generazione Token:** Creazione stringa casuale sicura e univoca.
3.  **Registrazione via Token:** Trova gruppo, crea studente associato al docente del gruppo, crea membership. Gestire autenticazione iniziale.
4.  **Assegnazione a Gruppo:** Crea record nella tabella ponte appropriata (`QuizAssignment`, `PathwayAssignment`, `LessonAssignment`, `RewardAvailability`) con `group_id` popolato. *Non* creare record individuali per studente.
5.  **Revoca da Gruppo:** Elimina il record di assegnazione/disponibilità del gruppo dalla tabella ponte appropriata.
6.  **Logica di Visualizzazione Studente:** Query che unisce assegnazioni/disponibilità dirette e quelle derivanti dai gruppi per tutti gli elementi (quiz, percorsi, lezioni, ricompense).

---

## 5. Considerazioni Aggiuntive

1.  **Permessi (DRF):** Permessi custom per ownership (docente gestisce solo propri gruppi/studenti/contenuti).
2.  **Frontend (Impatto):** Nuove interfacce docente per gruppi. Logica backend aggiornata per studente. Nuovo flusso di registrazione con token.
3.  **Test:** Verranno eseguiti manualmente dall'utente.

---

## 6. Prossimi Passi

1.  **Switch a Modalità "Code":** Richiesta passaggio a "Code" per implementazione.

---
---

## 7. Stato Implementazione (al 25 Aprile 2025 - Debug API Creazione Gruppo)

*   [X] Creata nuova app Django: `apps/student_groups`.
*   [X] Definiti modelli `StudentGroup` e `StudentGroupMembership` in `apps/student_groups/models.py`.
*   [X] Modificati modelli `QuizAssignment`, `PathwayAssignment` in `apps/education/models.py` per supportare assegnazione a gruppi.
*   [X] Modificato modello `LessonAssignment` in `lezioni/models.py` per supportare assegnazione a gruppi.
*   [X] Modificato modello `Reward` e aggiunto modello `RewardAvailability` in `apps/rewards/models.py` per disponibilità a gruppi (rimosso `RewardStudentSpecificAvailability`).
*   [X] Aggiornati `admin.py` e `serializers.py` nelle app `education` e `rewards` per riflettere le modifiche ai modelli e risolvere `ImportError`.
*   [X] Registrati i nuovi modelli (`StudentGroup`, `StudentGroupMembership`) in `apps/student_groups/admin.py`.
*   [X] Generate e applicate migrazioni del database per `student_groups`, `education`, `lezioni`, `rewards`.
*   [X] Implementati Serializers, Views, e URLs per la gestione dei gruppi (`apps/student_groups`).
*   [X] Implementate azioni `assign`/`revoke` nei ViewSet di `Quiz`, `Pathway` (`apps/education`) e `Lesson` (`lezioni`) per gestire assegnazioni a studenti/gruppi.
*   [X] Implementate azioni `make_available`/`revoke_availability` nel ViewSet di `Reward` (`apps/rewards`) per gestire la disponibilità a studenti/gruppi.
*   [X] Aggiornate le viste studenti (`StudentAssignedQuizzesView`, `StudentAssignedPathwaysView`, `StudentShopViewSet`) per considerare le assegnazioni/disponibilità via gruppo.
*   [X] Risolti `ImportError` relativi a `StudentBasicSerializer` e `BulkLessonAssignSerializer`/`LessonAssignmentViewSet` in `apps/users`, `apps/rewards`, `lezioni`.

*   [X] **Frontend Docente (`frontend-teacher`):**
    *   [X] Definiti Tipi TypeScript (`types/groups.ts`).
    *   [X] Creato Store Pinia (`stores/groups.ts`) per gestione stato gruppi.
    *   [X] Implementate chiamate API (`api/groups.ts`) per CRUD gruppi, membri, token.
    *   [X] Creata Vista Elenco Gruppi (`views/GroupsListView.vue`).
    *   [X] Creata Vista Form Gruppi (`views/GroupFormView.vue`) per creazione/modifica.
    *   [X] Creata Vista Dettaglio Gruppo (`views/GroupDetailView.vue`) per visualizzazione info, gestione membri e token.
    *   [X] Aggiunte rotte per le viste dei gruppi in `router/index.ts`.
    *   [X] Aggiunto link "Gruppi" alla navigazione in `App.vue`.
    *   [X] Modificata Vista Assegnazioni (`views/AssignmentView.vue`) per permettere la selezione di gruppi come destinatari per l'assegnazione di Template Quiz e Template Percorsi.
    *   [X] Aggiunte funzioni API (`api/quizzes.ts`, `api/pathways.ts`) per assegnare template a gruppi.
*   [X] **Bloccante Risolto:** Risolti errori (405, 500, vari) che impedivano la creazione e l'elenco dei gruppi tramite `POST /api/groups/` e `GET /api/groups/`. La gestione degli errori 400 (nome duplicato) è stata migliorata anche nel frontend.
*   [X] **Frontend Docente (`frontend-teacher`):**
    *   [X] Implementare disponibilità Ricompense per gruppi. # COMPLETATO
*   [X] **Frontend Lezioni (`frontend-lessons`):** # CORRETTO
    *   [X] Implementare assegnazione Lezioni a gruppi. # COMPLETATO
*   [X] **Frontend Studente (`frontend-student`):** # CORRETTO NOME
    *   [X] Aggiornare logica per visualizzare Quiz, Percorsi, Lezioni assegnati tramite gruppo. (Verificato, gestito da backend/lezioni FE)
    *   [X] Aggiornare logica per visualizzare Ricompense disponibili tramite gruppo. (Verificato, gestito da backend)
    *   [X] Implementare flusso di registrazione tramite token di gruppo (se previsto). # COMPLETATO

**Prossimi Passi:** Eseguire test manuali completi delle funzionalità dei gruppi (creazione, gestione membri, assegnazioni, disponibilità, registrazione token). # AGGIORNATO PROSSIMI PASSI