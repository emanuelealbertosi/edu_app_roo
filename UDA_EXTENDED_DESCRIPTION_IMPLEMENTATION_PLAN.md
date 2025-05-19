# Proposta di Modifica a `UDA_IMPLEMENTATION_PLAN.md` (Revisione 2) per l'Integrazione dei Box Descrittivi Aggiuntivi

**Versione Documento Originale:** 1.1
**Data Proposta:** 17 Maggio 2025
**Autore Proposta:** Roo (Architect AI)
**Riferimento Piano Originale:** [`UDA_IMPLEMENTATION_PLAN.md`](UDA_IMPLEMENTATION_PLAN.md:1)
**Modifiche Chiave Introdotte:**
*   Aggiunta di tre nuovi campi (`knowledge_html`, `skills_html`, `competences_html`) al modello `UDA` e relativi serializer per memorizzare contenuti WYSIWYG per "Conoscenze", "Abilità" e "Competenze".
*   In `UdaDetailView.vue`, questi tre campi saranno presentati come sezioni individualmente espandibili/collassabili.
*   Quando espanse, queste sezioni cercheranno di allinearsi orizzontalmente (es. usando CSS Flexbox/Grid), permettendo l'apertura simultanea di più sezioni. Su schermi più piccoli, si adatteranno impilandosi verticalmente.
*   L'editing del contenuto di queste sezioni avverrà "on-click" all'interno della sezione espansa, utilizzando un editor WYSIWYG esistente nel progetto.
*   In `UdaFormView.vue`, verranno aggiunti editor WYSIWYG standard per questi tre nuovi campi.

Questo documento delinea le modifiche necessarie al piano di implementazione originale per le Unità Didattiche di Apprendimento (UDA) per integrare queste nuove funzionalità.

---

## 1. Modifiche al Backend (Django & Django REST Framework)

### 1.1. Modelli Django (Rif. Sezione 2.2 del Piano Originale)

Modificheremo il modello `UDA` nel file `uda/models.py` (riga 28 del piano originale) per includere tre nuovi campi di testo che supporteranno contenuto HTML:

*   **`UDA`**: MODIFICATO
    *   Campi Esistenti: ... (come da piano originale) ... `description` (TextField, opzionale), ...
    *   **Nuovi Campi:**
        *   `knowledge_html` (TextField, opzionale, `blank=True`, `null=True`): Conterrà l'HTML per la sezione "Conoscenze".
        *   `skills_html` (TextField, opzionale, `blank=True`, `null=True`): Conterrà l'HTML per la sezione "Abilità".
        *   `competences_html` (TextField, opzionale, `blank=True`, `null=True`): Conterrà l'HTML per la sezione "Competenze".
    *   ... (restanti campi come da piano originale) ...

*   **Azioni (Aggiornamento):**
    *   Definire i nuovi campi nel modello `UDA`.
    *   Creare e applicare le migrazioni Django (`makemigrations uda`, `migrate`).

### 1.2. Serializer (DRF) (Rif. Sezione 2.3 del Piano Originale)

Aggiorneremo `UDASerializer` in `uda/serializers.py` (riga 47 del piano originale) per includere i nuovi campi:

*   **`UDASerializer`**: MODIFICATO
    *   Includere `knowledge_html`, `skills_html`, `competences_html` nei campi del serializer. Questi campi saranno sia leggibili che scrivibili.

*   **Azioni (Aggiornamento):**
    *   Aggiornare `UDASerializer` per gestire i nuovi campi.

---

## 2. Modifiche al Frontend (frontend-lessons - Vue.js)

### 2.1. Store Management (Pinia) (Rif. Sezione 3.1 del Piano Originale)

Aggiorneremo `udaStore.ts` (riga 88 del piano originale):

*   **`udaStore.ts`**: MODIFICATO
    *   **State**:
        *   Aggiornare l'interfaccia/tipo per `currentUda` e gli elementi in `udas` per includere `knowledge_html`, `skills_html`, `competences_html`.
    *   **Actions**:
        *   Modificare `createUda` e `updateUda`: assicurarsi che i payload di queste azioni possano includere i dati per `knowledge_html`, `skills_html`, `competences_html` e che questi vengano inviati al backend.
        *   Modificare `fetchUda` e `fetchUdas`: assicurarsi che i nuovi campi vengano recuperati e memorizzati correttamente nello state.

