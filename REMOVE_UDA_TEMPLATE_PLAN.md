# Piano di Implementazione: Rimozione Template UDA e Introduzione Copia UDA

**Obiettivo:** Rimuovere il concetto di "Template UDA" dall'interfaccia utente e sostituirlo con una funzionalità che permetta di copiare UDA esistenti.

**Fasi del Piano:**

**Fase 1: Rimozione dei Template UDA dall'Interfaccia Utente**

1.  **Modifica Menu di Navigazione ([`frontend-lessons/src/App.vue`](frontend-lessons/src/App.vue:1))**
    *   Rimuovere la voce di menu "Template UDA" sia dalla sidebar desktop (righe 190-196) che da quella mobile (righe 292-298).
    *   Rimuovere la voce "Template UDA" dal dropdown "Crea" nell'header (riga 363).
    *   Rimuovere l'import dell'icona `DocumentDuplicateIcon` se non più utilizzata altrove (riga 23).

2.  **Modifica Pagina Dettaglio Corso ([`frontend-lessons/src/views/courses/CourseDetailView.vue`](frontend-lessons/src/views/courses/CourseDetailView.vue:1))**
    *   Rimuovere il pulsante "Aggiungi da Template" (righe 47-53).
    *   Rimuovere la logica associata alla modale `AddUdaFromTemplateModal`:
        *   Rimuovere l'import del componente [`AddUdaFromTemplateModal.vue`](frontend-lessons/src/components/courses/AddUdaFromTemplateModal.vue:1) (riga 193).
        *   Rimuovere la dichiarazione della variabile `showAddUdaFromTemplateModal` (riga 215).
        *   Rimuovere la funzione `openAddUdaFromTemplateModal` (righe 219-226).
        *   Rimuovere l'utilizzo del componente `<AddUdaFromTemplateModal>` nel template (righe 166-171).
        *   Potrebbe essere necessario aggiornare la funzione `handleUdaCreated` se era specificamente legata alla creazione da template, anche se sembra generica.

3.  **Modifica Form Creazione/Modifica UDA ([`frontend-lessons/src/views/uda/UdaFormView.vue`](frontend-lessons/src/views/uda/UdaFormView.vue:1))**
    *   Rimuovere la sezione "Parti da un Template (Opzionale)" (righe 21-30).
    *   Rimuovere la variabile `selectedSourceTemplateId` (riga 210) e la logica associata nel `watch` (righe 301-326) e in `onMounted` (riga 376-378).
    *   Rimuovere il campo `source_template` da `formData` (riga 222) e `source_template_id` da `UdaApiPayload` (riga 175) e dalla logica di `handleSubmit` (riga 402).
    *   Rimuovere l'import e l'utilizzo di `udaTemplateStore` se non più necessario per altre funzionalità in questo file (righe 140, 183, 230, 336).
    *   Rimuovere la funzione `loadTemplateData` (righe 266-299).
    *   Rimuovere la variabile `queryTemplateId` (riga 190) se usata solo per pre-selezionare un template.

4.  **Rimozione Route e Componenti non più utilizzati (da verificare)**
    *   Verificare se le route `/uda-templates`, `/uda-templates/new`, `/uda-templates/:id/edit` definite in [`frontend-lessons/src/router/index.ts`](frontend-lessons/src/router/index.ts:1) (come da [`UDA_IMPLEMENTATION_PLAN.md`](UDA_IMPLEMENTATION_PLAN.md:126-128)) sono ancora necessarie. Se servono solo per i template UDA, possono essere rimosse.
    *   Verificare se i componenti `UdaTemplateListView.vue`, `UdaTemplateFormView.vue` (come da [`UDA_IMPLEMENTATION_PLAN.md`](UDA_IMPLEMENTATION_PLAN.md:145-146)) sono ancora necessari. Se sì, rimuoverli.
    *   Rimuovere lo store `udaTemplateStore.ts` ([`frontend-lessons/src/stores/udaTemplateStore.ts`](frontend-lessons/src/stores/udaTemplateStore.ts:1)) se non più utilizzato.

**Fase 2: Implementazione Funzionalità "Copia UDA"**

1.  **Backend (Django & DRF - `apps/uda/views.py` e `apps/uda/serializers.py`)**
    *   **Nuovo Endpoint API:** Creare un nuovo endpoint API, ad esempio `POST /api/udas/{uda_id}/copy/`.
        *   Questo endpoint riceverà l'ID dell'UDA da copiare.
        *   La view associata dovrà:
            *   Recuperare l'UDA originale.
            *   Creare una nuova istanza di `UDA` duplicando i campi dell'originale (es. `title`, `description`, `start_date`, `end_date`, `status`, `subjects`, `topics`).
            *   Il titolo della nuova UDA potrebbe essere prefissato con "Copia di " o simile.
            *   Associare i contenuti duplicati: creare nuove istanze di `UDAContent` basate sui contenuti dell'UDA originale.
            *   La nuova UDA NON dovrebbe essere associata a nessun corso inizialmente, oppure potrebbe essere opzionalmente associata allo stesso corso dell'originale (da decidere). L'utente la modificherà successivamente.
            *   Restituire la nuova UDA serializzata.
    *   **Serializer:** Non dovrebbe essere necessario un nuovo serializer specifico se si riutilizza `UDASerializer` per la risposta.

