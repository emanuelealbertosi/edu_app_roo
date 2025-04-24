<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-2xl font-semibold text-gray-900 mb-6">
      {{ isEditing ? 'Modifica Quiz' : 'Crea Nuovo Quiz' }}
    </h1>

    <!-- Messaggio di successo -->
    <div v-if="successMessage" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-6" role="alert">
      <span class="block sm:inline">{{ successMessage }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-10">
      <p class="text-gray-500">Caricamento dati quiz...</p>
      <!-- Optional: Add a spinner here -->
    </div>

    <!-- Error State (Generale) -->
    <div v-if="error && !isLoading" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <!-- Form -->
    <form v-if="!isLoading" @submit.prevent="saveQuiz" class="space-y-6 bg-white p-8 rounded-lg shadow-md max-w-4xl mx-auto mb-8">
      <!-- Title -->
      <div>
        <label for="title" class="block text-sm font-medium text-gray-700 mb-1">Titolo</label>
        <input type="text" id="title" v-model="quizData.title" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
      </div>

      <!-- Description -->
      <div>
        <label for="description" class="block text-sm font-medium text-gray-700 mb-1">Descrizione (Opzionale)</label>
        <textarea id="description" v-model="quizData.description" rows="3"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"></textarea>
      </div>

      <!-- Availability Dates -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label for="available_from" class="block text-sm font-medium text-gray-700 mb-1">Disponibile Dal</label>
          <input type="datetime-local" id="available_from" v-model="quizData.available_from"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
        </div>
        <div>
          <label for="available_until" class="block text-sm font-medium text-gray-700 mb-1">Disponibile Fino Al</label>
          <input type="datetime-local" id="available_until" v-model="quizData.available_until"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
        </div>
      </div>

      <!-- Metadata Fields -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label for="points_on_completion" class="block text-sm font-medium text-gray-700 mb-1">Punti al Completamento</label>
          <input type="number" id="points_on_completion" v-model.number="quizData.metadata.points_on_completion" min="0"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
        </div>
        <div>
          <label for="completion_threshold_percent" class="block text-sm font-medium text-gray-700 mb-1">Soglia Completamento (%)</label>
          <input type="number" id="completion_threshold_percent" v-model.number="quizData.metadata.completion_threshold_percent" min="0" max="100" step="0.1"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
          <p class="mt-2 text-xs text-gray-500">Percentuale minima (0-100) per considerare il quiz superato. Default: 100%.</p>
        </div>
      </div>

      <!-- Form Actions -->
      <div class="flex justify-end space-x-3 border-t border-gray-200 pt-6">
        <button type="button" @click="cancel"
                class="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
          Annulla
        </button>
        <button type="submit" :disabled="isSaving"
                :class="['py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
                         isSaving ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700']">
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche Quiz' : 'Crea Quiz e Aggiungi Domande') }}
        </button>
      </div>
    </form>

    <!-- Questions Section (only in editing mode) -->
    <div v-if="isEditing && quizId && !isLoading" class="bg-white p-8 rounded-lg shadow-md max-w-4xl mx-auto">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Domande del Quiz</h2>

        <!-- Loading Questions State -->
        <div v-if="isLoadingQuestions" class="text-center py-6">
            <p class="text-gray-500">Caricamento domande...</p>
            <!-- Optional: Add a spinner here -->
        </div>

        <!-- Error Questions State -->
        <div v-else-if="questionsError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
            <strong class="font-bold">Errore Domande!</strong>
            <span class="block sm:inline"> {{ questionsError }}</span>
        </div>

        <!-- Questions List -->
        <div v-else-if="questions.length > 0" class="space-y-4">
            <!-- QuestionEditor gestirà il proprio stile interno -->
            <QuestionEditor
                v-for="(question, index) in questions"
                :key="question.id"
                :question="question"
                :question-index="index"
                @edit="handleEditQuestion"
                @delete="handleDeleteQuestion"
                class="border-b border-gray-200 pb-4 last:border-b-0"
            />
        </div>

        <!-- No Questions Yet -->
        <div v-else class="text-center py-6 border-t border-gray-200 mt-4">
            <p class="text-gray-500">Nessuna domanda ancora aggiunta a questo quiz.</p>
        </div>

        <!-- Add Question Button -->
        <div class="mt-6 text-right border-t border-gray-200 pt-6">
            <button type="button" @click="addQuestion"
                    class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
                </svg>
                Aggiungi Domanda
            </button>
        </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createQuiz, fetchQuizDetails, updateQuiz, type QuizPayload, type Quiz } from '@/api/quizzes'; // Importa anche Quiz type
