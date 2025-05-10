<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-2xl font-semibold text-gray-900 mb-6">
      {{ isEditing ? 'Modifica Domanda' : 'Aggiungi Nuova Domanda' }}
      <span v-if="quizId" class="text-base font-normal text-gray-600 ml-2">(per Quiz ID: {{ quizId }})</span>
    </h1>

    <!-- Success Message -->
    <div v-if="successMessage" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-6" role="alert">
      <span class="block sm:inline">{{ successMessage }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-10">
      <p class="text-gray-500">Caricamento dati domanda...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <!-- Form Container -->
    <form v-else @submit.prevent="saveQuestion" class="space-y-6 bg-white p-8 rounded-lg shadow-md max-w-4xl mx-auto">
      <!-- Question Text -->
      <div>
        <label for="text" class="block text-sm font-medium text-gray-700 mb-1">Testo Domanda</label>
        <textarea id="text" v-model="questionData.text" required rows="4"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"></textarea>
      </div>

      <!-- Question Type -->
      <div>
        <label for="question_type" class="block text-sm font-medium text-gray-700 mb-1">Tipo Domanda</label>
        <select id="question_type" v-model="questionData.question_type" required
                class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
          <option disabled value="">Seleziona un tipo</option>
          <option v-for="qType in questionTypes" :key="qType.value" :value="qType.value">
            {{ qType.label }}
          </option>
        </select>
      </div>

      <!-- Order -->
      <div>
        <label for="order" class="block text-sm font-medium text-gray-700 mb-1">Ordine</label>
        <input type="number" id="order" v-model.number="questionData.order" required min="0"
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
        <p class="mt-1 text-xs text-gray-500">Ordine della domanda all'interno del quiz (0, 1, 2...).</p>
      </div>

      <!-- TODO: Aggiungere gestione metadata (JSON editor o campi specifici?) -->
      <!-- <div class="pt-6 border-t border-gray-200">
        <h3 class="text-lg font-medium text-gray-900">Metadati (Opzionale)</h3>
         Qui si potrebbe inserire un editor JSON o campi specifici
      </div> -->

      <!-- Answer Options Section (conditionally rendered) -->
      <div v-if="showAnswerOptionsEditor" class="pt-6 border-t border-gray-200">
          <h2 class="text-lg font-medium text-gray-900 mb-4">Opzioni di Risposta</h2>
          <AnswerOptionsEditor
              :quiz-id="quizId!"
              :question-id="questionId!"
              :initial-options="initialAnswerOptions"
              :question-type="questionData.question_type"
              @options-saved="handleOptionsSaved"
              @error="handleOptionsError"
          />
      </div>
      <div v-else-if="isEditing && !showAnswerOptionsEditor" class="pt-6 border-t border-gray-200">
          <p class="text-sm text-gray-500 italic">Questo tipo di domanda non richiede opzioni di risposta predefinite.</p>
      </div>
       <div v-else-if="!isEditing" class="pt-6 border-t border-gray-200">
          <p class="text-sm text-gray-500 italic">Salva la domanda prima di poter aggiungere le opzioni di risposta (se applicabile).</p>
      </div>

     <!-- FillBlankQuestionEditor Section (conditionally rendered) -->
     <div v-if="showFillBlankEditor" class="pt-6 border-t border-gray-200">
       <h2 class="text-lg font-medium text-gray-900 mb-4">Configurazione Domanda Fill in the Blank</h2>
       <FillBlankQuestionEditor
         :initial-question-text="questionData.text"
         :initial-metadata="questionData.metadata as FillBlankMetadata | null"
         @update:metadata="handleFillBlankMetadataUpdate"
       />
       <p class="mt-2 text-xs text-gray-500 italic">
         Il testo della domanda inserito sopra verrà utilizzato da questo editor.
         Assicurati di definire gli spazi vuoti (usando '___') nel testo principale della domanda.
       </p>
     </div>

     <!-- Form Actions -->
     <div class="flex justify-end space-x-3 pt-6 border-t border-gray-200 mt-6">
        <button type="button" @click="goBack"
                class="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
          Annulla
        </button>
        <button type="submit" :disabled="isSaving"
                :class="['py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
                         isSaving ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700']">
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche Domanda' : 'Crea Domanda') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createQuestion, fetchQuestionDetails, updateQuestion, type QuestionPayload, fetchQuestions } from '@/api/questions';
import AnswerOptionsEditor from '@/components/AnswerOptionsEditor.vue';
import FillBlankQuestionEditor, { type FillBlankMetadata } from '@/components/questions/FillBlankQuestionEditor.vue';
import type { AnswerOption, Question } from '@/api/questions';

const route = useRoute();
const router = useRouter();

// --- State Refs ---
const quizId = ref<number | null>(null);
const questionId = ref<number | null>(null);
const isLoading = ref(false);
const isSaving = ref(false);
const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);

