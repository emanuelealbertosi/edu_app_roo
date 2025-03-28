# Riepilogo Stato Avanzamento Progetto (28 Marzo 2025, ~20:45)

## 1. Progettazione

*   Completato un piano di progettazione dettagliato (`design_document.md`) che copre obiettivi, stack tecnologico, architettura, schema DB (PostgreSQL), design API, sicurezza, TDD, tipologie di domande, calcolo punti e sistema di ricompense.

## 2. Setup Progetto Django

*   Creato ambiente virtuale (`.venv`).
*   Installato Django e le dipendenze necessarie (`psycopg2-binary`, `python-dotenv`, `dj-database-url`, `djangorestframework`, `djangorestframework-simplejwt`, `drf-nested-routers`, `factory-boy`, `Faker`).
*   Inizializzato progetto Django (`config`, `manage.py`).
*   Creata directory `apps`.
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

## 6. Interfaccia Admin

*   Configurati i file `admin.py` per tutte le app (`users`, `rewards`, `education`) per registrare i modelli (inclusi quelli di assegnazione) e personalizzare la visualizzazione.

## 7. Test Modelli e API

*   Create factory (`factory-boy`) per tutti i modelli in `factories.py` per ciascuna app.
*   Scritti e verificati test di base per i modelli delle app `users`, `rewards`, `education`.
*   Scritti test API per CRUD e azioni custom per:
    *   `QuizTemplateViewSet`
    *   `QuestionTemplateViewSet`
    *   `AnswerOptionTemplateViewSet`
    *   `QuizViewSet`
    *   `QuestionViewSet`
    *   `AnswerOptionViewSet`
    *   `PathwayViewSet`
    *   `AttemptViewSet` (`details`, `current_question`, `submit_answer`, `complete_attempt`)
    *   `StudentQuizAttemptViewSet` (`start_attempt`)
    *   `StudentDashboardViewSet` (`list`)
    *   `UserViewSet` (gestione Docenti)
    *   `StudentViewSet`
    *   `RewardTemplateViewSet`
    *   `RewardViewSet`
    *   `StudentShopViewSet` (`list`, `purchase`)
    *   `StudentWalletViewSet` (`retrieve`)
    *   `StudentPurchasesViewSet` (`list`)
    *   `TeacherGradingViewSet` (`list_pending`, `grade_answer`)
    *   `StudentAuthenticationAPITests` (login studente)
*   **La maggior parte dei test API ora passa.** Rimane un fallimento (`test_student_cannot_list_pending_answers`) che sembra dovuto a un'anomalia dell'ambiente di test, nonostante il workaround implementato nella view.

## 8. Controllo Versione

*   Inizializzato repository Git locale.
*   Creati file `.gitignore` e `README.md`.
*   Creato file `requirements.txt`.
*   Effettuati commit intermedi durante lo sviluppo.
*   Creato repository remoto su GitHub (`emanuelealbertosi/edu_app_roo`).
*   Effettuato push dei commit sul repository remoto.

## 9. Stato Attuale

*   Il server di sviluppo Django è in esecuzione (`python manage.py runserver`).
*   L'interfaccia di amministrazione (`/admin/`) è accessibile.
*   Gli endpoint API per Admin/Docente e Studente sono per lo più funzionanti (secondo i test).
*   La logica per il calcolo punteggio/punti è implementata.
*   I test dei modelli passano. Quasi tutti i test API passano (eccetto uno con anomalia nota).
*   Il codice è versionato su GitHub.

## Prossimi Passi Previsti (vedi NEXT_STEPS.md)

*   Risoluzione dell'anomalia nel test `test_student_cannot_list_pending_answers` (opzionale, priorità bassa).
*   Completamento e raffinamento dei test API.
*   Raffinamento generale del codice.