# Riepilogo Stato Avanzamento Progetto (13 Aprile 2025, ~15:35)

## 1. Progettazione

*   Completato un piano di progettazione dettagliato (`design_document.md`) che copre obiettivi, stack tecnologico, architettura, schema DB (PostgreSQL), design API, sicurezza, TDD, tipologie di domande, calcolo punti e sistema di ricompense.

## 2. Setup Progetto Django

*   Creato ambiente virtuale (`.venv`).
*   Installato Django e le dipendenze necessarie (`psycopg2-binary`, `python-dotenv`, `dj-database-url`, `djangorestframework`, `djangorestframework-simplejwt`, `drf-nested-routers`, `factory-boy`, `Faker`, `django-json-widget`, `django-cors-headers`, `PyPDF2`, `python-docx`, `markdown`, `Pillow`).
*   Aggiunto `pytest` e `pytest-django` alle dipendenze e creato `pytest.ini`. Aggiornato `requirements.txt`.
*   Inizializzato progetto Django (`config`, `manage.py`).
*   Creata directory `apps` e aggiunto `apps/__init__.py`.
*   Create app Django: `users`, `education`, `rewards` all'interno di `apps/`.
*   Configurato `settings.py` per riconoscere la directory `apps` (`sys.path`).
*   Registrate le app (`apps.users.apps.UsersConfig`, etc.) e corretto il loro attributo `name` nei rispettivi file `apps.py`.

## 3. Configurazione Database

*   Configurato `settings.py` per usare PostgreSQL leggendo la `DATABASE_URL` da un file `.env` tramite `dj-database-url`.
*   Creato file `.env` con le credenziali corrette per il database locale (`postgres://postgres:admin@localhost:5432/edu_app_db`).

## 4. Modelli e Migrazioni

*   Definiti tutti i modelli del database come da piano nei rispettivi file `models.py`.
*   Risolto problema iniziale con le migrazioni resettando le cartelle `migrations` e il database PostgreSQL.
*   Create e applicate con successo tutte le migrazioni iniziali (inclusi campi studente, modelli assegnazione) per le app `users`, `rewards`, `education` al database PostgreSQL.
*   Aggiunta property `is_authenticated` al modello `Student` per tentare di risolvere problemi con i permessi DRF.
*   Aggiunto campo `first_correct_completion` al modello `PathwayProgress` e creata/applicata relativa migrazione.
*   Aggiunto stato `FAILED` al modello `QuizAttempt` e applicata relativa migrazione.
*   Reso il campo `description` del modello `Quiz` opzionale (`null=True`) e applicata relativa migrazione.
*   **Refactoring Template:**
    *   Aggiunti modelli `PathwayTemplate` e `PathwayQuizTemplate` per gestire template di percorsi.
    *   Aggiunto campo `source_template` al modello `Pathway`.
    *   Modificato modello `QuizTemplate` per aggiungere campo `teacher` (opzionale) e rendere `admin` opzionale, con vincoli per assicurare almeno un creatore.
    *   Create e applicate migrazioni `0007` e `0008` per l'app `education` per riflettere queste modifiche.
*   **Correzione Assegnazione Percorsi:** Modificato modello `PathwayAssignment` per permettere `null=True` sul campo `pathway` e applicata migrazione `0009`.
*   **Correzione Assegnazione Quiz:** Aggiunto campo `due_date` al modello `QuizAssignment` e applicata migrazione `0010`.
*   **Correzione Migrazioni Inconsistenti:** Risolto problema `InconsistentMigrationHistory` per `education.0012` usando `--fake`.
*   **Modifica Immagine Badge:** Modificato campo `image_url` in `image` (`ImageField`) nel modello `Badge` per permettere upload. Creata e applicata migrazione `rewards.0004`.
*   **Migliorato Help Text Badge:** Aggiornato `help_text` per `trigger_condition` nel modello `Badge` con esempi chiari.

## 5. Autenticazione e API Base

