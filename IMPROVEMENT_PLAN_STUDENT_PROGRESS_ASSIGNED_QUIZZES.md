# Piano di Riprogettazione: Pagine Progressi Studenti e Quiz Assegnati

**Versione Piano:** 1.3 (Aggiornato il 21 Maggio 2025, 10:52)

**Obiettivo Primario:** Migliorare l'esperienza utente nelle sezioni "Progressi Studenti" e "Quiz Assegnati" del `frontend-teacher` implementando pagine di dettaglio ricche di informazioni e funzionali, e assicurando la coerenza grafica secondo il `GRAPHIC_UPGRADE_PLAN.md`.

---

### 0. Note sui Problemi Riscontrati e Priorità Immediata

*   **Problemi con `apply_diff`:** Durante l'implementazione, si sono verificati frequenti problemi con lo strumento `apply_diff`, specialmente su file che subivano modifiche multiple. Questo ha portato a stati intermedi incoerenti dei file e alla necessità di riletture frequenti e diff correttivi.
    *   **Azione Raccomandata:** Per modifiche future su file complessi o che hanno già subito tentativi di modifica, considerare l'uso di `insert_content` per blocchi di codice nuovi e `apply_diff` solo per porzioni di codice molto piccole e ben identificate, dopo aver verificato l'esatto contenuto con `read_file`.
*   **Priorità Immediata:**
    *   **Risolvere Errori TypeScript Residui:** Assicurarsi che non ci siano errori TypeScript in `StudentProgressDetailView.vue` e `AssignedQuizDetailView.vue`. L'ultimo errore noto in `AssignedQuizDetailView.vue` riguardava `getAssigneeKey` non trovato; un tentativo di correzione è stato applicato ma necessita verifica.

---

### 1. Aggiornamenti Comuni e Prerequisiti

*   **Aggiornamento `BaseButton.vue` in `frontend-teacher`:**
    *   ✅ **[FATTO]** Verificato: i file `BaseButton.vue` in `frontend-teacher` e `frontend-student` sono risultati identici. Nessun allineamento necessario al momento.
*   **Verifica Componenti Comuni:**
    *   `BaseModal.vue`: ✅ **[FATTO]** Verificato e aggiornato il colore del titolo per coerenza con la palette.
    *   `BaseTabs.vue`: ⚠️ **[ACCANTONATO]** Non trovato in `frontend-teacher/src/components/common/`. L'utente ha indicato che non è cruciale per ora.
    *   `BaseCard.vue`: ✅ **[FATTO]** Creato nuovo componente in `frontend-teacher/src/components/common/BaseCard.vue` per strutturare le sezioni.

---

### 2. Riprogettazione Pagina "Progressi Studenti" (`StudentProgressView.vue`)

*   **Tabella Principale (`StudentProgressView.vue`):**
    *   Miglioramenti UI (Opzionali): Filtri e ordinamento non implementati in questa fase.
    *   Funzionalità Link "Visualizza": ✅ **[FATTO]** Attivato il pulsante "Visualizza" per navigare alla vista di dettaglio.
*   **Router (`frontend-teacher/src/router/index.ts`):**
    *   ✅ **[FATTO]** Aggiunta nuova rotta `student-progress-detail` con path `/student-progress/:studentId`.
*   **Nuova Vista: `StudentProgressDetailView.vue`:** ✅ **[FATTO]** Creata.
    *   Layout Generale: ✅ Struttura base con header, pulsante "Indietro", gestione `isLoading`/`error`.
    *   Sezione 1: Riepilogo Generale Studente: ✅ Implementata con `BaseCard` e dati placeholder. Interfaccia `StudentProgressDetail` definita.
    *   Sezione 2: Andamento e Statistiche: ✅ Implementata con `BaseCard`, statistiche testuali placeholder e grafico ApexCharts (line chart per `score_trend`) con dati placeholder. Libreria ApexCharts indicata come installata. Interfacce `ScoreTrendPoint`, `OverallStats`, `StudentAnalyticsData` definite.
    *   Sezione 3: Dettaglio Quiz Svolti: ✅ Implementata con `BaseCard`, tabella placeholder e funzioni helper per lo stato. Interfaccia `StudentQuizAttempt` definita.
    *   Sezione 4: Dettaglio Percorsi Svolti: ❌ **[RIMOSSO]** Questa sezione è stata rimossa come da richiesta.
    *   Sezione 5: Storico Ricompense e Punti: ✅ Implementata con `BaseCard`, struttura per bilancio punti e tabella ricompense acquistate (placeholder). Interfacce `StudentWallet`, `RewardPurchaseItem` e tipo `RewardPurchaseStatus` definiti. Funzioni helper per stato ricompense aggiunte.
    *   Logica di Fetch: ✅ Funzioni `fetchStudentDetails`, `fetchStudentAnalytics`, `fetchQuizAttempts`, `fetchStudentRewardPurchases`, `fetchStudentWallet` definite. ✅ **[AGGIORNATO]** Le funzioni di fetch ora utilizzano chiamate API reali (con endpoint ipotetici) invece di dati placeholder.
    *   `onMounted`: ✅ Logica aggiornata per chiamare tutte le funzioni di fetch. Corretti errori TypeScript relativi ad `async/await`.

---

### 3. Riprogettazione Pagina "Quiz Assegnati" (`AssignedQuizzesView.vue`)

