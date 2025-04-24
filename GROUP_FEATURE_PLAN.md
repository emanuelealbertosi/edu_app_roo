# Piano di Progettazione: Funzionalità Gruppi di Studenti

**Versione:** 1.1 (Aggiornamento del 24 Aprile 2025)

**Obiettivo:** Introdurre la possibilità per i Docenti di creare Gruppi, assegnare Studenti ai Gruppi, generare link di registrazione specifici per Gruppo e gestire assegnazioni (Quiz, Percorsi, disponibilità Ricompense) e revoche a livello di Gruppo.

---

## 1. Modifiche allo Schema del Database

Introdurremo due nuove tabelle principali: `STUDENT_GROUP` e `STUDENT_GROUP_MEMBERSHIP`. Aggiorneremo anche le relazioni per le assegnazioni.

```mermaid
erDiagram
    USER ||--o{ STUDENT : "è_docente_di"
    USER ||--o{ QUIZ_TEMPLATE : "creato_da (Admin)"
    USER ||--o{ QUIZ : "creato_da (Docente)"
    USER ||--o{ PATHWAY : "creato_da (Docente)"
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

    REWARD_TEMPLATE ||--o{ REWARD : "è_template_per"
    REWARD ||--o{ REWARD_PURCHASE : "è_acquistata_in"
    REWARD }|..|{ REWARD_AVAILABILITY : "ha_disponibilità" # NUOVA TABELLA/RELAZIONE (Sostituisce REWARD_STUDENT_SPECIFIC_AVAILABILITY)

    STUDENT_GROUP ||--|{ STUDENT_GROUP_MEMBERSHIP : "ha_membri" # NUOVA RELAZIONE
    STUDENT_GROUP ||--|{ QUIZ_ASSIGNMENT : "assegnato_a_gruppo" # NUOVA RELAZIONE
    STUDENT_GROUP ||--|{ PATHWAY_ASSIGNMENT : "assegnato_a_gruppo" # NUOVA RELAZIONE
    STUDENT_GROUP ||--|{ REWARD_AVAILABILITY : "disponibile_per_gruppo" # NUOVA RELAZIONE

    STUDENT ||--|{ QUIZ_ASSIGNMENT : "assegnato_a_studente" # NUOVA RELAZIONE
    STUDENT ||--|{ PATHWAY_ASSIGNMENT : "assegnato_a_studente" # NUOVA RELAZIONE
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
3.  **Tabelle di Assegnazione/Disponibilità (`QUIZ_ASSIGNMENT`, `PATHWAY_ASSIGNMENT`, `REWARD_AVAILABILITY`)**: Queste tabelle servono a tracciare a *chi* (studente singolo o gruppo) è stato assegnato un quiz/percorso o resa disponibile una ricompensa. Sostituiscono l'approccio precedente.
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
4.  **`apps/rewards/models.py`**:
    *   `RewardAvailability(models.Model)`: Campi `reward`, `student` (nullable), `group` (nullable), `made_available_at`. Constraint `CHECK`.
    *   Rimuovere `RewardStudentSpecificAvailability`.
    *   Aggiornare `Reward` per usare `RewardAvailability`.

---

## 3. Modifiche alle API REST (Endpoint DRF)

*   **Gestione Gruppi (Docente):** CRUD per gruppi, gestione membri (`/api/groups/...`, `/api/groups/{id}/students/...`), generazione/eliminazione token (`/api/groups/{id}/...-token/`).
*   **Registrazione Studente via Token (Pubblico?):** `POST /api/auth/register-by-token/`.
*   **Assegnazione a Gruppi (Docente):** Nuovi endpoint per assegnare/revocare quiz, percorsi, disponibilità ricompense a gruppi (`/api/quizzes/{id}/assign-to-group/`, `/api/rewards/{id}/make-available-to-group/`, etc.).
*   **Endpoint Esistenti (Aggiornamenti):** La logica di visualizzazione studente (`/api/student/...`) deve considerare l'appartenenza ai gruppi. Gli endpoint di assegnazione individuale devono usare le nuove tabelle ponte.

---

## 4. Logica di Business Principale

1.  **Creazione Gruppo/Gestione Membri:** Operazioni CRUD standard sui nuovi modelli.
2.  **Generazione Token:** Creazione stringa casuale sicura e univoca.
3.  **Registrazione via Token:** Trova gruppo, crea studente associato al docente del gruppo, crea membership. Gestire autenticazione iniziale.
4.  **Assegnazione a Gruppo:** Crea record nella tabella ponte appropriata con `group_id` popolato. *Non* creare record individuali per studente.
5.  **Revoca da Gruppo:** Elimina il record di assegnazione/disponibilità del gruppo dalla tabella ponte.
6.  **Logica di Visualizzazione Studente:** Query che unisce assegnazioni/disponibilità dirette e quelle derivanti dai gruppi.

---

## 5. Considerazioni Aggiuntive

1.  **Permessi (DRF):** Permessi custom per ownership (docente gestisce solo propri gruppi/studenti/contenuti).
2.  **Frontend (Impatto):** Nuove interfacce docente per gruppi. Logica backend aggiornata per studente. Nuovo flusso di registrazione con token.
3.  **Test:** Verranno eseguiti manualmente dall'utente.

---

## 6. Prossimi Passi

1.  **Switch a Modalità "Code":** Richiesta passaggio a "Code" per implementazione.

---