import { fetchQuestions, deleteQuestionApi, type Question } from '@/api/questions'; // Importa anche deleteQuestionApi
import QuestionEditor from '@/components/QuestionEditor.vue'; // Importa il nuovo componente

// Interfaccia temporanea per i dati del form
interface QuizFormData {
  title: string;
  description: string | null;
  available_from: string | null;
  available_until: string | null;
  metadata: { // Aggiunto metadata
    points_on_completion: number | null;
    completion_threshold_percent: number | null; // Aggiunto campo soglia
    // Aggiungere altri metadati qui se necessario (es. difficulty)
  };
}

const route = useRoute();
const router = useRouter();

const quizId = ref<number | null>(null);
const isEditing = computed(() => !!quizId.value);
const isSaving = ref(false);
const error = ref<string | null>(null); // Errore generale del form/quiz
const isLoading = ref(false); // Stato caricamento dati quiz
const successMessage = ref<string | null>(null); // Messaggio di successo

// Stato per le domande
const questions = ref<Question[]>([]);
const isLoadingQuestions = ref(false);
const questionsError = ref<string | null>(null);

// Usiamo reactive per l'oggetto del form
const quizData = reactive<QuizFormData>({
  title: '',
  description: null,
  available_from: null,
  available_until: null,
  metadata: { // Inizializza metadata
    points_on_completion: null,
    completion_threshold_percent: 100.0 // Impostato default a 100.0
  }
});

onMounted(async () => {
  const idParam = route.params.id;
  if (idParam && idParam !== 'new') { // Controlla che non sia 'new'
    quizId.value = Number(idParam);
    if (!isNaN(quizId.value)) {
      // ID valido, carica dati quiz e domande
      await loadQuizData(quizId.value);
      await loadQuestions(quizId.value);
    } else {
      // ID non valido (non numerico)
      console.error("ID Quiz non valido (non numerico):", idParam);
      error.value = "ID Quiz fornito nella URL non è valido.";
      quizId.value = null; // Resetta ID
    }
  } else {
      // Siamo in modalità creazione
      quizId.value = null;
  }
});