2.  **Frontend (Vue.js)**
    *   **Modifica Store UDA ([`frontend-lessons/src/stores/udaStore.ts`](frontend-lessons/src/stores/udaStore.ts:1))**
        *   Aggiungere una nuova action `copyUda(udaId: number)`.
        *   Questa action chiamerà il nuovo endpoint API `/api/udas/{uda_id}/copy/`.
        *   Al successo, potrebbe aggiungere la nuova UDA alla lista `udas` o invalidare la cache per forzare un refetch.
    *   **Modifica Servizio API ([`frontend-lessons/src/services/udaService.ts`](frontend-lessons/src/services/udaService.ts:1) o simile)**
        *   Aggiungere una nuova funzione `copyUda(udaId: number)` che effettua la chiamata POST al nuovo endpoint.
    *   **Aggiunta Pulsante "Copia UDA" in `UdaListView.vue` ([`frontend-lessons/src/views/uda/UdaListView.vue`](frontend-lessons/src/views/uda/UdaListView.vue:1))**
        *   Nella tabella delle UDA, aggiungere un'icona/pulsante "Copia" per ogni riga.
        *   Al click, chiamare una funzione che invoca `udaStore.copyUda(uda.id)`.
        *   Dopo la copia, mostrare una notifica di successo e reindirizzare l'utente al form di modifica della nuova UDA creata (`/udas/{new_uda_id}/edit`) oppure aggiornare la lista.
    *   **Aggiunta Pulsante "Copia UDA" in `CourseDetailView.vue` ([`frontend-lessons/src/views/courses/CourseDetailView.vue`](frontend-lessons/src/views/courses/CourseDetailView.vue:1))**
        *   Nella tabella delle UDA associate al corso, aggiungere un'icona/pulsante "Copia" per ogni UDA.
        *   Al click, chiamare una funzione che invoca `udaStore.copyUda(uda.id)`.
        *   Dopo la copia, la nuova UDA (che inizialmente potrebbe non essere associata a questo corso, a seconda della logica backend) dovrebbe essere modificabile. L'utente potrà poi associarla al corso desiderato tramite il form di modifica UDA.
        *   Una possibile UX: dopo la copia, si potrebbe aprire direttamente il form di modifica della nuova UDA.
    *   **Logica di Modifica Post-Copia:**
        *   Quando l'utente viene reindirizzato al form di modifica della UDA copiata, tutti i campi saranno pre-popolati. Il titolo sarà "Copia di [Titolo Originale]". L'utente potrà modificare tutti i campi, inclusa l'associazione al corso.

**Fase 3: Testing**

*   Testare approfonditamente la rimozione dei Template UDA (nessun riferimento residuo nell'UI, nessuna chiamata API relativa ai template).
*   Testare la funzionalità di copia UDA:
    *   Copia da `UdaListView`.
    *   Copia da `CourseDetailView`.
    *   Verificare che tutti i campi e i contenuti siano duplicati correttamente.
    *   Verificare che la nuova UDA sia modificabile e salvabile.
    *   Verificare l'associazione (o non associazione) iniziale al corso.

**Considerazioni Aggiuntive:**

*   **Pulizia Backend:** Valutare se i modelli Django `UDATemplate`, `UDATemplateTopic`, `UDATemplateContent` e le relative view API, serializer e URL possono essere rimossi completamente dal backend se non più utilizzati da altre parti del sistema. Questo va oltre la semplice modifica dell'interfaccia utente. Per ora, il task si concentra sul nascondere/rimuovere dall'UI.
*   **Impatto su `UDA_IMPLEMENTATION_PLAN.md`:** Questo documento dovrà essere aggiornato per riflettere la rimozione dei Template UDA e l'introduzione della funzionalità di copia.

**Diagramma Mermaid (Flusso di Copia UDA - Frontend):**

```mermaid
sequenceDiagram
    participant User
    participant UdaListView/CourseDetailView as View
    participant UdaStore
    participant UdaApiService
    participant BackendApi as API

    User->>View: Clicca "Copia UDA" su una UDA esistente (ID: X)
    View->>UdaStore: chiama copyUda(X)
    UdaStore->>UdaApiService: chiama copyUdaApi(X)
    UdaApiService->>API: POST /api/udas/X/copy/
    API-->>UdaApiService: Risposta (nuova UDA con ID: Y)
    UdaApiService-->>UdaStore: Ritorna nuova UDA (Y)
    UdaStore-->>View: Notifica successo / Aggiorna stato
    alt Apertura Form Modifica
        View->>Router: Naviga a /udas/Y/edit
    else Aggiornamento Lista
        View->>UdaStore: (opzionale) Richiede fetchUdas()
        UdaStore->>View: Lista UDA aggiornata
    end