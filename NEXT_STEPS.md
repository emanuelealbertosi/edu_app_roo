# Prossimi Passi per lo Sviluppo

*(Stato al 6 Aprile 2025, ~10:50)*

## Priorità Immediata

1.  **Risolvere Problemi Deployment Docker Produzione:**
    *   **Obiettivo:** Investigare e risolvere il problema per cui le variabili d'ambiente (`DATABASE_URL`, `SECRET_KEY`, etc.) definite in `.env.prod` non vengono lette correttamente dallo script `entrypoint.prod.sh` all'interno del container `backend` durante l'esecuzione dei comandi `manage.py` (migrate, collectstatic, create_initial_superuser). Questo causa il fallback a SQLite e fallimenti successivi.
    *   **Stato Attuale:** Diversi tentativi (uso di `env_file`, `environment`, ibrido, `export` nello script di deployment, `source` nell'entrypoint) non hanno risolto il problema. Il container `backend` non si avvia correttamente.
    *   **Azione:**
        *   Verificare attentamente la versione di Docker e Docker Compose sul server Ubuntu.
        *   Esaminare possibili conflitti di permessi o configurazioni specifiche dell'ambiente server.
        *   Considerare approcci alternativi per passare le variabili (es. montare `.env.prod` come volume e leggerlo esplicitamente in `settings.py` o nell'entrypoint).
        *   Semplificare temporaneamente `entrypoint.prod.sh` per isolare il problema (es. rimuovere temporaneamente `migrate` o `create_initial_superuser`).

2.  **Eseguire Test Backend (Pytest):** (Posticipato fino alla risoluzione del deployment)
    *   **Obiettivo:** Assicurarsi che il refactoring dei template, l'aggiunta dell'upload template e le correzioni ai serializer di assegnazione non abbiano introdotto regressioni. Aggiornare/creare test per coprire le nuove funzionalità (upload template, assegnazione da template).
    *   **Azione:** Lanciare `pytest` nella root del progetto (nell'ambiente locale). Correggere eventuali fallimenti.

3.  **Eseguire Test Manuali (Nuovo Flusso Docente):** (Posticipato fino alla risoluzione del deployment)
    *   **Obiettivo:** Verificare manualmente il nuovo flusso di lavoro del docente: creazione/gestione template quiz (incluso upload da file) e percorsi, gestione domande/opzioni template (con salvataggio automatico), assegnazione da template, visualizzazione istanze assegnate. Aggiornare `test.md` per includere i passaggi di upload.
    *   **Azione:** Seguire i passaggi aggiornati in `test.md`.

## Frontend Docente

4.  **Raffinamento Editor Domande/Opzioni Template:**
    *   **Priorità Alta:** Implementare la gestione completa dei metadati per le domande template (es. risposte corrette per FillBlank, punteggio max per OpenManual) in `QuestionTemplateFormView.vue`. (Nota: L'input manuale JSON è stato rimosso, serve un'interfaccia dedicata per tipo).
    *   **Priorità Media:** Migliorare l'interfaccia per l'ordinamento di domande e opzioni template.
    *   **Priorità Bassa:** Raffinare UI/UX generale dell'editor (`TemplateQuestionEditor`, `TemplateAnswerOptionsEditor`).

5.  **Raffinamento Viste Istanze Assegnate:**
    *   **Priorità Media:** Migliorare le viste `AssignedQuizzesView.vue` e `AssignedPathwaysView.vue` (es. aggiungere filtri, paginazione, link ai dettagli studente/tentativi).
    *   **Priorità Media:** Implementare la vista dettagli (read-only?) per le istanze quiz/percorsi assegnati.

6.  **Completare Funzionalità Core (Restanti):**
    *   **Priorità Media:** Implementare l'UI per la selezione degli studenti specifici per le Ricompense.
    *   **Priorità Media:** Implementare la visualizzazione dettagliata dei progressi degli studenti (oltre al sommario).

7.  **Applicare Stile Tailwind (Coerente):**
    *   **Priorità Media:** Completare l'applicazione dello stile Tailwind alle viste e componenti restanti per coerenza.

8.  **Test Frontend Docente:**
    *   **Priorità Media:** Scrivere test unitari (Vitest) per i nuovi componenti e viste (template, upload template, istanze assegnate).
    *   **Priorità Bassa:** Riprendere e stabilizzare i test E2E (Playwright) per coprire il nuovo flusso template.

## Backend

9.  **Test API Refactoring Template e Upload:**
    *   **Priorità Alta:** Scrivere test API specifici per i nuovi endpoint (`TeacherQuizTemplateViewSet` e relativi endpoint nidificati, inclusa azione `upload_template`), creazione istanze da template nelle azioni di assegnazione (`assign_student`, `assign_student_pathway`).

10. **Raffinamento Upload Quiz/Template (Se Necessario):**
    *   **Priorità Bassa:** Migliorare ulteriormente il parsing del testo se emergono problemi con formati diversi.

11. **Raffinamento Generale:**
    *   **Priorità Bassa:** Valutare l'implementazione di `GlobalSetting` o gruppi di studenti se necessario.

## Frontend Studente

12. **Test Frontend Studente:**
    *   **Priorità Bassa:** Scrivere test E2E (Playwright) per i flussi principali (incluso storico acquisti).

## Dockerizzazione (Priorità Abbassata - Bloccata da Problemi Prod)

13. **Risolvere Problemi Build Docker Frontend Docente:**
    *   **Obiettivo:** Investigare e risolvere gli errori TypeScript e di dipendenze che impediscono il build Docker di `frontend-teacher`. Rimuovere il workaround dallo script `build`.
    *   **Azione:** Analizzare configurazioni e ambiente Docker (può essere posticipato).