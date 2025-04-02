<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import QuizService, { type AttemptDetails, type Question, type StudentAnswerResult } from '@/api/quiz'; // Aggiunto StudentAnswerResult

// State
const route = useRoute();
const router = useRouter();
const attemptDetails = ref<AttemptDetails | null>(null);
const isLoading = ref(true);
const error = ref<string | null>(null);

const attemptId = computed(() => Number(route.params.attemptId));

// Funzioni
async function fetchAttemptResults() {
  if (!attemptId.value) {
    error.value = "ID del tentativo non valido.";
    isLoading.value = false;
    return;
  }
  isLoading.value = true;
  error.value = null;
  try {
    attemptDetails.value = await QuizService.getAttemptDetails(attemptId.value);
  } catch (err) {
    console.error(`Errore durante il recupero dei risultati per il tentativo ${attemptId.value}:`, err);
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


// Lifecycle Hooks
onMounted(() => {
  fetchAttemptResults();
});

</script>

<template>
  <div class="quiz-result-view">
    <h1>Risultati del Quiz</h1>

    <div v-if="isLoading" class="loading">
      <p>Caricamento risultati...</p>
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>

    <div v-if="attemptDetails &amp;&amp; !isLoading" class="results-container">
      <h2>{{ attemptDetails.quiz.title }}</h2>
      <p><strong>Descrizione:</strong> {{ attemptDetails.quiz.description }}</p>
      <p><strong>Stato:</strong> {{ attemptDetails.status }}</p>
      <p v-if="attemptDetails.completed_at"><strong>Completato il:</strong> {{ new Date(attemptDetails.completed_at).toLocaleString() }}</p>
      
      <div v-if="attemptDetails.status === 'completed'" class="summary-scores">
          <p><strong>Punteggio Finale:</strong> {{ attemptDetails.score !== null ? Math.round(attemptDetails.score) : 'N/D' }}%</p> <!-- Aggiunto % e arrotondamento -->
          <!-- <p><strong>Punti Guadagnati:</strong> {{ attemptDetails.points_earned ?? 0 }}</p> --> <!-- Rimosso: points_earned non è sul modello Attempt -->
      </div>
       <div v-else-if="attemptDetails.status === 'pending_manual_grading'" class="summary-scores pending">
          <p>Il punteggio finale e i punti guadagnati saranno disponibili dopo la correzione manuale.</p>
      </div>

      <h3>Dettaglio Risposte</h3>
      <ul class="answers-list">
        <li v-for="question in attemptDetails.questions" :key="question.id" class="answer-item">
          <p class="question-text"><strong>{{ question.order + 1 }}. {{ question.text }}</strong> ({{ question.question_type }})</p> <!-- Corretto numero domanda -->
          <div v-if="getStudentAnswerForQuestion(question.id)" :class="['student-answer', getCorrectnessClass(getStudentAnswerForQuestion(question.id)?.is_correct ?? null)]"> <!-- Aggiunto ?? null -->
            <!-- Passa l'intero oggetto question a formatAnswer -->
            <p><strong>Tua Risposta:</strong> {{ formatAnswer(getStudentAnswerForQuestion(question.id)?.selected_answers, question) }}</p>
            <p><strong>Esito:</strong> {{ getCorrectnessText(getStudentAnswerForQuestion(question.id)?.is_correct ?? null) }} <!-- Aggiunto ?? null -->
               <span v-if="getStudentAnswerForQuestion(question.id)?.score !== null"> (Punti: {{ getStudentAnswerForQuestion(question.id)?.score }})</span>
            </p>
            <!-- Qui potremmo aggiungere la risposta corretta se disponibile e se vogliamo mostrarla -->
          </div>
          <div v-else class="student-answer no-answer">
            <p>Nessuna risposta fornita.</p>
          </div>
        </li>
      </ul>

      <button @click="router.push('/dashboard')" class="back-button">Torna alla Dashboard</button>
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
</style>