# Piano di Implementazione: Revisione Tentativi Quiz

**Piano Proposto:**

1.  **Modifiche al Backend (Python/Django):**
    *   **Nuovo Endpoint API:** Creare un nuovo endpoint API (es. `/api/student/attempts/{attempt_id}/review/`) che restituisca i dettagli di un tentativo specifico, incluse le domande e le risposte date dallo studente per quel tentativo.
        *   **Dati da Restituire:** Per ogni domanda del tentativo:
            *   ID della domanda
            *   Testo della domanda (`Question.text`)
            *   Tipo di domanda (`Question.question_type`)
            *   Opzioni di risposta (se applicabile, da `AnswerOption.text`)
            *   La risposta data dallo studente (`StudentAnswer.selected_answers`)
            *   L'ordine della domanda nel quiz (`Question.order`)
        *   **Importante:** Questo endpoint NON deve restituire `is_correct` per le opzioni o per `StudentAnswer`.
    *   **Serializers:** Definire i serializers DRF necessari per questo nuovo endpoint.
        *   `StudentAnswerReviewSerializer` (o simile) per la risposta dello studente.
        *   `QuestionReviewSerializer` (o simile) per la domanda, che includa la risposta dello studente serializzata.
        *   `QuizAttemptReviewSerializer` (o simile) per l'intero tentativo, che includa una lista di `QuestionReviewSerializer`.
    *   **View API:** Implementare la view API che utilizzi questi serializers e recuperi i dati dal database basandosi su `attempt_id`. Assicurarsi che solo lo studente proprietario del tentativo possa accedervi.
    *   **Permessi:** Garantire che solo lo studente che ha effettuato il tentativo possa accedere a questi dati.

2.  **Modifiche allo Store (Pinia - `frontend-student/src/stores/quiz.ts` o un nuovo store dedicato):**
    *   **Nuova Azione:** Aggiungere un'azione per chiamare il nuovo endpoint API `/api/student/attempts/{attempt_id}/review/`.
        *   Questa azione prenderà `attempt_id` come parametro.
        *   Memorizzerà i dati del tentativo recuperato (domande e risposte date) nello stato dello store.
        *   Gestirà lo stato di caricamento e gli eventuali errori.
    *   **Nuovo Stato:** Aggiungere le proprietà di stato necessarie per memorizzare i dati del "review" del tentativo (es. `currentAttemptReview`, `isLoadingAttemptReview`, `attemptReviewError`).
    *   **Nuovi Getters (opzionale):** Getter per accedere facilmente ai dati del review.

3.  **Modifiche ai Componenti Frontend (Vue.js - `frontend-student`):**
    *   **Nuovo Componente Modale (`QuizAttemptReviewModal.vue`):**
        *   Creare un nuovo componente Vue per la modale che visualizzerà le domande e le risposte date.
        *   Questo componente riceverà `attempt_id` come prop.
        *   All'apertura, utilizzerà l'azione dello store per caricare i dati del review del tentativo.
        *   Visualizzerà un indicatore di caricamento mentre i dati vengono recuperati.
        *   Mostrerà un messaggio di errore se il caricamento fallisce.
        *   Itererà sulle domande del tentativo e visualizzerà:
            *   Il testo della domanda.
            *   La risposta data dallo studente (formattata in modo appropriato a seconda del `question_type`; es. per "fill-in-the-blank", la risposta dovrebbe essere inserita nello spazio vuoto del testo della domanda, come in "Testo domanda con [risposta_studente] inserita").
            *   L'ordine della domanda.
        *   **NON** dovrà indicare se le risposte sono corrette o meno.
        *   Avrà un pulsante "Chiudi".
    *   **Modifiche a `QuizList.vue`:**
        *   **Importare e Registrare la Nuova Modale:** Importare `QuizAttemptReviewModal.vue` e il componente `BaseModal` se non già presente per questo scopo.
        *   **Nuovo Stato per la Modale di Review:**
            *   `isReviewModalOpen = ref(false)`
            *   `attemptIdForReview = ref<number | null>(null)`
        *   **Nuova Funzione `openReviewModal(attemptId: number)`:**
            *   Imposta `attemptIdForReview.value = attemptId`.
            *   Imposta `isReviewModalOpen.value = true`.
        *   **Nuova Funzione `closeReviewModal()`:**
            *   Imposta `isReviewModalOpen.value = false`.
            *   Resetta `attemptIdForReview.value = null`.
        *   **Aggiungere il Pulsante "Rivedi Domande":**
            *   Nel template, all'interno del loop `v-for="attempt in quizzes"`, nel footer della card del quiz, aggiungere un nuovo pulsante.
            *   Questo pulsante sarà visibile solo se `attempt.status` è `COMPLETED` o `FAILED`.
            *   Il pulsante chiamerà `@click="openReviewModal(attempt.attempt_id)"`.
            *   Testo del pulsante: "Rivedi Domande".
            *   Stile del pulsante: simile agli altri pulsanti di azione, magari con un colore secondario.
        *   **Template della Nuova Modale:**
            *   Aggiungere l'istanza di `<BaseModal>` e al suo interno `<QuizAttemptReviewModal>` nel template di `QuizList.vue`, simile a come sono gestite le altre modali.
            *   Passare `:show="isReviewModalOpen"`, `@close="closeReviewModal"`, e `:attempt-id="attemptIdForReview"`.

