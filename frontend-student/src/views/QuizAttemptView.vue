<script setup lang="ts">
import { ref, onMounted, computed, shallowRef } from 'vue'; // Aggiunto shallowRef
import { useRoute, useRouter } from 'vue-router';
import QuizService, { type Question, type QuizAttempt, type Answer } from '@/api/quiz';
// Importa i componenti delle domande
import MultipleChoiceSingleQuestion from '@/components/quiz/questions/MultipleChoiceSingleQuestion.vue';
import MultipleChoiceMultipleQuestion from '@/components/quiz/questions/MultipleChoiceMultipleQuestion.vue';
import TrueFalseQuestion from '@/components/quiz/questions/TrueFalseQuestion.vue';
import FillBlankQuestion from '@/components/quiz/questions/FillBlankQuestion.vue';
import OpenAnswerManualQuestion from '@/components/quiz/questions/OpenAnswerManualQuestion.vue';
// import TrueFalseQuestion from '@/components/quiz/questions/TrueFalseQuestion.vue';
// import FillBlankQuestion from '@/components/quiz/questions/FillBlankQuestion.vue';
// import OpenAnswerManualQuestion from '@/components/quiz/questions/OpenAnswerManualQuestion.vue';
import { useAuthStore } from '@/stores/auth'; // Potrebbe servire per info studente o token

// State
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore(); // Se necessario

const quizId = computed(() => Number(route.params.quizId));
const attempt = ref<QuizAttempt | null>(null);
const currentQuestion = ref<Question | null>(null);
const userAnswer = ref<Answer | null>(null); // Da definire meglio in base al tipo di domanda
const isLoading = ref(false);
const error = ref<string | null>(null);
const isSubmitting = ref(false);
const isCompleting = ref(false);

// --- Funzioni Logiche ---

async function startQuizAttempt() {
  if (!quizId.value) {
    error.value = "ID del quiz non valido.";
    return;
  }
  isLoading.value = true;
  error.value = null;
  try {
    attempt.value = await QuizService.startAttempt(quizId.value);
    await fetchCurrentQuestion(); // Carica la prima domanda subito dopo aver iniziato
  } catch (err: any) { // Aggiunto :any per accedere a err.response
    console.error("Errore durante l'avvio del tentativo:", err);
    if (err.response?.data?.detail) {
        error.value = `Errore avvio: ${err.response.data.detail}`;
    } else {
        error.value = "Impossibile avviare il tentativo di quiz. Controlla la connessione o riprova più tardi.";
    }
    // Cancella l'errore dopo 7 secondi
    setTimeout(() => { error.value = null; }, 7000);
  } finally {
    isLoading.value = false;
  }
}

async function fetchCurrentQuestion() {
  if (!attempt.value) return;
  isLoading.value = true; // Potrebbe essere un loading diverso per la domanda
  error.value = null; // Resetta errore precedente
  try {
    currentQuestion.value = await QuizService.getCurrentQuestion(attempt.value.id);
    userAnswer.value = null; // Resetta la risposta precedente
  } catch (err: any) {
    // Se l'API restituisce 404 o un errore specifico quando non ci sono più domande,
    // potremmo gestirlo qui per indicare la fine del quiz.
    // Altrimenti, potrebbe essere un errore generico.
    if (err.response && err.response.status === 404) {
       // Probabilmente il quiz è finito, ma l'endpoint /current-question/ non è pensato per questo.
       // L'azione di completamento è separata.
       console.log("Nessuna domanda successiva trovata, considerare il completamento.");
       currentQuestion.value = null; // Indica che non ci sono più domande da mostrare
    } else {
      console.error("Errore durante il recupero della domanda:", err);
      if (err.response?.data?.detail) {
          error.value = `Errore caricamento domanda: ${err.response.data.detail}`;
      } else {
          error.value = "Impossibile caricare la domanda successiva.";
      }
      // Cancella l'errore dopo 7 secondi
      setTimeout(() => { error.value = null; }, 7000);
      error.value = "Impossibile caricare la domanda successiva.";
    }
    currentQuestion.value = null; // Assicura che non venga mostrata una domanda vecchia in caso di errore
  } finally {
    isLoading.value = false;
  }
}

async function submitAnswerHandler() {
  if (!attempt.value || !currentQuestion.value || !userAnswer.value) {
    error.value = "Impossibile inviare la risposta: mancano dati.";
    return;
  }
  isSubmitting.value = true;
  error.value = null;
  try {
    const result = await QuizService.submitAnswer(
      attempt.value.id,
      currentQuestion.value.id,
      userAnswer.value
    );
    console.log("Risposta inviata:", result); // Log per debug
    // Dopo aver inviato la risposta, carica la domanda successiva
    await fetchCurrentQuestion();
  } catch (err: any) { // Aggiunto :any
    console.error("Errore durante l'invio della risposta:", err);
     if (err.response?.data?.detail) {
        error.value = `Errore invio risposta: ${err.response.data.detail}`;
    } else if (err.response?.data?.selected_answers) { // Errore di validazione specifico
         error.value = `Errore dati risposta: ${err.response.data.selected_answers.join(', ')}`;
    } else {
        error.value = "Errore nell'invio della risposta. Riprova.";
    }
     // Cancella l'errore dopo 7 secondi
    setTimeout(() => { error.value = null; }, 7000);
  } finally {
    isSubmitting.value = false;
  }
}

