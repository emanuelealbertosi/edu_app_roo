# Prossimi Passi per lo Sviluppo

*(Stato al 3 Aprile 2025, ~18:10)*

## Priorità Immediata

1.  **Risolvere Problemi Build Docker Frontend Docente:**
    *   **Obiettivo:** Investigare e risolvere gli errori TypeScript persistenti (specialmente in `QuestionFormView.vue`) e i problemi con le dipendenze di linting/typing (`@eslint/js`, `eslint-config-prettier`) che impediscono il build Docker di `frontend-teacher`. Rimuovere il workaround dallo script `build` in `package.json` una volta risolto.
    *   **Azione:** Analizzare la configurazione di `vue-tsc`, `tsconfig.json`, `eslint.config.ts` e l'ambiente di build Docker. Verificare possibili conflitti o errori di interpretazione del template Vue.

2.  **Eseguire Test Backend (Pytest):**
    *   **Obiettivo:** Assicurarsi che le recenti modifiche (upload quiz, stato FAILED, riordino domande, descrizione opzionale, correzioni API dashboard studente) non abbiano introdotto regressioni nel backend.
    *   **Azione:** Lanciare `pytest` nella root del progetto (nell'ambiente locale). Correggere eventuali fallimenti.

3.  **Eseguire Test Manuali:**
    *   **Obiettivo:** Verificare manualmente le funzionalità chiave dei frontend docente e studente (in esecuzione locale), come descritto in `test.md`, includendo le nuove funzionalità e correzioni (stile bottoni, auto-salvataggio opzioni, no redirect salvataggio quiz, visualizzazione percorsi studente).
    *   **Azione:** Seguire i passaggi definiti in `test.md`.

4.  **Risolvere Problema Indicatore Caricamento Upload Quiz:**
    *   **Obiettivo:** Investigare perché l'indicatore di caricamento in `QuizUploadForm.vue` rimane visibile dopo il completamento dell'upload, nonostante i log indichino che `isLoading` è `false`.
    *   **Azione:** Analizzare i log della console del browser durante l'upload. Verificare se l'errore nel rendering del `<router-link>` (ora commentato) impedisce l'aggiornamento dell'UI. Ripristinare e correggere il `<router-link>` se necessario.

## Frontend Docente

5.  **Applicare Stile Tailwind (Coerente con Studenti):**
    *   **Priorità Alta:** Applicare classi Tailwind alle restanti viste e componenti del frontend docenti (es. Dashboard, Studenti, form specifici, tabelle) per allineare lo stile a quello degli studenti. (Parzialmente completato con stile bottoni).

6.  **Completare Gestione Domande/Opzioni:**
    *   **Priorità Alta:** Implementare la gestione dei metadati per le domande (es. risposte corrette per FillBlank, punteggio max per OpenManual).
    *   **Priorità Media:** Migliorare l'interfaccia per l'ordinamento di domande e opzioni (se non già robusta).
    *   **Priorità Bassa:** Raffinare UI/UX dell'editor domande/opzioni.

7.  **Completare Funzionalità Core:**
    *   **Priorità Media:** Implementare l'UI per la selezione degli studenti specifici per le Ricompense.
    *   **Priorità Media:** Implementare la visualizzazione dettagliata dei progressi degli studenti (oltre al sommario).
    *   **Priorità Bassa:** Completare la gestione dei Quiz/Percorsi nei Percorsi (es. rimozione, modifica ordine più intuitiva).

8.  **Test Frontend Docente:**
    *   **Priorità Media:** Scrivere test unitari (Vitest) per i componenti principali.
    *   **Priorità Bassa:** Riprendere e stabilizzare i test E2E (Playwright), specialmente per il flusso domande/opzioni, una volta che le funzionalità sono complete e stabili.

## Frontend Studente

9.  **Test Frontend Studente:**
    *   **Priorità Bassa:** Scrivere test E2E (Playwright) per i flussi principali (svolgimento quiz, shop, acquisti, storico, visualizzazione percorsi).

## Backend

10. **Raffinamento Upload Quiz:**
    *   **Priorità Media:** Migliorare il parsing del testo per gestire diversi formati di domande/opzioni e tentare di identificare il tipo di domanda corretto (non solo MC_SINGLE/OPEN_MANUAL).
    *   **Priorità Media:** Gestire l'estrazione e l'impostazione delle risposte corrette (se indicate nel file, es. con asterisco).

11. **Completare Test API:**
    *   **Priorità Bassa:** Scrivere test API per gli endpoint della dashboard studente (`/api/student/dashboard/...`).
    *   **Priorità Media:** Scrivere test API per la nuova azione `upload_quiz`.

12. **Raffinamento Generale:**
    *   **Priorità Bassa:** Valutare l'implementazione di `GlobalSetting` se necessario.
    *   **Priorità Bassa:** Valutare l'implementazione di gruppi di studenti per assegnazioni/disponibilità.