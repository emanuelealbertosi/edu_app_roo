# Piano di Progettazione: Applicazione Educativa

**Versione:** 1.0 (27 Marzo 2025)

## 1. Obiettivi Principali

*   Creare una piattaforma web per Admin, Docenti e Studenti.
*   **Admin:** Gestione Docenti, creazione Template Quiz (globali), creazione Template Ricompense (globali), gestione Impostazioni Globali (opzionale).
*   **Docente:** Gestione Studenti, creazione/assegnazione Quiz (da template Admin o da zero), creazione/assegnazione Percorsi, creazione Template Ricompense (locali), creazione Ricompense specifiche (da template globali/locali o da zero), gestione disponibilità Ricompense (tutti/specifici), conferma consegna Ricompense reali.
*   **Studente:** Svolgimento Quiz/Percorsi, guadagno punti, visualizzazione/acquisto Ricompense disponibili.
*   Garantire sicurezza (Security by Design) e testabilità (Test Driven Development - TDD).

## 2. Stack Tecnologico

*   **Backend:** Python 3.x, Django 4.x/5.x, Django REST Framework (DRF)
*   **Database:** PostgreSQL (per relazioni complesse e supporto JSONB)
*   **Autenticazione/Autorizzazione:** Django Allauth (opzionale per registrazione/social), JSON Web Tokens (JWT - es. `djangorestframework-simplejwt`) per API stateless, Permessi custom Django/DRF.
*   **Testing:** Framework di test integrato di Django (`unittest` o `pytest-django`), `factory-boy` per fixtures, `coverage.py` per code coverage.
*   **Frontend:** Vue.js 3 (sviluppo futuro, separato dal backend).
*   **Deployment (Considerazione futura):** Docker, Docker Compose.

## 3. Architettura Generale & Struttura Progetto Django

Proposta di struttura modulare:

```
edu_app_roo/
├── config/             # Impostazioni progetto, urls principali, wsgi/asgi
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── apps/               # Directory contenente le app specifiche
│   ├── users/          # Gestione utenti (Admin, Docente, Studente), profili, autenticazione
│   ├── education/      # Core educativo: Quiz, Domande, Percorsi, Risposte Studenti
│   ├── rewards/        # Gestione Ricompense (Template, Specifiche), Shop, Transazioni Punti
│   └── ... (eventuali altre app future, es. analytics)
├── static/             # File statici globali (se necessari)
├── templates/          # Template globali (es. email, pagine base se non SPA pura)
├── requirements.txt    # Dipendenze Python
├── manage.py
├── Dockerfile          # Per containerizzare l'app
└── docker-compose.yml  # Per orchestrare servizi (app, db, ecc.)
├── index.html          # Homepage statica principale
```

## 4. Schema del Database (PostgreSQL - Modelli Chiave)