*   Creato superutente Django (`admin`).
*   Configurato DRF e Simple JWT in `settings.py`.
*   Aggiunti URL per l'autenticazione JWT Admin/Docente in `config/urls.py`.
*   Implementati Serializer, Permessi, ViewSet e URL di base per le app `users`, `rewards`, `education`.
*   Inclusi gli URL delle app negli URL principali (`config/urls.py` sotto `/api/`).
*   Implementata autenticazione custom per Studenti (codice+PIN) con backend, view di login JWT custom, classe di autenticazione DRF custom (`StudentJWTAuthentication`), e permesso `IsStudent`.
*   Implementata logica di base per l'assegnazione di Quiz e Percorsi nelle ViewSet (`QuizViewSet`, `PathwayViewSet`, `StudentDashboardViewSet`).
*   Implementata logica di svolgimento quiz in `AttemptViewSet`:
    *   Validazione input `submit_answer` per tutti i tipi di domanda (inclusi `fill_blank`).
    *   Azione `details` per recuperare dettagli tentativo (domande e risposte date).
    *   Azione `current_question` per recupero sequenziale domanda successiva.
    *   Azione `complete_attempt` con gestione stato `PENDING_GRADING` per domande manuali.
*   **Risolti problemi di autenticazione studente:** Modificata `StudentJWTAuthentication` per gestire correttamente i token studente, risolvendo la maggior parte dei fallimenti `401 Unauthorized` nei test API.
*   **Implementata logica core:** Completata l'implementazione di `calculate_score` (incluso `FILL_BLANK`) e `check_and_assign_points` (inclusa creazione `PointTransaction`) in `AttemptViewSet`.
*   Aggiunta view e URL di test (`StudentProtectedTestView`) per debug autenticazione studente.
*   **Workaround per permessi:** Aggiunto controllo manuale con restituzione `403 Forbidden` nelle azioni `list_pending` e `grade_answer` di `TeacherGradingViewSet` a causa di un comportamento anomalo dei permessi standard in quel contesto.
*   **Corretti permessi e logica ViewSet:** Aggiornati i permessi (`IsQuizOwnerOrAdmin`, `IsPathwayOwnerOrAdmin`, `IsRewardOwnerOrAdmin`, `IsRewardTemplateOwnerOrAdmin`) e i metodi `get_queryset` in `QuizViewSet`, `PathwayViewSet`, `RewardViewSet`, `RewardTemplateViewSet` per gestire correttamente l'accesso degli utenti e restituire `403 Forbidden` o `404 Not Found` appropriati. **Corretti permessi per `QuizViewSet` list action**.
*   **Corretta logica di completamento/grading:** Risolto `ValueError` in `complete_attempt` rimuovendo il salvataggio del campo inesistente `points_earned`. Risolto `AttributeError` in `grade_answer` chiamando i metodi corretti (`calculate_final_score`, `assign_completion_points`) sul modello `QuizAttempt`. Corretto calcolo punteggio per domande manuali. **Implementato stato `FAILED`** per tentativi non superati e aggiornata logica in `AttemptViewSet` e `TeacherGradingViewSet`. **Aggiunto metodo `get_max_possible_score`** al modello `Quiz`.
*   **Implementata logica punti percorso:** Aggiunto metodo `update_pathway_progress` al modello `QuizAttempt` per gestire l'aggiornamento del progresso e l'assegnazione dei punti al completamento del percorso.
*   **Implementata creazione utenti API:** Aggiunto `UserCreateSerializer` e modificato `UserViewSet` per gestire correttamente la creazione di utenti (Admin/Docente) con hashing della password.
*   **Implementata gestione ProtectedError:** Sovrascritto metodo `destroy` in `RewardViewSet` per restituire 409 Conflict se si tenta di eliminare una ricompensa acquistata.
*   **Implementata creazione quiz da file:**
    *   Aggiunte librerie `PyPDF2`, `python-docx`, `markdown`.
    *   Creato `QuizUploadSerializer` per gestire upload e parsing (PDF, DOCX, MD).
    *   Aggiunta azione `upload_quiz` a `QuizViewSet`.
