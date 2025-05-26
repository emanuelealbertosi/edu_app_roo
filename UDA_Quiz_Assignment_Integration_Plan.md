# Piano di Implementazione: Integrazione Assegnazione Quiz in Vista Dettaglio UDA

**Obiettivo:** Permettere ai docenti di assegnare un Quiz Template (associato come contenuto a un'UDA) a studenti o gruppi direttamente dalla vista di dettaglio dell'UDA in `frontend-lessons`, replicando un'esperienza utente simile a quella dell'assegnazione delle lezioni e utilizzando una modale di assegnazione simile a quella presente in `frontend-teacher`.

**Applicazioni Coinvolte:**
*   `frontend-lessons` (modifiche principali)
*   `frontend-teacher` (come riferimento per la UI/UX della modale e per l'eventuale riutilizzo di logica/componenti)

---

### Fase 1: Modifiche a `frontend-lessons`

#### 1.1. Aggiornamento di `UdaContentItemRenderer.vue` ([`frontend-lessons/src/components/uda/UdaContentItemRenderer.vue`](frontend-lessons/src/components/uda/UdaContentItemRenderer.vue))

*   **Aggiungere Pulsante "Assegna Quiz":**
    *   All'interno del template, nella sezione dove vengono mostrati i pulsanti di azione per i contenuti (vicino ai pulsanti per le lezioni, linee 108-133), aggiungere una condizione per visualizzare un pulsante "Assegna Quiz" quando `content.content_type` è `UDAContentType.QUIZ` o `UDATemplateContentType.QUIZ_TEMPLATE`.
    *   Il pulsante dovrebbe avere un'icona appropriata (es. `PaperAirplaneIcon` o simile) e il testo "Assegna Quiz".
    *   Al click, questo pulsante dovrà emettere un nuovo evento, ad esempio `assign-quiz`, passando l'ID del `quiz_template` associato al contenuto.
    ```html
    <!-- Esempio di aggiunta pulsante (da adattare) -->
    <div v-if="isUDAContext && (content.content_type === UDAContentType.QUIZ || content.content_type === UDATemplateContentType.QUIZ_TEMPLATE) && content.quiz_template && !props.isEditing" class="flex items-center space-x-1.5">
        <button
            @click="emitAssignQuiz"
            type="button"
            class="p-1.5 border border-transparent shadow-sm rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-green-500"
            title="Assegna Quiz"
        >
            <PaperAirplaneIcon class="h-4 w-4" /> <!-- O altra icona -->
            <span class="ml-1 hidden sm:inline">Assegna Quiz</span>
        </button>
    </div>
    ```
*   **Definire l'evento `assign-quiz`:**
    *   Aggiungere `assign-quiz` all'array `emits` del componente.
    *   Creare una funzione `emitAssignQuiz` che emetta l'evento con l'ID del `quiz_template`.
    ```typescript
    // Nello script setup
    const emit = defineEmits([/*'altri eventi...',*/ 'assign-quiz']);

    const emitAssignQuiz = () => {
      if (isUDAContext.value && (props.content.content_type === UDAContentType.QUIZ || props.content.content_type === UDATemplateContentType.QUIZ_TEMPLATE) && (props.content as QuizUDAContent).quiz_template) {
        emit('assign-quiz', (props.content as QuizUDAContent).quiz_template);
      }
    };
    ```

#### 1.2. Aggiornamento di `UdaDetailView.vue` ([`frontend-lessons/src/views/uda/UdaDetailView.vue`](frontend-lessons/src/views/uda/UdaDetailView.vue))

*   **Gestire l'evento `assign-quiz`:**
    *   Nel template, sull'istanza di `UdaContentItemRenderer` (linea 163), aggiungere un listener per l'evento `@assign-quiz` che chiami una nuova funzione, ad esempio `handleAssignQuiz`.
    ```html
    <UdaContentItemRenderer
        ...
        @assign-quiz="handleAssignQuiz"
    ></UdaContentItemRenderer>
    ```
*   **Implementare `handleAssignQuiz`:**
    *   Questa funzione riceverà l'ID del `quiz_template`.
    *   Dovrà impostare delle variabili reattive per controllare l'apertura di una nuova modale di assegnazione quiz e per memorizzare l'ID del quiz template da assegnare.
    ```typescript
    // Nello script setup
    const isAssignQuizModalOpen = ref(false);
    const currentQuizTemplateIdToAssign = ref<number | null>(null);

    const handleAssignQuiz = (quizTemplateIdInput: number | string) => {
      console.log(`Assign quiz template with ID: ${quizTemplateIdInput} from UdaDetailView`);
      const idAsNumber = typeof quizTemplateIdInput === 'string' ? parseInt(quizTemplateIdInput, 10) : quizTemplateIdInput;

      if (isNaN(idAsNumber)) {
        console.error(`Invalid quizTemplateId: ${quizTemplateIdInput}. Cannot open assign modal.`);
        uiStore.addNotification({ message: 'ID template quiz non valido per l\'assegnazione.', type: 'error' });
        return;
      }
      currentQuizTemplateIdToAssign.value = idAsNumber;
      isAssignQuizModalOpen.value = true;
    };

    const closeAssignQuizModal = () => {
      isAssignQuizModalOpen.value = false;
      currentQuizTemplateIdToAssign.value = null;
    };

    const handleQuizAssignmentCompleted = () => {
      uiStore.addNotification({ message: 'Quiz assegnato con successo!', type: 'success', duration: 3000 });
      closeAssignQuizModal();
      // Eventuale logica di refresh dati se necessario
    };
    ```
*   **Importare e Registrare la Nuova Modale di Assegnazione Quiz:**
    *   Creare un nuovo componente modale (vedi Fase 1.3).
    *   Importarlo in `UdaDetailView.vue`.
    *   Aggiungerlo al template, controllandone la visibilità con `isAssignQuizModalOpen` e passando le props necessarie (ID del quiz template, ecc.).
    ```html
    <!-- Esempio nel template di UdaDetailView.vue -->
    <AssignQuizModal
        :show="isAssignQuizModalOpen"
        :quiz-template-id="currentQuizTemplateIdToAssign"
        @close="closeAssignQuizModal"
        @assignment-complete="handleQuizAssignmentCompleted"
    />
    ```

#### 1.3. Creazione del Componente Modale `AssignQuizModal.vue` (in `frontend-lessons`)

*   **Struttura Base:**
    *   Creare un nuovo file, ad esempio [`frontend-lessons/src/components/features/quiz/AssignQuizModal.vue`](frontend-lessons/src/components/features/quiz/AssignQuizModal.vue).
    *   Questo componente sarà molto simile nella struttura e funzionalità alla modale vista in [`frontend-teacher/src/views/QuizTemplatesView.vue`](frontend-teacher/src/views/QuizTemplatesView.vue) (sezioni da linea 386 a 476).
    *   Dovrà utilizzare un `BaseModal` o simile.
*   **Props:**
    *   `show` (boolean, per controllare la visibilità)
    *   `quizTemplateId` (number, l'ID del template quiz da assegnare)
*   **Emits:**
    *   `close` (quando la modale viene chiusa)
    *   `assignment-complete` (quando l'assegnazione ha successo)
*   **Logica Interna (da adattare da `QuizTemplatesView.vue` e `AssignLessonModal.vue`):**
    *   **Recupero Dati:**
        *   Recuperare la lista degli studenti utilizzando `lessonStore.fetchStudentsForTeacher()` (da `frontend-lessons/src/stores/lessons.ts`).
        *   Recuperare la lista dei gruppi utilizzando `lessonStore.fetchGroupsAction()` (da `frontend-lessons/src/stores/lessons.ts`).
        *   Recuperare i dettagli del `QuizTemplate` specifico usando `quizTemplateId` (tramite `quizStore` in `frontend-lessons`).
    *   **Tipi di Dati:**
        *   Utilizzare il tipo `Student` da `@/types/lezioni`.
        *   Utilizzare il tipo `StudentGroup` da `@/types/groups`.
    *   **Selezione Target:**
        *   Permettere la selezione tra "Studenti Singoli" e "Gruppi".
        *   Utilizzare (o ricreare componenti simili a) `StudentSelectionModal.vue` e `GroupSelectionModal.vue` per la selezione effettiva. Questi componenti potrebbero essere resi più generici e spostati in una directory `shared` o `common` se non lo sono già, per essere usati da entrambe le applicazioni. In alternativa, copiare la loro struttura/logica in `frontend-lessons`.
    *   **Data di Scadenza:**
        *   Includere un input per la data di scadenza (opzionale).
    *   **Logica di Assegnazione:**
        *   Chiamare le funzioni `assignQuizToStudent` e `assignQuizTemplateToGroup` dal nuovo servizio `frontend-lessons/src/services/quizService.ts`.
        *   Gestire stati di caricamento (`isAssigning`), errori (`assignmentError`), e messaggi di successo (`assignmentSuccess`).
*   **API Calls e Servizi:**
    *   Creare un nuovo file di servizio [`frontend-lessons/src/services/quizService.ts`](frontend-lessons/src/services/quizService.ts).
    *   Questo servizio importerà `apiClient` e definirà le funzioni `assignQuizToStudent` e `assignQuizTemplateToGroup`, basate sulla logica vista in `frontend-teacher/src/api/quizzes.ts`, per chiamare gli endpoint API del backend (es. `/education/teacher/quiz-templates/{templateId}/assign-student/` e `/education/teacher/quiz-templates/{templateId}/assign-group/`).

#### 1.4. Aggiornamenti agli Store (Pinia) in `frontend-lessons`

*   **`quizStore.ts` ([`frontend-lessons/src/stores/quizStore.ts`](frontend-lessons/src/stores/quizStore.ts)):**
    *   Assicurarsi che fornisca un metodo per recuperare i dettagli di un `QuizTemplate` tramite ID (es. `getQuizTemplateById(id)` e un'azione `fetchQuizTemplate(id)` se i dettagli non sono già caricati).
    *   Le azioni per l'assegnazione (`assignQuizToStudent`, `assignQuizTemplateToGroup`) saranno gestite direttamente dal componente modale tramite il `quizService.ts`, ma lo store potrebbe essere notificato per aggiornare stati locali se necessario (valutare in fase di implementazione).
*   **`lessonStore.ts` ([`frontend-lessons/src/stores/lessons.ts`](frontend-lessons/src/stores/lessons.ts)):**
    *   Verrà utilizzato per recuperare la lista degli studenti (tramite `fetchStudentsForTeacher()`) e dei gruppi (tramite `fetchGroupsAction()`) necessari per la modale di assegnazione. Non sono richieste modifiche a questo store se le funzioni esistono e sono adeguate.
*   **Non sono necessari `studentStore.ts` o `groupStore.ts` dedicati** per questa specifica funzionalità, dato il riutilizzo di `lessonStore` e la creazione di `quizService.ts`.

---

### Fase 2: Test e Rifinitura

*   **Test Funzionali:**
    *   Verificare che il pulsante "Assegna Quiz" appaia correttamente solo per i contenuti di tipo Quiz.
    *   Testare l'apertura e la chiusura della modale `AssignQuizModal`.
    *   Testare la selezione di studenti e gruppi.
    *   Testare l'impostazione della data di scadenza.
    *   Testare il processo di assegnazione a un singolo studente.
    *   Testare il processo di assegnazione a un gruppo.
    *   Verificare la gestione degli errori e dei messaggi di successo.
*   **Test UI/UX:**
    *   Assicurare che la modale sia visivamente coerente con il resto di `frontend-lessons`.
    *   Garantire un'esperienza utente fluida e intuitiva.

---

### Diagramma di Flusso (Mermaid)

```mermaid
graph TD
    A[Docente in UdaDetailView.vue] --> B{Contenuto UDA è un Quiz?};
    B -- Sì --> C[Mostra Pulsante "Assegna Quiz"];
    B -- No --> D[Nessun pulsante Assegna Quiz];
    C -- Click --> E[UdaContentItemRenderer emette 'assign-quiz' con quiz_template_id];
    E --> F[UdaDetailView.vue riceve 'assign-quiz'];
    F --> G[handleAssignQuiz(quiz_template_id)];
    G --> H[Apre AssignQuizModal.vue con quiz_template_id];
    H --> I{Seleziona Studenti/Gruppi e Data Scadenza};
    I -- Conferma Assegnazione --> J[AssignQuizModal chiama API assignQuizToStudent/Group];
    J -- Successo --> K[Modale emette 'assignment-complete'];
    J -- Errore --> L[Mostra errore in modale];
    K --> M[UdaDetailView riceve 'assignment-complete'];
    M --> N[Mostra notifica successo, chiude modale];
```
---