<script setup lang="ts">
import { ref, onMounted, computed, shallowRef, watch, defineProps, defineEmits, onUnmounted } from 'vue'; // Aggiungere onUnmounted
// Rimuovere useRoute
// import { useRoute, useRouter } from 'vue-router';
import { useRouter } from 'vue-router'; // Mantenere useRouter per ora, se serve per altro
import QuizService, {
  type Question,
  type QuizAttempt,
  type Answer as ApiAnswer, // Rinomino Answer per evitare conflitti con il tipo interno
  type QuestionMetadataFillBlankApi,
  // Importo i tipi specifici per costruire UserProvidedAnswer
  type MultipleChoiceSingleAnswer,
  type MultipleChoiceMultipleAnswer,
  type TrueFalseAnswer,
  type OpenAnswerManualAnswer
} from '@/api/quiz';
// StudentAnswerPayloadFillBlank è ciò che FillBlankQuestion.vue emette
import type { StudentAnswerPayloadFillBlank } from '@/types/education';
// Importa i componenti delle domande
import MultipleChoiceSingleQuestion from '@/components/quiz/questions/MultipleChoiceSingleQuestion.vue';
import MultipleChoiceMultipleQuestion from '@/components/quiz/questions/MultipleChoiceMultipleQuestion.vue';
import TrueFalseQuestion from '@/components/quiz/questions/TrueFalseQuestion.vue';
import FillBlankQuestion from '@/components/quiz/questions/FillBlankQuestion.vue';
import OpenAnswerManualQuestion from '@/components/quiz/questions/OpenAnswerManualQuestion.vue';
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification'; // Importa lo store notifiche
import { useDashboardStore } from '@/stores/dashboard'; // <-- AGGIUNTO: Importa lo store dashboard

// Definiamo un tipo per lo stato interno di userAnswer.value, che riflette
// i dati così come emessi dai componenti domanda.
type UserProvidedAnswer =
  | MultipleChoiceSingleAnswer
  | MultipleChoiceMultipleAnswer
  | TrueFalseAnswer
  | StudentAnswerPayloadFillBlank // Questo è ciò che FillBlankQuestion.vue emette
  | OpenAnswerManualAnswer;

// --- Props & Emits ---
const props = defineProps<{
  quizId: number; // Accetta quizId come prop
  attemptId?: number | null; // Nuovo: ID del tentativo esistente (opzionale)
}>();

const emit = defineEmits<{
  (e: 'close'): void; // Evento per chiudere la modale
  (e: 'completed', attemptId: number): void; // Evento al completamento
}>();

// --- Sfondi e Animazioni (invariato) ---
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
// Rimuovere useRoute
// const route = useRoute();
const router = useRouter(); // Mantenere per ora
const authStore = useAuthStore();
const dashboardStore = useDashboardStore(); // <-- AGGIUNTO: Istanza dello store dashboard

// Rimuovere il computed basato sulla route
// const quizId = computed(() => Number(route.params.quizId));
// Usiamo direttamente props.quizId dove serve

const attempt = ref<QuizAttempt | null>(null);
const currentQuestion = ref<Question | null>(null);
const userAnswer = ref<UserProvidedAnswer | null>(null);
const isLoading = ref(false);
const error = ref<string | null>(null);
const isSubmitting = ref(false);
const isCompleting = ref(false);
const showFeedback = ref(false); // Nuovo: Controlla visibilità feedback
const isCorrectFeedback = ref(false); // Nuovo: Indica se il feedback è per risposta corretta
const feedbackTimeoutId = ref<number | null>(null); // Nuovo: Per gestire il timeout (tipo corretto per browser)
const showPendingGradingMessage = ref(false); // Nuovo: Controlla visibilità messaggio "pending grading"

// --- Funzioni Logiche ---

