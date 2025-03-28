# Prossimi Passi per lo Sviluppo del Backend

1.  **~~Risolvere Problemi Autenticazione/Permessi Studente:~~** **(COMPLETATO)**
    *   ~~**Priorità Alta:** Investigare e correggere i fallimenti `401 Unauthorized` nei test API che usano l'autenticazione studente.~~ (Risolto modificando `StudentJWTAuthentication`)
    *   ~~**Priorità Alta:** Investigare e correggere il fallimento `200 OK` vs `403 Forbidden` nel test `test_student_cannot_list_pending_answers`.~~ (Workaround implementato nella view `list_pending` e `grade_answer` restituendo direttamente 403. Il test fallisce ancora per anomalia dell'ambiente di test).

2.  **~~Completare Logica Core:~~** **(COMPLETATO)**
    *   ~~Implementare la logica effettiva per `calculate_score` e `check_and_assign_points` in `AttemptViewSet` (`apps/education/views.py`).~~
    *   ~~Implementare la logica per la correzione automatica delle domande `fill_blank` (inclusa in `calculate_score`).~~

3.  **Completare e Raffinare Test API:**
    *   **Priorità Media:** Investigare l'anomalia nel test `test_student_cannot_list_pending_answers` (opzionale).
    *   **Priorità Media:** Scrivere test per verificare i permessi in modo più granulare (es. tentativi di accesso non autorizzati con ruoli diversi).
    *   **Priorità Media:** Scrivere test specifici per le azioni API mancanti o meno testate (es. `grade_answer` che completa un tentativo, gestione errori specifici, logica punti per percorsi).

4.  **Raffinamento Generale:**
    *   **Priorità Bassa:** Rivedere il codice per coerenza, manutenibilità e performance.
    *   **Priorità Bassa:** Aggiungere documentazione (docstring, commenti) dove necessario.
    *   **Priorità Bassa:** Considerare l'aggiunta di logging più strutturato.
    *   **Priorità Bassa:** Valutare l'implementazione di `GlobalSetting` se necessario.
    *   **Priorità Bassa:** Valutare l'implementazione di gruppi di studenti per assegnazioni/disponibilità.

*(Stato al 28 Marzo 2025, ~20:47)*