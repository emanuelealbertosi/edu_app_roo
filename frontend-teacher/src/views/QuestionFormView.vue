<template>
  <div class="question-form-view">
    <h1>{{ isEditing ? &#39;Modifica Domanda&#39; : &#39;Aggiungi Nuova Domanda&#39; }}</h1>
    <div v-if="isLoading" class="loading">Caricamento dati domanda...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>

    <form v-else @submit.prevent="saveQuestion">
      <div class="form-group">
        <label for="text">Testo Domanda:</label>
        <textarea id="text" v-model="textRef" required></textarea>
      </div>

      <div class="form-group">
        <label for="question_type">Tipo Domanda:</label>
        <select id="question_type" v-model="questionTypeRef" required>
          <option disabled value="">Seleziona un tipo</option>
          <option v-for="qType in questionTypes" :key="qType.value" :value="qType.value">
            {{ qType.label }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="order">Ordine:</label>
        <input type="number" id="order" v-model.number="orderRef" required min="0" />
      </div>

      <!-- TODO: Aggiungere gestione metadata (JSON editor?) -->

      <!-- Gestione Opzioni di Risposta -->
      <div v-if="showAnswerOptionsEditor" class="answer-options-section">
          <AnswerOptionsEditor
              :quiz-id="quizId!"
              :question-id="questionId!"
              :initial-options="initialAnswerOptions"
              :question-type="questionTypeRef"
              @options-saved="handleOptionsSaved"
              @error="handleOptionsError"
          />
      </div>

      <div class="form-actions">
        <button type="submit" :disabled="isSaving">
          {{ isSaving ? &#39;Salvataggio...&#39; : (isEditing ? &#39;Salva Modifiche&#39; : &#39;Crea Domanda&#39;) }}
        </button>
        <button type="button" @click="goBack">Annulla</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted } from 'vue'; // Aggiunto onMounted
import { useRoute, useRouter } from 'vue-router';
import { createQuestion, fetchQuestionDetails, updateQuestion, type QuestionPayload, fetchQuestions } from '@/api/questions';
import AnswerOptionsEditor from '@/components/AnswerOptionsEditor.vue';
import type { AnswerOption } from '@/api/questions';

const route = useRoute();
const router = useRouter();

// --- State Refs ---
const quizId = ref<number | null>(null);
const questionId = ref<number | null>(null);
const isLoading = ref(false);
const isSaving = ref(false);
const error = ref<string | null>(null);

// Form data refs
const textRef = ref('');
const questionTypeRef = ref('');
const orderRef = ref(0);
const metadataRef = ref<Record<string, any>>({});
const initialAnswerOptions = ref<AnswerOption[]>([]);

// --- Computed Properties ---
const isEditing = computed(() => !!questionId.value);
const showAnswerOptionsEditor = computed(() => isEditing.value); // Mostra sempre se in modifica

// --- Constants ---
const questionTypes = [
    { value: 'MC_SINGLE', label: 'Multiple Choice (Single Answer)' },
    { value: 'MC_MULTI', label: 'Multiple Choice (Multiple Answers)' },
    { value: 'TF', label: 'True/False' },
    { value: 'FILL_BLANK', label: 'Fill in the Blank' },
    { value: 'OPEN_MANUAL', label: 'Open Answer (Manual Grading)' },
];
const typesWithOptions: string[] = ['MC_SINGLE', 'MC_MULTI', 'TF'];

// --- Functions (definite prima dei watchers) ---

const goBack = () => {
    if (quizId.value) {
        router.push({ name: 'quiz-edit', params: { id: quizId.value.toString() } });
    } else {
        router.push({ name: 'quizzes' });
    }
};

const loadQuestionData = async (qId: number, questId: number) => {
    isLoading.value = true;
    error.value = null;
    try {
        console.log(`Fetching details for Quiz ${qId}, Question ${questId}`);
        const fetchedQuestion = await fetchQuestionDetails(qId, questId);
        console.log("Fetched question data:", JSON.stringify(fetchedQuestion));
        textRef.value = fetchedQuestion.text;
        questionTypeRef.value = fetchedQuestion.question_type;
        orderRef.value = fetchedQuestion.order;
        metadataRef.value = fetchedQuestion.metadata || {};
        initialAnswerOptions.value = fetchedQuestion.answer_options || [];
        console.log(`Assigned text: "${textRef.value}"`);
        await nextTick();
    } catch (err: any) {
        console.error(`Errore caricamento domanda ${questId}:`, err);
        error.value = `Errore caricamento domanda: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    } finally {
        isLoading.value = false;
    }
};

const saveQuestion = async () => {
    if (!quizId.value) {
        error.value = "Impossibile salvare: ID Quiz mancante.";
        return;
    }

    isSaving.value = true;
    error.value = null;

    const payload: QuestionPayload = {
        text: textRef.value,
        question_type: questionTypeRef.value,
        order: orderRef.value,
        metadata: metadataRef.value && Object.keys(metadataRef.value).length > 0 ? metadataRef.value : {},
    };

    try {
        if (isEditing.value && questionId.value) {
            await updateQuestion(quizId.value, questionId.value, payload);
            goBack(); // Torna indietro solo dopo update
        } else {
            const newQuestion = await createQuestion(quizId.value, payload);
            router.push({
                name: 'question-edit',
                params: {
                    quizId: quizId.value.toString(),
                    questionId: newQuestion.id.toString()
                }
            });
            // Non chiamare goBack() qui, la navigazione è già avvenuta
        }
    } catch (err: any) {
        console.error("Errore durante il salvataggio della domanda:", err);
        error.value = `Errore salvataggio domanda: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
        if (err.response?.data && typeof err.response.data === 'object') {
             console.log("Dettagli errore API:", err.response.data);
        }
    } finally {
        isSaving.value = false;
    }
};

const handleOptionsSaved = (savedOptions: AnswerOption[]) => {
    console.log("Opzioni salvate dal componente figlio:", savedOptions);
    initialAnswerOptions.value = savedOptions;
};

const handleOptionsError = (errorMessage: string) => {
    console.error("Errore dall&#39;editor opzioni:", errorMessage);
    error.value = errorMessage;
};

// Funzione per processare i parametri della rotta e caricare/resettare i dati
const processRouteParams = async (params: any, query: any) => {
  console.log("[QuestionFormView] START processRouteParams - params:", JSON.stringify(params), "query:", JSON.stringify(query)); // Log dettagliato
  const qIdParam = params.quizId;
  const questIdParam = params.questionId;

  // Reset error and IDs
  error.value = null;
  let currentQuizId: number | null = null;
  let currentQuestionId: number | null = null;

  // Gestisci quizId
  if (qIdParam) {
    const parsedQuizId = Number(qIdParam);
    if (!isNaN(parsedQuizId)) {
      currentQuizId = parsedQuizId;
    } else {
      console.error("ID Quiz non valido (non numerico):", qIdParam);
      error.value = "ID Quiz fornito nella URL non è valido.";
      return;
    }
  } else {
      error.value = "ID Quiz mancante nella rotta.";
      console.error("ID Quiz mancante nella rotta.");
      return;
  }
  quizId.value = currentQuizId; // Aggiorna ref solo dopo validazione

  // Gestisci questionId
  if (questIdParam) {
    const parsedQuestionId = Number(questIdParam);
    if (!isNaN(parsedQuestionId)) {
        currentQuestionId = parsedQuestionId;
        console.log("Question ID parsed:", currentQuestionId);
    } else {
        console.error("ID Domanda non valido (non numerico):", questIdParam);
        error.value = "ID Domanda fornito nella URL non è valido.";
        return;
    }
  } else {
      currentQuestionId = null;
      console.log("Question ID parsed as null (creation mode)");
  }
  questionId.value = currentQuestionId; // Aggiorna ref solo dopo validazione

  // Determina se caricare dati o resettare per creazione
  if (currentQuestionId) { // Modalità modifica
    console.log(`Loading data for Quiz ${currentQuizId}, Question ${currentQuestionId}`);
    await loadQuestionData(currentQuizId, currentQuestionId); // Ora loadQuestionData è definita
  } else { // Modalità creazione
    console.log(`Setting defaults for creation in Quiz ${currentQuizId}`);
    // Resetta i dati del form
    textRef.value = '';
    questionTypeRef.value = '';
    metadataRef.value = {};
    initialAnswerOptions.value = [];
    // Leggi l'ordine default dalla query
    const defaultOrderParam = query.defaultOrder;
    console.log(`[QuestionFormView] Received defaultOrder query param: ${defaultOrderParam}`); // Log the received param
    if (defaultOrderParam && !isNaN(Number(defaultOrderParam))) {
        orderRef.value = Number(defaultOrderParam);
    } else {
        // Fallback: calcola ordine basato sulle domande esistenti
        console.warn("Parametro defaultOrder mancante o non valido, calcolando ordine...");
        isLoading.value = true; // Mostra loading mentre calcoliamo
        try {
            // Assicurati che fetchQuestions sia importato
            const existingQuestions = await fetchQuestions(currentQuizId);
            orderRef.value = existingQuestions.length;
        } catch (err) {
            console.error(`Errore nel recupero domande per calcolare ordine default (Quiz ID: ${currentQuizId}):`, err);
            error.value = "Impossibile calcolare l'ordine predefinito.";
            orderRef.value = 0; // Fallback a 0 in caso di errore
        } finally {
            isLoading.value = false;
        }
    }
  }
};

// --- Watchers (definiti dopo le funzioni) ---

// Watch per reagire ai cambiamenti dei parametri della rotta
// Watch per reagire ai cambiamenti SUCCESSIVI dei parametri della rotta
watch(
  () => route.params,
  async (newParams, oldParams) => {
    // Esegui solo se i parametri rilevanti sono effettivamente cambiati e non è la chiamata iniziale
    const relevantParamsChanged = (newParams?.quizId !== oldParams?.quizId) || (newParams?.questionId !== oldParams?.questionId);
    if (relevantParamsChanged) {
        console.log("Route params changed AFTER mount, processing:", newParams);
        await processRouteParams(newParams, route.query);
    }
  },
  { deep: true } // Rimosso immediate: true
);

// onMounted per gestire il caricamento iniziale
onMounted(() => {
    console.log("[QuestionFormView] Component mounted. Initial route params:", JSON.stringify(route.params), "query:", JSON.stringify(route.query)); // Log dettagliato
    // Ritarda leggermente l'esecuzione per assicurarsi che tutte le funzioni siano definite
    nextTick(async () => {
        try {
            console.log("[QuestionFormView] Calling processRouteParams from onMounted...");
            await processRouteParams(route.params, route.query);
            console.log("[QuestionFormView] processRouteParams finished successfully.");
        } catch (mountError: any) {
            console.error("[QuestionFormView] CRITICAL ERROR during onMounted/processRouteParams:", mountError);
            error.value = `Errore critico durante l'inizializzazione: ${mountError.message}`;
        }
    });
});

// Watcher per il tipo di domanda
watch(questionTypeRef, (newType) => {
    console.log("Question type changed to:", newType);
    if (!typesWithOptions.includes(newType)) {
        initialAnswerOptions.value = [];
    }
});

</script>

<style scoped>
.question-form-view {
  padding: 20px;
  max-width: 700px;
  margin: auto;
}

/* Stili copiati e adattati da QuizFormView */
.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input[type="number"],
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

.form-group textarea {
  min-height: 150px;
  resize: vertical;
}

.form-actions {
  margin-top: 20px;
}

.form-actions button {
  padding: 10px 15px;
  margin-right: 10px;
  cursor: pointer;
  border-radius: 4px;
  border: none;
}

.form-actions button[type="submit"] {
  background-color: #4CAF50; /* Green */
  color: white;
}
.form-actions button[type="submit"]:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

.form-actions button[type="button"] {
  background-color: #f44336; /* Red */
  color: white;
}

.error-message {
  color: red;
  margin-top: 10px;
  font-weight: bold;
}

.loading {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}

.answer-options-section {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}
</style>