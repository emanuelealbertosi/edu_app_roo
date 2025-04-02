# Prossimi Passi per lo Sviluppo

*(Stato al 2 Aprile 2025, ~12:43)*

## Priorità Immediata

1.  **Eseguire Test Backend (Pytest):**
    *   **Obiettivo:** Assicurarsi che le recenti modifiche (specialmente quelle legate al debug E2E) non abbiano introdotto regressioni nel backend.
    *   **Azione:** Lanciare `pytest` nella root del progetto.

2.  **Eseguire Test Manuali:**
    *   **Obiettivo:** Verificare manualmente le funzionalità chiave dei frontend docente e studente, inclusi i bug fix recenti, come descritto in `test.md`.
    *   **Azione:** Seguire i passaggi definiti in `test.md`.

## Frontend Docente

3.  **Completare Gestione Domande/Opzioni:**
    *   **Priorità Alta:** Implementare la gestione dei metadati per le domande (es. risposte corrette per FillBlank, punteggio max per OpenManual).
    *   **Priorità Media:** Migliorare l'interfaccia per l'ordinamento di domande e opzioni (se non già robusta).
    *   **Priorità Bassa:** Raffinare UI/UX dell'editor domande/opzioni.

4.  **Completare Funzionalità Core:**
    *   **Priorità Media:** Implementare la gestione degli studenti specifici per le Ricompense (se necessario).
    *   **Priorità Media:** Implementare la visualizzazione dettagliata dei progressi degli studenti (oltre al sommario).
    *   **Priorità Bassa:** Completare la gestione dei Quiz/Percorsi nei Percorsi (es. rimozione, modifica ordine più intuitiva).

5.  **Test Frontend Docente:**
    *   **Priorità Media:** Scrivere test unitari (Vitest) per i componenti principali.
    *   **Priorità Bassa:** Riprendere e stabilizzare i test E2E (Playwright), specialmente per il flusso domande/opzioni, una volta che le funzionalità sono complete e stabili.

## Frontend Studente

6.  **Test Frontend Studente:**
    *   **Priorità Bassa:** Scrivere test E2E (Playwright) per il flusso di svolgimento quiz e visualizzazione risultati/percorsi/shop/profilo.

## Backend

7.  **Completare Test API:**
    *   **Priorità Media:** Scrivere test API per i nuovi endpoint della dashboard studente (`/api/student/dashboard/...`).

8.  **Raffinamento Generale:**
    *   **Priorità Bassa:** Valutare l'implementazione di `GlobalSetting` se necessario.
    *   **Priorità Bassa:** Valutare l'implementazione di gruppi di studenti per assegnazioni/disponibilità.