const loadQuizData = async (id: number) => {
  isLoading.value = true;
  error.value = null;
  try {
    const fetchedQuiz = await fetchQuizDetails(id); // Usa la funzione API reale
    quizData.title = fetchedQuiz.title;
    quizData.description = fetchedQuiz.description;
    // Assicurati che i campi metadata, source_template etc. siano gestiti se necessario
    quizData.available_from = formatDateTimeForInput(fetchedQuiz.available_from);
    quizData.available_until = formatDateTimeForInput(fetchedQuiz.available_until);
    // Carica i metadati esistenti
    quizData.metadata.points_on_completion = fetchedQuiz.metadata?.points_on_completion ?? null;
    // Carica anche la soglia esistente, o usa il default 100 se non presente
    // Converti da 0-1 a 0-100 se necessario (assumendo che l'API restituisca 0-1)
    const threshold_api = fetchedQuiz.metadata?.completion_threshold;
    quizData.metadata.completion_threshold_percent = threshold_api !== undefined && threshold_api !== null ? threshold_api * 100 : 100.0;

  } catch (err: any) {
    console.error("Errore nel caricamento del quiz:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore nel caricamento dei dati del quiz.';
  } finally {
    isLoading.value = false;
  }
};

const loadQuestions = async (id: number) => {
    isLoadingQuestions.value = true;
    questionsError.value = null;
    try {
        questions.value = await fetchQuestions(id);
    } catch (err: any) {
        console.error(`Errore nel caricamento delle domande per il quiz ${id}:`, err);
        questionsError.value = err.response?.data?.detail || err.message || 'Errore nel caricamento delle domande.';
    } finally {
        isLoadingQuestions.value = false;
    }
};

const saveQuiz = async () => {
  isSaving.value = true;
  error.value = null;
  successMessage.value = null; // Resetta messaggio successo

  // Prepara il payload assicurandosi che metadata sia un oggetto valido
  // e convertendo le date nel formato ISO atteso dall'API
  // Converti la soglia da % (0-100) a decimale (0-1) per l'API
  const threshold_percent = quizData.metadata.completion_threshold_percent;
  const completion_threshold = threshold_percent === null || isNaN(Number(threshold_percent)) ? 1.0 : Number(threshold_percent) / 100; // Default a 1 (100%) se non valido

  const payload: QuizPayload = {
      title: quizData.title,
      description: quizData.description,
      available_from: quizData.available_from ? new Date(quizData.available_from).toISOString() : null,
      available_until: quizData.available_until ? new Date(quizData.available_until).toISOString() : null,
      metadata: {
          points_on_completion: quizData.metadata.points_on_completion === null || isNaN(Number(quizData.metadata.points_on_completion)) ? 0 : Number(quizData.metadata.points_on_completion),
          completion_threshold: completion_threshold, // Invia come decimale 0-1
          // Aggiungere altri metadati qui se necessario
      },
  };

  try {
    let savedQuiz: Quiz | null = null;
    if (isEditing.value && quizId.value) {
      savedQuiz = await updateQuiz(quizId.value, payload);
      // Ricarica i dati dopo l'aggiornamento per mostrare eventuali cambiamenti fatti dal backend
      await loadQuizData(quizId.value);
      successMessage.value = "Quiz aggiornato con successo!";
    } else {
      savedQuiz = await createQuiz(payload); // Usa la funzione API reale
      successMessage.value = "Quiz creato con successo! Ora puoi aggiungere domande.";
      // Aggiorna l'URL e lo stato per riflettere la modalità di modifica senza ricaricare la pagina
      quizId.value = savedQuiz.id;
      router.replace({ name: 'quiz-edit', params: { id: savedQuiz.id.toString() } }); // Usa replace per non aggiungere alla history
      // Carica le domande (saranno vuote)
      await loadQuestions(savedQuiz.id);
    }

    // Nascondi il messaggio di successo dopo qualche secondo
    setTimeout(() => {
        successMessage.value = null;
    }, 3000);

    // Rimosso: router.push({ name: 'quizzes' });
  } catch (err: any) {
    console.error("Errore durante il salvataggio del quiz:", err);
    // Tenta di estrarre errori specifici dei campi se disponibili
    if (err.response?.data && typeof err.response.data === 'object') {
        const errorDetails = Object.entries(err.response.data)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ');
        error.value = `Errore salvataggio: ${errorDetails}`;
    } else {
        error.value = err.response?.data?.detail || err.message || 'Errore durante il salvataggio del quiz.';
    }
  } finally {
    isSaving.value = false;
  }
};

const cancel = () => {
  router.push({ name: 'quizzes' }); // Torna alla lista
};

// Funzione helper per formattare le date ISO per l'input datetime-local
// Nota: l'input datetime-local richiede 'YYYY-MM-DDTHH:mm'
const formatDateTimeForInput = (isoString: string | null): string | null => {
  if (!isoString) return null;
  try {
    const date = new Date(isoString);
    // Estrai le parti e formatta (attenzione ai fusi orari se necessario)
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  } catch (e) {
    console.error("Errore formattazione data:", e);
    return null;
  }
};

const addQuestion = () => {
    console.log("Add Question button clicked. Attempting navigation..."); // Log
    if (!quizId.value) return;
    // Passa il numero attuale di domande come query param per l'ordine default
    const defaultOrder = questions.value.length;
    router.push({
        name: 'question-new',
        params: { quizId: quizId.value.toString() },
        query: { defaultOrder: defaultOrder } // Aggiunto query param
    });
};

const handleEditQuestion = (questionId: number) => {
    if (!quizId.value) return; // Assicurati che quizId sia definito
    // Naviga alla rotta per modificare la domanda specifica
    router.push({ name: 'question-edit', params: { quizId: quizId.value.toString(), questionId: questionId.toString() } });
};

const handleDeleteQuestion = async (questionId: number) => {
    if (!quizId.value) return; // Assicurati che quizId sia definito

    if (!confirm(`Sei sicuro di voler eliminare la domanda con ID ${questionId}?`)) {
        return;
    }

    questionsError.value = null; // Resetta errore precedente
    try {
        await deleteQuestionApi(quizId.value, questionId);
        // Ricarica l'elenco delle domande dal backend per riflettere il nuovo ordine
        await loadQuestions(quizId.value);
        console.log(`Domanda ${questionId} eliminata e lista domande ricaricata.`);
        // Mostra notifica successo (opzionale)
        successMessage.value = `Domanda ${questionId} eliminata con successo.`;
         setTimeout(() => { successMessage.value = null; }, 3000);
    } catch (err: any) {
        console.error(`Errore durante l'eliminazione della domanda ${questionId}:`, err);
        // Mostra errore all'utente
        questionsError.value = `Errore eliminazione domanda: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    }
};

</script>

<style scoped>
/* Rimuoviamo la maggior parte degli stili scoped, ora gestiti da Tailwind. */
/* Eventuali stili specifici che Tailwind non copre facilmente possono rimanere qui. */

/* Esempio: Potrebbe essere necessario forzare l'aspetto dell'input datetime-local se Tailwind non basta */
/* input[type="datetime-local"]::-webkit-calendar-picker-indicator {
    background-color: white;
} */
</style>