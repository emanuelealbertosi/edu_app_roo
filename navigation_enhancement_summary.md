# Documento di Sintesi: Miglioramento Navigazione Frontend

**Data:** 8 Luglio 2025

## 1. Obiettivo Iniziale

La richiesta iniziale era di modificare il comportamento dei menu di navigazione principali nelle tre applicazioni frontend (`frontend-teacher`, `frontend-lessons`, `frontend-student`). L'obiettivo era far sì che un clic sulla voce di menu corrispondente alla pagina già attiva innescasse un ricaricamento della vista, anziché non avere alcun effetto.

## 2. Evoluzione della Funzionalità

Durante lo sviluppo, la funzionalità è stata raffinata per migliorare l'esperienza utente:

1.  **Navigazione alla Radice della Sezione:** Invece di un semplice ricaricamento della pagina corrente (es. `students/1/edit`), si è deciso di navigare sempre alla pagina principale della sezione (es. `students`). Il ricaricamento completo (`window.location.reload()`) avviene solo se l'utente si trova già sulla pagina principale della sezione.
2.  **Persistenza dello Stato dei Sottomenu:** Per evitare che i sottomenu espandibili (presenti in `frontend-teacher`) si chiudessero dopo il ricaricamento della pagina, il loro stato (aperto/chiuso) viene ora salvato nel `sessionStorage` del browser e ripristinato al caricamento della pagina.
3.  **Persistenza dello Stato della Sidebar:** Allo stesso modo, per preservare la preferenza dell'utente, lo stato di espansione della sidebar laterale (presente in `frontend-teacher` e `frontend-student`) viene salvato nel `sessionStorage` e ripristinato dopo il ricaricamento.

## 3. Soluzione Tecnica Implementata

È stata creata e utilizzata una funzione di utilità `navigateTo` in ciascun frontend. Questa funzione centralizza la logica di navigazione:

```typescript
export function navigateTo(router: Router, routeName: string) {
  if (router.currentRoute.value.name === routeName) {
    // Ricarica la pagina se l'utente è già sulla rotta principale
    window.location.reload();
  } else {
    // Altrimenti, naviga alla rotta principale della sezione
    router.push({ name: routeName });
  }
}
```

Per mantenere lo stato dell'interfaccia, le funzioni che gestiscono l'apertura/chiusura dei menu e della sidebar sono state aggiornate per scrivere il loro stato nel `sessionStorage`. Al caricamento iniziale del componente (`onMounted`), questi valori vengono letti e l'interfaccia viene ripristinata di conseguenza.

## 4. File Modificati

Sono stati creati o modificati i seguenti file:

### `frontend-teacher`
-   `src/utils/navigation.ts` (Modificato)
-   `src/App.vue` (Modificato)

### `frontend-lessons`
-   `src/utils/navigation.ts` (Creato)
-   `src/views/DashboardView.vue` (Modificato)

### `frontend-student`
-   `src/utils/navigation.ts` (Creato)
-   `src/App.vue` (Modificato)

## 5. Sostituzione del Pulsante "Indietro" con Breadcrumb

**Data:** 8 Luglio 2025

### 5.1. Motivazione del Cambiamento

A seguito di persistenti difficoltà nell'implementazione di un comportamento affidabile e intuitivo per il pulsante di navigazione "Indietro", si è deciso di rimuovere completamente tale funzionalità. La gestione della cronologia in un'applicazione complessa con iframe e navigazioni incrociate si è rivelata problematica e fonte di confusione per l'utente.

In sostituzione, si è scelto di progettare e implementare un sistema di navigazione basato su **breadcrumb** (briciole di pane). Questo approccio offre una chiara visualizzazione della gerarchia della pagina corrente e permette all'utente di navigare facilmente ai livelli superiori con un solo clic.

### 5.2. Piano di Implementazione per i Breadcrumb

La nuova funzionalità verrà sviluppata in modo incrementale e modulare per tutti e tre i frontend.

#### Fase 1: Definizione della Struttura dei Dati

La generazione dei breadcrumb si baserà sui metadati delle rotte definiti in `router/index.ts`. Ogni rotta che necessita di un breadcrumb avrà un campo `meta` strutturato in questo modo:

