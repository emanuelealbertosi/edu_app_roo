# Prossimi Passi per lo Sviluppo

*(Stato al 3 Aprile 2025, ~13:40)*

## Priorità Immediata

1.  **Risolvere Problemi Build Docker Frontend Docente:**
    *   **Obiettivo:** Investigare e risolvere gli errori TypeScript persistenti (specialmente in `QuestionFormView.vue`) e i problemi con le dipendenze di linting/typing (`@eslint/js`, `eslint-config-prettier`) che impediscono il build Docker di `frontend-teacher`. Rimuovere il workaround dallo script `build` in `package.json` una volta risolto.
    *   **Azione:** Analizzare la configurazione di `vue-tsc`, `tsconfig.json`, `eslint.config.ts` e l'ambiente di build Docker. Verificare possibili conflitti o errori di interpretazione del template Vue.

2.  **Eseguire Test Backend (Pytest):**
    *   **Obiettivo:** Assicurarsi che le recenti modifiche (inclusa l'aggiunta del comando `create_initial_superuser`) non abbiano introdotto regressioni nel backend.
    *   **Azione:** Lanciare `pytest` nella root del progetto (nell'ambiente locale o Docker, una volta funzionante).

3.  **Eseguire Test Manuali:**
    *   **Obiettivo:** Verificare manualmente le funzionalità chiave dei frontend docente e studente (in esecuzione locale per ora), come descritto in `test.md`.
    *   **Azione:** Seguire i passaggi definiti in `test.md`.

## Frontend Docente

4.  **Applicare Stile Tailwind (Coerente con Studenti):**
    *   **Priorità Alta:** Applicare classi Tailwind alle restanti viste e componenti del frontend docenti (Dashboard, Studenti, Quiz, Percorsi, Ricompense, Assegna, Valutazioni, Consegne, Progressi) per allineare lo stile a quello degli studenti.

5.  **Completare Gestione Domande/Opzioni:**
    *   **Priorità Alta:** Implementare la gestione dei metadati per le domande (es. risposte corrette per FillBlank, punteggio max per OpenManual).
    *   **Priorità Media:** Migliorare l'interfaccia per l'ordinamento di domande e opzioni (se non già robusta).
    *   **Priorità Bassa:** Raffinare UI/UX dell'editor domande/opzioni.

6.  **Completare Funzionalità Core:**
    *   **Priorità Media:** Implementare l'UI per la selezione degli studenti specifici per le Ricompense.
    *   **Priorità Media:** Implementare la visualizzazione dettagliata dei progressi degli studenti (oltre al sommario).
    *   **Priorità Bassa:** Completare la gestione dei Quiz/Percorsi nei Percorsi (es. rimozione, modifica ordine più intuitiva).

7.  **Test Frontend Docente:**
    *   **Priorità Media:** Scrivere test unitari (Vitest) per i componenti principali.
    *   **Priorità Bassa:** Riprendere e stabilizzare i test E2E (Playwright), specialmente per il flusso domande/opzioni, una volta che le funzionalità sono complete e stabili.

## Frontend Studente

8.  **Test Frontend Studente:**
    *   **Priorità Bassa:** Scrivere test E2E (Playwright) per i flussi principali (svolgimento quiz, shop, acquisti, storico).

## Backend

9.  **Completare Test API:**
    *   **Priorità Bassa:** Scrivere test API per gli endpoint della dashboard studente (`/api/student/dashboard/...`).

10. **Raffinamento Generale:**
    *   **Priorità Bassa:** Valutare l'implementazione di `GlobalSetting` se necessario.
    *   **Priorità Bassa:** Valutare l'implementazione di gruppi di studenti per assegnazioni/disponibilità.