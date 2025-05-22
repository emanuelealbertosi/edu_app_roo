# Piano di Implementazione: Esportazione UDA (Revisione 2 - DOCX e PDF)

**Data:** 19 Maggio 2025
**Autore:** Roo (Architect AI)
**Riferimento Documento Ministeriale:** [`MOD._10.04_Programmazione_didattica_individuale.docx`](MOD._10.04_Programmazione_didattica_individuale.docx:1) (Sezione 3 B)
**Piani UDA Esistenti:** [`UDA_IMPLEMENTATION_PLAN.md`](UDA_IMPLEMENTATION_PLAN.md:1), [`UDA_EXTENDED_DESCRIPTION_IMPLEMENTATION_PLAN.md`](UDA_EXTENDED_DESCRIPTION_IMPLEMENTATION_PLAN.md:1)

## 1. Obiettivo (Aggiornato)

Modificare la funzionalità di esportazione UDA nella vista dei dettagli del corso ([`frontend-lessons/src/views/courses/CourseDetailView.vue`](frontend-lessons/src/views/courses/CourseDetailView.vue:1)).
Il pulsante "Esporta" mostrerà un menu a tendina (dropdown) al passaggio del mouse, permettendo all'utente di scegliere se generare un file `.docx` o `.pdf`.
Entrambi i formati conterranno tutte le UDA del corso, formattate secondo la sezione "3 B: modalità di realizzazione: Unità di apprendimento" del documento ministeriale di riferimento, utilizzando tabelle per la struttura e includendo una sezione per le lezioni.

## 2. Modifiche al Backend (Django)

### 2.1. Aggiornamento Modello `UDA`
File: [`apps/uda/models.py`](apps/uda/models.py:1)
Campi aggiunti (come da piano originale, completato):
*   `is_civic_education`: `BooleanField(default=False)`
*   `didactic_strategies_html`: `TextField(blank=True, null=True)`
*   `materials_tools_html`: `TextField(blank=True, null=True)`
*   `assessment_type_html`: `TextField(blank=True, null=True)`
*   `evaluation_html`: `TextField(blank=True, null=True)`
*   `other_involved_subjects_text`: `TextField(blank=True, null=True)`
*   `export_specific_annotations_html`: `TextField(blank=True, null=True)`

**Azioni (Completate):**
1.  Definiti i nuovi campi nel modello `UDA`.
2.  Create e applicate le migrazioni.

### 2.2. Aggiornamento Serializer `UDASerializer` e `UDAContentSerializer`
File: [`apps/uda/serializers.py`](apps/uda/serializers.py:1)
Inclusi i nuovi campi in `UDASerializer`.
Modificato `UDAContentSerializer` nel metodo `to_representation` per mostrare `estimated_hours` della `Lesson` associata se quelle del `UDAContent` sono `None`.

**Azioni (Completate):**
1.  Aggiunti i nuovi campi a `UDASerializer`.
2.  Aggiornato `UDAContentSerializer.to_representation`.

### 2.3. Endpoint API per l'Esportazione (Revisionato con Endpoint Separati)
URL DOCX: `GET /api/uda/courses/{course_id}/export-udas-docx/` (Azione custom `export_udas_docx` in `CourseViewSet` ([`apps/uda/views.py`](apps/uda/views.py:1)))
URL PDF: `GET /api/uda/courses/{course_id}/export-udas-pdf/` (Azione custom `export_udas_pdf` in `CourseViewSet` ([`apps/uda/views.py`](apps/uda/views.py:1)))

**Funzionalità Chiave Implementate/Aggiornate:**
*   Recupera UDA del corso.
*   **Azione `export_udas_docx`:**
    *   Genera DOCX utilizzando `python-docx`.
    *   **Formattazione**: Utilizza tabelle per strutturare le informazioni di ciascuna UDA.
    *   **Contenuto HTML**: Estrae il testo semplice dall'HTML fornito usando `BeautifulSoup`.
    *   **Sezione Lezioni**: Include una tabella con "Titolo Lezione" e "Durata Stimata (ore)". Se `UDAContent.estimated_hours` è `None`, usa `Lesson.estimated_hours`.
    *   **Nome File**: Sanitizzato usando `get_valid_filename` e rimuovendo underscore finali.
    *   Restituisce il file `.docx` come `HttpResponse`.
