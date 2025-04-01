<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useQuizStore } from '@/stores/quiz';

const props = defineProps<{
  id: string;
}>();

const authStore = useAuthStore();
const quizStore = useQuizStore();
const router = useRouter();

const quizId = computed(() => parseInt(props.id));
const isLoading = ref(true);
const error = ref('');
const showStartConfirmation = ref(false);

// Verifica se c'è un tentativo esistente non completato
const hasInProgressAttempt = computed(() => {
  if (!quizStore.attemptDetails) return false;
  return quizStore.attemptDetails.status === 'in_progress';
});

onMounted(async () => {
  // Verifichiamo che l'utente sia autenticato
  const isAuthenticated = await authStore.checkAuth();
  if (!isAuthenticated) {
    router.push('/login');
    return;
  }
  
  isLoading.value = true;
  error.value = '';
  
  try {
    // Carichiamo i dettagli del quiz
    await quizStore.loadQuiz(quizId.value);
  } catch (err) {
    console.error('Errore nel caricamento del quiz:', err);
    error.value = 'Si è verificato un errore nel caricamento del quiz. Riprova più tardi.';
  } finally {
    isLoading.value = false;
  }
});

// Inizia un nuovo tentativo per il quiz
const startAttempt = async () => {
  isLoading.value = true;
  error.value = '';
  
  try {
    // Iniziamo un nuovo tentativo
    await quizStore.startAttempt(quizId.value);
    
    // Navighiamo alla pagina del tentativo
    if (quizStore.currentAttempt) {
      router.push(`/quiz/${quizId.value}/attempt/${quizStore.currentAttempt.id}`);
    } else {
      throw new Error('Impossibile creare il tentativo');
    }
  } catch (err) {
    console.error('Errore nell\'avvio del tentativo:', err);
    error.value = 'Si è verificato un errore nell\'avvio del tentativo. Riprova più tardi.';
    isLoading.value = false;
  }
};

// Funzione per tornare alla dashboard
const goToDashboard = () => {
  quizStore.resetStore();
  router.push('/dashboard');
};

// Formatta la data in un formato più leggibile
const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'Non specificata';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<template>
  <div class="quiz-details-view">
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Caricamento in corso...</p>
    </div>
    
    <div v-else-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
      <button @click="goToDashboard" class="back-button">Torna alla Dashboard</button>
    </div>
    
    <div v-else-if="!quizStore.currentQuiz" class="error-container">
      <p class="error-message">Quiz non trovato.</p>
      <button @click="goToDashboard" class="back-button">Torna alla Dashboard</button>
    </div>
    
    <div v-else class="quiz-details-container">
      <header class="quiz-header">
        <button @click="goToDashboard" class="back-button">
          <span class="button-icon">←</span> Torna alla Dashboard
        </button>
      </header>
      
      <div class="quiz-info-card">
        <h1>{{ quizStore.currentQuiz.title }}</h1>
        
        <div class="quiz-metadata">
          <div v-if="quizStore.currentQuiz.metadata.difficulty" class="metadata-item">
            <span class="metadata-label">Difficoltà:</span>
            <span class="metadata-value">{{ quizStore.currentQuiz.metadata.difficulty }}</span>
          </div>
          
          <div v-if="quizStore.currentQuiz.metadata.subject" class="metadata-item">
            <span class="metadata-label">Materia:</span>
            <span class="metadata-value">{{ quizStore.currentQuiz.metadata.subject }}</span>
          </div>
          
          <div v-if="quizStore.currentQuiz.metadata.points_on_completion" class="metadata-item">
            <span class="metadata-label">Punti al completamento:</span>
            <span class="metadata-value">{{ quizStore.currentQuiz.metadata.points_on_completion }}</span>
          </div>
          
          <div v-if="quizStore.currentQuiz.metadata.completion_threshold" class="metadata-item">
            <span class="metadata-label">Soglia di superamento:</span>
            <span class="metadata-value">{{ Math.round(quizStore.currentQuiz.metadata.completion_threshold * 100) }}%</span>
          </div>
        </div>
        
        <div class="quiz-dates">
          <div v-if="quizStore.currentQuiz.available_from" class="date-item">
            <span class="date-label">Disponibile da:</span>
            <span class="date-value">{{ formatDate(quizStore.currentQuiz.available_from) }}</span>
          </div>
          
          <div v-if="quizStore.currentQuiz.available_until" class="date-item">
            <span class="date-label">Disponibile fino a:</span>
            <span class="date-value">{{ formatDate(quizStore.currentQuiz.available_until) }}</span>
          </div>
        </div>
        
        <div class="quiz-description">
          <p>{{ quizStore.currentQuiz.description }}</p>
        </div>
        
        <div class="quiz-actions">
          <button 
            v-if="!showStartConfirmation" 
            @click="showStartConfirmation = true" 
            class="start-button"
          >
            Inizia Quiz
          </button>
          
          <div v-if="showStartConfirmation" class="confirmation-dialog">
            <p>Sei sicuro di voler iniziare questo quiz?</p>
            <p>Una volta iniziato, dovrai completarlo in un'unica sessione.</p>
            <div class="confirmation-actions">
              <button @click="startAttempt" class="confirm-button" :disabled="isLoading">
                {{ isLoading ? 'Avvio in corso...' : 'Inizia ora' }}
              </button>
              <button @click="showStartConfirmation = false" class="cancel-button">
                Annulla
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quiz-details-view {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.quiz-header {
  margin-bottom: 2rem;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background-color: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.back-button:hover {
  background-color: #e0e0e0;
}

.button-icon {
  font-size: 1.2rem;
}

.quiz-info-card {
  background-color: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.quiz-info-card h1 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #333;
}

.quiz-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.metadata-item {
  background-color: #f8f9fa;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.metadata-label {
  font-weight: 500;
  color: #666;
}

.metadata-value {
  font-weight: 600;
  color: #333;
}

.quiz-dates {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
  color: #666;
}

.date-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.date-label {
  font-weight: 500;
}

.quiz-description {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.quiz-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.start-button {
  padding: 0.75rem 2rem;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.start-button:hover {
  background-color: #388e3c;
}

.confirmation-dialog {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #ff9800;
  text-align: center;
  width: 100%;
}

.confirmation-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1rem;
}

.confirm-button {
  padding: 0.75rem 1.5rem;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.confirm-button:hover:not(:disabled) {
  background-color: #388e3c;
}

.confirm-button:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.cancel-button {
  padding: 0.75rem 1.5rem;
  background-color: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.cancel-button:hover {
  background-color: #e0e0e0;
}

.loading-container, .error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: var(--vt-c-indigo);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.error-message {
  margin-bottom: 1.5rem;
  color: #d32f2f;
  font-weight: 500;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>