async function completeAttemptHandler() {
  if (!attempt.value) return;
  isCompleting.value = true;
  error.value = null;
  try {
    const finalAttemptDetails = await QuizService.completeAttempt(attempt.value.id);
    console.log("Tentativo completato:", finalAttemptDetails);
    // Reindirizza alla pagina dei risultati (da creare)
    // Passando l'ID del tentativo completato
    router.push({ name: 'QuizResult', params: { attemptId: attempt.value.id } });
  } catch (err: any) { // Aggiunto :any
    console.error("Errore durante il completamento del tentativo:", err);
    if (err.response?.data?.detail) {
        error.value = `Errore completamento: ${err.response.data.detail}`;
    } else {
        error.value = "Impossibile completare il quiz. Riprova.";
    }
     // Cancella l'errore dopo 7 secondi
    setTimeout(() => { error.value = null; }, 7000);
  } finally {
    isCompleting.value = false;
  }
}

// --- Lifecycle Hooks ---

onMounted(() => {
  startQuizAttempt();
});

// --- Computed Properties ---
// Mappa i tipi di domanda ai componenti importati
// Usiamo shallowRef per i componenti dinamici per ottimizzare le performance
const questionComponentMap = {
  'MC_SINGLE': shallowRef(MultipleChoiceSingleQuestion), // Aggiornato per corrispondere al backend
  'MC_MULTI': shallowRef(MultipleChoiceMultipleQuestion), // Aggiornato per corrispondere al backend
  'TF': shallowRef(TrueFalseQuestion), // Aggiornato per corrispondere al backend
  'FILL_BLANK': shallowRef(FillBlankQuestion), // Aggiornato per corrispondere al backend
  'OPEN_MANUAL': shallowRef(OpenAnswerManualQuestion), // Aggiornato per corrispondere al backend
  // 'true_false': shallowRef(TrueFalseQuestion),
  // 'fill_blank': shallowRef(FillBlankQuestion),
  // 'open_answer_manual': shallowRef(OpenAnswerManualQuestion),
};

const currentQuestionComponent = computed(() => {
  if (!currentQuestion.value?.question_type) return null;
  const componentRef = questionComponentMap[currentQuestion.value.question_type];
  return componentRef ? componentRef.value : null; // Accedi a .value dello shallowRef
});

// Funzione per aggiornare la risposta dell'utente dal componente figlio
function updateUserAnswer(answer: Answer | null) {
  userAnswer.value = answer;
}

</script>

<template>
  <div class="quiz-attempt-view container mx-auto px-4 py-8 max-w-3xl">
    <h1 class="text-3xl font-bold text-center text-purple-800 mb-6">Svolgimento Quiz</h1>

    <div v-if="isLoading && !attempt" class="loading bg-blue-100 border border-blue-200 text-blue-700 px-4 py-3 rounded relative text-center mb-6">
      <p>Avvio del tentativo...</p>
      {/* TODO: Aggiungere uno spinner Tailwind */}
    </div>

    <div v-if="error" class="error-message bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-if="attempt && !isLoading" class="bg-white p-6 rounded-lg shadow-lg">
      <h2 class="text-2xl font-semibold text-gray-800 mb-2">{{ attempt.quiz.title }}</h2>
      <p class="text-gray-600 mb-6">{{ attempt.quiz.description }}</p>

      <div v-if="isLoading && currentQuestion === null" class="loading bg-gray-100 text-gray-600 px-4 py-3 rounded text-center mb-6">
        <p>Caricamento domanda...</p>
      </div>

      <div v-if="currentQuestion" class="question-container bg-purple-50 border border-purple-200 p-6 rounded-lg mb-6">
        <h3 class="text-lg font-semibold text-purple-700 mb-3">Domanda {{ currentQuestion.order + 1 }}</h3>
        <p class="question-text text-gray-800 text-lg mb-5">{{ currentQuestion.text }}</p>

        <!-- Renderizza dinamicamente il componente domanda corretto -->
        <div class="answer-area">
          <component
            v-if="currentQuestionComponent && currentQuestion"
            :is="currentQuestionComponent"
            :question="currentQuestion"
            @update:answer="updateUserAnswer"
          />
          <div v-else>
             <p v-if="currentQuestion">Tipo di domanda non supportato: {{ currentQuestion.question_type }}</p>
             <!-- Potrebbe essere un placeholder o un messaggio di errore -->
          </div>
        </div>

        <button
          @click="submitAnswerHandler"
          :disabled="isSubmitting || !userAnswer"
          class="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg shadow transition-colors duration-200"
        >
          {{ isSubmitting ? 'Invio...' : 'Invia Risposta' }}
        </button>
      </div>

      <div v-else-if="!isLoading && !error" class="text-center mt-8">
        <p class="text-xl text-green-600 font-semibold mb-4">Hai risposto a tutte le domande!</p>
        <button
          @click="completeAttemptHandler"
          :disabled="isCompleting"
          class="bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg shadow transition-colors duration-200"
        >
          {{ isCompleting ? 'Completamento...' : 'Completa Quiz e Vedi Risultati 🎉' }}
        </button>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* Stili specifici rimasti o che richiedono override */
.loading, .error-message {
  /* Stili Tailwind applicati direttamente nel template */
}

.answer-area {
  /* Questo spazio conterrà i componenti delle domande specifiche */
  /* Potremmo aggiungere un margine inferiore qui se necessario universalmente */
   margin-bottom: 1.5rem; /* Esempio: 24px */
}

/* Eventuali altri stili specifici non coperti da Tailwind */
</style>