*   **Corretto riordinamento domande:** Implementata logica in `QuestionViewSet.perform_destroy` per aggiornare l'ordine delle domande successive dopo un'eliminazione.
*   **Resa descrizione quiz opzionale:** Modificato modello `Quiz` (`null=True`) e `QuizSerializer` (`extra_kwargs`).
*   **Corretto errore 500 dashboard studente (percorsi):** Risolto `AttributeError` in `StudentAssignedPathwaysView` correggendo il `related_name` in `prefetch_related` da `progress` a `progresses`.
*   **Refactoring Template API:**
    *   Aggiunti Serializer (`PathwayTemplateSerializer`, `PathwayQuizTemplateSerializer`, `QuizAssignmentSerializer`, `PathwayAssignmentSerializer`) per gestire i template e l'assegnazione da template.
    *   Aggiunti ViewSet (`PathwayTemplateViewSet`, `PathwayQuizTemplateViewSet`, `TeacherQuizTemplateViewSet`, `TeacherQuestionTemplateViewSet`, `TeacherAnswerOptionTemplateViewSet`) per il CRUD dei template e delle loro domande/opzioni da parte del docente.
    *   Modificata logica di assegnazione in `QuizViewSet` e `PathwayViewSet` per creare istanze concrete (`Quiz`, `Pathway`) a partire dai template quando viene fornito `quiz_template_id` o `pathway_template_id`.
    *   Aggiornati URL (`apps/education/urls.py`) per includere i nuovi endpoint per i template gestiti dai docenti.
    *   Aggiornato `PathwaySerializer` per includere `source_template`.
*   **Implementata creazione template quiz da file:**
    *   Creato `QuizTemplateUploadSerializer` per gestire upload e parsing (PDF, DOCX, MD) per i template.
    *   Aggiunta azione `upload_template` a `TeacherQuizTemplateViewSet`.
*   **Corretta validazione assegnazione da template:**
    *   Risolto errore `400 Bad Request` per l'assegnazione di percorsi da template (modificato modello `PathwayAssignment`, usato serializer dedicato `PathwayAssignActionSerializer`, corretta view `assign_student_pathway`).
    *   Risolto errore `400 Bad Request` per l'assegnazione di quiz da template (usato serializer dedicato `QuizAssignActionSerializer`, corretta view `assign_student`).
    *   Risolti `IndentationError` e `NameError` in `serializers.py` emersi durante le correzioni.
*   **Corretto errore API caricamento Wallet Studente:** Risolto `NameError` in `config/urls.py` ripristinando l'URL e l'import per `StudentWalletInfoView`.
*   **Corretto errore API caricamento Badge Studente:** Risolto `ImproperlyConfigured` in `BadgeSerializer` correggendo il campo `image_url` in `image`.
*   **Corretta logica soglia superamento quiz:** Modificato `QuizAttempt.assign_completion_points` per leggere correttamente la soglia (`completion_threshold`) dai metadati del `Quiz` (invece di un campo inesistente) e confrontarla con il punteggio percentuale calcolato.

## 6. Interfaccia Admin

*   Configurati i file `admin.py` per tutte le app (`users`, `rewards`, `education`) per registrare i modelli (inclusi quelli di assegnazione e template) e personalizzare la visualizzazione (inclusi `inlines` per gestione nidificata).
*   Installato e configurato `django-json-widget` per migliorare l'editing dei campi `metadata` nell'admin.
*   **Aggiunta gestione Badge:** Registrati modelli `Badge` e `EarnedBadge`.
*   **Abilitato upload immagini Badge:** Modificato `BadgeAdmin` per usare `ImageField` (con anteprima).
*   **Migliorato help text condizioni Badge:** Aggiornato `help_text` per `trigger_condition` in `BadgeAdmin`.

## 7. Test Modelli e API

