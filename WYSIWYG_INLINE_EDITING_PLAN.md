# Piano di Implementazione: Editor WYSIWYG e Modifica Inline per Contenuti UDA

**Versione:** 1.0
**Data:** 15 Maggio 2025
**Riferimento Piano Esistente:** UDA_IMPLEMENTATION_PLAN.md

## 1. Introduzione

Questo documento descrive il piano per integrare un editor WYSIWYG (What You See Is What You Get) e la funzionalità di modifica inline per i campi di testo relativi a note e attività all'interno delle Unità Didattiche di Apprendimento (UDA) e dei Template UDA.

Le funzionalità chiave includono:
*   **Editor WYSIWYG:** Basato su TipTap.
*   **Formattazione Testo:** Grassetto, corsivo, sottolineato, hyperlink, elenchi puntati e numerati.
*   **Colore Testo:** Selezione da una palette predefinita di 8-10 colori.
*   **Modifica Inline:** Attivazione tramite click sul testo. Appariranno i pulsanti "Salva" e "Annulla" sotto l'area di modifica per confermare o scartare le modifiche.
*   **Sicurezza:** Sanitizzazione dell'HTML nel backend.

## 2. Impatto sul Backend (Django & Django REST Framework)

Le modifiche principali riguardano la gestione sicura dell'HTML generato dall'editor.

### 2.1. Modelli Django (`apps/uda/models.py`)
*   **Campi Esistenti:** I campi `TextField` come `UDAContent.note_content`, `UDAContent.activity_description`, `UDATemplateContent.note_template_content`, `UDATemplateContent.activity_template_description` rimangono invariati nella loro struttura.
*   **Azione - Sanitizzazione HTML:**
    *   Implementare la sanitizzazione dell'HTML sul backend prima di salvare qualsiasi contenuto proveniente dall'editor WYSIWYG.
    *   Utilizzare una libreria Python come `bleach`.
    *   Configurare `bleach` per permettere:
        *   Tag di base per la formattazione (es. `<strong>`, `<em>`, `<u>`, `<s>`, `<a>`, `<ul>`, `<ol>`, `<li>`). (Aggiunto `<s>` per il barrato)
        *   Attributi necessari (es. `href` per `<a>`, `target="_blank"`).
        *   Tag `<span>` con l'attributo `style`.
        *   Limitare le proprietà CSS permesse nell'attributo `style` esclusivamente a `color` (es. `style="color: #RRGGBB;"`) per i colori della palette predefinita.
    *   La sanitizzazione può essere integrata nei metodi `save()` dei modelli o nei serializer DRF.

### 2.2. Serializer (DRF) (`apps/uda/serializers.py`)
*   Nessuna modifica strutturale diretta richiesta. La logica di sanitizzazione (se implementata qui) dovrà essere aggiunta.

### 2.3. View API (DRF) (`apps/uda/views.py`)
*   Nessuna modifica diretta richiesta.

## 3. Impatto sul Frontend (frontend-lessons - Vue.js)

Questa sezione vedrà le modifiche più significative.

### 3.1. Installazione Dipendenze (npm/yarn)
*   Aggiungere le seguenti dipendenze al progetto `frontend-lessons`:
    *   `@tiptap/vue-3`
    *   `@tiptap/pm` (peer dependency)
    *   `@tiptap/starter-kit` (include bold, italic, strike, bulletList, orderedList, listItem, heading, blockquote, horizontalRule, paragraph, text, hardBreak)
    *   `@tiptap/extension-link` (per hyperlink)
    *   `@tiptap/extension-underline` (per sottolineato)
    *   `@tiptap/extension-text-style` (necessario per il colore)
    *   `@tiptap/extension-color` (per il colore del testo)

### 3.2. Componenti UI (`frontend-lessons/src/components/`)

