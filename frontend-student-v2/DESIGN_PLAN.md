# Piano di Progettazione: Frontend Studenti V2 (React)

**Data:** 2025-04-19

**Versione:** 1.0

---

**Avviso Importante - Confini del Progetto:**

*   **NON MODIFICARE IL BACKEND:** Questo progetto riguarda **esclusivamente** lo sviluppo del nuovo frontend per gli studenti (`frontend-student-v2/`). Il codice del backend (presumibilmente nelle cartelle `apps/`, `config/`, e i file Python alla root) **non deve essere modificato** in alcun modo. Il nuovo frontend dovrà interagire con le API esistenti fornite dal backend così come sono.
*   **NON MODIFICARE IL FRONTEND DOCENTI:** Allo stesso modo, il frontend dedicato ai docenti (presumibilmente nella cartella `frontend-teacher/`) è **fuori dallo scopo** di questo progetto e non deve essere toccato.

---

## 1. Obiettivo

Creare un'applicazione frontend moderna, interattiva e performante per gli studenti, utilizzando React e sovrascrivendo il contenuto della cartella `frontend-student-v2/`. L'interfaccia utente includerà elementi dinamici come finestre modali, overlay, notifiche, badge e icone animate.

## 2. Stack Tecnologico

*   **Framework:** React 18+
*   **Build Tool:** Vite
*   **Linguaggio:** TypeScript
*   **Styling:** Tailwind CSS (con possibile integrazione di Headless UI / Radix UI)
*   **Package Manager:** npm
*   **Gestione Stato Globale:** Zustand
*   **Gestione Stato API / Caching:** TanStack Query (React Query)
*   **Routing:** React Router (v6+)
*   **Animazioni:** Framer Motion
*   **Cartella di Lavoro:** `frontend-student-v2/`

## 3. Struttura delle Cartelle Proposta

```
frontend-student-v2/
├── public/             # Asset statici
├── src/
│   ├── assets/         # Immagini, font, icone SVG
│   ├── components/     # Componenti UI riutilizzabili
│   │   ├── common/     # Bottoni, Input, Badge, Icone Animate, etc.
│   │   ├── layout/     # Header, Footer, Sidebar, Layout Principale
│   │   ├── features/   # Componenti specifici per funzionalità (es. Quiz, Dashboard)
│   │   └── ui/         # Componenti UI più complessi (Modali, Overlay, Notifiche)
│   ├── config/         # Configurazioni (es. API endpoint, temi)
│   ├── hooks/          # Custom Hooks React
│   ├── lib/            # Funzioni utility, helpers
│   ├── pages/          # Componenti "pagina" o "vista" (corrispondenti alle route)
│   ├── router/         # Configurazione del routing
│   ├── services/       # Logica per le chiamate API
│   ├── stores/         # Gestione dello stato globale (es. Zustand)
│   ├── styles/         # File CSS globali, configurazione Tailwind
│   ├── types/          # Definizioni TypeScript
│   ├── App.tsx         # Componente Root dell'applicazione
│   └── main.tsx        # Entry point dell'applicazione
├── .eslintrc.cjs       # Configurazione ESLint
├── .gitignore
├── index.html          # Template HTML principale (usato da Vite)
├── package.json
├── postcss.config.js   # Configurazione PostCSS (per Tailwind)
├── tailwind.config.js  # Configurazione Tailwind CSS
├── tsconfig.json       # Configurazione TypeScript
├── tsconfig.node.json
└── vite.config.ts      # Configurazione Vite
```

## 4. Gestione dello Stato

*   **Globale:** Zustand (leggero, performante).
*   **Locale:** Hook standard di React (`useState`, `useReducer`).
*   **API/Server State:** TanStack Query (React Query) per caching, re-fetching, ecc.

## 5. Routing

*   React Router (v6+) per la navigazione client-side.

## 6. Componenti Chiave da Sviluppare

*   Layout Principale (Header, Sidebar?, Footer, Area Contenuti)
*   Componenti UI Base (Bottoni, Input, Card, Badge animati)
*   Icone Animate (SVG con animazioni)
*   Sistema di Notifiche (Toast)
*   Finestre Modali/Overlay (Componente riutilizzabile)
*   Componenti Specifici (Dashboard, Corsi, Attività, Profilo, etc.)

## 7. Interattività e Animazioni

*   Framer Motion per animazioni fluide (transizioni, apparizioni, feedback).

## 8. Integrazione API

*   Funzioni dedicate in `src/services/`.
*   Utilizzo di TanStack Query per gestire le chiamate e lo stato dei dati server.

## 9. Fasi di Sviluppo (Alto Livello)