*   Create factory (`factory-boy`) per tutti i modelli in `factories.py` per ciascuna app. Aggiunte factory mancanti (`QuizAssignmentFactory`, `PathwayAssignmentFactory`) e risolte importazioni circolari.
*   Scritti e verificati test di base per i modelli delle app `users`, `rewards`, `education`.
*   Scritti test API per CRUD e azioni custom per le principali ViewSet.
*   **Corretti tutti i fallimenti nei test API dell'app `education`:** Risolti problemi di permessi, logica, autenticazione e asserzioni errate.
*   **Aggiunti nuovi test API (`test_permissions.py`):**
    *   Verificato accesso Admin a risorse di altri docenti.
    *   Verificato che i Docenti non possano accedere a risorse di altri docenti.
    *   Verificato che gli Studenti non possano accedere agli endpoint dei docenti.
    *   Verificata la logica di assegnazione punti per i Percorsi (primo completamento, fallimento quiz, secondo completamento, grading manuale).
*   **Aggiunti test API mancanti per `education`:** Coperti tutti i tipi di domanda in `submit_answer` e casi limite per grading manuale.
*   **Corretti tutti i fallimenti nei test API dell'app `users`:** Abilitato e corretto test creazione utente API.
*   **Corretti tutti i fallimenti nei test API dell'app `rewards`:** Risolti problemi con factory (Wallet, Reward, RewardTemplate, RewardPurchase), permessi (IsRewardOwnerOrAdmin, IsRewardTemplateOwnerOrAdmin), autenticazione studente e gestione ProtectedError.
*   **Tutti i test (295) ora passano.** (Nota: Da riverificare dopo refactoring template, aggiunta upload e modifiche Badge)

## 8. Controllo Versione

*   Inizializzato repository Git locale.
*   Creati file `.gitignore` e `README.md`.
*   Creato file `requirements.txt`.
*   Effettuati commit intermedi durante lo sviluppo.
*   Creato repository remoto su GitHub (`emanuelealbertosi/edu_app_roo`).
*   Effettuato push dei commit sul repository remoto.

## 9. Stato Attuale

*   Il server di sviluppo Django è in esecuzione (`python manage.py runserver`).
*   L'interfaccia di amministrazione (`/admin/`) è accessibile e migliorata con `django-json-widget`. Permette ora la gestione dei Badge con upload di immagini.
*   Gli endpoint API per Admin/Docente e Studente sono funzionanti, inclusi quelli per wallet e badge.
*   La logica per il calcolo punteggio/punti per Quiz e Percorsi è implementata.
*   Il codice è versionato su GitHub.
*   Il database contiene dati di test generati dal comando `seed_test_data`.
*   Il frontend studenti (`frontend-student`) è funzionante con le funzionalità principali implementate e stile base Tailwind CSS applicato.
*   Il frontend docenti (`frontend-teacher`) è stato **refattorizzato** per adottare il flusso basato sui template:
    *   Le sezioni "Quiz Templates" e "Template Percorsi" gestiscono ora i template.
    *   La sezione "Assegna" permette di assegnare contenuti solo a partire dai template.
    *   Sono state aggiunte le sezioni "Quiz Assegnati" e "Percorsi Assegnati" per visualizzare le istanze concrete.
    *   È stato implementato l'editor per domande e opzioni all'interno dei template quiz.
    *   Il client API, il router e la navigazione sono stati aggiornati.
    *   **Aggiunta funzionalità upload template quiz da file.**
    *   **Corretta gestione domande/opzioni template (visualizzazione e salvataggio automatico).**
    *   **Corretti errori di sintassi HTML.**

## 10. Raffinamento Codice

*   Rimosse istruzioni `print()` di debug dai file `views.py` e `models.py` delle app `education`, `users`, `rewards`.
*   Chiariti commenti sulla logica di calcolo del punteggio e assegnazione punti in `apps/education/models.py`.
*   Aggiunti/Migliorati docstring e `help_text` nei modelli delle app `education`, `users`, `rewards`.
*   Aggiunto logging di base per errori/eccezioni nei metodi dei modelli e delle view (incluso logging DEBUG per stato quiz e validazione serializer assegnazione).
*   **Corretto `settings.py`** per leggere `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` da variabili d'ambiente. Aggiunte configurazioni `MEDIA_URL` e `MEDIA_ROOT`.
*   **Aggiunto `whitenoise`** alla configurazione per servire file statici in produzione.
*   **Aggiornato `config/urls.py`** per servire file media in sviluppo.

