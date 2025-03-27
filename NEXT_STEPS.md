# Prossimi Passi per lo Sviluppo del Backend

1.  **Implementare Logica Svolgimento Quiz:**
    *   Completare l'azione `submit_answer` in `AttemptViewSet` (`apps/education/views.py`) per validare il formato di `selected_answers` in base al `question.question_type`.
    *   Implementare l'azione `details` in `AttemptViewSet` per recuperare i dettagli di un tentativo, incluse le domande e le risposte già date.
    *   Considerare come gestire il recupero sequenziale delle domande se necessario (potrebbe richiedere un'azione aggiuntiva o modifiche a `details`).

2.  **Implementare Calcolo Punteggio e Assegnazione Punti:**
    *   Raffinare la logica nel metodo `calculate_score` in `AttemptViewSet` per gestire correttamente tutti i tipi di domande (inclusi `FILL_BLANK` e punteggi da domande `OPEN_ANSWER_MANUAL` corrette dal docente). Considerare se i punti per domanda sono definiti nei metadati.
    *   Raffinare la logica nel metodo `check_and_assign_points` in `AttemptViewSet` per assicurare la correttezza e robustezza (gestione errori, race condition).
    *   Implementare logica simile per l'assegnazione punti al completamento dei `Pathway` (potrebbe richiedere un segnale o un controllo dopo il completamento dell'ultimo quiz del percorso).

3.  **Scrivere Test API Aggiuntivi:**
    *   Scrivere test per le azioni API mancanti (retrieve, update, delete) nelle ViewSet esistenti (`UserViewSet`, `QuizTemplateViewSet`, `QuizViewSet`, `PathwayViewSet`, `RewardTemplateViewSet`, `RewardViewSet`).
    *   Scrivere test specifici per le azioni custom (`create_from_template`, `assign_student`, `add_quiz`, `purchase`, `mark_delivered`, `start_attempt`, `submit_answer`, `complete_attempt`, `details`, `list_pending`, `grade_answer`).
    *   Scrivere test per verificare i permessi in modo più granulare (es. tentativi di accesso non autorizzati).
    *   Scrivere test per l'autenticazione studente (`StudentLoginView`, `StudentJWTAuthentication`).
    *   Scrivere test per le ViewSet specifiche dello studente (`StudentShopViewSet`, `StudentWalletViewSet`, `StudentPurchasesViewSet`, `StudentDashboardViewSet`).

4.  **Raffinamento Generale:**
    *   Rivedere il codice per coerenza, manutenibilità e performance.
    *   Aggiungere documentazione (docstring, commenti) dove necessario.
    *   Considerare l'aggiunta di logging più strutturato.
    *   Valutare l'implementazione di `GlobalSetting` se necessario.
    *   Valutare l'implementazione di gruppi di studenti per assegnazioni/disponibilità.