```mermaid
erDiagram
    USER ||--o{ STUDENT : "è_docente_di"
    USER ||--o{ STUDENT_GROUP : "gestisce"
    USER ||--o{ STUDENT_REGISTRATION_TOKEN : "crea_token_per"
    USER ||--o{ QUIZ_TEMPLATE : "creato_da (Admin)"
    USER ||--o{ QUIZ : "creato_da (Docente)"
    USER ||--o{ PATHWAY : "creato_da (Docente)"
    USER ||--o{ REWARD_TEMPLATE : "creato_da (Admin/Docente)"
    USER ||--o{ REWARD : "creato_da (Docente)"
    USER ||--o{ REWARD_PURCHASE : "consegnato_da"

    STUDENT ||--o{ QUIZ_ATTEMPT : "svolge"
    STUDENT ||--o{ PATHWAY_PROGRESS : "progredisce_in"
    STUDENT ||--o{ WALLET : "possiede"
    STUDENT ||--o{ REWARD_PURCHASE : "acquista"
    STUDENT }|..|{ REWARD : "disponibile_per (specifico)"
    STUDENT ||--o{ STUDENT_GROUP : "appartiene_a"

    WALLET ||--o{ POINT_TRANSACTION : "ha_transazioni"

    QUIZ_TEMPLATE ||--o{ QUESTION_TEMPLATE : "contiene"
    QUIZ ||--o{ QUESTION : "contiene"
    QUIZ ||--o{ QUIZ_ATTEMPT : "ha_tentativi"

    QUESTION_TEMPLATE ||--o{ ANSWER_OPTION_TEMPLATE : "ha_opzioni"
    QUESTION ||--o{ ANSWER_OPTION : "ha_opzioni"
    QUESTION ||--o{ STUDENT_ANSWER : "ha_risposte"

    QUIZ_ATTEMPT ||--o{ STUDENT_ANSWER : "contiene"

    PATHWAY ||--o{ PATHWAY_QUIZ : "contiene"
    PATHWAY ||--o{ PATHWAY_PROGRESS : "ha_progressi"
    QUIZ ||--|{ PATHWAY_QUIZ : "fa_parte_di"

    REWARD_TEMPLATE ||--o{ REWARD : "è_template_per"
    REWARD ||--o{ REWARD_PURCHASE : "è_acquistata_in"
    REWARD }|..|{ REWARD_STUDENT_SPECIFIC_AVAILABILITY : "ha_disponibilità_specifica"

    STUDENT_GROUP ||--o{ STUDENT : "ha_membro"
    STUDENT_GROUP ||--o{ STUDENT_REGISTRATION_TOKEN : "ha_token_per"


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
        int teacher_id FK "Docente associato"
        string student_code UK "Codice univoco studente"
        string pin_hash "Hash del PIN"
        string first_name
        string last_name
        int group_id FK NULL "Gruppo di appartenenza (opzionale)"
        datetime created_at
        bool is_active
    }

    WALLET {
        int id PK
        int student_id FK UK
        int current_points DEFAULT 0
    }

    POINT_TRANSACTION {
        int id PK
        int wallet_id FK
        int points_change
        string reason "Es: Completamento Quiz X, Acquisto Ricompensa Y"
        datetime timestamp
    }

    QUIZ_TEMPLATE {
        int id PK
        int admin_id FK
        string title
        string description
        jsonb metadata "Es: difficoltà, materia"
        datetime created_at
    }

    QUESTION_TEMPLATE {
        int id PK
        int quiz_template_id FK
        string text
        string question_type "Es: multiple_choice_single, true_false, fill_blank, open_answer_manual"
        int order
        jsonb metadata "Es: punti per risposta corretta (se applicabile)"
    }

    ANSWER_OPTION_TEMPLATE {
        int id PK
        int question_template_id FK
        string text
        bool is_correct
        int order
    }

    QUIZ {
        int id PK
        int teacher_id FK
        int source_template_id FK NULL "Template originale (opzionale)"
        string title
        string description
        jsonb metadata "Es: difficoltà, materia, completion_threshold (0-1), points_on_completion"
        datetime created_at
        datetime available_from NULL
        datetime available_until NULL
    }

    QUESTION {
        int id PK
        int quiz_id FK
        string text
        string question_type
        int order
        jsonb metadata "Es: punti per risposta corretta, config per fill_blank"
    }

    ANSWER_OPTION {
        int id PK
        int question_id FK
        string text
        bool is_correct
        int order
    }

    PATHWAY {
        int id PK
        int teacher_id FK
        string title
        string description
        jsonb metadata "Es: points_on_completion"
        datetime created_at
    }

    PATHWAY_QUIZ {
        int id PK
        int pathway_id FK
        int quiz_id FK
        int order "Ordine del quiz nel percorso"
    }

    QUIZ_ATTEMPT {
        int id PK
        int student_id FK
        int quiz_id FK
        datetime started_at
        datetime completed_at NULL
        int score NULL
        int points_earned NULL
        bool first_correct_completion DEFAULT false
        string status "in_progress, pending_manual_grading, completed"
    }

    STUDENT_ANSWER {
        int id PK
        int quiz_attempt_id FK
        int question_id FK
        jsonb selected_answers "Formato dipende da question_type"
        bool is_correct NULL "Null per manual grading"
        int score NULL "Punteggio specifico risposta (per manuale)"
        datetime answered_at
    }

    PATHWAY_PROGRESS {
        int id PK
        int student_id FK
        int pathway_id FK
        int last_completed_quiz_order NULL
        datetime completed_at NULL
        int points_earned NULL
        bool first_correct_completion DEFAULT false
        string status "in_progress, completed"
    }

    REWARD_TEMPLATE {
        int id PK
        int creator_id FK "Admin o Docente"
        string scope "global, local"
        string name
        string description
        string type "digital, real_world_tracked"
        jsonb metadata "Es: immagine, link"
        datetime created_at
    }

    REWARD {
        int id PK
        int teacher_id FK "Docente proprietario"
        int template_id FK NULL "Template opzionale"
        string name
        string description
        string type
        int cost_points
        string availability_type "all_students, specific_students"
        jsonb metadata
        bool is_active DEFAULT true
        datetime created_at
    }

    REWARD_STUDENT_SPECIFIC_AVAILABILITY {
         int reward_id FK
         int student_id FK
         PRIMARY KEY (reward_id, student_id)
    }

    REWARD_PURCHASE {
        int id PK
        int student_id FK
        int reward_id FK
        int points_spent
        datetime purchased_at
        string status "purchased, delivered, cancelled"
        int delivered_by_id FK NULL "Utente che ha consegnato"
        datetime delivered_at DATETIME NULL
        string delivery_notes TEXT NULL
    }

    GLOBAL_SETTING { # Modello opzionale ma consigliato
        string key PK "Nome univoco impostazione"
        string value "Valore impostazione"
        string description "Descrizione per l'Admin"
        string data_type "string, integer, boolean, json"
    }

    STUDENT_GROUP {
        int id PK
        int teacher_id FK "Docente proprietario"
        string name
        datetime created_at
        datetime updated_at
    }

    STUDENT_REGISTRATION_TOKEN {
        uuid token PK
        int teacher_id FK "Docente creatore"
        int group_id FK NULL "Gruppo associato (opzionale)"
        datetime created_at
        datetime expires_at
        bool is_active
    }
```