```typescript
meta: {
  breadcrumb: (route) => [
    { text: 'Home', to: { name: 'dashboard' } },
    { text: 'UDA', to: { name: 'uda-list' } },
    { text: `Dettaglio: ${route.params.id}`, to: { name: 'uda-detail', params: { id: route.params.id } } }
    // L'ultimo elemento non avrà un link 'to'
  ]
}
```

-   Il campo `breadcrumb` sarà una funzione che riceve l'oggetto `route` corrente.
-   Questo permette di creare breadcrumb dinamici che includono parametri dalla rotta (es. ID di un'entità).
-   Ogni elemento dell'array rappresenterà un "pezzo" del breadcrumb, con un testo da visualizzare e un link di navigazione (opzionale per l'ultimo elemento).

#### Fase 2: Creazione del Componente `Breadcrumb.vue`

Verrà creato un componente riutilizzabile `Breadcrumb.vue` che:
1.  Utilizzerà `useRoute()` per accedere alla rotta corrente.
2.  Controllerà il campo `route.meta.breadcrumb` per ottenere i dati necessari.
3.  Renderizzerà dinamicamente la lista di link e separatori.
4.  Sarà stilizzato in modo coerente con il design system dell'applicazione.

#### Fase 3: Integrazione e Test

1.  Il componente `Breadcrumb.vue` verrà aggiunto al layout principale (`App.vue`) di ciascun frontend, in una posizione prominente (solitamente sotto l'header).
2.  Verranno aggiornate le definizioni delle rotte in `router/index.ts` per includere i metadati `breadcrumb` necessari.
3.  Verrà condotto un test approfondito su tutte le sezioni dell'applicazione per garantire che i breadcrumb vengano generati correttamente e che la navigazione funzioni come previsto.

### 5.3. Rollback del Pulsante "Indietro"

Per completare la transizione, è stato eseguito un rollback completo della funzionalità precedente:
-   **Rimozione Componenti:** I file `BackButton.vue` sono stati eliminati da tutti i frontend.
-   **Rimozione Servizi:** I file `navigationHistory.ts` sono stati eliminati.
-   **Pulizia Codice:** Tutti i riferimenti ai componenti e ai servizi rimossi sono stati eliminati dai file `App.vue` e `router/index.ts` di ciascun progetto.

---

## 6. Stato Attuale e Prossimi Passi (Breadcrumb)

**Data:** 8 Luglio 2025

### 6.1. Stato dell'Implementazione

-   **Implementazione Breadcrumb:**
    -   `frontend-student`: Completato. I metadati per i breadcrumb sono stati aggiunti a tutte le rotte.
    -   `frontend-lessons`: Completato. Il componente `Breadcrumb.vue` è stato creato, integrato in `App.vue` e i metadati sono stati aggiunti al router.
    -   `frontend-teacher`: Completato. I metadati per i breadcrumb sono stati aggiunti a tutte le rotte.
-   **Problema Rilevato:** È stato identificato un bug visivo: quando `frontend-lessons` viene visualizzato all'interno di `frontend-teacher` o `frontend-student`, i breadcrumb vengono duplicati.
-   **Correzione Iniziata:**
    -   In `frontend-teacher/src/router/index.ts`, ho sostituito le definizioni `breadcrumb` per le rotte "embedded" con un nuovo flag `meta: { hideHostBreadcrumb: true }`.

### 6.2. Prossimi Passi

1.  **Completare la correzione in `frontend-teacher`:**
    -   Modificare `frontend-teacher/src/App.vue` per leggere il flag `hideHostBreadcrumb` dalla rotta corrente e nascondere il proprio componente `Breadcrumb` di conseguenza.
2.  **Implementare la stessa correzione in `frontend-student`:**
    -   Aggiungere un flag simile (es. `hideHostBreadcrumb: true`) alle rotte in `frontend-student/src/router/index.ts` che caricano contenuti da `frontend-lessons` (es. la rotta `EmbeddedLessons`).
    -   Modificare `frontend-student/src/App.vue` per nascondere il suo breadcrumb quando il flag è presente.
3.  **Test Finale:** Verificare che il breadcrumb duplicato non appaia più e che la navigazione funzioni correttamente in tutti e tre i frontend.

### 6.3. Correzione Navigazione Breadcrumb in Contesto Embedded

**Data:** 8 Luglio 2025

#### Problema
È stato riscontrato che, quando `frontend-lessons` è visualizzato all'interno di un'altra applicazione (es. `frontend-teacher`), il link "Home" nel suo breadcrumb puntava alla dashboard di `frontend-lessons` stessa, invece che alla dashboard dell'applicazione ospitante. Questo comportamento era disorientante per l'utente.

#### Soluzione Implementata
È stata implementata una soluzione basata sulla comunicazione tra l'iframe (`frontend-lessons`) e la finestra principale dell'host (`frontend-teacher` o `frontend-student`) tramite `window.postMessage`.

1.  **Modifiche a `frontend-lessons`:**
    *   **`router/index.ts`**: È stata creata una funzione helper, `getHomeBreadcrumb`, che rileva se l'applicazione è in esecuzione all'interno di un iframe (controllando il parametro URL `embedded=true`). Se sì, il breadcrumb "Home" viene generato con un flag speciale (`isHostLink: true`) invece di un link di navigazione interno.
    *   **`components/common/Breadcrumb.vue`**: Il componente è stato aggiornato per riconoscere il flag `isHostLink`. Se presente, il link "Home" non è più un `<RouterLink>`, ma un elemento `<a>` che, al clic, esegue la funzione `handleHostLinkClick`. Questa funzione invia un messaggio `{ type: 'navigate-to-host-home' }` alla finestra genitore.

2.  **Modifiche a `frontend-teacher` e `frontend-student` (Host):**
    *   In tutte le viste che caricano `frontend-lessons` in un iframe (es. `EmbeddedTeacherSubjectsView.vue`, `EmbeddedLessonsView.vue`, etc.), è stato aggiunto un listener per l'evento `message` nel ciclo di vita del componente (`onMounted`).
    *   Questo listener attende messaggi dall'iframe. Quando riceve un messaggio con `type: 'navigate-to-host-home'`, utilizza il router dell'applicazione host per navigare alla propria pagina principale (es. `{ name: 'dashboard' }`).
    *   Il listener viene rimosso in `onBeforeUnmount` per prevenire memory leak.

Questa soluzione garantisce che la navigazione del breadcrumb sia sempre contestuale e intuitiva per l'utente, indipendentemente da come le applicazioni sono annidate.

### 6.4. Correzione Visibilità Breadcrumb in Viste Modali

**Data:** 8 Luglio 2025

#### Problema
È stato riscontrato che il componente `Breadcrumb` rimaneva visibile quando una vista veniva aperta all'interno di una finestra modale (sia una modale nativa dell'applicazione che una caricata in un iframe), coprendo parte dell'interfaccia e creando confusione.