// Form data refs - Usiamo reactive per raggruppare i dati del form
const questionData = reactive({
    text: '',
    question_type: '',
    order: 0,
    metadata: {} as Record<string, any>,
});
const initialAnswerOptions = ref<AnswerOption[]>([]);

// --- Computed Properties ---
const isEditing = computed(() => !!questionId.value);
// Mostra l'editor opzioni solo se in modifica E il tipo domanda le supporta
const showAnswerOptionsEditor = computed(() =>
    isEditing.value && questionId.value && typesWithOptions.includes(questionData.question_type)
);

const showFillBlankEditor = computed(() => questionData.question_type === 'fill_blank');


// --- Constants ---
const questionTypes = [
    { value: 'MC_SINGLE', label: 'Multiple Choice (Single Answer)' },
    { value: 'MC_MULTI', label: 'Multiple Choice (Multiple Answers)' },
    { value: 'TF', label: 'True/False' },
    { value: 'fill_blank', label: 'Fill in the Blank' },
    { value: 'OPEN_MANUAL', label: 'Open Answer (Manual Grading)' },
];
const typesWithOptions: string[] = ['MC_SINGLE', 'MC_MULTI', 'TF'];

// --- Functions ---

const goBack = () => {
    if (quizId.value) {
        // Torna alla vista di modifica del quiz
        router.push({ name: 'quiz-edit', params: { id: quizId.value.toString() } });
    } else {
        // Fallback se quizId non è disponibile (improbabile ma sicuro)
        router.push({ name: 'quizzes' });
    }
};

