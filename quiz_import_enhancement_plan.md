# Piano di Aggiornamento: Importazione Avanzata Template Quiz da File

**Obiettivo:** Modificare la procedura esistente in `fe-teacher` per l'importazione di template quiz da file di testo, permettendo il caricamento e il riconoscimento automatico di tre tipi di domande: Risposta Multipla (scelta singola e multipla), Fill-in-the-Blank e Risposta Aperta.

**Riferimento Documento di Progettazione:** [`design_document.md`](design_document.md)

**1. Logica di Parsing del File di Testo (Backend)**

Il file di testo verrà processato riga per riga. La logica principale identificherà l'inizio di una nuova domanda e poi ne determinerà il tipo e le relative componenti.

**Input:** File di testo caricato dall'utente.
**Output:** Una struttura dati (es. lista di dizionari) rappresentante i `QuestionTemplate` e i loro `AnswerOptionTemplate` pronti per essere salvati nel database.

**Diagramma di Flusso del Parser (Logica Concettuale):**

```mermaid
graph TD
    A[Inizio Parsing File] --> B{Nuova Riga};
    B -- Sì --> C{Riga inizia con "numero."? (es. "1.")};
    B -- No --> B;
    C -- Sì --> D[Salva Domanda Precedente se esiste];
    D --> E[Inizia Nuova Domanda: Estrai testo domanda];
    E --> F{Testo Domanda contiene "___" (3+ underscore)?};
    F -- Sì (Fill-in-the-Blank) --> G[Tipo = fill_blank];
    G --> H[Leggi Righe Successive per Risposte "lettera)"];
    H --> I[Processa Risposte Fill-in-the-Blank (sequenziali, opzioni con ';;')];
    I --> B;
    F -- No --> J{Prossima Riga inizia con "lettera)"? (es. "A)")};
    J -- Sì (Risposta Multipla) --> K[Tipo = multiple_choice];
    K --> L[Leggi Righe Successive per Opzioni "lettera)"];
    L --> M[Processa Opzioni Risposta Multipla];
    M --> N{Determina single/multiple choice basato su numero di '*'};
    N --> B;
    J -- No (Risposta Aperta) --> O[Tipo = open_answer_manual];
    O --> B;
    C -- No (Riga non è inizio domanda) --> B;
    B -- Fine File --> R[Salva Ultima Domanda se esiste];
    R --> S[Fine Parsing];
```

**Dettagli del Parsing per Tipo di Domanda:**

*   **Identificazione Inizio Domanda:**
    *   Una riga che inizia con un numero seguito da un punto (es., `1.`, `2.`).
    *   Il testo della domanda è tutto ciò che segue `numero. ` su quella riga.

