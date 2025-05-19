# Piano di Implementazione: Unità Didattiche di Apprendimento (UDA) e Funzionalità di Copia

**Versione:** 1.1
**Data:** 16 Maggio 2025
**Riferimento Documento di Progettazione:** [`design_document.md`](design_document.md:1) (Sezione 12 e relativi aggiornamenti)
**Modifiche Recenti:** Rimozione concetto "Template UDA", introduzione funzionalità "Copia UDA".

## 1. Introduzione

Questo documento descrive il piano di implementazione per la funzionalità "Unità Didattiche di Apprendimento (UDA)" e l'introduzione della possibilità di copiare UDA esistenti per l'applicazione educativa. L'obiettivo è fornire ai docenti uno strumento per pianificare, organizzare e tracciare sequenze di contenuti didattici in modo efficiente. Il concetto di "Template UDA" è stato rimosso.

## 2. Backend (Django & Django REST Framework) [COMPLETATO]

### 2.1. Struttura del Progetto [COMPLETATO]
*   **Nuova App Django:** [VERIFICATO ESISTENTE] L'app Django `uda` esiste.
    *   Alternativa (da valutare in fase di sviluppo): Integrare i modelli e la logica all'interno dell'app esistente `lessons` se la coesione risulta maggiore. Per questo piano, si assume una nuova app `uda`.
*   Registrare la nuova app `uda` in `config/settings.py`. [COMPLETATO]

### 2.2. Modelli Django [COMPLETATO]
Verranno creati i seguenti modelli nel file `uda/models.py` (o, se più appropriato, il modello `Course` potrebbe risiedere in una nuova app `courses`) come specificato nel [`design_document.md`](design_document.md:1):

*   **Nota importante sulla gestione dei Nomi di Argomenti e Materie:** Si specifica che i nomi delle entità come Materie (`Subject`) e soprattutto Argomenti (`Topic`) devono essere gestiti e salvati in modo atomico. Ad esempio, un `Topic` deve avere un campo nome che contiene solo il titolo dell'argomento (es., "Le equazioni di primo grado") e non una stringa combinata come "Matematica - Le equazioni di primo grado". L'associazione tra UDA, Materie e Argomenti è gestita tramite le relazioni M2M definite (`UDASubject`, `UDATopic`). Questa atomicità è cruciale per la corretta visualizzazione e interrogazione dei dati.
*   **`Course`**: NUOVO MODELLO [COMPLETATO]
    *   Campi: `teacher` (FK a User), `name` (CharField, univoco per docente), `description` (TextField, opzionale), `created_at`, `updated_at`.
