<script setup lang="ts">
import { ref, onMounted, computed, defineProps, defineEmits } from 'vue'; // Aggiunto defineProps, defineEmits
// Rimosso useRoute, useRouter
import QuizService, { type AttemptDetails, type Question, type StudentAnswerResult } from '@/api/quiz';
import RewardsService from '@/api/rewards'; // Importa RewardsService
import { useNotificationStore } from '@/stores/notification'; // Importa store notifiche
// import confetti from 'canvas-confetti'; // Per animazione successo

// State
// Rimosso route, router
const attemptDetails = ref<AttemptDetails | null>(null);
const notificationStore = useNotificationStore(); // Inizializza store notifiche
const isLoading = ref(true);
const error = ref<string | null>(null);
const showConfetti = ref(false); // State per animazione successo

// --- Props & Emits ---
const props = defineProps<{
  attemptId: number; // Accetta attemptId come prop
}>();

const emit = defineEmits<{
  (e: 'close'): void; // Evento per chiudere la modale
}>();

// Funzioni
async function fetchAttemptResults() {
  // Usa props.attemptId invece di attemptId.value (che era basato su route)
  if (!props.attemptId) {
    error.value = "ID del tentativo non valido.";
    isLoading.value = false;
    return;
  }
  isLoading.value = true;
  error.value = null;
  try {
    // Usa props.attemptId
    attemptDetails.value = await QuizService.getAttemptDetails(props.attemptId);
    // Log per debug: vediamo cosa riceviamo dall'API
    console.log('Attempt Details Received in QuizResultView:', JSON.stringify(attemptDetails.value, null, 2));
  } catch (err) {
    // Usa props.attemptId nel log
    console.error(`Errore durante il recupero dei risultati per il tentativo ${props.attemptId}:`, err);
    error.value = "Impossibile caricare i risultati del quiz. Riprova più tardi.";
    // Potrebbe essere utile gestire errori specifici (es. 404 Not Found)
  } finally {
    isLoading.value = false;
  }
}

function getStudentAnswerForQuestion(questionId: number) {
  // Corretto per usare 'given_answers' come definito nel serializer
  // Corretto per usare 'question' invece di 'question_id'
  return attemptDetails.value?.given_answers.find((ans: StudentAnswerResult) => ans.question === questionId);
}

function getQuestionById(questionId: number): Question | undefined {
    return attemptDetails.value?.questions.find(q => q.id === questionId);
}

// Modificato per accettare l'oggetto Question completo
function formatAnswer(answerData: any, question: Question): string {
    if (answerData === null || answerData === undefined) return 'Nessuna risposta';

    // Usa question.question_type dall'oggetto passato
    switch (question.question_type) {
        case 'MC_SINGLE': { // Usa il tipo corretto dal backend
            const optionId = answerData.answer_option_id;
            // Usa direttamente l'oggetto question passato
            const option = question.answer_options?.find(opt => opt.id === optionId);
            return option ? option.text : 'Opzione non trovata';
        }
        case 'MC_MULTI': { // Usa il tipo corretto dal backend
            const optionIds = answerData.answer_option_ids || [];
            // Usa direttamente l'oggetto question passato
            const selectedTexts = optionIds
                .map((id: number) => question.answer_options?.find(opt => opt.id === id)?.text)
                .filter(Boolean); // Filtra eventuali undefined
            return selectedTexts.length > 0 ? selectedTexts.join(', ') : 'Nessuna opzione selezionata';
        }
        case 'TF': // Usa il tipo corretto dal backend
            return answerData.is_true ? 'Vero' : 'Falso';
        case 'FILL_BLANK': { // Usa il tipo corretto dal backend
            // Assumendo che answerData.answers sia ora una lista di stringhe come salvato nel backend
            const answersList = answerData.answers || [];
            return answersList.map((ans: string, index: number) => `#${index + 1}: ${ans}`).join('; ');
        }
        case 'OPEN_MANUAL': // Usa il tipo corretto dal backend
            // Assumendo che la chiave sia 'answer_text' come nella validazione backend
            return answerData.answer_text || 'Nessuna risposta fornita';
        default:
            return JSON.stringify(answerData); // Fallback
    }
}

function getCorrectnessClass(isCorrect: boolean | null): string {
    if (isCorrect === true) return 'correct-answer';
    if (isCorrect === false) return 'incorrect-answer';
    return 'pending-answer'; // Per risposte manuali non ancora corrette
}

function getCorrectnessText(isCorrect: boolean | null): string {
    if (isCorrect === true) return 'Corretta';
    if (isCorrect === false) return 'Errata';
    return 'In attesa di correzione';
}

