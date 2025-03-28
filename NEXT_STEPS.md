# Prossimi Passi per lo Sviluppo del Backend

1.  **Risolvere Problemi Autenticazione/Permessi Studente:**
    *   **Priorità Alta:** Investigare e correggere i fallimenti `401 Unauthorized` nei test API che usano l'autenticazione studente. Il problema sembra legato all'interazione tra `StudentJWTAuthentication`, `request.user` (impostato come oggetto `Student`), e i permessi standard di DRF come `IsAuthenticated`.
    *   **Priorità Alta:** Investigare e correggere il fallimento `200 OK` vs `403 Forbidden` nel test `test_student_cannot_list_pending_answers`. Assicurarsi che `IsTeacherUser` blocchi correttamente gli studenti.

2.  **Completare Logica Core:**
    *   Implementare la logica effettiva per `calculate_score` e `check_and_assign_points` in `AttemptViewSet` (`apps/education/views.py`), attualmente placeholder.
    *   Implementare la logica per la correzione automatica delle domande `fill_blank` (se non già inclusa in `calculate_score`).

3.  **Completare e Raffinare Test API:**
    *   Una volta risolti i problemi di autenticazione, verificare e correggere eventuali fallimenti rimanenti nei test API esistenti.
    *   Scrivere test per verificare i permessi in modo più granulare (es. tentativi di accesso non autorizzati con ruoli diversi).
    *   Scrivere test specifici per le azioni API mancanti o meno testate (es. `grade_answer` che completa un tentativo, gestione errori specifici).

4.  **Raffinamento Generale:**
    *   Rivedere il codice per coerenza, manutenibilità e performance.
    *   Aggiungere documentazione (docstring, commenti) dove necessario.
    *   Considerare l'aggiunta di logging più strutturato.
    *   Valutare l'implementazione di `GlobalSetting` se necessario.
    *   Valutare l'implementazione di gruppi di studenti per assegnazioni/disponibilità.

*(Stato al 28 Marzo 2025, ~15:22)*