<script setup lang="ts">
import { ref, onMounted, computed, shallowRef, watch } from 'vue'; // Aggiunto watch
import { useRoute, useRouter } from 'vue-router';
import QuizService, { type Question, type QuizAttempt, type Answer } from '@/api/quiz';
// Importa i componenti delle domande
import MultipleChoiceSingleQuestion from '@/components/quiz/questions/MultipleChoiceSingleQuestion.vue';
import MultipleChoiceMultipleQuestion from '@/components/quiz/questions/MultipleChoiceMultipleQuestion.vue';
import TrueFalseQuestion from '@/components/quiz/questions/TrueFalseQuestion.vue';
import FillBlankQuestion from '@/components/quiz/questions/FillBlankQuestion.vue';
import OpenAnswerManualQuestion from '@/components/quiz/questions/OpenAnswerManualQuestion.vue';
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification'; // Importa lo store notifiche

// --- Sfondi e Animazioni ---
// Lista di classi Tailwind per i gradienti di sfondo
const backgroundGradients = [
  'bg-gradient-to-br from-red-500 to-red-700',
  'bg-gradient-to-br from-blue-500 to-blue-700',
  'bg-gradient-to-br from-green-500 to-green-700',
  'bg-gradient-to-br from-yellow-500 to-yellow-700',
  'bg-gradient-to-br from-purple-600 to-indigo-700', // Gradiente login
  'bg-gradient-to-br from-pink-500 to-pink-700',
];
const currentBackgroundClass = ref(backgroundGradients[0]); // Inizia con il primo
const backgroundIndex = ref(0);
const showStartAnimation = ref(true); // Controlla la visibilità dell'intera animazione
const countdownValue = ref<number | string>(3); // Inizia da 3, poi diventa 'Via!'
const countdownActive = ref(false); // Controlla l'intervallo

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
    // getCurrentQuestion ora ritorna Question | null
    const nextQuestion = await QuizService.getCurrentQuestion(attempt.value.id);

    if (nextQuestion) {
      // È una domanda valida
      currentQuestion.value = nextQuestion;
      console.log('Current Question Object:', JSON.parse(JSON.stringify(currentQuestion.value))); // Log per debug ordine
      userAnswer.value = null; // Resetta la risposta precedente
    } else {
      // getCurrentQuestion ha restituito null, significa fine quiz o errore 404 gestito
      console.log("fetchCurrentQuestion: Ricevuto null da getCurrentQuestion, il quiz è terminato o si è verificato un errore 404 gestito.");
      currentQuestion.value = null; // Imposta a null per mostrare il pulsante Completa
    }
  } catch (err: any) {
    // Gestisce solo errori NON gestiti da getCurrentQuestion (es. 500, network error)
    console.error("Errore non gestito durante il recupero della domanda:", err);
     if (err.response?.data?.detail) {
        error.value = `Errore caricamento domanda: ${err.response.data.detail}`;
    } else {
        error.value = "Impossibile caricare la domanda successiva.";
    }
    // Cancella l'errore dopo 7 secondi
    setTimeout(() => { error.value = null; }, 7000);
    currentQuestion.value = null; // Assicura che non venga mostrata una domanda vecchia in caso di errore grave
  } finally {
    isLoading.value = false; // Assicurati che isLoading sia gestito correttamente
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
    // Log dettagliato prima dell'invio
    console.log('Submitting answer with:', {
        attemptId: attempt.value.id,
        questionId: currentQuestion.value.id,
        // Usiamo JSON.stringify/parse per fare una deep copy e loggare lo stato esatto al momento della chiamata
        answerPayload: JSON.parse(JSON.stringify(userAnswer.value))
    });
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

    // --- Logica Notifica Badge ---
    // Assicurati di importare useNotificationStore all'inizio dello script setup
    const notificationStore = useNotificationStore();
    if (finalAttemptDetails.newly_earned_badges && finalAttemptDetails.newly_earned_badges.length > 0) {
      console.log("Nuovi badge guadagnati:", finalAttemptDetails.newly_earned_badges);
      finalAttemptDetails.newly_earned_badges.forEach((badge: any) => { // Usa 'any' o definisci un tipo/interfaccia per Badge
        notificationStore.addBadgeNotification(
          badge.id,
          badge.name,
          badge.image_url // Assicurati che questo campo sia restituito dal SimpleBadgeSerializer
        );
      });
    }
    // --- Fine Logica Notifica Badge ---

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
  // Imposta il primo gradiente
  currentBackgroundClass.value = backgroundGradients[backgroundIndex.value];

  // Avvia il contatore
  startCountdown();

  // Avvia il quiz
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

// --- Funzioni per il Contatore ---
function startCountdown() {
  countdownActive.value = true;
  countdownValue.value = 3; // Reset iniziale

  const intervalId = setInterval(() => {
    if (typeof countdownValue.value === 'number' && countdownValue.value > 1) {
      countdownValue.value--;
    } else if (countdownValue.value === 1) {
      countdownValue.value = 'Via!';
    } else { // Quando è 'Via!'
      clearInterval(intervalId);
      countdownActive.value = false;
      // Nasconde l'animazione dopo che "Via!" è stato mostrato per un po'
      setTimeout(() => {
        showStartAnimation.value = false;
      }, 500); // Mostra "Via!" per 0.5 secondi
    }
  }, 1000); // Intervallo di 1 secondo
}

// Osserva quando la domanda cambia per ciclare lo sfondo e gestire la transizione
watch(currentQuestion, (newQuestion, oldQuestion) => {
  if (newQuestion && (!oldQuestion || newQuestion.id !== oldQuestion.id)) {
    console.log(`Transitioning to question ${newQuestion.order + 1}`);
    // Cambia sfondo ciclicamente
    backgroundIndex.value = (backgroundIndex.value + 1) % backgroundGradients.length;
    currentBackgroundClass.value = backgroundGradients[backgroundIndex.value];
  }
});

</script>

<template>
  <div
    class="quiz-attempt-view min-h-screen flex flex-col items-center justify-center p-4 relative transition-colors duration-500"
    :class="currentBackgroundClass"
  >
    <!-- Overlay per leggibilità -->
    <div class="absolute inset-0 bg-black bg-opacity-50 z-0"></div>

    <!-- Contenuto principale sopra l'overlay -->
    <div class="main-content container mx-auto max-w-3xl relative z-10">

      <!-- Animazione Iniziale -->
      <!-- Animazione Iniziale con Contatore -->
      <transition name="start-anim">
        <div v-if="showStartAnimation" class="start-animation text-center mb-8 p-10 rounded-lg bg-blue-500 bg-opacity-90 shadow-xl">
          <p class="text-6xl font-bold text-white animate-pulse">
            {{ countdownValue }}
          </p>
        </div>
      </transition>

      <h1 class="text-3xl font-bold text-center text-white mb-6">Svolgimento Quiz</h1>

    <div v-if="isLoading && !attempt" class="loading bg-white bg-opacity-80 text-blue-700 px-4 py-3 rounded relative text-center mb-6 shadow">
      <p>Avvio del tentativo...</p>
      {/* Spinner Tailwind */}
      <svg class="animate-spin h-5 w-5 text-blue-600 mx-auto mt-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>

    <div v-if="error" class="error-message bg-red-100 bg-opacity-90 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6 shadow" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <!-- Mostra il contenuto del quiz solo se l'animazione iniziale è finita -->
    <div v-if="attempt && !isLoading && !showStartAnimation" class="bg-white bg-opacity-95 p-6 rounded-lg shadow-xl">
      <h2 class="text-2xl font-semibold text-gray-800 mb-2">{{ attempt.quiz.title }}</h2>
      <p class="text-gray-600 mb-6">{{ attempt.quiz.description }}</p>

      <div v-if="isLoading && currentQuestion === null" class="loading bg-gray-100 text-gray-600 px-4 py-3 rounded text-center mb-6 shadow-inner">
        <p>Caricamento domanda...</p>
        <!-- Spinner rimosso -->
        <svg class="animate-spin h-5 w-5 text-gray-500 mx-auto mt-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>

      <!-- Blocco Condizionale per Domanda o Completamento -->
      <!-- Usiamo un template per il v-if in modo che la transizione non interrompa la catena -->
      <template v-if="currentQuestion">
        <transition name="question-fade" mode="out-in" appear>
           <!-- Blocco Domanda Effettivo -->
          <div :key="currentQuestion.id" class="question-container bg-purple-50 bg-opacity-90 border border-purple-200 p-6 rounded-lg mb-6 shadow-md">
            <h3 class="text-lg font-semibold text-purple-700 mb-3">Domanda {{ currentQuestion.order }}</h3>
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
        </transition>
      </template>
      <!-- Blocco Completamento: mostrato se NON c'è domanda corrente, NON sta caricando e NON c'è errore -->
      <!-- Questo v-else-if ora segue direttamente il <template v-if="currentQuestion"> -->
      <div v-else-if="!currentQuestion && !isLoading && !error" class="text-center mt-8">
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
    </div> <!-- Fine main-content -->
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

/* Stili per l'animazione iniziale */
.start-anim-enter-active,
.start-anim-leave-active {
  transition: opacity 0.8s ease-in-out, transform 0.8s ease-in-out;
}
.start-anim-enter-from,
.start-anim-leave-to {
  opacity: 0;
  transform: scale(0.8) translateY(20px);
}
.start-anim-enter-to,
.start-anim-leave-from {
  opacity: 1;
  transform: scale(1) translateY(0);
}

/* Stili per la transizione delle domande */
.question-fade-enter-active,
.question-fade-leave-active {
  transition: opacity 0.3s ease; /* Durata e tipo di transizione */
}
.question-fade-enter-from,
.question-fade-leave-to {
  opacity: 0;
}

/* Eventuali altri stili specifici non coperti da Tailwind */

</style>