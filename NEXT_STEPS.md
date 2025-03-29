# Prossimi Passi per lo Sviluppo del Backend

1.  **~~Risolvere Problemi Autenticazione/Permessi Studente:~~** **(COMPLETATO)**
    *   ~~**Priorità Alta:** Investigare e correggere i fallimenti `401 Unauthorized` nei test API che usano l'autenticazione studente.~~ (Risolto modificando `StudentJWTAuthentication`)
    *   ~~**Priorità Alta:** Investigare e correggere il fallimento `200 OK` vs `403 Forbidden` nel test `test_student_cannot_list_pending_answers`.~~ (Risolto correggendo l'autenticazione usata nel test - JWT invece di `force_authenticate`).

2.  **~~Completare Logica Core:~~** **(COMPLETATO)**
    *   ~~Implementare la logica effettiva per `calculate_score` e `check_and_assign_points` in `AttemptViewSet` (`apps/education/views.py`).~~ (Spostata sul modello `QuizAttempt` e corretta).
    *   ~~Implementare la logica per la correzione automatica delle domande `fill_blank` (inclusa in `calculate_score`).~~ (Inclusa in `calculate_final_score` sul modello).
    *   ~~Implementare la logica per l'aggiornamento del progresso e l'assegnazione punti dei Percorsi.~~ (Aggiunta al modello `QuizAttempt`).

3.  **Completare e Raffinare Test API:**
    *   **~~Priorità Media:~~** ~~Scrivere test per verificare i permessi in modo più granulare (es. tentativi di accesso non autorizzati con ruoli diversi, accesso admin).~~ **(COMPLETATO)**
    *   **~~Priorità Media:~~** ~~Scrivere test specifici per le azioni API mancanti o meno testate (es. logica punti per percorsi, gestione errori specifici, edge case).~~ **(PARZIALMENTE COMPLETATO - Logica punti percorsi base)**
    *   **Priorità Media:** Scrivere test specifici per altri casi limite o azioni API meno testate (es. gestione errori specifici, altri edge case logica punti percorsi, grading manuale).
    *   **Priorità Bassa:** Verificare e aggiungere test per le altre app (`users`, `rewards`).

4.  **Raffinamento Generale:**
    *   **Priorità Bassa:** Rivedere il codice per coerenza, manutenibilità e performance.
    *   **Priorità Bassa:** Aggiungere documentazione (docstring, commenti) dove necessario.
    *   **Priorità Bassa:** Considerare l'aggiunta di logging più strutturato.
    *   **Priorità Bassa:** Valutare l'implementazione di `GlobalSetting` se necessario.
    *   **Priorità Bassa:** Valutare l'implementazione di gruppi di studenti per assegnazioni/disponibilità.

*(Stato al 29 Marzo 2025, ~09:53)*