*   **Azioni (Aggiornamento):**
    *   Aggiornare le interfacce/tipi e le actions in `udaStore.ts`.

### 2.2. Servizi API (Rif. Sezione 3.2 del Piano Originale)

Le funzioni esistenti in `services/udaService.ts` (riga 108 del piano originale) per `createUda(data)` e `updateUda(id, data)` dovrebbero già essere in grado di gestire i nuovi campi se questi vengono aggiunti all'oggetto `data`. Non sono previste modifiche dirette alle firme delle funzioni, ma andrà verificato in fase di implementazione.

### 2.3. Componenti UI (Rif. Sezione 3.4 del Piano Originale)

*   **`UdaDetailView.vue`** (Rif. riga 145, 186-191 del piano originale):
    *   Sotto la visualizzazione attuale dei "Dati Principali UDA", verrà implementato un contenitore (es. un `div` con `display: flex; flex-wrap: wrap;` o `display: grid;` per l'allineamento orizzontale su schermi larghi e l'adattamento su quelli piccoli).
    *   All'interno di questo contenitore, verranno istanziate tre componenti `CollapsibleEditableSection.vue` (vedi sotto), una per "Conoscenze", una per "Abilità", e una per "Competenze".
    *   Queste sezioni potranno essere espanse o collassate individualmente.
    *   Quando espanse, cercheranno di disporsi orizzontalmente. Su schermi più piccoli (o se lo spazio non è sufficiente), si impileranno verticalmente.

*   **`UdaFormView.vue`** (Rif. riga 144 del piano originale):
    *   Verranno aggiunti tre editor WYSIWYG (utilizzando il componente editor esistente nel progetto) per "Conoscenze", "Abilità" e "Competenze". L'allineamento qui seguirà probabilmente un layout di form standard (tipicamente verticale per i campi).