#### Soluzione Implementata
È stata adottata una soluzione a due livelli per gestire tutti i possibili contesti in cui una vista può essere considerata "modale":

1.  **Gestione Modali Interne con Pinia:**
    *   È stato aggiunto uno stato `isModalOpen` allo store Pinia `ui.ts` di `frontend-lessons`.
    *   Tutti i componenti che aprono una modale all'interno di `frontend-lessons` (es. `LessonEditModal.vue`, `SelectExistingContentModal.vue`, `IFrameModal.vue`) sono stati modificati per impostare `isModalOpen` a `true` quando vengono montati e a `false` quando vengono chiusi o smontati.
    *   Il componente `App.vue` di `frontend-lessons` è stato aggiornato per nascondere il `Breadcrumb` se `isModalOpen` è `true`.

2.  **Gestione Modali Esterne (Iframe) con Parametro URL:**
    *   Per i casi in cui una vista di `frontend-lessons` viene caricata in un `IFrameModal` da un'applicazione host (es. `frontend-teacher`), non è possibile fare affidamento sullo store Pinia dell'host.
    *   È stato introdotto un nuovo parametro query nell'URL: `inModal=true`.
    *   Il componente `App.vue` di `frontend-lessons` è stato modificato per controllare la presenza di questo parametro. Se `route.query.inModal === 'true'`, il breadcrumb viene nascosto.
    *   Il codice nell'applicazione host (`frontend-teacher/src/views/TeacherLessonListView.vue`) che genera l'URL per l'iframe della modale dei contenuti è stato aggiornato per aggiungere `&inModal=true` all'URL.

Questa doppia strategia assicura che il breadcrumb venga nascosto in modo affidabile ogni volta che una vista funziona come una modale, migliorando la coerenza e l'usabilità dell'interfaccia.