## 5. Tipologie di Domande Supportate

*   **`multiple_choice_single`:** Scelta multipla, risposta singola corretta.
*   **`multiple_choice_multiple`:** Scelta multipla, risposte multiple corrette.
*   **`true_false`:** Vero o Falso.
*   **`fill_blank`:** Completamento di spazi vuoti (correzione automatica basata su `Question.metadata`).
*   **`open_answer_manual`:** Risposta aperta testuale (richiede correzione manuale del Docente).

**Struttura Dati:**
*   `Question.question_type`: Definisce il tipo.
*   `Question.metadata`: Contiene configurazioni specifiche del tipo (es. risposte per `fill_blank`).
*   `AnswerOption`: Usato per opzioni predefinite (`multiple_choice_*`, `true_false`).
*   `StudentAnswer.selected_answers` (JSONB): Memorizza la risposta dello studente in formato variabile.
*   `StudentAnswer.is_correct` (`BooleanField(null=True)`): `NULL` per risposte in attesa di correzione manuale.
*   `StudentAnswer.score` (`IntegerField(null=True)`): Punteggio specifico per la risposta (utile per manuali).

## 6. Calcolo e Assegnazione Punti

*   **Condizione:** Assegnati solo al *primo completamento corretto* di un Quiz o Percorso.
*   **"Completamento Corretto":** Definito dal superamento di una soglia di punteggio (`completion_threshold`, float 0-1) specificata in `Quiz.metadata` (con default globale).
*   **Quantità Punti:** Valore fisso (`points_on_completion`, integer) specificato in `Quiz.metadata` e `Pathway.metadata`.
*   **Domande Manuali:** Il punteggio finale del tentativo e l'eventuale assegnazione dei punti avvengono solo *dopo* che il Docente ha corretto tutte le risposte `open_answer_manual`. Lo stato del tentativo (`QuizAttempt.status`) sarà `pending_manual_grading` fino ad allora.
*   **Tracciamento:** Ogni variazione di punti è registrata in `PointTransaction`.

## 7. Sistema di Ricompense

*   **Template:**
    *   Globali: Creati da Admin (`RewardTemplate.scope = 'global'`).
    *   Locali: Creati da Docente (`RewardTemplate.scope = 'local'`).
*   **Ricompense Specifiche (`Reward`):**
    *   Create da Docenti, possono opzionalmente derivare da un template (globale o locale).
    *   Hanno un `type` (`digital`, `real_world_tracked`) e `cost_points`.
*   **Disponibilità per Studenti:**
    *   Definita da `Reward.availability_type`:
        *   `'all_students'`: Disponibile a tutti gli studenti del Docente creatore.
        *   `'specific_students'`: Disponibile solo agli studenti elencati nella tabella M2M `RewardStudentSpecificAvailability`.
*   **Shop Studente:** Mostra solo le ricompense attive (`is_active=true`) e disponibili per quello specifico studente in base alle regole di disponibilità.
*   **Acquisto (`RewardPurchase`):**
    *   Registra l'acquisto, scala i punti dal `Wallet`.
    *   Traccia lo `status` (`purchased`, `delivered`, `cancelled`).
*   **Consegna Ricompense Reali:**
    *   Il Docente può visualizzare gli acquisti `real_world_tracked` con stato `purchased`.
    *   Il Docente può marcare un acquisto come `delivered`, registrando chi (`delivered_by_id`), quando (`delivered_at`) e note (`delivery_notes`).

## 8. Design API REST (Endpoint Principali - DRF)

*   **Autenticazione:**
    *   `POST /api/auth/login/` (JWT Token)
    *   `POST /api/auth/logout/`
    *   `GET /api/auth/user/`
*   **Admin - Gestione Utenti:**
    *   `GET, POST /api/admin/teachers/`
    *   `GET, PUT, PATCH, DELETE /api/admin/teachers/{user_id}/`
