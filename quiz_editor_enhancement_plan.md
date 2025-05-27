# Piano di Progettazione: Miglioramenti Editor Quiz e Visualizzazione Dettagli Domande

**Data:** 27 Maggio 2025
**Stato:** COMPLETATO

**Obiettivi Principali:**

1.  **Integrare l'editor WYSIWYG (TipTap) nel form di creazione/modifica delle domande quiz** in `fe-teacher`.
2.  **Assicurare che il testo formattato (HTML) della domanda venga salvato correttamente** nel backend.
3.  **Visualizzare correttamente il testo formattato della domanda** durante lo svolgimento del quiz in `fe-student`.
4.  **Nell'elenco delle domande in `fe-teacher` (pagina di modifica del quiz template), visualizzare:**
    *   Il numero di opzioni di risposta impostate (es. "Opzioni: N").
    *   Un'indicazione dello stato di configurazione delle risposte corrette (es. "Risposte corrette: OK/Mancanti").
    *   Un'indicazione dello stato di configurazione per le domande `fill_blank` (es. "Fill-blank: OK/Mancanti").

**Diagramma di Flusso Generale:**

```mermaid
graph TD
    subgraph fe-teacher
        A[QuizTemplateFormView.vue] -- Modifica Testo Domanda --> B(Integra WysiwygEditor.vue in QuestionTemplateFormView.vue);
        B -- Salva Domanda (HTML) --> C[API Call];
        A -- Visualizza Elenco Domande --> D(TemplateQuestionEditor.vue);
        D -- Mostra Info Aggiuntive --> E[Dati da API];
    end

    subgraph Backend (Django DRF)
        C --> F[apps/education/serializers.py: QuestionTemplateSerializer];
        F -- Processa e Salva HTML nel DB --> G[Modello QuestionTemplate];
        F -- Aggiunge Campi Calcolati (num_options, status_corrette, status_fillblank) --> E;
    end

    subgraph fe-student
        H[Studente apre Quiz] --> I[API Call per Domanda];
        I --> J[apps/education/serializers.py: QuestionSerializer];
        J -- Restituisce Domanda con Testo HTML --> K[QuizAttemptView.vue];
        K -- Renderizza Testo Domanda con v-html e DOMPurify --> L[Visualizzazione Domanda Formattata];
        K -- Passa dati domanda a --> M[Componente Specifico per Tipo Domanda (es. MultipleChoiceSingleQuestion.vue)];
    end
```

**Passaggi Dettagliati e File Coinvolti:**

**Fase 1: Backend (Modifiche API e Serializers)**

*   **File da Modificare:** [`apps/education/serializers.py`](apps/education/serializers.py:1)
    *   **Target Serializer:** `QuestionTemplateSerializer`
    *   **Azioni:**
        1.  **Conferma Gestione HTML per `text`**: Il campo `text` standard dovrebbe già accettare e salvare l'HTML. Non sono previste modifiche per *abilitare* il salvataggio dell'HTML.
        2.  **Aggiungere `num_answer_options`**:
            *   Tipo: `serializers.SerializerMethodField()`
            *   Logica: `obj.answer_option_templates.count()`
        3.  **Aggiungere `correct_answers_status`**:
            *   Tipo: `serializers.SerializerMethodField()`
            *   Logica:
                *   Per `MC_SINGLE`, `TF`: "OK" se esiste almeno una `is_correct=True`, altrimenti "MISSING".
                *   Per `MC_MULTI`: "OK" se esiste almeno una `is_correct=True`, altrimenti "MISSING".
                *   Altri tipi: "N/A".
        4.  **Aggiungere `fill_blank_status`**:
            *   Tipo: `serializers.SerializerMethodField()`
            *   Logica:
                *   Per `FILL_BLANK`: "OK" se `obj.metadata` contiene chiavi specifiche per la configurazione fill-blank (es. `text_with_placeholders`, `blanks` non vuoto), altrimenti "MISSING".
                *   Altri tipi: "N/A".
        5.  Aggiungere i nuovi campi (`num_answer_options`, `correct_answers_status`, `fill_blank_status`) all'elenco `fields` nella `Meta` class del `QuestionTemplateSerializer`.
    *   **Target Serializer (Verifica):** `QuestionSerializer`
    *   **Azioni:**
        1.  **Conferma Gestione HTML per `text`**: Il campo `text` standard dovrebbe già accettare e salvare/restituire l'HTML. La logica esistente in `to_representation` per i metadati `FILL_BLANK` dovrà essere testata con contenuto HTML nel campo `text`.

**Fase 2: Frontend Teacher (`fe-teacher`)**