*   **Nuovo Componente Wrapper: `WysiwygEditor.vue`**
    *   Creare un componente Vue riutilizzabile che incapsuli l'istanza di TipTap.
    *   **Props:** `modelValue` (per `v-model`), `editable` (boolean).
    *   **Events:** `update:modelValue`, `blur`.
    *   **Configurazione TipTap:**
        *   Utilizzare `useEditor` da `@tiptap/vue-3`.
        *   Estensioni da abilitare:
            *   `StarterKit.configure({...})` (configurare per escludere funzionalità non desiderate se necessario).
            *   `Link.configure({ openOnClick: false, autolink: true, linkOnPaste: true })`.
            *   `Underline`.
            *   `TextStyle` (necessario per `Color`).
            *   `Color`.
        *   Il contenuto dell'editor sarà gestito tramite `v-model` con il componente padre.
    *   **Barra degli Strumenti (Toolbar):**
        *   Implementare una barra degli strumenti fissa o flottante (usando `BubbleMenu` o `FloatingMenu` di TipTap se desiderato per un look più moderno, o una toolbar statica).
        *   Controlli per: Grassetto, Corsivo, Sottolineato, Link (con modale per inserire URL), Elenco Puntato, Elenco Numerato.
        *   **Selettore Colore:** Un set di 8-10 pulsanti/campioni di colore predefiniti (la palette esatta sarà definita in collaborazione). Cliccando su un colore, si applica al testo selezionato. Includere un'opzione per "rimuovere colore" (tornare al default).
    *   Stilizzare con Tailwind CSS.

*   **Aggiornamento Componenti di Visualizzazione per Inline Editing:**
    *   Componenti interessati: `UdaContentNoteDisplay.vue` (in `frontend-lessons/src/components/uda/content-display/`), `UdaContentActivityDisplay.vue` (in `frontend-lessons/src/components/uda/`), `NoteTemplateContentDisplay.vue` (in `frontend-lessons/src/components/uda/content-display/`), `ActivityTemplateContentDisplay.vue` (in `frontend-lessons/src/components/uda/content-display/`).
    *   **Logica di Funzionamento:**
        1.  Mantenere uno stato interno `isEditing` (default `false`).
        2.  Visualizzare il contenuto HTML (sanitizzato dal backend) usando `v-html` quando `isEditing` è `false`.
        3.  Al `click` sull'area del contenuto (quando `isEditing` è `false`):
            *   Impostare `isEditing` a `true`.
            *   Il template mostrerà ora il componente `WysiwygEditor.vue` invece del `div` con `v-html`.
            *   Passare il contenuto HTML corrente al `WysiwygEditor.vue` tramite `v-model`.
        4.  Sotto il componente `WysiwygEditor.vue` (visibile solo quando `isEditing` è `true`), mostrare due pulsanti: "Salva" e "Annulla".
            *   **Pulsante "Salva":**
                *   Recuperare il nuovo contenuto HTML dal `WysiwygEditor.vue`.
                *   Chiamare l'azione Pinia appropriata (es. `udaStore.updateContentInUda()`) per inviare il nuovo contenuto al backend.
                *   Dopo la conferma del salvataggio (o anche in caso di errore, gestendo il feedback utente), impostare `isEditing` a `false`.
                *   Il componente tornerà a visualizzare il contenuto aggiornato (o precedente in caso di errore non gestito a livello di UI) tramite `v-html`.
            *   **Pulsante "Annulla":**
                *   Impostare `isEditing` a `false`.
                *   Il contenuto dell'editor non viene salvato e il display torna a mostrare il contenuto originale (quello prima dell'attivazione della modifica). Potrebbe essere necessario assicurarsi che il `v-model` del `WysiwygEditor.vue` non abbia modificato una variabile che viene poi usata per ripristinare lo stato, o ricaricare il dato originale se necessario.

*   **Aggiornamento Componenti di Editing Esistenti (Modali e Form):**
    *   Componenti interessati: `UdaContentEditor.vue` (in `frontend-lessons/src/components/uda/`), `EditNoteContentModal.vue` (in `frontend-lessons/src/components/uda/`), `EditActivityContentModal.vue` (in `frontend-lessons/src/components/uda/`).
    *   Sostituire i `textarea` esistenti usati per `note_content`, `activity_description`, etc., con il nuovo componente `WysiwygEditor.vue`.
    *   La logica di salvataggio esistente (tramite pulsanti "Salva" nelle modali) rimarrà, ma il `v-model` sarà collegato al `WysiwygEditor.vue` che fornirà contenuto HTML.

