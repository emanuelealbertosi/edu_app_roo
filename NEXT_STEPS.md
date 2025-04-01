# Prossimi Passi per lo Sviluppo del Backend

1.  **~~Risolvere Problemi Autenticazione/Permessi Studente:~~** **(COMPLETATO)**
    *   ~~**Priorità Alta:** Investigare e correggere i fallimenti `401 Unauthorized` nei test API che usano l'autenticazione studente.~~ (Risolto modificando `StudentJWTAuthentication`)
    *   ~~**Priorità Alta:** Investigare e correggere il fallimento `200 OK` vs `403 Forbidden` nel test `test_student_cannot_list_pending_answers`.~~ (Risolto correggendo l'autenticazione usata nel test - JWT invece di `force_authenticate`).

2.  **~~Completare Logica Core:~~** **(COMPLETATO)**
    *   ~~Implementare la logica effettiva per `calculate_score` e `check_and_assign_points` in `AttemptViewSet` (`apps/education/views.py`).~~ (Spostata sul modello `QuizAttempt` e corretta).
    *   ~~Implementare la logica per la correzione automatica delle domande `fill_blank` (inclusa in `calculate_score`).~~ (Inclusa in `calculate_final_score` sul modello).
    *   ~~Implementare la logica per l'aggiornamento del progresso e l'assegnazione punti dei Percorsi.~~ (Aggiunta al modello `QuizAttempt`).

3.  **Completare e Raffinare Test API:** **(PARZIALMENTE COMPLETATO)**
    *   **~~Priorità Media:~~** ~~Scrivere test per verificare i permessi in modo più granulare (es. tentativi di accesso non autorizzati con ruoli diversi, accesso admin).~~ **(COMPLETATO)**
    *   **~~Priorità Media:~~** ~~Scrivere test specifici per le azioni API mancanti o meno testate (es. logica punti per percorsi, gestione errori specifici, edge case).~~ **(COMPLETATO - Logica punti percorsi, grading manuale, tipi domande)**
    *   **~~Priorità Media:~~** ~~Scrivere test specifici per altri casi limite o azioni API meno testate (es. gestione errori specifici, altri edge case logica punti percorsi, grading manuale).~~ **(COMPLETATO)**
    *   **~~Priorità Bassa:~~** ~~Verificare e aggiungere test per le altre app (`users`, `rewards`).~~ **(COMPLETATO - Test API base e correzioni)**
    *   **Priorità Media:** Scrivere test API per i nuovi endpoint della dashboard studente (`/api/student/dashboard/...`).

4.  **Raffinamento Generale:**
    *   **Priorità Bassa:** ~~Rivedere il codice per coerenza, manutenibilità e performance.~~ **(COMPLETATO - Rimosse stampe debug, chiariti commenti)**
    *   **Priorità Bassa:** ~~Aggiungere documentazione (docstring, commenti) dove necessario.~~ **(COMPLETATO - Aggiunti/migliorati docstring e help_text)**
    *   **Priorità Bassa:** ~~Considerare l'aggiunta di logging più strutturato.~~ **(COMPLETATO - Aggiunto logging base per errori)**
    *   **Priorità Bassa:** Valutare l'implementazione di `GlobalSetting` se necessario.
    *   **Priorità Bassa:** Valutare l'implementazione di gruppi di studenti per assegnazioni/disponibilità.

# Prossimi Passi per lo Sviluppo del Frontend Studenti

1.  **~~Attivare Backend e Testare Integrazione:~~** **(COMPLETATO)**
    *   **~~Priorità Alta:~~** ~~Avviare il server Django (`python manage.py runserver`).~~ **(COMPLETATO)**
    *   **~~Priorità Alta:~~** ~~Testare il login studente utilizzando le API reali (non il mock).~~ **(COMPLETATO)**
    *   **~~Priorità Alta:~~** ~~Verificare che il token JWT venga salvato e che l'utente venga reindirizzato alla dashboard.~~ **(COMPLETATO)**
    *   **~~Priorità Alta:~~** ~~Verificare che la guardia di navigazione protegga correttamente la dashboard.~~ **(COMPLETATO)**

2.  **Completare Funzionalità Core:**
    *   **~~Priorità Media:~~** ~~Completare l'implementazione della dashboard studente (`DashboardView.vue`) recuperando e visualizzando i dati reali dal backend (es. nome utente, corsi/quiz/percorsi assegnati).~~ **(COMPLETATO - Recupero dati base funzionante)**
    *   **Priorità Media:** Implementare la vista per svolgere un quiz, con supporto per tutti i tipi di domande.
    *   **Priorità Media:** Implementare la vista per visualizzare i risultati di quiz e percorsi completati.

3.  **Funzionalità Aggiuntive:**
    *   **Priorità Bassa:** Implementare la vista per il negozio ricompense e l'acquisto.
    *   **Priorità Bassa:** Implementare la vista del profilo studente con informazioni e statistiche.
    *   **Priorità Bassa:** Aggiungere barra di navigazione e menu laterale per l'accesso alle funzionalità.

4.  **Miglioramenti UI/UX:**
    *   **Priorità Bassa:** Migliorare l'aspetto visivo con un design coerente e responsivo.
    *   **Priorità Bassa:** Implementare animazioni e transizioni per migliorare l'esperienza utente.
    *   **Priorità Bassa:** Aggiungere temi chiari/scuri e opzioni di personalizzazione.

5.  **Robustezza e Testing:**
    *   **Priorità Media:** Implementare una gestione errori più robusta e feedback utente per le chiamate API.
    *   **Priorità Bassa:** Scrivere test unitari con Vitest per i componenti principali (Login, Dashboard, ecc.).
    *   **Priorità Bassa:** Scrivere test e2e con Playwright per i flussi utente critici (login, logout, accesso dashboard).

*(Stato al 1 Aprile 2025, ~20:35)*