*   **Tabella Principale (`AssignedQuizzesView.vue`):**
    *   Miglioramenti UI (Opzionali): Filtri e ordinamento non implementati in questa fase.
    *   Funzionalità Link "Visualizza": ✅ **[FATTO]** Attivato il pulsante "Visualizza" per navigare alla vista di dettaglio.
*   **Router (`frontend-teacher/src/router/index.ts`):**
    *   ✅ **[FATTO]** Aggiunta nuova rotta `assigned-quiz-details` con path `/assigned-quizzes/:id`.
*   **Nuova Vista: `AssignedQuizDetailView.vue`:** ✅ **[FATTO]** Creata.
    *   Layout Generale: ✅ Struttura base con header, pulsante "Indietro", gestione `isLoading`/`error`.
    *   Sezione 1: Riepilogo Quiz: ✅ Implementata con `BaseCard` e dati placeholder. Interfaccia `AssignedQuizUIDetails` definita.
    *   Sezione 2: Statistiche di Completamento: ✅ Implementata con `BaseCard`, statistiche testuali placeholder e grafico ApexCharts (bar chart per `score_distribution`) con dati placeholder. Interfacce `ScoreDistributionPoint`, `QuizCompletionStatsData` definite.
    *   Sezione 3: Studenti Assegnatari e Stati: ✅ Implementata con `BaseCard`, tabella placeholder, filtro per stato (placeholder) e funzioni helper per lo stato. Interfaccia `QuizAssignee` e tipo `AssigneeQuizStatus` definiti. Corretto errore TypeScript per `:key` nel `v-for` (con la funzione `getAssigneeKey`).
    *   Logica di Fetch: ✅ Funzioni `fetchAssignedQuizDetails`, `fetchQuizCompletionStats`, `fetchQuizAssignees` definite. ✅ **[AGGIORNATO]** Le funzioni di fetch ora utilizzano chiamate API reali (con endpoint ipotetici) invece di dati placeholder.
    *   `onMounted`: ✅ Logica aggiornata per chiamare le funzioni di fetch.

---

### 4. Diagrammi di Flusso Utente (Mermaid)
    *   ✅ **[CONFERMATO]** Il diagramma esistente rimane valido.

---

### 5. Considerazioni API
    *   ✅ **[CONFERMATO]** Le strutture dati API per `StudentProgressDetailView.vue` (sez. Statistiche) sono state discusse e approvate (tralasciando `time_analytics` per ora). Per le altre sezioni e per `AssignedQuizDetailView.vue`, si presume che le API forniranno dati conformi alle interfacce definite e al `design_document.md`.

---

### 6. Lavoro Rimanente Specifico per Questo Task (Rivisitare Pagine e Implementare Link "Visualizza")

*   **Priorità Alta:**
    *   **Verifica Finale Errori TypeScript:**
        *   ✅ **[FATTO]** Rileggere `frontend-teacher/src/views/AssignedQuizDetailView.vue` per confermare che l'ultimo tentativo di correzione (aggiunta di `getAssigneeKey` e altre funzioni helper) abbia risolto tutti gli errori TypeScript e che il file sia sintatticamente corretto.
        *   ✅ **[FATTO]** Rileggere `frontend-teacher/src/views/StudentProgressDetailView.vue` per una verifica finale di eventuali errori residui.
*   **Completamento Struttura `AssignedQuizDetailView.vue`:**
    *   ✅ **[FATTO]** Assicurarsi che la Sezione 3 (Studenti Assegnatari) sia completamente strutturata nel template e nello script, con tutte le funzioni helper definite e utilizzate.
*   **Test di Navigazione (Manuale/Dev):**
    *   Verificare che cliccando sui pulsanti "Visualizza" in `StudentProgressView.vue` e `AssignedQuizzesView.vue` si navighi correttamente alle rispettive viste di dettaglio (`StudentProgressDetailView.vue` e `AssignedQuizDetailView.vue`) e che i parametri ID siano passati e visualizzati.
    *   Verificare che i pulsanti "Indietro" nelle viste di dettaglio funzionino.

---

### 7. Passi Successivi (Oltre lo Scope del Task Attuale di Strutturazione)

*   **Implementazione Chiamate API Reali:**
    *   ✅ **[PARZIALMENTE FATTO]** Sostituire i dati placeholder e le funzioni di fetch simulate con chiamate API effettive agli endpoint del backend in:
        *   `StudentProgressDetailView.vue` (per dettagli studente, analytics, quiz attempts, wallet, reward purchases). Endpoint API ipotetici implementati.
        *   `AssignedQuizDetailView.vue` (per dettagli quiz, statistiche completamento, studenti assegnatari). Endpoint API ipotetici implementati.
*   **Implementazione Funzionalità Pulsanti di Azione:**
    *   In `StudentProgressDetailView.vue`: Funzionalità "Visualizza Risposte" per i quiz.
    *   In `AssignedQuizDetailView.vue`: Funzionalità "Visualizza Tentativo" / "Correggi" (che potrebbe navigare a `GradingAttemptView.vue`).
*   **Rifinimento UI/UX:**
    *   Migliorare l'aspetto dei grafici ApexCharts (colori, tooltip, etichette).
    *   Assicurare che tutte le tabelle siano responsive e ben formattate.
    *   Migliorare la gestione degli stati di caricamento ed errore per ogni sezione.
*   **Filtri e Ordinamento Avanzati (Opzionale):**
    *   Implementare filtri più robusti e opzioni di ordinamento nelle tabelle principali e di dettaglio, se necessario.
*   **Test Completi:**
    *   Testare tutte le funzionalità con dati reali e casi limite.