# Piano di Progettazione: Applicazione Educativa

**Versione:** 1.1 (Aggiornamento del 2 Maggio 2025 - Integrazione Gruppi)

## 1. Obiettivi Principali

*   Creare una piattaforma web per Admin, Docenti e Studenti.
*   **Admin:** Gestione Docenti, creazione Template Quiz (globali), creazione Template Ricompense (globali), gestione Impostazioni Globali (opzionale).
*   **Docente:** Gestione Studenti, creazione/assegnazione Quiz (da template Admin o da zero, con possibilità di associare Materia e Argomento opzionali), creazione/assegnazione Percorsi, creazione Template Ricompense (locali), creazione Ricompense specifiche (da template globali/locali o da zero), gestione disponibilità Ricompense (tutti/specifici), conferma consegna Ricompense reali.
*   **Studente:** Svolgimento Quiz/Percorsi (la modale di svolgimento quiz deve occupare almeno l'89% della larghezza del browser su desktop), guadagno punti, visualizzazione/acquisto Ricompense disponibili.
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
│   ├── student_groups/ # Gestione Gruppi Studenti, Membership, Token Registrazione
│   └── ... (eventuali altre app future, es. analytics)
├── static/             # File statici globali (se necessari)
├── templates/          # Template globali (es. email, pagine base se non SPA pura)
├── requirements.txt    # Dipendenze Python
├── manage.py
├── Dockerfile          # Per containerizzare l'app
└── docker-compose.yml  # Per orchestrare servizi (app, db, ecc.)
```

## 4. Schema del Database (PostgreSQL - Modelli Chiave)

```mermaid
erDiagram
    USER ||--o{ SUBJECT : "crea_materia"
    USER ||--o{ TOPIC : "crea_argomento"
    SUBJECT ||--o{ TOPIC : "ha_argomenti"

    QUIZ_TEMPLATE }o--|| SUBJECT : "materia_del_template_quiz (opz.)"
    QUIZ_TEMPLATE }o--|| TOPIC : "argomento_del_template_quiz (opz.)"

    QUIZ }o--|| SUBJECT : "materia_del_quiz (opz.)"
    QUIZ }o--|| TOPIC : "argomento_del_quiz (opz.)"

    LESSON }o--|| SUBJECT : "materia_della_lezione (opz.)"
    LESSON }o--|| TOPIC : "argomento_della_lezione (opz.)"

    USER ||--o{ STUDENT : "è_docente_di"
    USER ||--o{ QUIZ_TEMPLATE : "creato_da (Admin)"
    USER ||--o{ QUIZ : "creato_da (Docente)"
    USER ||--o{ PATHWAY : "creato_da (Docente)"
    USER ||--o{ LESSON : "creato_da (Docente)"
    USER ||--o{ REWARD_TEMPLATE : "creato_da (Admin/Docente)"
    USER ||--o{ REWARD : "creato_da (Docente)"
    USER ||--o{ REWARD_PURCHASE : "consegnato_da"
    USER ||--o{ STUDENT_GROUP : "creato_da (Docente)"

    STUDENT ||--o{ QUIZ_ATTEMPT : "svolge"
    STUDENT ||--o{ PATHWAY_PROGRESS : "progredisce_in"
    STUDENT ||--o{ WALLET : "possiede"
    STUDENT ||--o{ REWARD_PURCHASE : "acquista"
    STUDENT }|..|{ REWARD : "disponibile_per (specifico)" // OBSOLETO, vedi REWARD_AVAILABILITY
    STUDENT ||--|{ STUDENT_GROUP_MEMBERSHIP : "appartiene_a"

    WALLET ||--o{ POINT_TRANSACTION : "ha_transazioni"

    QUIZ_TEMPLATE ||--o{ QUESTION_TEMPLATE : "contiene"
    QUIZ ||--o{ QUESTION : "contiene"
    QUIZ ||--o{ QUIZ_ATTEMPT : "ha_tentativi"
    QUIZ ||--|{ QUIZ_ASSIGNMENT : "è_assegnato_via"

    QUESTION_TEMPLATE ||--o{ ANSWER_OPTION_TEMPLATE : "ha_opzioni"
    QUESTION ||--o{ ANSWER_OPTION : "ha_opzioni"
    QUESTION ||--o{ STUDENT_ANSWER : "ha_risposte"

    QUIZ_ATTEMPT ||--o{ STUDENT_ANSWER : "contiene"

    PATHWAY ||--o{ PATHWAY_QUIZ : "contiene"
    PATHWAY ||--o{ PATHWAY_PROGRESS : "ha_progressi"
    PATHWAY ||--|{ PATHWAY_ASSIGNMENT : "è_assegnato_via"
    QUIZ ||--|{ PATHWAY_QUIZ : "fa_parte_di"

    LESSON ||--|{ LESSON_ASSIGNMENT : "è_assegnato_via"

    REWARD_TEMPLATE ||--o{ REWARD : "è_template_per"
    REWARD ||--o{ REWARD_PURCHASE : "è_acquistata_in"
    REWARD }|..|{ REWARD_AVAILABILITY : "ha_disponibilità"

    STUDENT_GROUP ||--|{ STUDENT_GROUP_MEMBERSHIP : "ha_membri"
    STUDENT_GROUP ||--|{ QUIZ_ASSIGNMENT : "assegnato_a_gruppo"
    STUDENT_GROUP ||--|{ PATHWAY_ASSIGNMENT : "assegnato_a_gruppo"
    STUDENT_GROUP ||--|{ LESSON_ASSIGNMENT : "assegnato_a_gruppo"
    STUDENT_GROUP ||--|{ REWARD_AVAILABILITY : "disponibile_per_gruppo"

    STUDENT ||--|{ QUIZ_ASSIGNMENT : "assegnato_a_studente"
    STUDENT ||--|{ PATHWAY_ASSIGNMENT : "assegnato_a_studente"
    STUDENT ||--|{ LESSON_ASSIGNMENT : "assegnato_a_studente"
    STUDENT ||--|{ REWARD_AVAILABILITY : "disponibile_per_studente"


    SUBJECT {
        int id PK
        int teacher_id FK "USER(id) - Docente creatore"
        string name UK "Nome materia (univoco per docente)"
        string color_placeholder "Colore esadecimale per placeholder SVG quiz (es. #FF5733)"
        datetime created_at
        datetime updated_at
    }

    TOPIC {
        int id PK
        int subject_id FK "SUBJECT(id) - Materia di appartenenza (NOT NULL)"
        int teacher_id FK "USER(id) - Docente creatore"
        string name UK "Nome argomento (univoco per materia e docente)"
        datetime created_at
        datetime updated_at
    }

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
        # GDPR: Campi aggiunti per tracciare accettazione policy
        datetime privacy_policy_accepted_at NULL
        datetime terms_of_service_accepted_at NULL
    }

    STUDENT {
        int id PK
        int user_id FK "Docente associato"
        string first_name
        string last_name
        string unique_identifier "Codice o username studente"
        datetime created_at
        bool is_active
        # GDPR: Campi aggiunti per tracciare accettazione policy
        datetime privacy_policy_accepted_at NULL
        datetime terms_of_service_accepted_at NULL
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
        int subject_id FK NULL "SUBJECT(id) - Materia associata (opzionale)"
        int topic_id FK NULL "TOPIC(id) - Argomento associato (opzionale, coerente con subject_id)"
        jsonb metadata "Es: difficoltà"
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
        int subject_id FK NULL "SUBJECT(id) - Materia associata (opzionale)"
        int topic_id FK NULL "TOPIC(id) - Argomento associato (opzionale)"
        string image_url NULL "URL immagine di copertina del quiz (opzionale)"
        jsonb metadata "Es: difficoltà, completion_threshold (0-1), points_on_completion"
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

    LESSON { // NUOVA TABELLA (o esistente)
        int id PK
        int teacher_id FK
        string title
        int subject_id FK NULL "SUBJECT(id) - Materia associata (opzionale)"
        int topic_id FK NULL "TOPIC(id) - Argomento associato (opzionale)"
        // ... altri campi della lezione ...
    }

    QUIZ_ASSIGNMENT { # NUOVA TABELLA
        int id PK
        int quiz_id FK
        int student_id FK NULL
        int group_id FK NULL
        datetime assigned_at
        CHECK (student_id IS NOT NULL OR group_id IS NOT NULL)
    }

    PATHWAY_ASSIGNMENT { # NUOVA TABELLA
        int id PK
        int pathway_id FK
        int student_id FK NULL
        int group_id FK NULL
        datetime assigned_at
        CHECK (student_id IS NOT NULL OR group_id IS NOT NULL)
    }

    LESSON_ASSIGNMENT { # NUOVA TABELLA
        int id PK
        int lesson_id FK
        int student_id FK NULL
        int group_id FK NULL
        datetime assigned_at
        CHECK (student_id IS NOT NULL OR group_id IS NOT NULL)
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
        string image_url NULL "URL immagine per il template ricompensa (opzionale)"
        jsonb metadata "Es: link (se immagine non in image_url), dettagli specifici del tipo"
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
        string image_url NULL "URL immagine specifica per la ricompensa (opzionale)"
        // string availability_type "all_students, specific_students" # Rimpiazzato da REWARD_AVAILABILITY
        jsonb metadata
        bool is_active DEFAULT true
        datetime created_at
    }

    REWARD_AVAILABILITY { # NUOVA TABELLA
        int id PK
        int reward_id FK
        int student_id FK NULL
        int group_id FK NULL
        datetime made_available_at
        CHECK (student_id IS NOT NULL OR group_id IS NOT NULL)
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
        *   La disponibilità è ora gestita tramite la tabella `RewardAvailability`. Una ricompensa è disponibile per uno studente se esiste un record in `RewardAvailability` che collega la ricompensa allo studente direttamente (`student_id`) o a un gruppo a cui lo studente appartiene (`group_id`).
*   **Shop Studente:** Mostra solo le ricompense attive (`is_active=true`) e disponibili per quello specifico studente in base alle regole di disponibilità.
*   **Acquisto (`RewardPurchase`):**
    *   Registra l'acquisto, scala i punti dal `Wallet`.
    *   Traccia lo `status` (`purchased`, `delivered`, `cancelled`).
*   **Consegna Ricompense Reali:**
    *   Il Docente può visualizzare gli acquisti `real_world_tracked` con stato `purchased`.
    *   Il Docente può marcare un acquisto come `delivered`, registrando chi (`delivered_by_id`), quando (`delivered_at`) e note (`delivery_notes`).

## 8. Gestione Gruppi Studenti

*   **Creazione/Gestione:** I Docenti possono creare `StudentGroup`, assegnare un nome, una descrizione e gestire i membri tramite `StudentGroupMembership`.
*   **Token Registrazione:** Ogni gruppo può avere un `registration_token` univoco (opzionale) che permette agli studenti di auto-registrarsi e venire automaticamente aggiunti al gruppo e associati al docente proprietario del gruppo.
*   **Assegnazioni/Disponibilità:** Quiz, Percorsi, Lezioni e Ricompense possono essere assegnati/resi disponibili a interi gruppi tramite le tabelle ponte (`QuizAssignment`, `PathwayAssignment`, `LessonAssignment`, `RewardAvailability`) specificando il `group_id`.
*   **Revoca:** La revoca di un'assegnazione/disponibilità per un gruppo avviene eliminando il record corrispondente dalla tabella ponte.
*   **Visibilità Studente:** Gli studenti vedono tutti i contenuti (Quiz, Percorsi, Lezioni, Ricompense) a loro assegnati direttamente o tramite i gruppi a cui appartengono.

## 9. Design API REST (Endpoint Principali - DRF)

*   **Autenticazione:**
    *   `POST /api/auth/login/` (JWT Token)
    *   `POST /api/auth/logout/`
    *   `GET /api/auth/user/`
*   **Admin - Gestione Utenti:**
    *   `GET, POST /api/admin/teachers/`
    *   `GET, PUT, PATCH, DELETE /api/admin/teachers/{user_id}/`
*   **Admin - Gestione Template:**
    *   `GET, POST /api/admin/quiz-templates/` (+ sub-routes per domande/opzioni; Payload POST e risposta GET includono `subject_id` (opz.), `topic_id` (opz.))
    *   `GET, PUT, PATCH, DELETE /api/admin/quiz-templates/{template_id}/` (Payload e risposta includono `subject_id` (opz.), `topic_id` (opz.))
    *   `GET, POST /api/admin/reward-templates/` (Solo globali)
    *   `GET, PUT, PATCH, DELETE /api/admin/reward-templates/{template_id}/` (Solo globali)
*   **Admin - Impostazioni (Opzionale):**
    *   `GET /api/admin/settings/`
    *   `GET, PUT /api/admin/settings/{setting_key}/`
*   **Docente - Gestione Materie:**
        *   `GET, POST /api/subjects/` (Lista e crea materie per il docente loggato)
        *   `GET, PUT, PATCH, DELETE /api/subjects/{subject_id}/` (CRUD su una materia specifica del docente)
    *   **Docente - Gestione Argomenti:**
        *   `GET, POST /api/subjects/{subject_id}/topics/` (Lista e crea argomenti per una data materia del docente)
        *   `GET, PUT, PATCH, DELETE /api/topics/{topic_id}/` (CRUD su un argomento specifico del docente; richiede subject_id nel payload se non parte dell'URL o per validazione)
*   **Docente - Gestione Studenti:**
    *   `GET, POST /api/students/`
    *   `GET, PUT, PATCH, DELETE /api/students/{student_id}/`
*   **Docente - Gestione Contenuti:**
   *   **Nota UI:** Durante la creazione/modifica di un Quiz o Quiz Template (se il docente può creare template), l'interfaccia (`fe-teacher`) permetterà di selezionare opzionalmente una Materia (dall'elenco delle materie del docente definite in `fe-lessons`) e, successivamente, un Argomento (filtrato in base alla materia scelta, anch'esso da `fe-lessons`). La selezione avverrà tramite menu a tendina.
   *   `GET, POST /api/quizzes/` (Payload POST e risposta GET includono `subject_id`, `topic_id`, `image_url`. GET lista include `subject_name`, `subject_color_placeholder`)
   *   `POST /api/quizzes/create-from-template/` (Il payload potrebbe includere `subject_id` e `topic_id` per sovrascrivere quelli del template, se presenti, o per aggiungerli se il template non li ha)
   *   `GET, PUT, PATCH, DELETE /api/quizzes/{quiz_id}/` (+ sub-routes domande/opzioni; Payload e risposta includono `subject_id`, `topic_id`, `image_url`. GET include `subject_name`, `subject_color_placeholder`)
   *   `POST /api/quizzes/{quiz_id}/assign/` (Body: `{"student_id": X}` o `{"group_id": Y}`)
    *   `POST /api/quizzes/{quiz_id}/revoke/` (Body: `{"student_id": X}` o `{"group_id": Y}`)
    *   `GET, POST /api/pathways/`
    *   `GET, PUT, PATCH, DELETE /api/pathways/{pathway_id}/`
    *   `POST /api/pathways/{pathway_id}/add-quiz/`
    *   `POST /api/pathways/{pathway_id}/assign/` (Body: `{"student_id": X}` o `{"group_id": Y}`)
    *   `POST /api/pathways/{pathway_id}/revoke/` (Body: `{"student_id": X}` o `{"group_id": Y}`)
*   **Docente - Gestione Ricompense:**
    *   `GET, POST /api/reward-templates/` (Locali + Globali; Payload POST e risposta GET includono `image_url`)
    *   `PUT, PATCH, DELETE /api/reward-templates/{template_id}/` (Solo locali propri; Payload e risposta includono `image_url`)
    *   `GET, POST /api/rewards/` (Include gestione disponibilità; Payload POST e risposta GET includono `image_url`)
    *   `GET, PUT, PATCH, DELETE /api/rewards/{reward_id}/` (Payload e risposta includono `image_url`)
    *   `POST /api/rewards/{reward_id}/make-available/` (Body: `{"student_id": X}` o `{"group_id": Y}`)
    *   `POST /api/rewards/{reward_id}/revoke-availability/` (Body: `{"student_id": X}` o `{"group_id": Y}`)
    *   `GET /api/reward-purchases/pending-delivery/`
    *   `POST /api/reward-purchases/{purchase_id}/mark-delivered/`
*   **Studente - Svolgimento & Profilo:**
    *   `GET /api/student/dashboard/` (Quiz/Percorsi assegnati; Quiz includono `subject_id`, `topic_id`, `image_url`, `subject_name`, `subject_color_placeholder`)
    *   `POST /api/quizzes/{quiz_id}/start-attempt/`
    *   `GET /api/attempts/{attempt_id}/`
    *   `POST /api/attempts/{attempt_id}/submit-answer/`
    *   `POST /api/attempts/{attempt_id}/complete/`
    *   `GET /api/student/pathways/{pathway_id}/progress/`
    *   `GET /api/student/wallet/`
    *   `GET /api/student/shop/` (Ricompense includono `image_url`)
    *   `POST /api/student/shop/purchase/{reward_id}/`
    *   `GET /api/student/purchases/`
*   **Docente - Gestione Gruppi:**
    *   `GET, POST /api/groups/`
    *   `GET, PUT, PATCH, DELETE /api/groups/{group_id}/`
    *   `GET, POST /api/groups/{group_id}/students/` (Aggiungere membro)
    *   `DELETE /api/groups/{group_id}/students/{student_id}/` (Rimuovere membro)
    *   `POST /api/groups/{group_id}/generate-token/`
    *   `DELETE /api/groups/{group_id}/delete-token/`
*   **Pubblico - Registrazione:**
    *   `POST /api/auth/register-by-token/` (Body: `{"token": "...", "first_name": "...", "last_name": "...", "pin": "...", "privacy_policy_accepted": true, "terms_of_service_accepted": true}`) # GDPR fields added
*   **GDPR / Profilo Utente (Studente):**
    *   `GET /api/profile/my-data/` (Esportazione dati personali)
    *   `PATCH /api/profile/me/` (Rettifica dati - es. nome/cognome)
    *   `POST /api/profile/request-deletion/` (Richiesta cancellazione account)
*   **Docente - Gestione Lezioni (Esempio):**
    *   `GET, POST /api/lessons/` (Payload POST e risposta GET includono `subject_id`, `topic_id`)
    *   `GET, PUT, PATCH, DELETE /api/lessons/{lesson_id}/` (Payload e risposta includono `subject_id`, `topic_id`)
    *   `POST /api/lessons/{lesson_id}/assign/` (Body: `{"student_id": X}` o `{"group_id": Y}`)
    *   `POST /api/lessons/{lesson_id}/revoke/` (Body: `{"student_id": X}` o `{"group_id": Y}`)

## 10. Sicurezza e Conformità GDPR (Security & Privacy by Design)

*   **Conformità GDPR:** L'applicazione è progettata per aderire ai principi del GDPR. Vedere [Piano di Conformità GDPR](GDPR_COMPLIANCE_PLAN.md) per dettagli.
*   **Autenticazione:** JWT obbligatorio per tutte le API protette.
*   **Autorizzazione:** Permessi DRF custom basati su ruolo (`IsAdminUser`, `IsTeacherUser`, `IsStudentUser`) e ownership (es. Docente modifica solo i *propri* quiz/studenti).
*   **Input Validation:** Uso rigoroso dei Serializers DRF per validare tutti i dati in ingresso.
*   **Protezioni Generali:** HTTPS obbligatorio, Rate Limiting, protezione contro SQL Injection (ORM), XSS (template escaping), CSRF (se applicabile), gestione sicura password (hashing Django).
*   **Minimizzazione Dati & Esposizione:**
    *   Raccolta dei soli dati strettamente necessari per le finalità dichiarate.
    *   Evitare ID sequenziali nelle API pubbliche se possibile (preferire UUID/slug).
    *   Logging attento, evitando dati personali non necessari.
*   **Anonimizzazione IP:** Gli indirizzi IP dei client vengono anonimizzati a livello di reverse proxy (Nginx) *prima* di essere loggati o passati al backend, in linea con i principi GDPR.
*   **Consenso:** Raccolta esplicita del consenso per Privacy Policy e Termini di Servizio durante la registrazione, con registrazione timestamp. Meccanismi per consenso minori in fase di sviluppo.
*   **Diritti Interessati:** API dedicate per permettere agli utenti l'esercizio dei diritti di accesso, rettifica, cancellazione e portabilità.

### 10.1 Procedura di Gestione Data Breach (Sintesi)

Questa procedura definisce i passi da seguire in caso di sospetta o confermata violazione dei dati personali (Data Breach) ai sensi del GDPR.

1.  **Identificazione e Valutazione Iniziale:**
    *   Qualsiasi dipendente/collaboratore che sospetti un Data Breach deve segnalarlo immediatamente al Responsabile Tecnico/DPO (se designato).
    *   Il Responsabile valuta rapidamente la natura dell'incidente per confermare se si tratta di un Data Breach e stimarne la potenziale gravità (tipologia di dati coinvolti, numero di interessati, possibili conseguenze).

2.  **Contenimento e Recupero:**
    *   Attivare il team tecnico per isolare i sistemi compromessi, bloccare accessi non autorizzati e limitare la diffusione della violazione.
    *   Avviare le procedure di recupero dei dati (se necessario e possibile) e ripristino della sicurezza dei sistemi.

3.  **Valutazione del Rischio e Notifica:**
    *   Valutare il rischio per i diritti e le libertà degli interessati.
    *   **Notifica all'Autorità Garante:** Se la violazione presenta un rischio, notificarla all'Autorità Garante per la Protezione dei Dati Personali competente (es. Garante Privacy italiano) **entro 72 ore** dalla scoperta, fornendo tutte le informazioni richieste (natura della violazione, categorie di dati e interessati, conseguenze probabili, misure adottate).
    *   **Comunicazione agli Interessati:** Se la violazione presenta un **rischio elevato** per i diritti e le libertà degli interessati, comunicare loro la violazione **senza ingiustificato ritardo**, descrivendo la natura della violazione, le probabili conseguenze e le misure adottate, a meno che non si applichino eccezioni (es. dati già crittografati, misure successive che hanno neutralizzato il rischio elevato).

4.  **Documentazione Interna:**
    *   Mantenere un registro interno dettagliato di tutte le violazioni dei dati, incluse quelle non notificate all'Autorità Garante. Il registro deve contenere i fatti relativi alla violazione, i suoi effetti e le misure adottate per porvi rimedio.

5.  **Revisione Post-Incidente:**
    *   Analizzare le cause della violazione e l'efficacia della risposta.
    *   Aggiornare le misure di sicurezza tecniche e organizzative e le procedure interne per prevenire incidenti futuri.

## 11. Approccio Sviluppo (Test Driven Development - TDD)

*   **Flusso:** Scrivere test fallimentare -> Scrivere codice minimo -> Refactoring.
*   **Copertura:** Test unitari (modelli, logica business), Test di integrazione (API views, flussi completi).
*   **Strumenti:** `manage.py test`, `coverage.py`, `factory-boy`.