// Funzione per caricare i dati della domanda specifica
const loadQuestionData = async (qId: number, questId: number) => {
    isLoading.value = true;
    error.value = null;
    try {
        console.log(`[QuestionFormView] Fetching details for Quiz ${qId}, Question ${questId}`);
        const fetchedQuestion = await fetchQuestionDetails(qId, questId);
        console.log("[QuestionFormView] Fetched question data:", JSON.stringify(fetchedQuestion));
        questionData.text = fetchedQuestion.text;
        // Normalizza question_type a minuscolo per coerenza con le definizioni interne
        questionData.question_type = fetchedQuestion.question_type ? fetchedQuestion.question_type.toLowerCase() : '';
        questionData.order = fetchedQuestion.order;
        questionData.metadata = fetchedQuestion.metadata || {};
        initialAnswerOptions.value = fetchedQuestion.answer_options || [];
        console.log(`[QuestionFormView] Assigned text: "${questionData.text}"`);
        console.log(`[QuestionFormView] questionData.question_type (normalized): "${questionData.question_type}"`);
        console.log(`[QuestionFormView] questionData.metadata:`, JSON.stringify(questionData.metadata));
        await nextTick();
        console.log(`[QuestionFormView] showFillBlankEditor computed: ${showFillBlankEditor.value}`);
    } catch (err: any) {
        console.error(`Errore caricamento domanda ${questId}:`, err);
        error.value = `Errore caricamento domanda: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
        questionData.text = '';
        questionData.question_type = '';
        questionData.order = 0;
        questionData.metadata = {};
        initialAnswerOptions.value = [];
    } finally {
        isLoading.value = false;
    }
};

// Funzione per resettare il form per la creazione
const resetFormForCreation = async (qId: number, defaultOrderQuery: any) => {
    questionData.text = '';
    questionData.question_type = '';
    questionData.metadata = {};
    initialAnswerOptions.value = [];
    questionId.value = null;

    const defaultOrderParam = defaultOrderQuery;
    console.log(`[QuestionFormView] Received defaultOrder query param: ${defaultOrderParam}`);
    if (defaultOrderParam && !isNaN(Number(defaultOrderParam))) {
        questionData.order = Number(defaultOrderParam);
    } else {
        console.warn("Parametro defaultOrder mancante o non valido, calcolando ordine...");
        isLoading.value = true;
        try {
            // NOTA: fetchQuestions qui è solo per calcolare l'ordine, non per popolare la lista
            const existingQuestions = await fetchQuestions(qId);
            questionData.order = existingQuestions.length;
        } catch (err) {
            console.error(`Errore nel recupero domande per calcolare ordine default (Quiz ID: ${qId}):`, err);
            error.value = "Impossibile calcolare l'ordine predefinito.";
            questionData.order = 0;
        } finally {
            isLoading.value = false;
        }
    }
     console.log(`[QuestionFormView] Order set to: ${questionData.order}`);
};


const saveQuestion = async () => {
    if (!quizId.value) {
        error.value = "Impossibile salvare: ID Quiz mancante.";
        return;
    }

    isSaving.value = true;
    error.value = null;
    successMessage.value = null;

    const payload: QuestionPayload = {
        text: questionData.text,
        question_type: questionData.question_type,
        order: questionData.order,
        metadata: questionData.metadata && Object.keys(questionData.metadata).length > 0 ? questionData.metadata : {},
    };

    try {
        let savedQuestion: Question | null = null;
        if (isEditing.value && questionId.value) {
            savedQuestion = await updateQuestion(quizId.value, questionId.value, payload);
            successMessage.value = "Domanda aggiornata con successo!";
            // Ricarica i dati della domanda specifica dopo il salvataggio
            await loadQuestionData(quizId.value, questionId.value);
        } else {
            savedQuestion = await createQuestion(quizId.value, payload);
            successMessage.value = "Domanda creata con successo!";
            // Aggiorna l'URL per riflettere la modalità modifica della nuova domanda
            router.replace({
                name: 'question-edit',
                params: {
                    quizId: quizId.value.toString(),
                    questionId: savedQuestion.id.toString()
                }
            });
            // Aggiorna lo stato locale per riflettere la nuova domanda
            questionId.value = savedQuestion.id;
            initialAnswerOptions.value = [];
        }

        // Nascondi messaggio dopo timeout
        setTimeout(() => { successMessage.value = null; }, 3000);

    } catch (err: any) {
        console.error("Errore durante il salvataggio della domanda:", err);
        if (err.response?.data && typeof err.response.data === 'object') {
             const errorDetails = Object.entries(err.response.data)
                 .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
                 .join('; ');
             error.value = `Errore salvataggio: ${errorDetails}`;
        } else {
             error.value = `Errore salvataggio domanda: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
        }
    } finally {
        isSaving.value = false;
    }
};

const handleOptionsSaved = (savedOptions: AnswerOption[]) => {
    console.log("Opzioni salvate dal componente figlio:", savedOptions);
    initialAnswerOptions.value = savedOptions;
    successMessage.value = "Opzioni salvate con successo.";
    setTimeout(() => { successMessage.value = null; }, 2000);
};

const handleOptionsError = (errorMessage: string) => {
    console.error("Errore dall'editor opzioni:", errorMessage);
    error.value = errorMessage;
};