*   **Nuovo Componente Proposto: `CollapsibleEditableSection.vue`**
    *   **Props**:
        *   `title`: String (es. "Conoscenze") - Titolo della sezione.
        *   `initialContentHtml`: String - Il contenuto HTML iniziale da visualizzare/editare.
        *   `onSave`: Function - Callback chiamata con il nuovo HTML al salvataggio (`async (newHtml: string) => Promise<void>`).
        *   `isInitiallyExpanded`: Boolean (opzionale, default `false`) - Se la sezione deve essere espansa al caricamento.
    *   **Stato Interno**:
        *   `isExpanded`: Boolean - Controlla se la sezione è espansa o collassata.
        *   `isEditing`: Boolean - Controlla se la sezione è in modalità di modifica.
        *   `currentHtml`: String - Il contenuto HTML attualmente visualizzato o in modifica.
        *   `isLoading`: Boolean - Per feedback durante il salvataggio.
    *   **Funzionalità**:
        *   Un'intestazione cliccabile (contenente `title` e un'icona tipo freccia) per gestire l'espansione/collasso.
        *   **Modalità Collassata**: Mostra solo l'intestazione.
        *   **Modalità Espansa (Non in Modifica)**: Mostra `currentHtml` renderizzato (usando `v-html`). Un pulsante/icona "Modifica" è visibile. Se `currentHtml` è vuoto, mostra un messaggio placeholder (es. "Nessun contenuto. Clicca su Modifica per aggiungerne.").
        *   **Modalità Espansa (In Modifica)**: Mostra un'istanza dell'editor WYSIWYG esistente, pre-caricata con `currentHtml`. Pulsanti "Salva" e "Annulla" sono visibili.
        *   **Logica di Salvataggio**: Al click su "Salva", imposta `isLoading` a true, chiama `onSave(currentHtml)`. Se `onSave` ha successo, esce dalla modalità di modifica (`isEditing = false`), `isLoading = false`. In caso di errore, `isLoading = false` e mostra un messaggio di errore (l'editor rimane attivo).
        *   **Logica di Annullamento**: Ripristina `currentHtml` al valore che aveva prima dell'inizio della modifica (o al `initialContentHtml` se non ci sono state modifiche salvate intermedie), esce dalla modalità di modifica.
    *   **Styling**: Il componente dovrà essere flessibile per adattarsi al contenitore flex/grid in `UdaDetailView.vue`. Ogni istanza di `CollapsibleEditableSection.vue` occuperà lo spazio necessario per il suo titolo quando collassata, e per il suo contenuto quando espansa.

*   **Azioni (Aggiornamento):**
    *   Identificare e preparare il componente editor WYSIWYG esistente per il riutilizzo.
    *   Sviluppare il nuovo componente `CollapsibleEditableSection.vue` con le funzionalità e lo styling descritti.
    *   In `UdaDetailView.vue`, creare un contenitore genitore (es. `div`) e integrare al suo interno tre istanze di `CollapsibleEditableSection.vue`. Applicare stili CSS al contenitore per ottenere l'allineamento orizzontale desiderato (es. `display: flex; flex-wrap: wrap; gap: 1rem;`) e gestire il responsive design.
    *   In `UdaFormView.vue`, aggiungere tre istanze dell'editor WYSIWYG standard.
    *   Assicurare la corretta gestione dei dati (caricamento, modifica, salvataggio) e degli stati (espanso/collassato, editing, loading) attraverso lo store Pinia e i servizi API.

---

## 3. Modifiche al Testing (Rif. Sezione 4 del Piano Originale)

### 3.1. Backend (Django) (Rif. Sezione 4.1)

*   **Test Unitari:**
    *   Aggiornare i test per `UDASerializer` per includere la validazione e la serializzazione/deserializzazione dei nuovi campi `knowledge_html`, `skills_html`, `competences_html`.
*   **Test di Integrazione:**
    *   Aggiornare i test degli endpoint API per `UDAViewSet` (CRUD) per assicurare che i nuovi campi possano essere creati e aggiornati correttamente. Testare con input HTML validi, vuoti, e potenzialmente malformati (per la gestione degli errori).

### 3.2. Frontend (Vue.js) (Rif. Sezione 4.2)

*   **Test Unitari:**
    *   Testare approfonditamente il nuovo componente `CollapsibleEditableSection.vue`:
        *   Interazioni di espansione/collasso.
        *   Passaggio tra modalità visualizzazione e modalità editing.
        *   Corretto caricamento del contenuto nell'editor.
        *   Logica di salvataggio (chiamata a `onSave`, gestione stati `isLoading`).
        *   Logica di annullamento.
        *   Visualizzazione placeholder per contenuti vuoti.
    *   Aggiornare i test per `UdaDetailView.vue` per coprire l'integrazione e l'interazione con le tre istanze di `CollapsibleEditableSection.vue`, incluso il layout responsive.
    *   Aggiornare i test per `UdaFormView.vue` per l'editing dei nuovi campi.
    *   Aggiornare i test per `udaStore.ts` per la gestione dei nuovi campi.
*   **Test E2E (End-to-End):**
    *   Aggiungere/modificare scenari di test per:
        *   Creare una nuova UDA includendo contenuti per Conoscenze, Abilità e Competenze tramite `UdaFormView.vue`.
        *   Visualizzare una UDA in `UdaDetailView.vue`:
            *   Verificare che le sezioni siano inizialmente collassate (o secondo la prop `isInitiallyExpanded` se usata).
            *   Testare l'espansione e il collasso indipendente di ogni sezione.
            *   Testare l'apertura simultanea di più sezioni e verificare il layout (orizzontale su schermi larghi, verticale su piccoli).
            *   Testare l'editing "on click" del contenuto all'interno di una sezione espansa, il salvataggio e l'annullamento.
            *   Verificare la corretta visualizzazione dei contenuti HTML renderizzati dopo il salvataggio.
            *   Verificare il comportamento con contenuti vuoti e l'aggiunta di nuovo contenuto.

---

## 4. Diagramma di Flusso Utente (Mermaid) - Interazione con `CollapsibleEditableSection.vue` in `UdaDetailView.vue`

```mermaid
graph TD
    subgraph UdaDetailView
        direction LR
        Cont[Contenitore Flex/Grid] --> SecConoscenze["CollapsibleEditableSection ('Conoscenze')"]
        Cont --> SecAbilita["CollapsibleEditableSection ('Abilità')"]
        Cont --> SecCompetenze["CollapsibleEditableSection ('Competenze')"]
    end

    subgraph CollapsibleEditableSection ('Titolo della Sezione')
        direction TB
        AA(Inizio: Sezione Collassata) -- Clic su Titolo/Icona Espandi --> AB[Stato: Espanso];
        AB -- Clic su Titolo/Icona Collassa --> AA;

        AB --> AC{In Modifica?};
        AC -- No --> AD[Mostra HTML Renderizzato del Contenuto];
        AD -- Contenuto Vuoto --> AE[Mostra Placeholder "Nessun contenuto..."];
        AD -- Contenuto Presente --> AF[Visualizza Contenuto];
        AE -- Clic su Btn 'Modifica' --> AG[Stato: In Modifica];
        AF -- Clic su Btn 'Modifica' --> AG;

        AC -- Sì --> AG[Mostra Editor WYSIWYG con Contenuto Attuale];
        AG --> AH{Interazione Utente};
        AH -- Clic su 'Salva' --> AI[Set isLoading=true, Chiama onSave(currentHtml)];
        AI -- Successo onSave --> AJ[Set isLoading=false, Stato: Non In Modifica];
        AJ --> AD;
        AI -- Errore onSave --> AK[Set isLoading=false, Mostra Errore, Editor Attivo];
        AK --> AG;
        AH -- Clic su 'Annulla' --> AL[Ripristina HTML originale, Stato: Non In Modifica];
        AL --> AD;
    end
```

---

## 5. Considerazioni UI/UX Aggiuntive (Rif. Sezione 5 del Piano Originale)

*   **Responsive Design**: Cruciale per il contenitore delle sezioni in `UdaDetailView.vue`. Utilizzare media queries e proprietà CSS flessibili per garantire che su schermi larghi le sezioni espanse si affianchino (es. 3 colonne, o 2+1, o 1+1+1 a seconda dello spazio), mentre su schermi più stretti si impilino verticalmente.
*   **Indicazioni Visive**:
    *   Icone chiare (es. `+`/`-` o frecce `▼`/`►`) per indicare lo stato espandibile/collassabile.
    *   Feedback visivo durante il `isLoading` del salvataggio (es. spinner sul pulsante Salva o overlay leggero sull'editor).
    *   Distinzione visiva chiara tra la modalità di visualizzazione del contenuto renderizzato e la modalità di modifica con l'editor.
*   **Animazioni**: Transizioni fluide (es. `max-height` o `transform`) per l'espansione/collasso possono migliorare l'esperienza, se implementate con attenzione alle performance.
*   **Accessibilità (a11y)**:
    *   Assicurare che le intestazioni delle sezioni siano bottoni o abbiano `role="button"` e siano navigabili e attivabili da tastiera.
    *   Utilizzare attributi `aria-expanded` per lo stato di espansione/collasso.
    *   Assicurare che l'editor WYSIWYG utilizzato sia accessibile.
*   **Gestione Contenuti Vuoti**: Il placeholder in modalità visualizzazione dovrebbe essere chiaro e incoraggiare l'azione.
*   **Performance**:
    *   L'inizializzazione di più editor WYSIWYG (anche se nascosti dentro sezioni collassate) potrebbe avere un impatto. Valutare se inizializzare l'editor solo quando la sezione viene espansa e si entra in modalità modifica, distruggendolo poi all'uscita dalla modalità modifica o al collasso della sezione. Questo approccio ("lazy loading" dell'editor) è generalmente preferibile.

---

## 6. Stima di Sviluppo (Rif. Sezione 6 del Piano Originale)

Le stime di impegno (giorni-uomo indicativi) andranno definite dal team di sviluppo, tenendo conto della complessità aggiunta.

*   **Backend**:
    *   Modelli e Serializer (aggiunta campi UDA): `X` giorni
*   **Frontend**:
    *   Store UDA (gestione nuovi campi): `Y` giorni
    *   Componente `CollapsibleEditableSection.vue` (sviluppo e test unitari): `Z'` giorni
    *   Integrazione in `UdaDetailView.vue` (con logica flex/grid, responsive, interazioni): `W'` giorni
    *   Integrazione in `UdaFormView.vue`: `U` giorni
*   **Testing**:
    *   Test Backend (unitari e integrazione): `V_be` giorni
    *   Test Frontend (unitari, integrazione, E2E inclusi test responsive): `V_fe` giorni

(Le lettere X, Y, Z', W', U, V_be, V_fe rappresentano stime di impegno).

---