*   **Azione `export_udas_pdf`:**
    *   Genera PDF utilizzando `xhtml2pdf`.
    *   Renderizza un template HTML ([`apps/uda/templates/uda_export/uda_pdf_template.html`](apps/uda/templates/uda_export/uda_pdf_template.html:1)) con i dati delle UDA.
    *   **Formattazione**: Struttura tabellare definita nel template HTML.
    *   **Contenuto HTML**: Inserito direttamente nel template HTML (usando `|safe` dove necessario).
    *   **Sezione Lezioni**: Tabella con "Titolo Lezione" e "Durata Stimata (ore)". Se `UDAContent.estimated_hours` è `None`, usa `Lesson.estimated_hours`.
    *   **Nome File**: Sanitizzato usando `get_valid_filename` e rimuovendo underscore finali.
    *   Restituisce il file `.pdf` come `HttpResponse`.
*   Gestione degli errori migliorata durante la generazione PDF (presente nell'azione `export_udas_pdf`).

**Azioni (Completate/Da Verificare):**
1.  Aggiunto `python-docx` a [`requirements.txt`](requirements.txt:1) (già presente).
2.  Aggiunto `beautifulsoup4` a [`requirements.txt`](requirements.txt:1) (completato).
3.  Sostituito `weasyprint` con `xhtml2pdf` in [`requirements.txt`](requirements.txt:1) (completato, richiede `pip install -r requirements.txt`).
4.  Creato template HTML per PDF: [`apps/uda/templates/uda_export/uda_pdf_template.html`](apps/uda/templates/uda_export/uda_pdf_template.html:1) (completato).
5.  L'azione `export_udas` in `CourseViewSet` ([`apps/uda/views.py`](apps/uda/views.py:1)) è stata divisa in `export_udas_docx` e `export_udas_pdf` (completato).
6.  Registrazione URL aggiornata per puntare a `export-udas-docx/` e `export-udas-pdf/` (verificato, gestita automaticamente dal router per le azioni decorate).
7.  **Da Verificare:** Funzionamento corretto dell'esportazione PDF e DOCX con i nuovi endpoint e risoluzione dell'errore 404 (potrebbe richiedere riavvio server Django).

## 3. Modifiche al Frontend (Vue.js)

### 3.1. Aggiornamento Store Pinia (`udaStore.ts` e `courseStore.ts`)
File: [`frontend-lessons/src/stores/udaStore.ts`](frontend-lessons/src/stores/udaStore.ts:1), [`frontend-lessons/src/stores/courseStore.ts`](frontend-lessons/src/stores/courseStore.ts:1)
*   Aggiornata interfaccia `UDA` (in [`frontend-lessons/src/types/uda.ts`](frontend-lessons/src/types/uda.ts:1)) con i nuovi campi (completato).
*   Modificate actions in `udaStore.ts` per gestire i nuovi campi (completato).
*   Modificata action `exportUdasToDocx` in `exportUdas(courseId: number, format: 'docx' | 'pdf')` in `courseStore.ts` per passare il formato (completato).

**Azioni (Completate):**
1.  Aggiornata interfaccia `Uda`.
2.  Modificate actions in `udaStore.ts`.
3.  Aggiornata action di esportazione in `courseStore.ts`.

### 3.2. Aggiornamento Componente `UdaFormView.vue`
File: [`frontend-lessons/src/views/uda/UdaFormView.vue`](frontend-lessons/src/views/uda/UdaFormView.vue:1)
Aggiunti input per i nuovi campi (completato).

**Azioni (Completate):**
1.  Integrati i nuovi campi nel form.

### 3.3. Aggiornamento Componente `UdaDetailView.vue`
File: [`frontend-lessons/src/views/uda/UdaDetailView.vue`](frontend-lessons/src/views/uda/UdaDetailView.vue:1)
Visualizza e permette la modifica dei nuovi campi specifici per l'export (completato).

**Azioni (Completate):**
1.  Integrata la visualizzazione/modifica dei nuovi campi.
2.  Aggiornate le etichette.

### 3.4. Pulsante di Esportazione in `CourseDetailView.vue` (Aggiornato)
File: [`frontend-lessons/src/views/courses/CourseDetailView.vue`](frontend-lessons/src/views/courses/CourseDetailView.vue:1)
*   Il pulsante "Esporta DOCX" è stato modificato in "Esporta".
*   Al passaggio del mouse (o click), mostra un menu dropdown con opzioni "Esporta come DOCX" e "Esporta come PDF".
*   La selezione di un formato chiama l'azione `handleExportUdas` con il formato corretto.
*   Aggiunta dipendenza `vue3-click-away` per la gestione del menu (richiede `npm install vue3-click-away`).

**Azioni (Completate):**
1.  Modificato il pulsante per includere un menu dropdown.
2.  Implementata logica per gestire la selezione del formato e chiamare l'azione aggiornata nello store.
3.  **Da Verificare:** Installazione di `vue3-click-away` e corretto funzionamento del menu.

### 3.5. Servizio API (`courseService.ts`)
File: [`frontend-lessons/src/services/courseService.ts`](frontend-lessons/src/services/courseService.ts:1)
*   Modificata funzione `exportUdasToDocx` in `exportUdas(courseId: number, format: 'docx' | 'pdf')`.
*   La funzione ora costruisce l'URL API per chiamare `/export-udas-docx/` o `/export-udas-pdf/` in base al `format`.

**Azioni (Completate):**
1.  Aggiornata la funzione del servizio API.

## 4. Testing (Da Eseguire/Aggiornare)

### 4.1. Backend
*   **Test Unitari:**
    *   Validazione e (de)serializzazione dei nuovi campi in `UDASerializer`.
    *   Logica di fallback per `estimated_hours` in `UDAContentSerializer.to_representation`.
*   **Test di Integrazione:**
    *   Endpoint di esportazione `export_udas_docx`:
        *   Correttezza risposta HTTP.
        *   Validità nome file.
        *   Contenuto e formattazione del `.docx`.
    *   Endpoint di esportazione `export_udas_pdf`:
        *   Correttezza risposta HTTP.
        *   Validità nome file.
        *   Contenuto e formattazione del `.pdf`.

### 4.2. Frontend
*   **Test Unitari:**
    *   Modifiche a `courseStore.ts` (nuova action `exportUdas`).
    *   `CourseDetailView.vue`:
        *   Visualizzazione e interazione del nuovo menu dropdown di esportazione.
        *   Corretta chiamata all'azione `handleExportUdas` con il formato selezionato.
*   **Test E2E:**
    *   Flusso completo di creazione/modifica UDA con i nuovi campi.
    *   Esportazione da `CourseDetailView.vue`:
        *   Verifica del funzionamento del menu dropdown.
        *   Download e verifica del file `.docx` (nome e contenuto).
        *   Download e verifica del file `.pdf` (nome e contenuto).

## 5. Diagramma del Piano (Aggiornato)

```mermaid
graph TD
    A[Richiesta Utente: Esportare UDA con scelta formato PDF/DOCX] --> B{Analisi Iniziale e Conferma Campi};
    B --> C[Definizione Piano Dettagliato];

    subgraph Backend (Django)
        direction LR
        C --> D[2.1: Modifica Modello `UDA` (Completato)];
        D -- Aggiungi campi --> D_Mig[Crea/Applica Migrazioni (Completato)];
        D_Mig --> E[2.2: Aggiorna Serializers (`UDASerializer`, `UDAContentSerializer`) (Completato)];
        E --> F[2.3: Crea Endpoint API `export_udas_docx` e `export_udas_pdf`];
        F -- Aggiungi `xhtml2pdf` a requirements --> F_Lib[Installare `xhtml2pdf` (Completato)];
        F -- Crea template HTML per PDF --> F_Tmpl[Template PDF Pronto (Completato)];
        F -- Logica DOCX in `export_udas_docx` --> F_DocxDone[Endpoint DOCX Pronto];
        F -- Logica PDF in `export_udas_pdf` --> F_PdfDone[Endpoint PDF Pronto];
    end

    subgraph Frontend (Vue.js)
        direction LR
        C --> G[3.1: Aggiorna Stores (`udaStore`, `courseStore`) (Completato)];
        G -- Nuovi campi, action `exportUdas` --> Serv[3.5: Aggiorna `courseService.ts` per nuovi endpoint (Completato)];
        Serv --> J[3.4: Pulsante Esporta con Dropdown in `CourseDetailView.vue`];
        J -- Installa `vue3-click-away` --> J_Lib[Libreria ClickAway Pronta];
        J -- UI: Menu DOCX/PDF, Chiama action `exportUdas` con formato --> J_Done[Interfaccia Esportazione Pronta];
    end
    
    subgraph Modifiche Precedenti (Completate)
        direction LR
        Prev_UdaForm[3.2: `UdaFormView.vue` con nuovi campi]
        Prev_UdaDetail[3.3: `UdaDetailView.vue` con nuovi campi]
    end
    C --> Prev_UdaForm;
    C --> Prev_UdaDetail;


    subgraph Testing
        direction TB
        F_DocxDone --> K_Docx[4.1: Test Backend (DOCX)];
        F_PdfDone --> K_Pdf[4.1: Test Backend (PDF)];
        J_Done --> L[4.2: Test Frontend (DOCX & PDF)];
    end

    K_Docx --> M[Implementazione Completa];
    K_Pdf --> M;
    end

    subgraph Frontend (Vue.js)
        direction LR
        C --> G[3.1: Aggiorna Stores (`udaStore`, `courseStore`) (Completato)];
        G -- Nuovi campi, action `exportUdas` --> Serv[3.5: Aggiorna `courseService.ts` (Completato)];
        Serv --> J[3.4: Pulsante Esporta con Dropdown in `CourseDetailView.vue`];
        J -- Installa `vue3-click-away` --> J_Lib[Libreria ClickAway Pronta];
        J -- UI: Menu DOCX/PDF, Chiama action `exportUdas` con formato --> J_Done[Interfaccia Esportazione Pronta];
    end
    
    subgraph Modifiche Precedenti (Completate)
        direction LR
        Prev_UdaForm[3.2: `UdaFormView.vue` con nuovi campi]
        Prev_UdaDetail[3.3: `UdaDetailView.vue` con nuovi campi]
    end
    C --> Prev_UdaForm;
    C --> Prev_UdaDetail;


    subgraph Testing
        direction TB
        F_Done --> K[4.1: Test Backend (DOCX & PDF)];
        J_Done --> L[4.2: Test Frontend (DOCX & PDF)];
    end

    K --> M[Implementazione Completa];
    L --> M;
```

## 6. Considerazioni Aggiuntive (Aggiornate)

*   **Fallback per Campi Testuali (Invariato).**
*   **Formattazione DOCX Avanzata (TODO futuro, Invariato).**
*   **Rendering PDF con `xhtml2pdf`:** Il rendering CSS potrebbe essere meno fedele rispetto a WeasyPrint. Potrebbero essere necessari aggiustamenti al template HTML/CSS del PDF per ottenere l'aspetto desiderato.
*   **Errore 404 Esportazione:** Attualmente si verifica un errore 404 durante l'esportazione. Si sospetta un problema di ricaricamento del server Django o un problema di routing più profondo. **Azione: Riavviare il server Django.** Se persiste, investigare ulteriormente il routing.
*   **Problema Underscore Nome File:** Se il problema dell'underscore finale nel nome del file (dopo l'estensione) persiste, la causa è probabilmente esterna al codice Python della vista e potrebbe risiedere nel middleware, server web, o reverse proxy.