// Calcola l'esito del quiz
const quizOutcome = computed(() => {
  if (!attemptDetails.value) return 'loading';
  const status = attemptDetails.value.status;
  // Converti score in numero (potrebbe essere stringa dall'API)
  const scoreString = attemptDetails.value.score;
  const score = typeof scoreString === 'string' ? parseFloat(scoreString) : scoreString; // Converte se stringa

  // Ottieni la soglia: prima dal tentativo, poi dai metadati del quiz
  let threshold = attemptDetails.value.completion_threshold;
  if (threshold === null && attemptDetails.value.quiz?.metadata?.completion_threshold !== undefined) {
    threshold = attemptDetails.value.quiz.metadata.completion_threshold;
  }

  // Usa i valori di stato MAIUSCOLI come definiti nel tipo aggiornato
  if (status === 'PENDING_GRADING') {
    return 'pending';
  }
  // Gestione stato COMPLETED
  // Gestione stato COMPLETED
  if (status === 'COMPLETED') {
    // Verifica se score è un numero valido (dopo la conversione)
    if (typeof score !== 'number' || isNaN(score)) { // Aggiunto controllo isNaN
        console.warn("Score non è un numero valido dopo la conversione:", scoreString, score);
        return 'unknown';
    }
    // Verifica se threshold è un numero valido (dopo averlo cercato)
    if (threshold !== null && typeof threshold === 'number') {
        return score >= threshold ? 'success' : 'failure';
    } else {
        // Se non c'è soglia valida (threshold è null o non è un numero),
        // considera COMPLETED come successo se score >= 0 (o altra logica di default se necessaria)
        console.warn("Soglia non valida o non definita, considerando successo se score >= 0. Soglia:", threshold);
        return score >= 0 ? 'success' : 'failure'; // Modificato: considera fallimento se score < 0
    }
  }
  // Gestione stato FAILED
  if (status === 'FAILED') {
    return 'failure';
  }
  return 'unknown'; // Fallback per stati inattesi o in_progress (non dovrebbe accadere qui)
});

// Funzione per lanciare i coriandoli
function triggerConfetti() {
   showConfetti.value = true; // Potresti usare questo per triggerare un componente/animazione CSS
   // Oppure usare direttamente la libreria:
   /*
   if (typeof confetti === 'function') {
       confetti({
           particleCount: 150,
           spread: 90,
           origin: { y: 0.6 }
       });
   }
   */
   console.log("Confetti triggered!"); // Placeholder
}

// Lifecycle Hooks
onMounted(async () => { // reso async
  await fetchAttemptResults();
  
  // La logica di notifica dei badge è stata spostata in QuizAttemptView.vue
  // Questa sezione può essere rimossa o commentata.
  /*
  if (attemptDetails.value && quizOutcome.value === 'success') {
      // ... vecchia logica rimossa ...
  }
  */

  // Trigger confetti solo se il risultato è successo al caricamento
  if (quizOutcome.value === 'success') {
      triggerConfetti();
  }
});

// Funzione per chiudere la modale
const handleClose = () => {
  emit('close');
};

// Calcola la soglia da visualizzare, gestendo decimali (0-1) e percentuali (0-100)
const displayThreshold = computed(() => {
  const thresholdValue = attemptDetails.value?.completion_threshold ?? attemptDetails.value?.quiz?.metadata?.completion_threshold;
  if (thresholdValue !== null && typeof thresholdValue === 'number') {
    // Se il valore è compreso tra 0 (escluso) e 1 (incluso), moltiplica per 100
    if (thresholdValue > 0 && thresholdValue <= 1) {
      return Math.round(thresholdValue * 100);
    }
    // Altrimenti, assumi sia già 0-100 e arrotonda
    return Math.round(thresholdValue);
  }
  return 'N/D'; // Fallback
});

</script>