const handleFillBlankMetadataUpdate = (metadata: FillBlankMetadata | null) => {
  if (metadata) {
    questionData.metadata = { ...questionData.metadata, ...metadata }; // Unisci per preservare altri metadati se presenti
    console.log('[QuestionFormView] FillBlank metadata updated:', JSON.stringify(questionData.metadata));
  } else {
    // Se i metadati sono null (es. testo domanda cambiato e blank non più validi)
    // potremmo voler pulire la parte specifica di fill_blank dai metadati.
    // Per ora, li sovrascriviamo o li uniamo. Se FillBlankQuestionEditor emette null,
    // significa che la sua configurazione non è valida/completa.
    const { text_with_placeholders, blanks, case_sensitive, ...rest } = questionData.metadata;
    questionData.metadata = rest; // Mantiene solo altri metadati non fill_blank
    console.log('[QuestionFormView] FillBlank metadata cleared/invalidated.');
  }
};

// --- Watchers e Lifecycle Hooks ---
const processRouteParams = async (params: any, query: any) => {
  console.log("[QuestionFormView] START processRouteParams - params:", JSON.stringify(params), "query:", JSON.stringify(query));
  const qIdParam = params.quizId; // Corretto
  const questIdParam = params.questionId;

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
      quizId.value = null;
      questionId.value = null;
      return;
    }
  } else {
      error.value = "ID Quiz mancante nella rotta.";
      console.error("ID Quiz mancante nella rotta.");
      quizId.value = null;
      questionId.value = null;
      return;
  }
  quizId.value = currentQuizId;

  // Gestisci questionId
  if (questIdParam) {
    const parsedQuestionId = Number(questIdParam);
    if (!isNaN(parsedQuestionId)) {
        currentQuestionId = parsedQuestionId;
        console.log("Question ID parsed:", currentQuestionId);
    } else {
        console.error("ID Domanda non valido (non numerico):", questIdParam);
        error.value = "ID Domanda fornito nella URL non è valido.";
        questionId.value = null;
    }
  } else {
      currentQuestionId = null;
      console.log("Question ID not found in params (creation or quiz edit mode)");
  }
  questionId.value = currentQuestionId;

  // --- Carica dati specifici ---
  if (questionId.value && quizId.value) {
    // === Modalità Modifica Domanda ===
    console.log(`Loading specific question data for Quiz ${quizId.value}, Question ${questionId.value}`);
    await loadQuestionData(quizId.value, questionId.value);
    // Non carichiamo la lista completa delle domande qui, viene fatto da QuizFormView
  } else if (quizId.value) {
    // === Modalità Creazione Domanda ===
    console.log(`Setting defaults for creation in Quiz ${quizId.value}`);
    await resetFormForCreation(quizId.value, query.defaultOrder);
    // Non carichiamo la lista completa delle domande qui
  } else {
      // === Stato Non Valido ===
      console.error("Stato non valido: ID Quiz non valido o mancante.");
      error.value = "Stato della rotta non valido.";
  }
};

// Watch per reagire ai cambiamenti dei parametri della rotta
watch(
  () => route.params,
  async (newParams, oldParams) => {
    const quizIdChanged = newParams?.quizId !== oldParams?.quizId;
    const questionIdChanged = newParams?.questionId !== oldParams?.questionId;

    if (quizIdChanged || questionIdChanged) {
        console.log("Route params changed AFTER mount, processing:", newParams);
        await processRouteParams(newParams, route.query);
    }
  },
  { deep: true }
);

// onMounted per gestire il caricamento iniziale
onMounted(() => {
    console.log("[QuestionFormView] Component mounted. Initial route params:", JSON.stringify(route.params), "query:", JSON.stringify(route.query));
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

// Watcher per il tipo di domanda (ora usa questionData.question_type)
watch(() => questionData.question_type, (newType) => {
    console.log("Question type changed to:", newType);
});

</script>

<style scoped>
/* Rimuoviamo la maggior parte degli stili scoped, ora gestiti da Tailwind. */
/* Eventuali stili specifici che Tailwind non copre facilmente possono rimanere qui. */
</style>