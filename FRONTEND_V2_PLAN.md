# Piano di Refactoring Frontend Studenti v2 ATTENZIONE NON MODIFICARE MAI NE I FE V1 (studenti e docenti) o il BANCKEND

Questo documento delinea i passi pianificati per il refactoring del frontend studenti, creando una versione v2 moderna utilizzando Vue.js 3, TypeScript, Vite, Tailwind CSS e DaisyUI.

## Obiettivi

*   Modernizzare l'aspetto grafico e l'esperienza utente.
*   Implementare una nuova interfaccia per lo svolgimento dei quiz tramite finestre modali (piccole).
*   Utilizzare la libreria di componenti DaisyUI basata su Tailwind CSS.
*   Creare una struttura parallela (`frontend-student-v2`) che possa coesistere con la versione attuale (`frontend-student`).
*   Configurare Docker per permettere uno switch facile tra le due versioni senza impattare il backend.

## Piano Dettagliato

1.  **Creazione Nuova Struttura:** [COMPLETATO]
    *   Creata cartella dedicata: `frontend-student-v2`.

2.  **Setup Progetto v2:** [COMPLETATO]
    *   Inizializzato progetto Vue 3 + TypeScript + Vite.
    *   Installate dipendenze: `vue`, `vue-router`, `pinia`, `axios`.
    *   Installate e configurate: `tailwindcss`, `postcss`, `autoprefixer`, `daisyui`.
    *   Configurati file base: `tailwind.config.js`, `postcss.config.js`, `src/style.css`.
    *   Integrati Router e Pinia in `src/main.ts`.
    *   Aggiornato `src/App.vue` per usare `<router-view>`.
    *   *Nota: Configurazione avanzata di ESLint/Prettier/TSconfig da rivedere/affinare se necessario.*

3.  **Configurazione Docker e Deployment Parallelo:** [COMPLETATO]
    *   **Nuovo Dockerfile:** Creato `frontend-student-v2/Dockerfile`.
    *   **Configurazione Nginx:** Creato `frontend-student-v2/nginx.conf`.
    *   **Aggiornamento `docker-compose.yml`:**
        *   Rinominato servizio esistente in `frontend-student-v1` e aggiunto `profiles: ["v1", "default"]`.
        *   Aggiunto nuovo servizio `frontend-student-v2` con `build context: ./frontend-student-v2` e `profiles: ["v2"]`.
        *   Entrambi i servizi usano la porta host `5175` (richiede avvio con profilo specifico: `docker compose --profile v1 up` o `docker compose --profile v2 up`).
            ```yaml
            # Estratto docker-compose.yml aggiornato
            services:
              # ... altri servizi ...

              frontend-student-v1:
                profiles: ["v1", "default"]
                build: ./frontend-student
                # ...
                ports:
                  - "5175:80"

              frontend-student-v2:
                profiles: ["v2"]
                build: ./frontend-student-v2
                # ...
                ports:
                  - "5175:80"
            ```
    *   **Diagramma Architettura Docker:**
        ```mermaid
        graph TD
            subgraph Docker Host
                P5174[Porta 5174] --- C_FT[frontend-teacher]
                P5175[Porta 5175] --- C_FS[frontend-student-v1/v2]
                P8000[Porta 8000] --- C_Web[web (Django)]
            end

            subgraph Docker Network
                C_FS -- API Calls --> C_Web
                C_FT -- API Calls --> C_Web
                C_Web -- DB Queries --> C_DB[db (Postgres)]
            end

            style C_FS fill:#f9f,stroke:#333,stroke-width:2px
        ```

4.  **Sviluppo Frontend v2 (In Corso):**
    *   **Struttura Base:** [COMPLETATO] (Routing e Store Pinia inizializzati e integrati).
    *   **Prossimi Passi UI:**
        *   [COMPLETATO] Definire un layout principale (`src/layouts/MainLayout.vue`) con header/navbar dinamica e footer (usando componenti DaisyUI).
        *   [COMPLETATO] Creare le cartelle per le viste (`src/views`) e i componenti (`src/components`).
        *   [COMPLETATO] Implementare la vista di Login (`src/views/LoginView.vue`) con form DaisyUI e integrazione store Pinia.
        *   [COMPLETATO] Configurare la rotta `/login` nel router.
        *   [COMPLETATO] Creare uno store Pinia base per l'autenticazione (`src/stores/auth.ts`) con gestione token e chiamate API (placeholder).
        *   [COMPLETATO] Implementare la logica di login nella vista, utilizzando lo store.
        *   [COMPLETATO] Creare vista Dashboard (`src/views/DashboardView.vue`) placeholder.
        *   [COMPLETATO] Gestire rotte protette tramite guardie di navigazione nel router.
        *   Successivamente: popolare Dashboard, implementare chiamate API reali, creare altre viste e componenti.
    *   Sviluppare interfaccia quiz con modali DaisyUI (piccole).
    *   Integrare chiamate API backend (Axios).
    *   Aggiornare/scrivere test (unitari con Vitest, E2E con Playwright).

5.  **Testing e Rifinitura:**
    *   Testare approfonditamente v2.
    *   Raccogliere feedback e iterare.

## Stato Attuale e Prossimi Passi

*   **Completati:** Passi 1, 2, 3 (Creazione struttura, Setup progetto base, Configurazione Docker).
*   **In Corso:** Passo 4 (Sviluppo Frontend v2).
*   **Prossimo Passo Immediato:** Popolare la Dashboard, implementare le chiamate API reali nello store `auth.ts` (sostituendo i placeholder con gli endpoint corretti), sviluppare l'interfaccia per i quiz con modali.