1.  **Integrazione Editor WYSIWYG:**
    *   **File da Modificare:** [`frontend-teacher/src/views/QuestionTemplateFormView.vue`](frontend-teacher/src/views/QuestionTemplateFormView.vue:1)
    *   **Azione:**
        *   Importare il componente [`WysiwygEditor.vue`](frontend-lessons/src/components/common/WysiwygEditor.vue:1) (da `frontend-lessons` o da una directory condivisa).
        *   Sostituire l'elemento `<textarea>` (attualmente associato a `questionData.text`) con `<WysiwygEditor v-model="questionData.text" />`.
    *   **Considerazione sulla Condivisione Componente:** Valutare se spostare [`WysiwygEditor.vue`](frontend-lessons/src/components/common/WysiwygEditor.vue:1) in una directory di componenti comuni accessibile sia da `frontend-lessons` che da `frontend-teacher` per evitare duplicazioni. Se non esiste una tale struttura, potrebbe essere necessario crearla o, come soluzione temporanea, copiare il componente.

2.  **Visualizzazione Informazioni Aggiuntive nell'Elenco Domande:**
    *   **File da Modificare:** [`frontend-teacher/src/components/TemplateQuestionEditor.vue`](frontend-teacher/src/components/TemplateQuestionEditor.vue:1)
    *   **Azione:**
        *   Modificare il template del componente per visualizzare i nuovi campi (`num_answer_options`, `correct_answers_status`, `fill_blank_status`) che saranno disponibili nella prop `question` (ricevuta da `QuizTemplateFormView.vue` dopo l'aggiornamento dell'API).
        *   Esempio di visualizzazione:
            *   `<span>Opzioni: {{ question.num_answer_options }}</span>`
            *   `<span>Corrette: {{ question.correct_answers_status }}</span>` (con logica condizionale per `N/A`)
            *   `<span>Fill-Blank: {{ question.fill_blank_status }}</span>` (con logica condizionale per `N/A` e solo se `question.question_type === 'fill_blank'`)

**Fase 3: Frontend Student (`fe-student`)**

1.  **Visualizzazione Testo Domanda Formattato (HTML):**
    *   **File da Modificare:** [`frontend-student/src/views/QuizAttemptView.vue`](frontend-student/src/views/QuizAttemptView.vue:1)
    *   **Azione:**
        *   Nel template di `QuizAttemptView.vue`, individuare il punto in cui viene visualizzato il testo della domanda corrente (probabilmente `currentQuestion.value.text`).
        *   Utilizzare la direttiva `v-html` per renderizzare questo testo: `<div v-html="sanitizedQuestionText"></div>`.
        *   Aggiungere un metodo o una computed property `sanitizedQuestionText` che utilizzi `DOMPurify` per sanitizzare `currentQuestion.value.text` prima di passarlo a `v-html`.
            ```typescript
            import DOMPurify from 'dompurify';

            // All'interno dello script setup
            const sanitizedQuestionText = computed(() => {
              if (currentQuestion.value?.text) {
                return DOMPurify.sanitize(currentQuestion.value.text);
              }
              return '';
            });
            ```
        *   Assicurarsi che `DOMPurify` sia installato come dipendenza (`npm install dompurify` o `yarn add dompurify`) e importato correttamente.

**Considerazioni Generali:**

*   **Styling:** Verificare e, se necessario, adattare gli stili CSS per l'editor WYSIWYG e per il contenuto HTML renderizzato in modo che siano coerenti con il design dell'applicazione.
*   **Test:** Prevedere test approfonditi per:
    *   Funzionalità dell'editor WYSIWYG.
    *   Corretto salvataggio e recupero del contenuto HTML.
    *   Corretta visualizzazione dei campi aggiuntivi nell'elenco domande.
    *   Corretta visualizzazione e sanitizzazione dell'HTML in `fe-student`.
    *   Nessuna regressione nelle funzionalità esistenti dei quiz.

**Log delle Modifiche (Completamento):**

*   **27 Maggio 2025:**
    *   **Backend:**
        *   Aggiornato `QuestionTemplateSerializer` in [`apps/education/serializers.py`](apps/education/serializers.py:1) con i campi `num_answer_options`, `correct_answers_status`, e `fill_blank_status`.
    *   **Frontend Teacher (`fe-teacher`):**
        *   Copiato `WysiwygEditor.vue` da `frontend-lessons` a [`frontend-teacher/src/components/common/WysiwygEditor.vue`](frontend-teacher/src/components/common/WysiwygEditor.vue:1).
        *   Modificato [`frontend-teacher/src/views/QuestionTemplateFormView.vue`](frontend-teacher/src/views/QuestionTemplateFormView.vue:1) per utilizzare `WysiwygEditor`.
        *   Modificato [`frontend-teacher/src/components/TemplateQuestionEditor.vue`](frontend-teacher/src/components/TemplateQuestionEditor.vue:1) per visualizzare le informazioni aggiuntive.
    *   **Frontend Student (`fe-student`):**
        *   Modificato [`frontend-student/src/views/QuizAttemptView.vue`](frontend-student/src/views/QuizAttemptView.vue:1) per importare `DOMPurify`, aggiungere `sanitizedQuestionText` computed property, e usare `v-html` per il testo della domanda.

Questo piano ha fornito una guida chiara per l'implementazione delle modifiche richieste e tutte le attività sono state completate.