<template>
  <div class="quiz-result-view">
    <!-- Titolo rimosso -->

    <div v-if="isLoading" class="loading">
      <p>Caricamento risultati...</p>
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>

    <div v-if="attemptDetails && !isLoading" class="results-container">
      <!-- Riepilogo Visivo Esito -->
      <div
        :class="[
          'outcome-summary',
          'p-6 rounded-lg mb-8 text-center shadow-md',
          { 'bg-green-100 border border-green-300 text-green-800': quizOutcome === 'success' },
          { 'bg-red-100 border border-red-300 text-red-800': quizOutcome === 'failure' },
          { 'bg-yellow-100 border border-yellow-300 text-yellow-800': quizOutcome === 'pending' },
          { 'bg-gray-100 border border-gray-300 text-gray-800': quizOutcome === 'unknown' || quizOutcome === 'loading' }
        ]"
      >
        <div v-if="quizOutcome === 'success'" class="outcome-content animate-fade-in">
          <span class="text-5xl mb-2 block">🎉</span>
          <h3 class="text-2xl font-semibold mb-2">Complimenti! Quiz Superato!</h3>
          <p class="text-lg">Punteggio: <strong>{{ Math.round(attemptDetails.score ?? 0) }}%</strong></p>
          <p>Hai risposto correttamente a <strong>{{ attemptDetails.correct_answers_count ?? '?' }}</strong> su <strong>{{ attemptDetails.total_questions ?? '?' }}</strong> domande.</p>
          <!-- Placeholder per animazione confetti attivata da showConfetti -->
          <div v-if="showConfetti" class="confetti-placeholder"></div>
        </div>
        <div v-else-if="quizOutcome === 'failure'" class="outcome-content animate-fade-in">
          <span class="text-5xl mb-2 block">😥</span>
          <h3 class="text-2xl font-semibold mb-2">Peccato! Non hai superato il quiz.</h3>
          <p class="text-lg">Punteggio: <strong>{{ Math.round(attemptDetails.score ?? 0) }}%</strong> (Soglia: {{ displayThreshold }}%)</p>
          <p>Hai risposto correttamente a <strong>{{ attemptDetails.correct_answers_count ?? '?' }}</strong> su <strong>{{ attemptDetails.total_questions ?? '?' }}</strong> domande.</p>
          <p class="mt-2 text-sm">Non arrenderti, riprova se possibile!</p>
        </div>
        <div v-else-if="quizOutcome === 'pending'" class="outcome-content animate-fade-in">
          <span class="text-5xl mb-2 block">⏳</span>
          <h3 class="text-2xl font-semibold mb-2">Risultato in attesa</h3>
          <p>Il tuo punteggio finale sarà disponibile dopo la correzione manuale da parte del docente.</p>
        </div>
        <div v-else class="outcome-content">
          <p>Stato del tentativo non determinato.</p>
        </div>
      </div>

      <!-- Dettagli Quiz e Risposte rimossi come richiesto -->

      <!-- Modificato per emettere 'close' invece di navigare -->
      <button @click="handleClose" class="back-button">Chiudi</button>
    </div>
  </div>
</template>

<style scoped>
.quiz-result-view {
  padding: 20px;
  max-width: 900px;
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

.results-container {
  margin-top: 20px;
  padding: 25px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #fff;
}

.summary-scores {
    background-color: #e9f5ff;
    border: 1px solid #b3d7ff;
    padding: 15px;
    margin: 20px 0;
    border-radius: 5px;
}
.summary-scores.pending {
    background-color: #fff8e1;
    border-color: #ffecb3;
}

.summary-scores p {
    margin: 5px 0;
    font-size: 1.1em;
}

.answers-list {
  list-style: none;
  padding: 0;
  margin-top: 30px;
}

.answer-item {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px dashed #eee;
}
.answer-item:last-child {
    border-bottom: none;
}

.question-text {
  font-size: 1.1em;
  margin-bottom: 10px;
  color: #333;
}

.student-answer {
  padding: 10px;
  border-radius: 4px;
  margin-top: 5px;
  border-left-width: 5px;
  border-left-style: solid;
}

.student-answer p {
    margin: 4px 0;
}

.correct-answer {
  background-color: #d4edda;
  border-left-color: #28a745;
}

.incorrect-answer {
  background-color: #f8d7da;
  border-left-color: #dc3545;
}

.pending-answer {
  background-color: #fff3cd;
  border-left-color: #ffc107;
}
.no-answer {
    background-color: #e9ecef;
    border-left-color: #6c757d;
    font-style: italic;
}

.back-button {
  margin-top: 30px;
  padding: 10px 20px;
  font-size: 1em;
  cursor: pointer;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 5px;
  transition: background-color 0.3s ease;
}

.back-button:hover {
  background-color: #5a6268;
}

h1, h2, h3 {
    color: #333;
}

/* Animazione Fade-in */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fadeIn 0.5s ease-out forwards;
}

/* Placeholder per animazione confetti */
.confetti-placeholder {
  /* Qui potresti aggiungere stili per un componente confetti o triggerare JS */
  min-height: 50px; /* Solo per dare spazio visivo */
}

</style>