## 11. Frontend Studenti (Vue.js)

*   Creato progetto Vue.js nella directory `frontend-student`.
*   Implementata struttura base e funzionalità core (login, dashboard, svolgimento quiz, risultati, shop, profilo, acquisti, navigazione).
*   Implementati test unitari (Vitest) e E2E (Playwright) per autenticazione.
*   **Test E2E Svolgimento Quiz:** Tentativi iniziali falliti. Test sospesi in favore di test manuali.
*   **Corretta logica visualizzazione stato quiz:** Il pulsante "Inizia Quiz" e le date di disponibilità vengono nascosti correttamente per i quiz completati (superati). I quiz falliti rimangono disponibili.
*   **Configurato Tailwind CSS v3:** Installato e configurato Tailwind, risolti problemi iniziali di applicazione stili.
*   **Applicato stile base:** Applicate classi Tailwind alle viste principali e ai componenti per uno stile "Kahoot-like".
*   **Corretto bug logout:** Risolto problema di reindirizzamento dopo il logout refattorizzando lo store di autenticazione.
*   **Aggiunta descrizione ricompensa allo storico acquisti.**
*   **Risolto errore 500 visualizzazione percorsi.**
*   **Risolto problema caricamento pagina storico acquisti** (richiesto riavvio server Vite).
*   **Corretti errori di rendering:** Risolti `InvalidCharacterError` e `TypeError: Cannot read properties of null (reading 'parentNode')` legati a commenti HTML mal posizionati e gestione transizioni/HMR.
*   **Corretta logica notifica badge:** Spostata la logica di notifica da `QuizResultView` a `QuizAttemptView` per usare l'array `newly_earned_badges` dalla risposta API `completeAttempt`.
*   **Corretto errore icona badge rotta:** Identificato e risolto problema con `ImageField` e serializer. Creato file SVG placeholder.
*   **Migliorata UX Svolgimento Quiz:**
   *   Sostituita animazione iniziale "Pronti? Via!" con contatore "3, 2, 1, Via!" su sfondo azzurro (`QuizAttemptView.vue`).
   *   Sostituito sfondo immagine casuale con sfondi a gradiente colorati che ciclano ad ogni domanda (`QuizAttemptView.vue`).
   *   Aggiunta transizione di dissolvenza all'apparizione delle domande (`QuizAttemptView.vue`).
   *   Corretto tipo `AttemptDetails` in `api/quiz.ts` per includere `newly_earned_badges`, risolvendo errori TypeScript.

## 12. Dati di Test

*   Creato comando di management `seed_test_data` utilizzando le factory per popolare il database.
*   **Corretto comando `seed_test_data`:** Abilitata pulizia database, corretto uso di `name` per badge, rimosso `due_date` da `PathwayAssignmentFactory`. Corretto uso di `update_or_create` per aggiornare `image_url` (ora `image`). Rimosso `image_url` dai defaults (da caricare manualmente).
*   Eseguito con successo il comando per avere dati di esempio disponibili.

## 13. Frontend Docenti (Vue.js) - Post Refactoring

*   **Refactoring Flusso Template:** Completato. Le viste principali ora gestiscono template, l'assegnazione parte da template, le istanze sono visualizzate separatamente.
*   **Editor Domande/Opzioni Template:** Implementato (`TemplateQuestionEditor`, `TemplateAnswerOptionsEditor`, viste e API integrate).
*   **Funzionalità Precedenti:** Mantenute (upload quiz, gestione ricompense, consegne, grading, progressi, stile Tailwind, interceptor 401, etc.).
*   **Correzioni UI/UX:** Rimossa textarea metadati da form domande, corretto salvataggio automatico opzioni, corretti errori HTML.
*   **Applicati stili bottoni standard:** Utilizzate classi `.btn-*` nelle viste e componenti principali per coerenza visiva.

