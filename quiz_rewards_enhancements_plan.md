# Piano di Miglioramento per Quiz e Ricompense

Questo documento riassume le modifiche proposte al database e alle API per integrare nuove funzionalità per i Quiz (materie, argomenti, immagini) e per le Ricompense (immagini).

## 1. Modifiche al Database

### Nuovi Modelli

*   **`Subject` (Materia)**
    *   **Scopo:** Memorizzare le materie create dai docenti, utilizzabili per Quiz e Lezioni.
    *   **Campi Chiave:**
        *   `id`: PK
        *   `teacher_id`: FK a `USER(id)` (docente creatore)
        *   `name`: VARCHAR (nome materia, es. "Matematica")
        *   `color_placeholder`: VARCHAR (colore per placeholder SVG quiz, es. "#FF5733")
        *   `created_at`, `updated_at`
    *   **Logica di Eliminazione:** Se una materia viene eliminata, i `subject_id` nei `Topic`, `Quiz` e `Lesson` associati verranno impostati a `NULL`.

*   **`Topic` (Argomento)**
    *   **Scopo:** Memorizzare gli argomenti, associati a una materia e creati da un docente.
    *   **Campi Chiave:**
        *   `id`: PK
        *   `subject_id`: FK a `SUBJECT(id)` (materia di appartenenza, NOT NULL)
        *   `teacher_id`: FK a `USER(id)` (docente creatore)
        *   `name`: VARCHAR (nome argomento, es. "Equazioni di primo grado")
        *   `created_at`, `updated_at`
    *   **Logica di Eliminazione:** Se un argomento viene eliminato, i `topic_id` nei `Quiz` e `Lesson` associati verranno impostati a `NULL`. L'eliminazione di una materia imposta `subject_id` a `NULL` qui se la relazione `Topic.subject_id` lo permette (ma abbiamo definito che `Topic.subject_id` è NOT NULL, quindi l'argomento verrebbe dissociato dalla materia se la materia viene eliminata e l'FK `Topic.subject_id` viene settato a NULL). Coerentemente con quanto detto per `Subject`, se `Subject` è eliminato, `Topic.subject_id` diventa `NULL`.

### Modifiche a Modelli Esistenti

*   **`QUIZ`**
    *   **Nuovi Campi:**
        *   `subject_id`: FK a `SUBJECT(id)`, `NULLABLE`
        *   `topic_id`: FK a `TOPIC(id)`, `NULLABLE`
        *   `image_url`: VARCHAR, `NULLABLE` (URL immagine copertina quiz)
    *   **Logica Immagine:** Se `image_url` presente, usarla. Altrimenti, se `subject_id` presente, usare placeholder SVG con `Subject.name` e `Subject.color_placeholder`. Altrimenti, placeholder generico.

*   **`LESSON`** (Assunto per coerenza)
    *   **Campi da Aggiungere/Confermare:**
        *   `subject_id`: FK a `SUBJECT(id)`, `NULLABLE`
        *   `topic_id`: FK a `TOPIC(id)`, `NULLABLE`

*   **`REWARD_TEMPLATE`**
    *   **Nuovo Campo:**
        *   `image_url`: VARCHAR, `NULLABLE` (URL immagine per il template ricompensa)

*   **`REWARD`**
    *   **Nuovo Campo:**
        *   `image_url`: VARCHAR, `NULLABLE` (URL immagine specifica per la ricompensa)
    *   **Logica Immagine:** Se `Reward.image_url` presente, usarla. Altrimenti, se `template_id` presente e `RewardTemplate.image_url` (del template) presente, usarla. Altrimenti, placeholder generico esistente.

## 2. Modifiche alle API REST

*   **Nuovi Endpoint per Docenti (Gestione Materie e Argomenti):**
    *   Materie:
        *   `GET, POST /api/subjects/`
        *   `GET, PUT, PATCH, DELETE /api/subjects/{subject_id}/`
    *   Argomenti:
        *   `GET, POST /api/subjects/{subject_id}/topics/` (Opzione consigliata: Nidificati)
        *   `GET, PUT, PATCH, DELETE /api/topics/{topic_id}/` (Accesso diretto e modifica argomento)

*   **Modifiche agli Endpoint `QUIZ`:**
    *   Creazione/Aggiornamento (`POST /api/quizzes/`, `PUT /api/quizzes/{quiz_id}/`):
        *   Payload accetta `subject_id` (opz.), `topic_id` (opz.), `image_url` (opz.).
    *   Recupero (`GET /api/quizzes/{quiz_id}/`, `GET /api/student/dashboard/`):
        *   Risposta include `subject_id`, `topic_id`, `image_url`, e dettagli materia (nome, colore) se `subject_id` presente.

*   **Modifiche agli Endpoint `REWARD_TEMPLATE` e `REWARD`:**
    *   Creazione/Aggiornamento (`POST /api/reward-templates/`, `POST /api/rewards/`):
        *   Payload accetta `image_url` (opz.).
    *   Recupero (`GET /api/reward-templates/{id}/`, `GET /api/rewards/{id}/`, `GET /api/student/shop/`):
        *   Risposta include `image_url`.

*   **Modifiche agli Endpoint `LESSON` (per coerenza):**
    *   Simili modifiche per accettare e restituire `subject_id` e `topic_id`.

## 3. Considerazioni Aggiuntive

*   **Gestione File Immagini:** I dettagli tecnici per il caricamento delle immagini (formati, dimensioni, storage) verranno definiti in fase di implementazione. I modelli memorizzeranno solo gli URL.
*   **Permessi:** I docenti potranno creare, modificare ed eliminare solo le proprie materie e argomenti.