// Nuovo: Funzione per caricare un tentativo esistente
async function loadExistingAttempt(existingAttemptId: number) {
  isLoading.value = true;
  error.value = null;
  try {
    // Carica i dettagli base del tentativo
    attempt.value = await QuizService.getAttemptDetails(existingAttemptId);

    if (attempt.value) {
       // Dopo aver caricato i dettagli del tentativo, recupera la domanda corrente
       await fetchCurrentQuestion();
    } else {
       throw new Error("Dettagli del tentativo non trovati.");
    }
    console.log(`Tentativo ${existingAttemptId} caricato.`);
    startCountdown(); // Avvia il countdown dopo il caricamento
  } catch (err: any) {
    console.error(`Errore durante il caricamento del tentativo ${existingAttemptId}:`, err);
    if (err.response?.data?.detail) {
        error.value = `Errore caricamento: ${err.response.data.detail}`;
    } else {
        error.value = "Impossibile caricare il tentativo esistente.";
    }
    setTimeout(() => { error.value = null; }, 7000);
    emit('close'); // Chiudi la modale in caso di errore nel caricamento
  } finally {
    isLoading.value = false;
  }
}

// Modificato: Funzione per avviare un *nuovo* tentativo
async function startNewQuizAttempt() {
  if (!props.quizId) {
    error.value = "ID del quiz non valido.";
    emit('close'); // Chiudi se l'ID non è valido
    return;
  }
  isLoading.value = true;
  error.value = null;
  try {
    attempt.value = await QuizService.startAttempt(props.quizId);
    // Non chiamare fetchCurrentQuestion qui, startAttempt dovrebbe restituire la prima domanda o getCurrentQuestion la gestirà
    await fetchCurrentQuestion(); // Manteniamo per ora, ma potrebbe essere ridondante se startAttempt restituisce la domanda
    console.log(`Nuovo tentativo avviato per quiz ${props.quizId}.`);
    startCountdown(); // Avvia il countdown dopo l'avvio
  } catch (err: any) {
    // ... (gestione errore invariata, ma potremmo emettere 'close' qui?)
    console.error("Errore durante l'avvio del nuovo tentativo:", err);
     if (err.response?.data?.detail) {
         error.value = `Errore avvio: ${err.response.data.detail}`;
     } else {
         error.value = "Impossibile avviare il tentativo di quiz. Controlla la connessione o riprova più tardi.";
     }
     // Cancella l'errore dopo 7 secondi
     setTimeout(() => { error.value = null; }, 7000);
     // Considera di chiudere la modale in caso di errore grave all'avvio
     emit('close'); // Chiudi la modale in caso di errore grave all'avvio
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
  if (!attempt.value || !currentQuestion.value || !userAnswer.value || isSubmitting.value) { // Aggiunto controllo isSubmitting
    // error.value = "Impossibile inviare la risposta: mancano dati o invio già in corso."; // Modificato messaggio
    // return; // Rimosso return per permettere reset errore
    if (!isSubmitting.value) { // Mostra errore solo se non è già in corso un invio
       error.value = "Impossibile inviare la risposta: mancano dati.";
    }
    return;
  }

  // Pulisci timeout precedente se esiste
  if (feedbackTimeoutId.value) {
    clearTimeout(feedbackTimeoutId.value);
    feedbackTimeoutId.value = null;
  }
  showFeedback.value = false; // Nascondi feedback precedente

  isSubmitting.value = true;
  error.value = null;

  try {
    let payloadForApi: ApiAnswer; // Il payload per l'API usa ApiAnswer

    if (currentQuestion.value.question_type === 'fill_blank' && userAnswer.value) {
      // Qui userAnswer.value è di tipo UserProvidedAnswer.
      // Se question_type è 'fill_blank', allora dovrebbe essere StudentAnswerPayloadFillBlank.
      // Il cast è più sicuro ora grazie alla tipizzazione di userAnswer.
      const fillBlankUserAnswer = userAnswer.value as StudentAnswerPayloadFillBlank;
      const questionMetadata = currentQuestion.value.metadata as QuestionMetadataFillBlankApi;

      if (fillBlankUserAnswer && fillBlankUserAnswer.answers && questionMetadata.blanks) {
        const sortedBlanks = [...questionMetadata.blanks].sort((a, b) => a.order - b.order);
        const orderedStudentResponses: string[] = sortedBlanks.map(blankDef => {
          const foundAnswer = fillBlankUserAnswer.answers.find(ans => ans.blank_id === blankDef.id);
          // Se foundAnswer esiste e foundAnswer.student_response è definito, usa quello, altrimenti stringa vuota.
          return (foundAnswer && typeof foundAnswer.student_response === 'string') ? foundAnswer.student_response : "";
        });
        // payloadForApi deve essere di tipo FillBlankApiPayload (che è { answers: string[] })
        // Questo è compatibile con ApiAnswer.
        payloadForApi = { answers: orderedStudentResponses };
      } else {
        console.error("Dati mancanti o malformati per formattare la risposta fill_blank:", userAnswer.value, questionMetadata);
        error.value = "Errore nella formattazione della risposta fill_blank (dati interni).";
        isSubmitting.value = false;
        return;
      }
    } else {
      // Per altri tipi di domande, userAnswer.value (che è UserProvidedAnswer)
      // dovrebbe essere direttamente assegnabile a payloadForApi (che è ApiAnswer)
      // se i tipi corrispondenti sono compatibili (es. MultipleChoiceSingleAnswer).
      payloadForApi = userAnswer.value as ApiAnswer; // Cast necessario perché UserProvidedAnswer e ApiAnswer differiscono per fill_blank
    }

    // --- Invio della risposta ---
    const result = await QuizService.submitAnswer(
      attempt.value.id,
      currentQuestion.value.id,
      payloadForApi // Ora payloadForApi è sempre di tipo Answer (che include FillBlankApiPayload)
    );
    console.log("Risposta inviata, risultato API:", result); // Log per debug

    // Mostra feedback
    isCorrectFeedback.value = result.is_correct ?? false; // Usa l'informazione dall'API (con fallback)
    showFeedback.value = true;

    // Nascondi feedback e carica prossima domanda dopo un ritardo
    feedbackTimeoutId.value = setTimeout(async () => {
      showFeedback.value = false;
      feedbackTimeoutId.value = null; // Resetta ID timeout
      isSubmitting.value = false; // Resetta isSubmitting qui dopo il feedback
      await fetchCurrentQuestion(); // Carica prossima domanda
    }, 1500); // Mostra feedback per 1.5 secondi

  } catch (err: any) {
    console.error("Errore durante l'invio della risposta:", err);
     if (err.response?.data?.detail) {
        error.value = `Errore invio risposta: ${err.response.data.detail}`;
    } else if (err.response?.data?.selected_answers) {
        const saError = err.response.data.selected_answers;
        if (typeof saError === 'string') {
            error.value = `Errore dati risposta: ${saError}`;
        } else if (Array.isArray(saError)) {
            error.value = `Errore dati risposta: ${saError.join(', ')}`;
        } else if (typeof saError === 'object' && saError !== null) {
            // Se selected_answers è un oggetto, potrebbe contenere messaggi per campo
            // Esempio: { "answers": ["Questo campo non è valido."] }
            // Tentiamo di estrarre il primo messaggio o una rappresentazione generica
            const messages = Object.values(saError).flat(); // Prende tutti i valori, li appiattisce se sono array
            if (messages.length > 0 && typeof messages[0] === 'string') {
                 error.value = `Errore dati risposta: ${messages[0]}`;
            } else {
                 error.value = `Errore dati risposta: Formato errore non riconosciuto per selected_answers.`;
            }
        } else {
            error.value = "Errore nei dati della risposta inviati (selected_answers).";
        }
    } else {
        error.value = "Errore nell'invio della risposta. Riprova.";
    }
     // Cancella l'errore dopo 7 secondi
    setTimeout(() => { error.value = null; }, 7000);
    isSubmitting.value = false; // Resetta lo stato di invio in caso di errore
  } finally {
    // isSubmitting viene resettato solo dopo il timeout o in caso di errore
     if (!feedbackTimeoutId.value && !error.value) { // Se non c'è un timeout attivo (quindi non c'è stato successo) e non c'è errore
        isSubmitting.value = false;
     } else if (error.value) {
        // Già gestito nel blocco catch
     } else {
        // Verrà resettato nel timeout
        // isSubmitting.value = false; // Non resettare qui, ma nel timeout
     }
  }
}

async function completeAttemptHandler() {
  if (!attempt.value) return;
  isCompleting.value = true;
  error.value = null;
  try {
    const finalAttemptDetails = await QuizService.completeAttempt(attempt.value.id);
    console.log("Tentativo completato:", finalAttemptDetails);

    // <-- AGGIUNTO: Ricarica i dati della dashboard in ogni caso -->
    await dashboardStore.loadDashboard();
    console.log("[QuizAttemptView] Dashboard data reload triggered after quiz completion attempt.");

    if (finalAttemptDetails.status === 'PENDING_GRADING') {
      console.log("Tentativo in attesa di correzione manuale.");
      showPendingGradingMessage.value = true;
      // Non emettere 'completed' qui. La modale si chiuderà tramite il messaggio.
      // Potremmo aggiungere un timeout per chiudere automaticamente la modale dopo aver mostrato il messaggio.
      setTimeout(() => {
        if (showPendingGradingMessage.value) { // Controlla se il messaggio è ancora visibile
          emit('close');
        }
      }, 5000); // Chiudi dopo 5 secondi se l'utente non lo fa prima
    } else {
      // --- Logica Notifica Badge (solo se non è pending) ---
      const notificationStore = useNotificationStore();
      if (finalAttemptDetails.newly_earned_badges && finalAttemptDetails.newly_earned_badges.length > 0) {
        console.log("Nuovi badge guadagnati:", finalAttemptDetails.newly_earned_badges);
        finalAttemptDetails.newly_earned_badges.forEach((badge: any) => {
          notificationStore.addBadgeToastNotification(badge);
        });
      }
      // --- Fine Logica Notifica Badge ---

      emit('completed', attempt.value.id); // Emetti evento con l'ID del tentativo
    }

  } catch (err: any) {
    // ... (gestione errore invariata) ...
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

// Nuovo: Decide se caricare o iniziare un tentativo
async function loadOrStartAttempt() {
  if (props.attemptId) {
    await loadExistingAttempt(props.attemptId);
  } else if (props.quizId) {
    await startNewQuizAttempt();
  } else {
    error.value = "ID del quiz o del tentativo mancante.";
    emit('close');
  }
}

onMounted(() => {
  // Imposta il primo gradiente
  currentBackgroundClass.value = backgroundGradients[backgroundIndex.value];

  // Carica o avvia il tentativo (il countdown partirà internamente dopo il successo)
  loadOrStartAttempt();
});

// --- Computed Properties ---
// Mappa i tipi di domanda ai componenti importati
// Usiamo shallowRef per i componenti dinamici per ottimizzare le performance
const questionComponentMap = {
  'MC_SINGLE': shallowRef(MultipleChoiceSingleQuestion), // Aggiornato per corrispondere al backend
  'MC_MULTI': shallowRef(MultipleChoiceMultipleQuestion), // Aggiornato per corrispondere al backend
  'TF': shallowRef(TrueFalseQuestion), // Aggiornato per corrispondere al backend
  'fill_blank': shallowRef(FillBlankQuestion), // Chiave aggiornata a minuscolo per corrispondenza backend
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
function updateUserAnswer(answerData: UserProvidedAnswer | null) {
  userAnswer.value = answerData;
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

// Aggiungi funzione per chiudere manualmente
const handleClose = () => {
  // Potremmo aggiungere una conferma se il tentativo è in corso
  emit('close');
};

// Modifica onUnmounted per pulire anche il timeout del feedback
onUnmounted(() => {
  if (feedbackTimeoutId.value) {
    clearTimeout(feedbackTimeoutId.value);
  }
  // ... (eventuale cleanup overflow body se necessario qui) ...
});

</script>

<template>
  <div class="quiz-attempt-view fixed inset-0 flex items-center justify-center z-50">
    <!-- Overlay con sfondo dinamico -->
    <div
      class="absolute inset-0 bg-black bg-opacity-50 z-0 transition-colors duration-500"
      :class="currentBackgroundClass"
    ></div>

    <!-- Box Modale Effettivo -->
    <div class="relative z-10 bg-white rounded-lg shadow-xl overflow-y-auto max-h-[80vh] w-full max-w-3xl flex flex-col pb-6">

      <!-- Pulsante Chiudi Modale (interno al box) -->
      <button
        @click="handleClose"
        class="absolute top-3 right-3 z-20 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full p-2 transition-colors"
        aria-label="Chiudi svolgimento quiz"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- Contenuto principale dentro il box modale -->
      <div class="main-content w-full px-6 pt-6">

        <!-- Animazione Iniziale con Contatore -->
        <transition name="start-anim">
          <div v-if="showStartAnimation" class="start-animation text-center mb-8 p-10 rounded-lg bg-blue-500 bg-opacity-90 shadow-xl">
            <p class="text-6xl font-bold text-white animate-pulse">
              {{ countdownValue }}
            </p>
          </div>
        </transition>

        <h1 class="text-3xl font-bold text-center text-gray-800 mb-6">Svolgimento Quiz</h1>

        <div v-if="isLoading && !attempt" class="loading bg-gray-100 text-blue-700 px-4 py-3 rounded relative text-center mb-6 shadow">
          <p>Avvio del tentativo...</p>
          <!-- Spinner Tailwind -->
          <svg class="animate-spin h-5 w-5 text-blue-600 mx-auto mt-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>

        <div v-if="error" class="error-message bg-red-100 bg-opacity-90 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6 shadow" role="alert">
          <strong class="font-bold">Errore!</strong>
          <span class="block sm:inline"> {{ error }}</span>
        </div>

        <!-- Messaggio di Attesa Correzione Manuale -->
        <div v-if="showPendingGradingMessage" class="pending-grading-message bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-6 rounded-md shadow-md my-6">
          <div class="flex">
            <div class="py-1">
              <svg class="fill-current h-6 w-6 text-yellow-500 mr-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zM9 11v2h2v-2H9zm0-4v3h2V7H9z"/></svg>
            </div>
            <div>
              <p class="font-bold text-lg mb-2">Quiz Inviato Correttamente!</p>
              <p class="text-sm">Alcune risposte richiedono la correzione manuale da parte del docente.</p>
              <p class="text-sm mt-1">Riceverai una notifica quando il risultato finale sarà disponibile.</p>
              <button
                @click="() => { showPendingGradingMessage = false; emit('close'); }"
                class="mt-4 bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-2 px-4 rounded text-sm transition-colors duration-150"
              >
                OK, Ho Capito
              </button>
            </div>
          </div>
        </div>

        <!-- Mostra il contenuto del quiz solo se l'animazione iniziale è finita E NON c'è il messaggio di pending grading -->
        <div v-if="attempt && !isLoading && !showStartAnimation && !showPendingGradingMessage" class="">
          <h2 class="text-2xl font-semibold text-gray-800 mb-2">{{ attempt?.quiz?.title }}</h2>
          <p class="text-gray-600 mb-6">{{ attempt?.quiz?.description }}</p>

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
              <div :key="currentQuestion.id" class="question-container py-4 px-6"> <!-- Rimosso bg, border, padding extra, shadow -->
                <h3 class="text-lg font-semibold text-purple-700 mb-3">Domanda {{ currentQuestion.order + 1 }}</h3>
                <p v-if="currentQuestion.question_type !== 'fill_blank'" class="question-text text-gray-800 text-lg mb-5">{{ currentQuestion.text }}</p>

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

        </div> <!-- Fine v-if attempt -->
      </div> <!-- Fine main-content -->
    </div> <!-- Fine Box Modale -->
  </div> <!-- Fine quiz-attempt-view -->
</template>

<style scoped>
/* Stili specifici rimasti o che richiedono override */
.loading, .error-message {
  /* Stili Tailwind applicati direttamente nel template */
}

.answer-area {
  /* Questo spazio conterrà i componenti delle domande specifiche */
  /* Potremmo aggiungere un margine inferiore qui se necessario universalmente */
   margin-bottom: 1.5rem; /* Ripristinato per spazio sotto risposte */
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

/* Nuove Animazioni per Feedback */
.feedback-fade-enter-active,
.feedback-fade-leave-active {
  transition: opacity 0.4s ease-out;
}
.feedback-fade-enter-from,
.feedback-fade-leave-to {
  opacity: 0;
}
.feedback-fade-enter-to,
.feedback-fade-leave-from {
  opacity: 1;
}

/* Stile aggiuntivo per l'overlay se necessario */
.feedback-overlay {
  /* backdrop-filter: blur(2px); /* Effetto blur opzionale */
}
</style>