## 14. Dockerizzazione Produzione

*   Creati `Dockerfile`, `docker-compose.prod.yml` e `entrypoint.prod.sh` per l'ambiente di produzione.
*   Configurate e pushate le immagini Docker per backend, frontend-studente, frontend-docente su Docker Hub (`albertosiemanuele/...`).
*   Creato script interattivo `deploy_on_ubuntu.sh` per facilitare il deployment su server Ubuntu.
*   **Iterazioni di Debug:**
    *   Risolto problema generazione `SECRET_KEY` nello script di deployment.
    *   Risolto errore `DisallowedHost` configurando `ALLOWED_HOSTS` e `CORS_ALLOWED_ORIGINS` tramite lo script interattivo.
    *   Affrontato problema persistente con le variabili d'ambiente (`DATABASE_URL`, `SECRET_KEY`, etc.) non lette correttamente dallo script `entrypoint.prod.sh` all'interno del container `backend` durante l'esecuzione dei comandi `manage.py`.
    *   Provate diverse configurazioni di `docker-compose.prod.yml` (`env_file`, `environment`, ibrido) e dello script `deploy_on_ubuntu.sh` (esportazione variabili).
    *   Modificato `entrypoint.prod.sh` per caricare esplicitamente `.env.prod` con `source`.
*   **Stato Attuale Problema Variabili d'Ambiente:** Nonostante le modifiche, i log del container `backend` mostrano ancora che `DATABASE_URL` è `None` e `SECRET_KEY` è vuota quando vengono eseguiti i comandi `manage.py` (migrate, collectstatic, create_initial_superuser), causando il fallback a SQLite e fallimenti successivi (es. `InconsistentMigrationHistory` o `no such table`). Gunicorn fallisce l'avvio a causa di questi errori. **Il deployment Docker in produzione NON è ancora completamente funzionante a causa di questo problema.**
*   **Risoluzione Problema Reverse Proxy (12/04/2025):**
    *   Modificato `nginx.conf` (proxy esterno) aggiungendo `^~` a `location /docenti/` per forzare la priorità.
    *   Modificato `frontend-teacher/nginx.conf` (Nginx interno) rimuovendo il blocco `location ~ ^/docenti/assets/` ridondante.
    *   Identificato e risolto problema di **caching del browser** (Edge) che manteneva un vecchio redirect 301. La pulizia della cache o l'uso della modalità InPrivate ha risolto il problema.
    *   **Stato Attuale:** Il reverse proxy funziona correttamente per `/studenti/`, `/docenti/`, `/admin/`, `/api/`.
    *   **Corretta configurazione Docker Compose locale:** Modificato `docker-compose.local-prod-test.yml` per usare `build:` invece di `image:` e per leggere le variabili da `.env.localprod` di default, permettendo test locali con codice aggiornato.

## 15. Miglioramenti UX (Piano `UX_IMPROVEMENT_PLAN.md`)

*   **Avvio Server Locali:** Avviati con successo backend Django, frontend studente e frontend docente.
*   **Stili Bottoni (Docente):** Applicati stili standard (`.btn-*`) ai bottoni nelle viste e componenti principali del frontend docente.
*   **Gamification (Badge):**
    *   Implementata logica backend per assegnare il badge "Primo Quiz Completato" (`first-quiz-completed`) nel modello `QuizAttempt`.
    *   Aggiornato lo store notifiche studente per tracciare badge notificati.
    *   Implementata logica frontend in `QuizAttemptView.vue` per recuperare badge guadagnati e mostrare notifica per i badge appena ottenuti. Rimossa logica duplicata da `QuizResultView.vue`.
    *   Aggiunta creazione badge "Primo Quiz Completato" nello script `seed_test_data`.
    *   **Corretto errore icona badge rotta:** Identificato e risolto problema con `ImageField` e serializer. Creato file SVG placeholder. Corretto errore API caricamento badge.
    *   **Migliorata interfaccia svolgimento quiz:** Vedi sezione 11.
   
   ## Prossimi Passi Previsti (vedi NEXT_STEPS.md)
