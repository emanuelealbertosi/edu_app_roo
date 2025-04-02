# Riepilogo Stato Avanzamento Progetto (2 Aprile 2025, ~19:03)

## 1. Progettazione

*   Completato un piano di progettazione dettagliato (`design_document.md`) che copre obiettivi, stack tecnologico, architettura, schema DB (PostgreSQL), design API, sicurezza, TDD, tipologie di domande, calcolo punti e sistema di ricompense.

## 2. Setup Progetto Django

*   Creato ambiente virtuale (`.venv`).
*   Installato Django e le dipendenze necessarie (`psycopg2-binary`, `python-dotenv`, `dj-database-url`, `djangorestframework`, `djangorestframework-simplejwt`, `drf-nested-routers`, `factory-boy`, `Faker`, `django-json-widget`, `django-cors-headers`).
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
*   Create e applicate con successo tutte le migrazioni (inclusi campi studente, modelli assegnazione) per le app `users`, `rewards`, `education` al database PostgreSQL.
*   Aggiunta property `is_authenticated` al modello `Student` per tentare di risolvere problemi con i permessi DRF.
*   Aggiunto campo `first_correct_completion` al modello `PathwayProgress` e creata/applicata relativa migrazione.

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
*   **Corretti permessi e logica ViewSet:** Aggiornati i permessi (`IsQuizOwnerOrAdmin`, `IsPathwayOwnerOrAdmin`, `IsRewardOwnerOrAdmin`, `IsRewardTemplateOwnerOrAdmin`) e i metodi `get_queryset` in `QuizViewSet`, `PathwayViewSet`, `RewardViewSet`, `RewardTemplateViewSet` per gestire correttamente l'accesso degli utenti e restituire `403 Forbidden` o `404 Not Found` appropriati.
*   **Corretta logica di completamento/grading:** Risolto `ValueError` in `complete_attempt` rimuovendo il salvataggio del campo inesistente `points_earned`. Risolto `AttributeError` in `grade_answer` chiamando i metodi corretti (`calculate_final_score`, `assign_completion_points`) sul modello `QuizAttempt`. Corretto calcolo punteggio per domande manuali.
*   **Implementata logica punti percorso:** Aggiunto metodo `update_pathway_progress` al modello `QuizAttempt` per gestire l'aggiornamento del progresso e l'assegnazione dei punti al completamento del percorso.
*   **Implementata creazione utenti API:** Aggiunto `UserCreateSerializer` e modificato `UserViewSet` per gestire correttamente la creazione di utenti (Admin/Docente) con hashing della password.
*   **Implementata gestione ProtectedError:** Sovrascritto metodo `destroy` in `RewardViewSet` per restituire 409 Conflict se si tenta di eliminare una ricompensa acquistata.

## 6. Interfaccia Admin

*   Configurati i file `admin.py` per tutte le app (`users`, `rewards`, `education`) per registrare i modelli (inclusi quelli di assegnazione) e personalizzare la visualizzazione (inclusi `inlines` per gestione nidificata).
*   Installato e configurato `django-json-widget` per migliorare l'editing dei campi `metadata` nell'admin.

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
*   **Tutti i test (295) ora passano.**

## 8. Controllo Versione

*   Inizializzato repository Git locale.
*   Creati file `.gitignore` e `README.md`.
*   Creato file `requirements.txt`.
*   Effettuati commit intermedi durante lo sviluppo.
*   Creato repository remoto su GitHub (`emanuelealbertosi/edu_app_roo`).
*   Effettuato push dei commit sul repository remoto.

## 9. Stato Attuale