*   **Riconoscimento Tipo Domanda:**
    1.  **Fill-in-the-Blank (`fill_blank`):**
        *   **Condizione:** Il testo della domanda (estratto sopra) contiene una o più sequenze di tre o più underscore (`___`).
        *   **Risposte:** Le righe successive che iniziano con `lettera)` (es., `A)`, `B)`) sono le risposte per gli spazi vuoti.
            *   L'associazione è sequenziale: `A)` per il primo `___`, `B)` per il secondo, e così via.
            *   Ogni riga di risposta può contenere multiple alternative corrette separate da due punti e virgola (`;;`). Esempio: `A) uno;;due;;tre`.
            *   Il confronto delle risposte fornite dallo studente dovrà essere *case-insensitive*.
        *   **Modello Dati:**
            *   `QuestionTemplate.question_type = "fill_blank"`
            *   `QuestionTemplate.text = "Testo della domanda con ___"`
            *   `QuestionTemplate.metadata = {"blanks": [["rispostaA1", "rispostaA2"], ["rispostaB1"]], "case_sensitive": false}` (la struttura `blanks` è una lista di liste, dove ogni lista interna contiene le alternative per uno specifico blank).

    2.  **Risposta Multipla (`multiple_choice_single` / `multiple_choice_multiple`):**
        *   **Condizione:** La domanda *non* è `fill_blank` (non ci sono `___` nel testo) E le righe immediatamente successive alla domanda iniziano con `lettera)` (es. `A)`, `B)`).
        *   **Opzioni:** Ogni riga `lettera)` rappresenta un'opzione di risposta.
        *   **Correttezza:** Un asterisco (`*`) prima della lettera (es., `*A) Opzione corretta`) indica che l'opzione è corretta.
        *   **Distinzione Single/Multiple:**
            *   Se una sola opzione per la domanda ha `*`, allora `QuestionTemplate.question_type = "multiple_choice_single"`.
            *   Se due o più opzioni per la domanda hanno `*`, allora `QuestionTemplate.question_type = "multiple_choice_multiple"`.
        *   **Modello Dati:**
            *   `QuestionTemplate.question_type = "multiple_choice_single"` o `"multiple_choice_multiple"`
            *   `QuestionTemplate.text = "Testo della domanda?"`
            *   Per ogni opzione, creare un `AnswerOptionTemplate`:
                *   `AnswerOptionTemplate.text = "Testo opzione"`
                *   `AnswerOptionTemplate.is_correct = True` se c'è `*`, altrimenti `False`.
                *   `AnswerOptionTemplate.order` basato sull'ordine di apparizione.

    3.  **Risposta Aperta (`open_answer_manual`):**
        *   **Condizione:** La domanda non è né `fill_blank` né `multiple_choice` secondo le regole sopra. (Cioè, inizia con `numero.`, non ha `___` nel testo, e non ci sono righe `lettera)` immediatamente successive).
        *   **Modello Dati:**
            *   `QuestionTemplate.question_type = "open_answer_manual"`
            *   `QuestionTemplate.text = "Testo della domanda a risposta aperta."`
            *   Nessun `AnswerOptionTemplate` associato.

**Esempio di File Fornito dall'Utente e Parsing Atteso:**

```text
1. Qual è la capitale dell'Italia?
*A) Roma
B) Parigi
C) Berlino
2. Il gatto fa ___ ed il cane fa ___.
A) miao;;meow
B) bau;;woof
3. Descrivi la fotosintesi.
```

**Output Strutturato Atteso (concettuale):**

```python
[
    { # Domanda 1
        "text": "Qual è la capitale dell'Italia?",
        "question_type": "multiple_choice_single",
        "order": 1,
        "answer_options": [
            {"text": "Roma", "is_correct": True, "order": 1},
            {"text": "Parigi", "is_correct": False, "order": 2},
            {"text": "Berlino", "is_correct": False, "order": 3}
        ]
    },
    { # Domanda 2
        "text": "Il gatto fa ___ ed il cane fa ___.",
        "question_type": "fill_blank",
        "order": 2,
        "metadata": {
            "blanks": [
                ["miao", "meow"],  # Per il primo ___
                ["bau", "woof"]    # Per il secondo ___
            ],
            "case_sensitive": False
        }
    },
    { # Domanda 3
        "text": "Descrivi la fotosintesi.",
        "question_type": "open_answer_manual",
        "order": 3
    }
]
```

**2. Modifiche al Backend (Django)**

*   **View/Servizio di Importazione:**
    *   La view esistente (o una nuova) che gestisce l'upload del file in `fe-teacher` (probabilmente in `apps/education/views.py` o un modulo dedicato ai `QuizTemplate`) dovrà incorporare la nuova logica di parsing.
    *   Dopo il parsing, iterare sulla struttura dati risultante.
    *   Per ogni domanda:
        *   Creare un'istanza di `QuestionTemplate` ([`design_document.md:241`](design_document.md:241)) associata al `QuizTemplate` genitore.
        *   Salvare `text`, `question_type`, `order`, e `metadata` (per `fill_blank`).
        *   Se `multiple_choice`, creare e associare le istanze di `AnswerOptionTemplate` ([`design_document.md:250`](design_document.md:250)).
*   **Serializers (DRF):**
    *   Potrebbe essere necessario aggiornare o creare serializers per gestire la creazione di `QuestionTemplate` con i nuovi tipi e `metadata`, e la creazione batch di `AnswerOptionTemplate`.
*   **Modelli:**
    *   Assicurarsi che `QuestionTemplate.question_type` accetti i valori: `"multiple_choice_single"`, `"multiple_choice_multiple"`, `"fill_blank"`, `"open_answer_manual"`.
    *   Il campo `QuestionTemplate.metadata` (JSONB) è adatto per memorizzare la configurazione di `fill_blank`.