*   **Admin - Gestione Template:**
    *   `GET, POST /api/admin/quiz-templates/` (+ sub-routes per domande/opzioni)
    *   `GET, PUT, PATCH, DELETE /api/admin/quiz-templates/{template_id}/`
    *   `GET, POST /api/admin/reward-templates/` (Solo globali)
    *   `GET, PUT, PATCH, DELETE /api/admin/reward-templates/{template_id}/` (Solo globali)
*   **Admin - Impostazioni (Opzionale):**
    *   `GET /api/admin/settings/`
    *   `GET, PUT /api/admin/settings/{setting_key}/`
*   **Docente - Gestione Studenti:**
    *   `GET, POST /api/students/`
    *   `GET, PUT, PATCH, DELETE /api/students/{student_id}/` (PATCH permette modifica `group_id`)
*   **Docente - Gestione Gruppi:**
    *   `GET, POST /api/teacher/groups/`
    *   `GET, PUT, PATCH, DELETE /api/teacher/groups/{group_id}/`
*   **Docente - Gestione Token Registrazione:**
    *   `GET, POST /api/teacher/registration-tokens/`
    *   `GET, DELETE /api/teacher/registration-tokens/{token_uuid}/`
    *   `POST /api/teacher/registration-tokens/{token_uuid}/deactivate/` (Azione custom)
*   **Docente - Gestione Contenuti:**
    *   `GET, POST /api/quizzes/`
*   **Registrazione Studente (Pubblica):**
    *   `GET /api/register/validate-token/{token_str}/` (Validazione token)
    *   `POST /api/register/complete/` (Completamento registrazione)
    *   `POST /api/quizzes/create-from-template/`
    *   `GET, PUT, PATCH, DELETE /api/quizzes/{quiz_id}/` (+ sub-routes domande/opzioni)
    *   `POST /api/quizzes/{quiz_id}/assign/{student_id}/` (o gestione assegnazioni separata)
    *   `GET, POST /api/pathways/`
    *   `GET, PUT, PATCH, DELETE /api/pathways/{pathway_id}/`
    *   `POST /api/pathways/{pathway_id}/add-quiz/`
    *   `POST /api/pathways/{pathway_id}/assign/{student_id}/` (o gestione assegnazioni separata)
*   **Docente - Gestione Ricompense:**
    *   `GET, POST /api/reward-templates/` (Locali + Globali)
    *   `PUT, PATCH, DELETE /api/reward-templates/{template_id}/` (Solo locali propri)
    *   `GET, POST /api/rewards/` (Include gestione disponibilità)
    *   `GET, PUT, PATCH, DELETE /api/rewards/{reward_id}/`
    *   `GET /api/reward-purchases/pending-delivery/`
    *   `POST /api/reward-purchases/{purchase_id}/mark-delivered/`
*   **Studente - Svolgimento & Profilo:**
    *   `GET /api/student/dashboard/` (Quiz/Percorsi assegnati)
    *   `POST /api/quizzes/{quiz_id}/start-attempt/`
    *   `GET /api/attempts/{attempt_id}/`
    *   `POST /api/attempts/{attempt_id}/submit-answer/`
    *   `POST /api/attempts/{attempt_id}/complete/`
    *   `GET /api/student/pathways/{pathway_id}/progress/`
    *   `GET /api/student/wallet/`
    *   `GET /api/student/shop/`
    *   `POST /api/student/shop/purchase/{reward_id}/`
    *   `GET /api/student/purchases/`

## 9. Sicurezza (Security by Design)

*   **Autenticazione:** JWT obbligatorio per tutte le API protette.
*   **Autorizzazione:** Permessi DRF custom basati su ruolo (`IsAdminUser`, `IsTeacherUser`, `IsStudentUser`) e ownership (es. Docente modifica solo i *propri* quiz/studenti).
*   **Input Validation:** Uso rigoroso dei Serializers DRF per validare tutti i dati in ingresso.
*   **Protezioni Generali:** HTTPS obbligatorio, Rate Limiting, protezione contro SQL Injection (ORM), XSS (template escaping), CSRF (se applicabile), gestione sicura password (hashing Django).
*   **Esposizione Dati:** Evitare ID sequenziali nelle API se possibile (preferire UUID/slug), logging attento.

## 10. Approccio Sviluppo (Test Driven Development - TDD)

*   **Flusso:** Scrivere test fallimentare -> Scrivere codice minimo -> Refactoring.
*   **Copertura:** Test unitari (modelli, logica business), Test di integrazione (API views, flussi completi).
*   **Strumenti:** `manage.py test`, `coverage.py`, `factory-boy`.