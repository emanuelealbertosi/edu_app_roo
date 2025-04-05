# Prossimi Passi per lo Sviluppo

*(Stato al 5 Aprile 2025, ~07:10)*

## Priorità Immediata

1.  **Eseguire Test Backend (Pytest):**
    *   **Obiettivo:** Assicurarsi che il refactoring dei template, l'aggiunta dell'upload template e le correzioni ai serializer di assegnazione non abbiano introdotto regressioni. Aggiornare/creare test per coprire le nuove funzionalità (upload template, assegnazione da template).
    *   **Azione:** Lanciare `pytest` nella root del progetto (nell'ambiente locale). Correggere eventuali fallimenti.

2.  **Eseguire Test Manuali (Nuovo Flusso Docente):**
    *   **Obiettivo:** Verificare manualmente il nuovo flusso di lavoro del docente: creazione/gestione template quiz (incluso upload da file) e percorsi, gestione domande/opzioni template (con salvataggio automatico), assegnazione da template, visualizzazione istanze assegnate. Aggiornare `test.md` per includere i passaggi di upload.
    *   **Azione:** Seguire i passaggi aggiornati in `test.md`.

3.  **Risolvere Problema Indicatore Caricamento Upload Quiz (Se Persistente):**
    *   **Obiettivo:** Verificare se il problema con l'indicatore di caricamento in `QuizUploadForm.vue` (nel frontend docente, per i quiz concreti) è ancora presente e risolverlo.
    *   **Azione:** Testare l'upload, analizzare console e correggere se necessario.

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

## Dockerizzazione (Priorità Abbassata)

13. **Risolvere Problemi Build Docker Frontend Docente:**
    *   **Obiettivo:** Investigare e risolvere gli errori TypeScript e di dipendenze che impediscono il build Docker di `frontend-teacher`. Rimuovere il workaround dallo script `build`.
    *   **Azione:** Analizzare configurazioni e ambiente Docker (può essere posticipato).