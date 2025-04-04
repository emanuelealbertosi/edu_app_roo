<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import PathwayService, { type PathwayAttemptDetails } from '@/api/pathway'; // Importa il tipo corretto

// State
const route = useRoute();
const router = useRouter();
const pathwayDetails = ref<PathwayAttemptDetails | null>(null); // Usa il tipo corretto
const isLoading = ref(true);
const error = ref<string | null>(null);

const pathwayId = computed(() => Number(route.params.pathwayId));

// Funzioni
async function fetchPathwayResults() {
  if (!pathwayId.value) {
    error.value = "ID del percorso non valido.";
    isLoading.value = false;
    return;
  }
  isLoading.value = true;
  error.value = null;
  try {
    const rawData = await PathwayService.getPathwayAttemptDetails(pathwayId.value); // Chiama la funzione corretta
    console.log('[PathwayResultView] Raw data received:', JSON.stringify(rawData)); // Log raw data
    pathwayDetails.value = rawData;
    console.log('[PathwayResultView] Data assigned to pathwayDetails.value'); // Log after assignment
    // Potremmo aggiungere un controllo qui per assicurarsi che il percorso sia effettivamente completato
    // if (pathwayDetails.value?.progress?.status !== 'COMPLETED') { // Usa stato corretto
    //   // Forse reindirizzare altrove o mostrare un messaggio diverso?
    // }
  } catch (err) { // Error is caught here
    console.error(`[PathwayResultView] Error in try block for pathway ${pathwayId.value}:`, err); // Log error object
    // Also log specific properties if available
    if (err instanceof Error) {
        console.error('[PathwayResultView] Error name:', err.name);
        console.error('[PathwayResultView] Error message:', err.message);
        console.error('[PathwayResultView] Error stack:', err.stack);
    }
    error.value = "Impossibile caricare i risultati del percorso. Riprova più tardi.";
  } finally {
    isLoading.value = false;
  }
}

// Formatta la data
const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'N/D';
  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
};

// Lifecycle Hooks
onMounted(() => {
  fetchPathwayResults();
});

</script>

<template>
  <div class="pathway-result-view">
    <h1>Risultati del Percorso Formativo</h1>

    <div v-if="isLoading" class="loading">
      <p>Caricamento risultati...</p>
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>

    <div v-if="pathwayDetails && !isLoading" class="results-container">
      <h2>{{ pathwayDetails.title }}</h2>
      <p><strong>Descrizione:</strong> {{ pathwayDetails.description }}</p>
      
      <div v-if="pathwayDetails.progress" class="summary-scores"
           :class="{ 'completed': pathwayDetails.progress.status === 'COMPLETED', 'in-progress': pathwayDetails.progress.status !== 'COMPLETED' }">
         <p><strong>Stato:</strong> {{ pathwayDetails.progress.status === 'COMPLETED' ? 'Completato' : 'In Corso' }}</p>
          <p v-if="pathwayDetails.progress.completed_at"><strong>Completato il:</strong> {{ formatDate(pathwayDetails.progress.completed_at) }}</p>
          <p><strong>Punti Guadagnati:</strong> {{ pathwayDetails.progress.points_earned ?? 0 }}</p>
      </div>
       <div v-else class="summary-scores not-started">
          <p>Questo percorso non è stato ancora iniziato.</p>
      </div>

      <!-- Opzionale: Elenco dei quiz nel percorso e il loro stato -->
      <h3>Quiz nel Percorso</h3>
      <ul class="quiz-list-in-pathway">
        <!-- Modificato per iterare su quiz_details e usare i dati corretti -->
        <li v-for="quizDetail in pathwayDetails.quiz_details" :key="quizDetail.quiz_id"
            :class="{ 'quiz-completed': pathwayDetails.progress?.completed_orders?.includes(quizDetail.order) }">
          <span class="quiz-order">{{ quizDetail.order + 1 }}.</span>
          <span class="quiz-title">{{ quizDetail.quiz_title }}</span>
          <span class="quiz-status-indicator">
             {{ pathwayDetails.progress?.completed_orders?.includes(quizDetail.order) ? '✔ Completato' : 'Non Completato' }}
          </span>
          <!-- TODO: Aggiungere link ai risultati del singolo quiz se necessario,
                     richiede di recuperare l'attempt_id corretto per questo quiz
                     all'interno di questo percorso -->
          <!-- <router-link
             v-if="pathwayDetails.progress?.completed_orders?.includes(quizDetail.order) && getAttemptIdForQuiz(quizDetail.quiz_id)"
             :to="{ name: 'QuizResult', params: { attemptId: getAttemptIdForQuiz(quizDetail.quiz_id) } }"
             class="view-quiz-results-link">
             Vedi Risultati Quiz
          </router-link> -->
        </li>
      </ul>

      <button @click="router.push('/dashboard')" class="back-button">Torna alla Dashboard</button>
    </div>
  </div>
</template>

<style scoped>
.pathway-result-view {
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
    border: 1px solid;
    padding: 15px;
    margin: 20px 0;
    border-radius: 5px;
}
.summary-scores.completed {
    background-color: #e9f5ff;
    border-color: #b3d7ff;
}
.summary-scores.in-progress {
    background-color: #fff8e1;
    border-color: #ffecb3;
}
.summary-scores.not-started {
    background-color: #f8f9fa;
    border-color: #dee2e6;
}

.summary-scores p {
    margin: 5px 0;
    font-size: 1.1em;
}

.quiz-list-in-pathway {
    list-style: none;
    padding: 0;
    margin-top: 20px;
}

.quiz-list-in-pathway li {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 4px;
    border: 1px solid #eee;
}

.quiz-list-in-pathway li.quiz-completed {
    background-color: #e8f5e9; /* Verde chiaro */
    border-left: 4px solid #4caf50;
}
.quiz-list-in-pathway li.quiz-available {
    background-color: #e3f2fd; /* Blu chiaro */
     border-left: 4px solid #2196f3;
}
.quiz-list-in-pathway li.quiz-locked {
    background-color: #f5f5f5; /* Grigio chiaro */
    color: #999;
    border-left: 4px solid #bdbdbd;
}


.quiz-order {
    font-weight: bold;
    min-width: 20px;
}

.quiz-title {
    flex-grow: 1;
}

.quiz-status-indicator {
    font-size: 0.9em;
    font-style: italic;
}

.view-quiz-results-link {
    margin-left: auto;
    font-size: 0.9em;
    color: #007bff;
    text-decoration: none;
    padding: 3px 8px;
    border: 1px solid #007bff;
    border-radius: 3px;
    transition: background-color 0.2s, color 0.2s;
}
.view-quiz-results-link:hover {
    background-color: #007bff;
    color: white;
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