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
    if (err.response &amp;&amp; err.response.status === 404) {
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
  'multiple_choice_single': shallowRef(MultipleChoiceSingleQuestion),
  'multiple_choice_multiple': shallowRef(MultipleChoiceMultipleQuestion),
  'true_false': shallowRef(TrueFalseQuestion),
  'fill_blank': shallowRef(FillBlankQuestion),
  'open_answer_manual': shallowRef(OpenAnswerManualQuestion),
  // 'true_false': shallowRef(TrueFalseQuestion),
  // 'fill_blank': shallowRef(FillBlankQuestion),
  // 'open_answer_manual': shallowRef(OpenAnswerManualQuestion),
};

const currentQuestionComponent = computed(() => {
  if (!currentQuestion.value?.question_type) return null;
  return questionComponentMap[currentQuestion.value.question_type] ?? null;
});

// Funzione per aggiornare la risposta dell'utente dal componente figlio
function updateUserAnswer(answer: Answer | null) {
  userAnswer.value = answer;
}

</script>

<template>
  <div class="quiz-attempt-view">
    <h1>Svolgimento Quiz</h1>

    <div v-if="isLoading &amp;&amp; !attempt" class="loading">
      <p>Avvio del tentativo...</p>
      <!-- Aggiungere uno spinner o indicatore di caricamento -->
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>

    <div v-if="attempt &amp;&amp; !isLoading">
      <h2>{{ attempt.quiz.title }}</h2>
      <p>{{ attempt.quiz.description }}</p>

      <div v-if="isLoading &amp;&amp; currentQuestion === null" class="loading">
        <p>Caricamento domanda...</p>
      </div>

      <div v-if="currentQuestion" class="question-container">
        <h3>Domanda {{ currentQuestion.order }}</h3>
        <p class="question-text">{{ currentQuestion.text }}</p>

        <!-- Renderizza dinamicamente il componente domanda corretto -->
        <div class="answer-area">
          <component
            v-if="currentQuestionComponent &amp;&amp; currentQuestion"
            :is="currentQuestionComponent"
            :question="currentQuestion"
            @update:answer="updateUserAnswer"
          />
          <div v-else>
             <p v-if="currentQuestion">Tipo di domanda non supportato: {{ currentQuestion.question_type }}</p>
             <!-- Potrebbe essere un placeholder o un messaggio di errore -->
          </div>
        </div>

        <button @click="submitAnswerHandler" :disabled="isSubmitting || !userAnswer">
          {{ isSubmitting ? 'Invio...' : 'Invia Risposta' }}
        </button>
      </div>

      <div v-else-if="!isLoading &amp;&amp; !error">
        <p>Hai risposto a tutte le domande!</p>
        <button @click="completeAttemptHandler" :disabled="isCompleting">
          {{ isCompleting ? 'Completamento...' : 'Completa Quiz e Vedi Risultati' }}
        </button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.quiz-attempt-view {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.loading, .error-message {
  margin-top: 20px;
  padding: 15px;
  border-radius: 5px;
}

.loading {
  background-color: #e0e0e0;
  text-align: center;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.question-container {
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.question-text {
  font-size: 1.1em;
  margin-bottom: 20px;
}

.answer-area {
  margin-bottom: 20px;
  /* Stili specifici verranno definiti nei componenti figlio */
}

button {
  padding: 10px 20px;
  font-size: 1em;
  cursor: pointer;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  transition: background-color 0.3s ease;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #0056b3;
}

h1, h2, h3 {
    color: #333;
}
</style>