**3. Considerazioni sull'Interfaccia Utente (`fe-teacher`)**

*   L'interfaccia di upload del file rimane sostanzialmente la stessa.
*   È importante fornire un feedback chiaro all'utente in caso di errori di parsing del file (es. formato non riconosciuto, domanda incompleta). Indicare il numero di riga dell'errore sarebbe utile.
*   Dopo l'importazione, l'utente dovrebbe poter vedere il `QuizTemplate` popolato con le diverse tipologie di domande e poterle modificare/verificare come di consueto.

**4. Gestione Errori e Validazione**

*   Il parser deve essere robusto a file malformati e fornire messaggi di errore specifici.
*   Esempi di errori da gestire:
    *   Domanda `fill_blank` senza risposte fornite.
    *   Domanda `multiple_choice` senza opzioni.
    *   Numero di risposte per `fill_blank` non corrispondente al numero di `___`.
    *   Formato non valido per le righe di opzione/risposta.

**5. Test**

*   Saranno necessari test unitari approfonditi per la logica di parsing, coprendo tutti i casi validi e i possibili errori di formato.
*   Test di integrazione per verificare l'intero flusso di upload, parsing e salvataggio nel database.

**6. Riepilogo Modifiche Implementate**

*   **Backend (`apps/education/serializers.py` - `QuizTemplateUploadSerializer`):**
    *   Il metodo `_parse_quiz_text` è stato riscritto per:
        *   Identificare le domande in base a `numero.` (es. `1.`).
        *   Determinare il tipo di domanda:
            *   **Fill-in-the-Blank (`fill_blank`):** Se il testo della domanda contiene `___`. Le risposte (es. `A) risposta1;;risposta2`) sono associate sequenzialmente ai blank. I metadati vengono popolati con `{"blanks": [["risposta1", "risposta2"], ...], "case_sensitive": false}`.
            *   **Risposta Multipla (`multiple_choice_single` / `multiple_choice_multiple`):** Se ci sono opzioni `lettera)` e non è fill-in-the-blank. Un `*` prima della lettera indica la correttezza. Il tipo viene impostato su `multiple_choice_multiple` se ci sono più risposte corrette, altrimenti `multiple_choice_single`. Le opzioni vengono salvate in `answer_options`.
            *   **Risposta Aperta (`open_answer_manual`):** Se non rientra nei casi precedenti.
    *   Il metodo `create` è stato aggiornato per:
        *   Utilizzare `q_data['question_type']` (invece di `q_data['type']`).
        *   Popolare `QuestionTemplate.metadata` con `q_data.get('metadata', {})`.
        *   Iterare su `q_data.get('answer_options', [])` (invece di `q_data['options']`) per creare `AnswerOptionTemplate`.
*   **Modelli Django (`apps/education/models.py`):**
    *   Verificato che `QuestionType` include già tutti i tipi necessari (`MC_SINGLE`, `MC_MULTI`, `FILL_BLANK`, `OPEN_MANUAL`).
    *   Verificato che `QuestionTemplate.metadata` (JSONField) è adatto per la nuova struttura dei metadati `fill_blank`. Nessuna modifica ai modelli è stata necessaria per la funzionalità di importazione.
*   **Frontend (`frontend-teacher/src/components/QuizUploadForm.vue`):**
    *   Aggiunto un pulsante di aiuto con icona a forma di punto interrogativo (`<svg>`) accanto all'input per la selezione del file.
    *   Implementata una variabile reattiva `isHelpModalVisible` e i metodi `openHelpModal` e `closeHelpModal` per gestire la visibilità della modale.
    *   Aggiunta la struttura HTML per una modale che:
        *   Si apre al click sul pulsante di aiuto.
        *   Visualizza una spiegazione dettagliata del formato file richiesto, con esempi per Risposta Multipla (singola/multipla), Fill-in-the-Blank e Risposta Aperta.
        *   Include un pulsante "Chiudi" per nascondere la modale.
    *   Il pulsante di aiuto è stato posizionato nel template per essere visualizzato direttamente a destra dell'elemento di input del file.