*   Il server di sviluppo Django è in esecuzione (`python manage.py runserver`).
*   L'interfaccia di amministrazione (`/admin/`) è accessibile e migliorata con `django-json-widget`.
*   Gli endpoint API per Admin/Docente e Studente sono funzionanti (secondo i test).
*   La logica per il calcolo punteggio/punti per Quiz e Percorsi è implementata.
*   Tutti i test backend (modelli e API) passano.
*   Il codice è versionato su GitHub.
*   Il database contiene dati di test generati dal comando `seed_test_data`.
*   Il frontend studenti (`frontend-student`) è funzionante con le funzionalità principali implementate. **Corretti numerosi bug relativi a:** visualizzazione quiz disponibili/completati, avvio tentativi, gestione tipi domanda, invio risposte, visualizzazione risultati (stato, numerazione), logout, shop (URL, aggiornamento dopo acquisto), storico acquisti (URL, visualizzazione stato con icone).
*   Il frontend docenti (`frontend-teacher`) è stato inizializzato ed è in esecuzione (`npm run dev`). Le funzionalità base (visualizzazione studenti/quiz/percorsi/ricompense, CRUD base quiz/percorsi/ricompense, assegnazione, grading, sommario progressi) sono implementate. La gestione delle domande e opzioni è parzialmente implementata. **Corretti bug relativi a:** creazione ricompense (permessi, validazione), logout. **Implementata vista "Consegne"** per gestire ricompense acquistate.

## 10. Raffinamento Codice

*   Rimosse istruzioni `print()` di debug dai file `views.py` e `models.py` delle app `education`, `users`, `rewards`.
*   Chiariti commenti sulla logica di calcolo del punteggio e assegnazione punti in `apps/education/models.py`.
*   Aggiunti/Migliorati docstring e `help_text` nei modelli delle app `education`, `users`, `rewards`.
*   Aggiunto logging di base per errori/eccezioni nei metodi dei modelli e delle view.

## 11. Frontend Studenti (Vue.js)

*   Creato progetto Vue.js nella directory `frontend-student`.
*   Implementata struttura base e funzionalità core (login, dashboard, svolgimento quiz, risultati, shop, profilo, acquisti, navigazione).
*   Implementati test unitari (Vitest) e E2E (Playwright) per autenticazione.
*   **Test E2E Svolgimento Quiz:** Tentativi iniziali falliti. Test sospesi in favore di test manuali.
*   **Corretta logica visualizzazione stato quiz:** Il pulsante "Inizia Quiz" e le date di disponibilità vengono nascosti correttamente per i quiz completati.

## 12. Dati di Test

*   Creato comando di management `seed_test_data` utilizzando le factory per popolare il database.
*   Eseguito con successo il comando per avere dati di esempio disponibili.

## 13. Frontend Docenti (Vue.js)

*   Creata struttura base del progetto (`frontend-teacher`).
*   Implementata logica di base per l'autenticazione dei docenti.
*   Implementate viste base per Studenti, Quiz, Percorsi, Ricompense, Assegnazione, Grading, Progressi.
*   Implementato CRUD base per Quiz, Percorsi, Ricompense.
*   Implementata gestione base Domande (visualizzazione, creazione, eliminazione).
*   Implementata gestione base Opzioni Risposta (visualizzazione, creazione, modifica, eliminazione).
*   **Risolto Bug Opzioni MC-Single:** Corretta la logica in `AnswerOptionsEditor.vue` che impediva il salvataggio corretto dello stato `is_correct`. Funzionalità verificata manualmente.
*   **Configurati Test E2E (Playwright):**
    *   Implementati test E2E per login, visualizzazione studenti/quiz, CRUD base quiz/percorsi/ricompense.
    *   **Debug Test E2E Domande/Opzioni:** Affrontati e risolti numerosi problemi. Test sospesi in favore di test manuali.
    *   **Aggiunto campo "Punti al Completamento"** al form dei quiz.

## Prossimi Passi Previsti (vedi NEXT_STEPS.md)

*   Esecuzione test backend (pytest).
*   Esecuzione test manuali (come da `test.md`).
*   Completamento e raffinamento frontend docente (es. UI selezione studenti specifici per ricompense).
*   Verifica assegnazione punti quiz (assicurarsi che `points_on_completion` > 0 nei metadati).