*   **`UDATemplate`**: [RIMOSSO]
*   **`UDATemplateTopic`**: [RIMOSSO]
*   **`UDATemplateContent`**: [RIMOSSO]
*   **`UDA`**: MODIFICATO [COMPLETATO]
    *   Campi: `teacher` (FK a User), `course` (FK a Course, opzionale, `null=True`, `blank=True`), `title`, `description`, `start_date`, `end_date`, `subjects` (M2M con Subject tramite `UDASubject`, opzionale) [IMPLEMENTATO], `topics` (M2M con Topic tramite `UDATopic`), `status` (CharField con choices: TODO, IN_PROGRESS, COMPLETED), `order_in_course` (PositiveIntegerField, opzionale, per l'ordinamento manuale nel corso), `created_at`, `updated_at`. (Campo `source_template` rimosso).
  *   **`UDATopic`**: [ESISTENTE - VERIFICATO] Tabella di join per `UDA` e `Topic`.
    *   Campi: `uda` (FK), `topic` (FK).
  *   **`UDASubject`**: NUOVO MODELLO [COMPLETATO] Tabella di join per `UDA` e `Subject`.
    *   Campi: `uda` (FK), `subject` (FK).
  *   **`UDAContent`**: MODIFICATO
    *   Campi: `uda` (FK), `content_type` (CharField con choices: LESSON, QUIZ_TEMPLATE, NOTE, ACTIVITY), `lesson` (FK a Lesson, opzionale), `quiz_template` (FK a QuizTemplate, opzionale, per riferirsi a un template di quiz da cui istanziare un quiz concreto in un secondo momento), `note_title`, `note_content`, `activity_title`, `activity_description`, `activity_attachment_url` (FileField/CharField, opzionale), `activity_completed` (BooleanField, specifico per `ACTIVITY`), `teacher_marked_completed` (BooleanField, default `False`, per tutti i tipi), `order` (PositiveIntegerField), `estimated_hours` (DecimalField, opzionale, `null=True`, `blank=True`, `max_digits=4`, `decimal_places=1`), `created_at`, `updated_at`.

*   **Azioni:**
    *   Definire i modelli (incluso il nuovo `Course`, il nuovo `UDASubject` [COMPLETATO] e le modifiche a `UDA` [COMPLETATO PER SUBJECTS E RIMOZIONE `source_template`], e `UDAContent` per aggiungere `estimated_hours`).
    *   Creare e applicare le migrazioni Django (`makemigrations uda`, `migrate` - o per la nuova app se `Course` è separato). [COMPLETATO, DA VERIFICARE MIGRAZIONE PER RIMOZIONE MODELLI TEMPLATE E CAMPO `source_template`]

### 2.3. Serializer (DRF) [COMPLETATO]
Verranno creati i serializer in `uda/serializers.py` (o file appropriati):

*   **`CourseSerializer`**: NUOVO SERIALIZER. [COMPLETATO]
*   `UDATemplateContentSerializer` [RIMOSSO]
*   `UDATemplateSerializer` [RIMOSSO]
*   `UDAContentSerializer` (MODIFICATO - gestirà `quiz_template` invece di `quiz`, upload/link allegati per `ACTIVITY`, lo stato `activity_completed`, `teacher_marked_completed` e `estimated_hours`).
*   `UDASerializer` (MODIFICATO - includerà `UDAContentSerializer`, gestirà i campi `course_id` e `order_in_course` per la scrittura, `course` (nested o ID) per la lettura, e il campo `subjects` M2M. Rimosso riferimento a `source_template`). [COMPLETATO PER `subjects`]
*   Serializer per `UDATopic`. `UDASubjectSerializer` non necessario, gestito implicitamente. `UDATemplateTopicSerializer` [RIMOSSO].

*   **Azioni:**
    *   Implementare i serializer, prestando attenzione alla validazione e alla gestione dei campi relazionati e dei contenuti nested/dinamici, inclusa la relazione UDA-Corso, l'ordinamento UDA nel corso, il completamento dei contenuti UDA e il nuovo campo `estimated_hours`. [COMPLETATO, DA AGGIORNARE PER `estimated_hours`]

### 2.4. View API (DRF) [COMPLETATO]
Verranno implementate le view in `uda/views.py` (o file appropriati, probabilmente utilizzando `ModelViewSet`):

*   **`CourseViewSet`**: NUOVO VIEWSET per CRUD su `Course`. [COMPLETATO]
    *   Endpoint custom per listare le UDA di un corso: `GET /api/courses/{course_id}/udas/` (rispetterà `order_in_course`). [COMPLETATO]
    *   Endpoint custom per riordinare le UDA in un corso: `POST /api/courses/{course_id}/udas/reorder/`. [COMPLETATO]
*   `UDATemplateViewSet`: [RIMOSSO]
*   `UDAViewSet`: Per CRUD su `UDA`. (MODIFICATO per gestire l'associazione con `Course`, `order_in_course` e il campo `subjects` M2M). [COMPLETATO PER `subjects` TRAMITE SERIALIZER]
    *   NUOVO Endpoint custom per copiare una UDA: `POST /api/udas/{uda_id}/copy/`. [IMPLEMENTATO]
*   Endpoint custom per la gestione dei `UDAContent` (es. `/api/udas/{uda_id}/contents/`). [ESISTENTE - VERIFICATO]
*   Endpoint custom per marcare un'`ACTIVITY` come completata (`activity_completed`): `PATCH /api/udas/{uda_id}/contents/{content_id}/complete-activity/`. [ESISTENTE - VERIFICATO]
    *   Endpoint custom per marcare `teacher_marked_completed` su un `UDAContent`: `PATCH /api/udas/{uda_id}/contents/{content_id}/update-teacher-completion/`. [COMPLETATO]

*   **Permessi:**
    *   Utilizzare permessi custom (es. `IsOwnerOrReadOnly` modificato o nuovo permesso `IsOwner`) per assicurare che solo il docente proprietario possa modificare/eliminare i propri Corsi e UDA. [COMPLETATO con `IsOwner`]
*   **Azioni:**
    *   Implementare i ViewSet (incluso `CourseViewSet`) e le azioni custom. [COMPLETATO]
    *   Configurare i permessi. [COMPLETATO]

### 2.5. URL Configuration [COMPLETATO]
Verranno configurati gli URL in `uda/urls.py` (o file appropriati) e inclusi nel file `config/urls.py` principale:

*   Registrare i router per i ViewSet (`CourseViewSet`, `UDAViewSet`). `UDATemplateViewSet` [RIMOSSO]. [COMPLETATO]
*   Mappare le azioni custom (inclusi gli endpoint per le UDA di un corso, riordino UDA, e aggiornamento `teacher_marked_completed`). [COMPLETATO tramite router]

*   **Azioni:**
    *   Definire gli URL. [COMPLETATO]

## 3. Frontend (frontend-lessons - Vue.js) [COMPLETATO]

### 3.1. Store Management (Pinia) [COMPLETATO]
*   **`courseStore.ts`**: NUOVO STORE [COMPLETATO]
    *   State: `courses`, `currentCourse`, `loading`, `error`.
    *   Actions: `fetchCourses`, `fetchCourse`, `createCourse`, `updateCourse`, `deleteCourse`, `fetchUdasForCourse`, `reorderUdasInCourse`.
*   **`udaTemplateStore.ts`**: [RIMOSSO]
*   **`udaStore.ts`**: [MODIFICATO]
    *   State: `udas`, `currentUda`, `loading`, `error`.
    *   Actions: `fetchUdas` (con filtri per status, e opzionalmente per `courseId`), `fetchUda`, `createUda` (da zero, gestendo `courseId`, `orderInCourse` e `subjectIds` [COMPLETATO]), `updateUda` (gestendo `courseId`, `orderInCourse` e `subjectIds` [COMPLETATO]), `deleteUda`, `addContentToUda` (gestirà `estimated_hours`), `updateContentInUda` (inclusa `teacher_marked_completed`, gestirà `estimated_hours`), `removeContentFromUda`, `completeActivityInUda` (per `activity_completed`), `updateUdaContentTeacherCompletion`, `copyUda` (NUOVA ACTION).
*   **`quizStore.ts`**: [MODIFICATO - VEDI NOTA SEZ. 3.4]
    *   Aggiunto state per `quizTemplates`, `currentQuizTemplate`.
    *   Aggiunta action `fetchQuizTemplates` per recuperare i template quiz (endpoint `/api/education/teacher/quiz-templates/`).
    *   Aggiunta action `createQuizFromTemplate` per creare un quiz da un template (endpoint `/api/quizzes/create-from-template/`).

*   **Azioni:**
    *   [MODIFICATO] Creare il file store `udaStore.ts` e implementare la struttura base di state e actions. `udaTemplateStore.ts` [RIMOSSO].
    *   [COMPLETATO] Creare il nuovo store `courseStore.ts` e implementare la struttura base (includendo action per riordinare UDA).
    *   [MODIFICATO] Aggiornare `udaStore.ts` per gestire l'associazione con i corsi, l'ordinamento, il completamento dei contenuti, il campo `estimated_hours` e la nuova action `copyUda`.
    *   `udaTemplateStore.ts` [RIMOSSO].
    *   [COMPLETATO] _Nota: Creato `uiStore.ts` per gestire richieste modali e successivamente esteso per notifiche globali._
    ### 3.2. Servizi API [COMPLETATO]
    Creare un modulo `services/udaService.ts` (o simile, potrebbe essere utile un `services/courseService.ts`): [COMPLETATO]
    
    *   Funzioni per ogni endpoint API definito nel backend:
        *   Per Corsi: `getCourses()`, `getCourse(id)`, `createCourse(data)`, `updateCourse(id, data)`, `deleteCourse(id)`, `getUdasForCourse(courseId)`, `reorderUdasInCourse(courseId, udaIds)`.
        *   Per Template UDA: [RIMOSSE]
        *   Per UDA: (es. `getUdas()`, `createUda(data)` - modificata per includere `courseId`, `orderInCourse` e `subjectIds` [VERIFICATO - GESTITO DA STORE], `getUdaContents(udaId)`, `addContentToUda(udaId, data)`, `updateContentInUda(udaId, contentId, data)`, `copyUda(udaId)` [NUOVA]).
        *   Per Contenuti UDA: (es. `uploadActivityAttachment(udaContentId, file)`, `updateUdaContentTeacherCompletion(udaContentId, completed)`). Le funzioni di creazione/aggiornamento contenuto (`addContentTo...`, `updateContentIn...`) dovranno accettare e inviare il campo `estimated_hours`.
    
    *   **Azioni:**
        *   [COMPLETATO] Implementare la struttura base delle funzioni di servizio API in `services/udaService.ts` e `services/courseService.ts`.
        *   [COMPLETATO] Aggiungere/Modificare le funzioni di servizio per includere la gestione dei Corsi, l'associazione UDA-Corso, l'ordinamento, il completamento dei contenuti e il campo `estimated_hours`.

### 3.3. Routing (Vue Router) [COMPLETATO]
Aggiungere nuove route in `router/index.ts` per `frontend-lessons`: [COMPLETATO]

*   `/courses`: Lista dei Corsi (`CourseListView`). NUOVA [COMPLETATO]
*   `/courses/new`: Creazione Corso (`CourseFormView`). NUOVA [COMPLETATO]
*   `/courses/:id`: Dettaglio Corso (`CourseDetailView`). NUOVA (mostrerà UDA associate) [COMPLETATO]
*   `/courses/:id/edit`: Modifica Corso (`CourseFormView`). NUOVA [COMPLETATO]
*   `/uda-templates`: [RIMOSSA]
*   `/uda-templates/new`: [RIMOSSA]
*   `/uda-templates/:id/edit`: [RIMOSSA]
*   `/udas`: Lista UDA (`UdaListView`). [COMPLETATO]
*   `/udas/new`: Creazione UDA (`UdaFormView`). [MODIFICATO - rimossa opzione template]
*   `/udas/:id`: Dettaglio UDA (`UdaDetailView`). [COMPLETATO]
*   `/udas/:id/edit`: Modifica UDA (`UdaFormView`). [COMPLETATO]

*   **Azioni:**
    *   [COMPLETATO] Definire le route in `router/index.ts` e associarle ai componenti.
    *   [COMPLETATO] Aggiungere le nuove route per i Corsi.

### 3.4. Componenti UI [COMPLETATO]
Sviluppare i seguenti componenti Vue.js in `frontend-lessons/src/views/` e `frontend-lessons/src/components/uda/` (o `components/courses/`):

*   **Viste Principali (Pages):**
    *   `CourseListView.vue`: NUOVA. [COMPLETATO]
    *   `CourseFormView.vue`: NUOVA. [COMPLETATO]
    *   `CourseDetailView.vue`: NUOVA. [COMPLETATO]
    *   `UdaTemplateListView.vue`: [RIMOSSO]
    *   `UdaTemplateFormView.vue`: [RIMOSSO]
    *   `UdaListView.vue`: MODIFICATA (aggiunto pulsante "Copia UDA"). [COMPLETATO]
    *   `UdaFormView.vue`: MODIFICATA (per gestire selezione multipla materie, rimossa sezione "Parti da Template"). [COMPLETATO]
    *   `UdaDetailView.vue`: [COMPLETATO]
*   **Componenti Specifici per Contenuti:**
    *   `UdaContentItemRenderer.vue`: MODIFICATO (per visualizzare `estimated_hours`). [COMPLETATO, DA AGGIORNARE]
    *   `UdaContentLessonDisplay.vue`: [COMPLETATO] (da aggiornare per visualizzare `estimated_hours`)
    *   `UdaContentQuizDisplay.vue`: [COMPLETATO] (da aggiornare per visualizzare `estimated_hours`)
    *   `UdaContentNoteDisplay.vue`: [COMPLETATO] (da aggiornare per visualizzare `estimated_hours`)
    *   `UdaContentActivityDisplay.vue`: [COMPLETATO] (da aggiornare per visualizzare `estimated_hours`)
    *   `NoteTemplateContentDisplay.vue`: [RIMOSSO] (se specifico per template)
    *   `ActivityTemplateContentDisplay.vue`: [RIMOSSO] (se specifico per template)
*   **Componenti di Supporto:**
    *   `UdaContentEditor.vue`: [COMPLETATO] (da aggiornare per includere input per `estimated_hours`)
    *   Modal per selezionare Lezioni/Quiz esistenti da aggiungere ai contenuti. [`SelectExistingContentModal.vue` - COMPLETATO]
    *   Componente per upload file per `activity_attachment_url`. [`FileUpload.vue` - COMPLETATO]
    *   _Nota: Creato `GlobalNotificationDisplay.vue` per visualizzare notifiche globali._ [COMPLETATO]
*   **Menu:** [MODIFICATO - rimossa voce "Template UDA"]

*   **Azioni:**
    *   [COMPLETATO] Creare i file base per i componenti delle viste principali UDA.
    *   [COMPLETATO] Creare i file base per i nuovi componenti dei Corsi.
    *   [MODIFICATO] Aggiungere la voce di menu per UDA. Modificarla/Aggiungere voce per Corsi. Rimuovere voce "Template UDA".
    *   [MODIFICATO] Sviluppare i componenti Vue.js, integrando gli store Pinia e i servizi API (rimosso `udaTemplateStore`).
    *   [MODIFICATO] Curare l'UI/UX per la gestione dei Corsi, l'ordinamento delle UDA nei corsi, l'associazione UDA-Corso, la marcatura del completamento dei contenuti UDA, l'inserimento/visualizzazione del tempo stimato (`estimated_hours`) e la nuova funzionalità di copia UDA.
    *   [MODIFICATO] Implementare l'aggiunta di UDA (nuove) e la copia di UDA esistenti direttamente da `CourseDetailView.vue`. Rimossa aggiunta da template.
        *   [COMPLETATO] Questo include la creazione di eventuali modali necessari (es. `CreateNewUdaModal`).
        *   [MODIFICATO] Aggiornamento di `udaStore.ts` (rimossa logica template, aggiunta `copyUda`).
        *   `udaTemplateStore.ts` [RIMOSSO].
    *   [COMPLETATO] Implementare la visualizzazione e il riordino delle UDA associate in `CourseDetailView.vue`.
    *   [COMPLETATO] Completare il form in `CreateNewUdaModal.vue`.
    *   [COMPLETATO] Implementare la logica per l'effettivo riordino delle UDA.
    *   [MODIFICATO E CORRETTO] Implementare la modale per selezionare Lezioni/Quiz esistenti ([`SelectExistingContentModal.vue`](frontend-lessons/src/components/uda/SelectExistingContentModal.vue:1)):
        *   Corretta la logica per la selezione dei Quiz: ora la modale carica e visualizza i `QuizTemplate` (tramite `quizStore.fetchQuizTemplates` dall'endpoint `/api/education/teacher/quiz-templates/`).
        *   Alla conferma della selezione di un `QuizTemplate`, l'ID del `QuizTemplate` viene passato al componente genitore.
        *   Per i **Template UDA**, [RIMOSSO - non più applicabile].
        *   Per le **UDA Concrete**, questo ID di `QuizTemplate` viene salvato nel `UDAContent.quiz_template`. L'istanza concreta di `Quiz` verrà generata in un secondo momento (es. all'avvio del quiz).
        *   Aggiornati i tipi `RawSelectedContentItem` e `SelectedContentItem` in [`frontend-lessons/src/types/uda.ts`](frontend-lessons/src/types/uda.ts:1) e creato [`frontend-lessons/src/types/quizTemplate.ts`](frontend-lessons/src/types/quizTemplate.ts:1).
    *   [COMPLETATO] Implementare il componente per l'upload dei file per `activity_attachment_url`.
    *   [COMPLETATO, DA AGGIORNARE] Migliorare/Completare `UdaContentItemRenderer.vue` (per visualizzare `estimated_hours`).
    *   [COMPLETATO, DA AGGIORNARE] Migliorare/Completare `UdaContentEditor.vue` (per aggiungere input `estimated_hours`).
    *   [COMPLETATO] Implementare la logica di eliminazione UDA in `CourseDetailView.vue`.
    *   [RIMANDATO] Valutare l'implementazione del drag-and-drop per il riordino delle UDA in `CourseDetailView.vue`.
    *   [MODIFICATO] Continuare lo sviluppo e il raffinamento degli altri componenti UI per UDA.
    *   [COMPLETATO] Completare `UdaDetailView.vue` per la visualizzazione dettagliata dei contenuti UDA:
        *   [COMPLETATO] Implementare il recupero e la visualizzazione dei dati principali dell'UDA, con la seguente disposizione compattata:
            *   **Dati Principali UDA (Layout Compattato):**
                *   Riga 1: Titolo, Descrizione (breve), Data Inizio, Data Fine.
                *   Riga 2: Stato, Corso, Materie (potenzialmente multiple), Argomenti.
            *   Visualizzazione dettagliata dei nomi per Materia (ora potenzialmente multiple), Argomenti (assicurandosi che venga visualizzato solo il nome atomico dell'argomento, es. "Le equazioni", e non "Materia - Le equazioni") e Corso, se non già inclusi in modo esauriente nel layout compattato.
        *   [COMPLETATO] Definire/Implementare la logica per gli handler degli eventi.
    *   [COMPLETATO, DA AGGIORNARE] Raffinare i componenti display specifici per contenuto (per visualizzare `estimated_hours`).
    *   [COMPLETATO] Implementare le modali di modifica per Note e Attività.
    *   [COMPLETATO] Gestire l'upload effettivo dei file per le attività UDA (Frontend e Backend verificato).

## 4. Testing [PROSSIMO PASSO]

### 4.1. Backend (Django)
*   **Test Unitari:**
    *   Testare i metodi custom dei modelli (se presenti), inclusi `Course` e `UDASubject`.
    *   Testare la logica dei serializer (validazione, creazione/aggiornamento oggetti), inclusi `CourseSerializer` e le modifiche a `UDASerializer` (per gestione `subjects` M2M) [DA VERIFICARE CON TEST].
    *   Testare la logica di business nelle view e i permessi, inclusi `CourseViewSet` e `UDAViewSet` per quanto riguarda la gestione delle materie multiple.
*   **Test di Integrazione:**
    *   Testare tutti gli endpoint API (CRUD, azioni custom) con diversi input e scenari di autenticazione/autorizzazione, inclusi quelli per i Corsi, l'associazione UDA-Corso e la gestione di materie multiple per UDA [DA VERIFICARE CON TEST].
    *   Verificare la corretta creazione/gestione delle relazioni (in particolare `UDA` <-> `Subject`) e dei contenuti nested, incluso il salvataggio e recupero di `estimated_hours`.
    *   **Strumenti:** `pytest-django`, `factory-boy`.
    *   **Azioni:**
        *   Scrivere e eseguire i test backend, coprendo le nuove funzionalità dei Corsi, la gestione di materie multiple per UDA e il campo `estimated_hours`. [DA FARE]
    
    ### 4.2. Frontend (Vue.js)
    *   **Test Unitari:**
        *   Testare la logica dei componenti (props, computed properties, methods), inclusi i nuovi componenti per i Corsi, le modifiche ai componenti UDA (`UdaFormView.vue`) per la selezione di materie multiple, e l'aggiornamento di `UdaContentEditor.vue` e dei componenti display per `estimated_hours`. [DA FARE]
        *   Testare le actions e mutations/getters degli store Pinia, inclusi `courseStore` e le modifiche a `udaStore` (per gestione `subjectIds`, `estimated_hours` e `copyUda`). `udaTemplateStore` [RIMOSSO]. [DA FARE]
    *   **Test E2E (End-to-End):**
        *   Simulare i flussi utente completi:
            *   Creazione/Modifica/Eliminazione di un Corso.
            *   Riordinamento delle UDA all'interno di un Corso.
            *   Creazione di un Template UDA. [RIMOSSO]
            *   Creazione di una UDA (da zero) con una o più materie e sua associazione a un Corso (con ordine). [DA TESTARE SPECIFICATAMENTE]
            *   Copia di una UDA esistente e successiva modifica. [NUOVO DA TESTARE]
            *   Visualizzazione delle UDA all'interno di un Corso (rispettando l'ordine).
            *   Visualizzazione delle materie multiple in `UdaDetailView.vue`. [DA TESTARE]
            *   Aggiunta di una UDA (nuova o copiata) dalla pagina di un Corso o dalla lista UDA.
            *   Aggiunta/modifica/rimozione di contenuti in una UDA, includendo l'inserimento e la visualizzazione di `estimated_hours`. [DA TESTARE SPECIFICATAMENTE]
            *   Marcatura di `teacher_marked_completed` per Lezioni, Quiz, Note e Attività all'interno di una UDA.
            *   Completamento di un'attività (`activity_completed`) in una UDA.
            *   Filtro delle UDA per stato, per Corso e (se implementato e funzionante con materie multiple) per materia. [DA VERIFICARE/TESTARE]
    *   **Strumenti:** Vitest/Jest per unit test, Playwright/Cypress per E2E test.
    *   **Azioni:**
        *   Scrivere e eseguire i test frontend, coprendo le nuove funzionalità dei Corsi, l'ordinamento, il completamento esteso, la gestione di materie multiple per UDA, il campo `estimated_hours` e la funzionalità di copia UDA. [DA FARE]

## 5. Considerazioni Aggiuntive

*   **Gestione File Allegati (Attività UDA):** [COMPLETATO]
    *   Decidere la strategia di storage (es. `django-storages` con S3, o file system locale per sviluppo). [DECISO: File system locale con `FileField`]
    *   Implementare la logica di upload/delete sicuro dei file. [COMPLETATO]
*   **UI/UX per Ordinamento Contenuti:** [COMPLETATO]
    *   Implementare una soluzione drag-and-drop o bottoni "su/giù" per l'ordinamento dei `UDAContent`. `UDATemplateContent` [RIMOSSO]. [COMPLETATO con bottoni]
    *   Implementare una soluzione simile (drag-and-drop o bottoni) per l'ordinamento delle `UDA` all'interno di un `Course`. [COMPLETATO con bottoni]
*   **UI/UX per Completamento Contenuti UDA:** [COMPLETATO]
    *   Prevedere checkbox o controlli simili per marcare `teacher_marked_completed` per ogni `UDAContent` nella vista di dettaglio e modifica dell'UDA. [COMPLETATO]
*   **Performance:**
    *   Considerare l'ottimizzazione delle query per il recupero di UDA/Template UDA con molti contenuti, e per i corsi con molte UDA.
*   **Traduzioni/Localizzazione:** Se l'applicazione supporta più lingue, assicurarsi che tutti i nuovi testi UI siano traducibili.
*   **Visualizzazione Tempo Stimato Totale:** Valutare l'aggiunta della visualizzazione del tempo totale stimato per un'intera UDA (somma degli `estimated_hours` dei suoi contenuti) nelle viste di dettaglio e lista. Riferimento a Template UDA [RIMOSSO].

## 6. Stima di Sviluppo (Indicativa)

*   Backend (Funzionalità Corsi + Modifiche UDA per materie multiple + `estimated_hours`): X+A+D giorni [COMPLETATO, DA AGGIORNARE PER `estimated_hours`]
*   Frontend (Funzionalità Corsi + Modifiche UDA per materie multiple + `estimated_hours`): Y+B+E giorni [COMPLETATO, DA AGGIORNARE PER `estimated_hours`]
*   Testing (complessivo, inclusi Corsi, materie multiple UDA e `estimated_hours`): Z+C+F giorni [DA FARE]

(Le stime X, Y, Z, A, B, C, D, E, F andranno definite dal team di sviluppo)

## 7. Priorità e Fasi (Opzionale)

*   **Fase 1 (MVP):** [COMPLETATO]
    *   Funzionalità base CRUD per Corsi.
    *   Funzionalità base CRUD per UDA, con associazione ai Corsi. Template UDA [RIMOSSO].
    *   Supporto per contenuti Lezione, Quiz, Nota, Attività in UDA.
    *   Gestione stato UDA.
    *   Visualizzazione UDA per Corso.
    *   Marcatura `teacher_marked_completed` per tutti i tipi di `UDAContent`.
    *   Marcatura `activity_completed` specifica per `ACTIVITY`.
*   **Fase 2:** [COMPLETATO]
    *   Ordinamento manuale delle UDA all'interno di un Corso.
    *   Ordinamento avanzato dei contenuti UDA (all'interno di una UDA).
    *   Filtri avanzati per le liste UDA (per stato, corso, ecc.).
    *   Possibilità di aggiungere UDA (nuova o copiata) direttamente dalla vista di un Corso o dalla lista UDA.

Questo piano di implementazione fornisce una roadmap per lo sviluppo della funzionalità UDA e Corsi, con la rimozione dei Template UDA e l'introduzione della copia UDA. La fase di sviluppo per l'aggiunta di materie multiple alle UDA è considerata conclusa. Il prossimo passo è il testing completo di tutte le funzionalità.