1.  **Setup Iniziale:** Creazione progetto React+Vite+TS, installazione dipendenze, configurazione base.
2.  **Layout e Routing:** Implementazione layout principale e route base.
3.  **Componenti UI Core:** Sviluppo componenti comuni riutilizzabili.
4.  **Gestione Stato e API:** Setup Zustand e TanStack Query.
5.  **Sviluppo Pagine/Funzionalità:** Creazione pagine e logiche specifiche.
6.  **Interattività e Animazioni:** Integrazione Framer Motion.
7.  **Testing e Refinement:** Test, bug fixing, ottimizzazioni.

## 10. Diagramma Struttura (Mermaid)

```mermaid
graph TD
    A[main.tsx] --> B(App.tsx);
    B --> C{React Router};
    C --> D[Layout Principale];
    D --> E[Header];
    D --> F[Contenuto Pagina];
    D --> G[Footer];
    C --> P1[Pagina Login];
    C --> P2[Pagina Dashboard];
    C --> P3[Pagina Corsi];
    C --> P4[Pagina Profilo];

    F --> CompFeat[Componenti Features];
    CompFeat --> API(Servizi API / TanStack Query);
    CompFeat --> Store(Zustand Store);
    CompFeat --> CompUI[Componenti UI];
    CompUI --> CompBase[Bottoni, Badge, etc.];
    CompUI --> CompAdv[Modali, Notifiche];
    CompUI --> Anim(Framer Motion);

    API --> Backend(API Backend Django);
    Store --> Backend;

    subgraph Styling
        direction LR
        Style1[Tailwind CSS]
        Style2[Headless UI / Radix UI (Opzionale)]
    end

    subgraph Build & Dev
        direction LR
        Build1[Vite]
        Build2[TypeScript]
    end

    B --> Build & Dev;
    CompUI --> Styling;

---

## 11. Stato Attuale e Note (al 2025-04-19 ~13:00)

**Progressi:**

*   **Fase 1 (Setup Iniziale):** Completata. Progetto React+Vite+TS creato, dipendenze base installate.
    *   *Nota:* Inizialmente installato Tailwind v4, ma causava problemi di configurazione/stile. Effettuato downgrade a Tailwind v3 (`tailwindcss@^3.x.x`) che ha risolto il problema. La configurazione attuale (`tailwind.config.js`, `postcss.config.js`, `src/index.css`) è per v3.
*   **Fase 2 (Layout e Routing Base):** Completata. Struttura layout con Header/Footer implementata. Routing base con `react-router-dom` configurato (HomePage, LoginPage, DashboardPage).
*   **Fase 3 (Componenti UI Core):** Parzialmente completata. Create cartelle per componenti. Creati componenti base `Button`, `Header`, `Footer`, `Modal`. Header è dinamico in base allo stato auth.
*   **Fase 4 (Gestione Stato e API):** Completata. Configurato Zustand (`authStore.ts` con persistenza) e TanStack Query (`QueryClientProvider`, `queryClient`). Configurato `apiClient` (Axios) con interceptor per token.
*   **Fase 5 (Sviluppo Pagine/Funzionalità):** Iniziata.
    *   Login (`LoginPage.tsx`) implementato e funzionante (collegato a `authStore` e API backend).
    *   Dashboard (`DashboardPage.tsx`) implementata con recupero dati (Quiz, Percorsi, Wallet) tramite TanStack Query.
    *   Implementata logica per aprire un **Quiz in una Modale** dalla Dashboard.
    *   Creato componente base per il tentativo di quiz (`QuizAttempt.tsx`) con recupero dati preliminare.

**Problemi Attuali / Prossimi Passi Immediati:**

*   **Recupero Dettagli Quiz:** La modale del quiz si apre, ma il caricamento dei dettagli completi (domande/opzioni) fallisce.
    *   La chiamata `POST /api/education/quizzes/{quizId}/attempts/start-attempt/` ha successo ma restituisce solo l'ID del tentativo, non le domande.
    *   La successiva chiamata `GET /api/education/attempts/{attemptId}/details/` (implementata nel frontend) fallisce perché la risposta del backend, pur avendo successo (status 200), **non contiene il campo `questions`** atteso dal frontend (come verificato dai log).
    *   **Azione Corrente:** È necessario ispezionare la risposta JSON esatta della chiamata `GET /api/education/attempts/{attemptId}/details/` nella scheda Network del browser per capire la struttura dati reale restituita dal backend e correggere i tipi (`src/types/quiz.ts`) e la logica di accesso ai dati in `QuizAttempt.tsx`.

**Obiettivi Successivi (dopo risoluzione problema API):**

*   Completare l'implementazione di `QuizAttempt.tsx` (visualizzazione domande/opzioni reali, gestione stato risposte, navigazione domande, invio risposte).
*   Implementare altre pagine/funzionalità (es. visualizzazione percorsi, profilo studente).
*   Aggiungere animazioni con Framer Motion.
*   Testing e refinement.