### 3.3. Styling (Tailwind CSS)
*   Assicurare che l'output HTML di TipTap (es. `p`, `ul`, `li`, `strong`, `em`, `u`, `a`, `span[style*="color"]`) sia stilizzato in modo coerente con il resto dell'applicazione.
*   Utilizzare il plugin `@tailwindcss/typography` se non già in uso, o definire stili personalizzati per gli elementi "prose".
*   Stilizzare la barra degli strumenti e l'area di editing del `WysiwygEditor.vue`.

### 3.4. Store Management (Pinia) (`frontend-lessons/src/stores/`)
*   Nessuna modifica strutturale diretta richiesta agli state o actions esistenti, poiché continueranno a gestire stringhe (ora HTML invece di testo semplice).

## 4. Testing

### 4.1. Backend (Django)
*   **Test Unitari:**
    *   Testare approfonditamente la logica di sanitizzazione dell'HTML:
        *   Verificare che i tag (incluso `<s>` per il barrato) e gli attributi permessi siano conservati.
        *   Verificare che i tag e gli attributi non permessi siano rimossi o resi innocui.
        *   Verificare specificamente la gestione degli stili `color` (permettendo solo quelli validi) e bloccando altre proprietà CSS.

### 4.2. Frontend (Vue.js - Vitest/Jest & Playwright/Cypress)
*   **Test Unitari:**
    *   Testare il componente `WysiwygEditor.vue`: interazioni con la toolbar, corretta emissione di evento `update:modelValue`, inizializzazione con contenuto.
    *   Testare la logica di attivazione/disattivazione dell'editing inline nei componenti di visualizzazione (`*Display.vue`), inclusa l'interazione con i pulsanti "Salva" e "Annulla".
    *   Verificare che le chiamate allo store Pinia vengano effettuate con il contenuto HTML corretto al momento del salvataggio (sia da inline editing che da modali).
*   **Test E2E (End-to-End):**
    *   Simulare flussi utente completi:
        *   Creazione di una nota/attività utilizzando tutte le funzionalità di formattazione WYSIWYG (bold, italic, underline, strike-through, link, liste, colori).
        *   Modifica inline di una nota/attività: attivazione, applicazione di varie formattazioni, salvataggio tramite pulsante "Salva", annullamento tramite pulsante "Annulla".
        *   Verificare la corretta visualizzazione del contenuto formattato in tutte le viste rilevanti.
        *   Testare l'inserimento di HTML potenzialmente dannoso per assicurarsi che la sanitizzazione (frontend e backend) funzioni.

## 5. Aggiornamenti al Documento UDA_IMPLEMENTATION_PLAN.md

Le seguenti sezioni del piano di implementazione UDA esistente dovranno essere aggiornate per riflettere queste modifiche:
*   **Sezione 2.2 (Modelli Django):** Aggiungere il task per la sanitizzazione HTML.
*   **Sezione 3.4 (Componenti UI):** Dettagliare la creazione di `WysiwygEditor.vue`, la modifica dei componenti `UdaContent*Display.vue`, `UdaContentEditor.vue`, e delle modali di editing. Aggiungere il task per l'installazione delle dipendenze TipTap.
*   **Sezione 4.1 (Backend Testing):** Aggiungere test specifici per la sanitizzazione.
*   **Sezione 4.2 (Frontend Testing):** Aggiungere test unitari ed E2E per le nuove funzionalità WYSIWYG e di inline editing.
*   **Sezione 5 (Considerazioni Aggiuntive):** Menzionare la scelta di TipTap, la strategia di sanitizzazione, e la palette di colori predefinita.
*   **Sezione 6 (Stima di Sviluppo):** Le stime dovranno essere riviste per includere il lavoro aggiuntivo.