4.  **Definizione Tipi TypeScript (`frontend-student/src/types/`):**
    *   Creare nuove interfacce per i dati restituiti dal nuovo endpoint API di review (es. `AttemptReviewData`, `QuestionReviewDetail`, `StudentAnswerReviewDetail`).

**Diagramma Mermaid (Flusso Frontend):**

```mermaid
graph TD
    A[QuizList.vue: Card Quiz (Completato/Fallito)] -- Click --> B(Pulsante "Rivedi Domande");
    B -- attempt_id --> C{openReviewModal(attempt_id)};
    C --> D[QuizList.vue: isReviewModalOpen = true, attemptIdForReview = attempt_id];
    D --> E[BaseModal mostra QuizAttemptReviewModal.vue];
    E -- attempt_id (prop) --> F[QuizAttemptReviewModal.vue];
    F -- onMounted/watch --> G{quizStore.fetchAttemptReview(attempt_id)};
    G --> H[API Call: GET /api/student/attempts/{attempt_id}/review/];
    H --> I{quizStore aggiorna stato con dati/errore};
    I --> J[QuizAttemptReviewModal.vue mostra domande e risposte date];
    J -- Click "Chiudi" --> K{closeReviewModal()};
    K --> L[QuizList.vue: isReviewModalOpen = false];
```

**Considerazioni Aggiuntive:**

*   **Stato "Fallito":** La logica attuale in `getAttemptStatusLabel` e `getStatusClass` gestisce già lo stato `FAILED`. Il nuovo pulsante "Rivedi Domande" dovrà essere visibile anche per questo stato.
*   **Performance:** Se un quiz ha molte domande, caricare tutti i dettagli potrebbe richiedere tempo. La modale dovrebbe avere un indicatore di caricamento chiaro.
*   **UI/UX della Modale di Review:** Assicurarsi che la visualizzazione delle domande e delle risposte date sia chiara e facile da leggere, specialmente per tipi di domande diversi (es. scelta multipla, testo libero).

---

## Stato Implementazione (Aggiornato il 26 Maggio 2025)

**La funzionalità è stata implementata come descritto sopra.**

**File Modificati/Creati:**

**Backend (`apps/education/`):**
*   [`serializers.py`](apps/education/serializers.py:2044): Aggiunti `StudentAnswerReviewSerializer`, `AnswerOptionReviewSerializer`, `QuestionReviewSerializer`, `QuizAttemptReviewSerializer`.
*   [`views.py`](apps/education/views.py:1823): Aggiunta la view `QuizAttemptReviewView`. (Import del serializer corretto alla linea 46).
*   [`urls.py`](apps/education/urls.py:69): Aggiunto il path per `QuizAttemptReviewView` (`student/attempts/<int:pk>/review/`). (Import della view corretto alla linea 16).

**Frontend (`frontend-student/src/`):**
*   [`types/education.ts`](frontend-student/src/types/education.ts:117): Aggiunte le interfacce `AnswerOptionReview`, `StudentAnswerReview`, `QuestionReview`, `QuizAttemptReviewData`.
*   [`stores/quiz.ts`](frontend-student/src/stores/quiz.ts):
    *   Aggiornata l'interfaccia `QuizState` e lo stato iniziale per includere `currentAttemptReviewData`, `loading.attemptReview`, `attemptReviewError`.
    *   Aggiunta l'azione `loadAttemptForReview`.
    *   Aggiornata l'azione `resetStore`.
    *   Corretto l'import di `QuizAttemptReviewData` da `types/education.ts`.
*   [`api/quiz.ts`](frontend-student/src/api/quiz.ts:229):
    *   Aggiunto il metodo `getAttemptReviewDetails` a `QuizService`.
    *   Importato `QuizAttemptReviewData` da `types/education.ts`.
*   [`components/quiz/QuizAttemptReviewModal.vue`](frontend-student/src/components/quiz/QuizAttemptReviewModal.vue): Nuovo componente creato per visualizzare la revisione del tentativo.
*   [`components/QuizList.vue`](frontend-student/src/components/QuizList.vue):
    *   Importato e registrato `QuizAttemptReviewModal`.
    *   Aggiunto stato e funzioni per gestire la modale di revisione.
    *   Aggiunto il pulsante "Rivedi Domande" alle card dei quiz completati/falliti.
    *   Incluso `<QuizAttemptReviewModal>` nel template.