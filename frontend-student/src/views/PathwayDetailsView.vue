<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { usePathwayStore } from '@/stores/pathway';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const pathwayStore = usePathwayStore();

// Ottiene l'ID del percorso dai parametri dell'URL
const pathwayId = computed(() => parseInt(route.params.id as string));

const isLoading = ref(true);

// All'avvio del componente, verifichiamo lo stato dell'autenticazione e carichiamo i dettagli del percorso
onMounted(async () => {
  const isAuthenticated = await authStore.checkAuth();
  if (!isAuthenticated) {
    router.push('/login');
    return;
  }
  
  isLoading.value = true;
  
  try {
    // Carica i dettagli del percorso
    await pathwayStore.loadPathwayDetails(pathwayId.value);
  } catch (error) {
    console.error('Errore nel caricamento dei dettagli del percorso:', error);
  } finally {
    isLoading.value = false;
  }
});

// // Avvia un quiz specifico del percorso (Funzione deprecata nello store)
// const startQuiz = async (quizId: number) => {
//   isLoading.value = true;
  
//   try {
//     // const attemptId = await pathwayStore.startQuiz(quizId); // Azione commentata nello store
//     console.warn("Tentativo di chiamare startQuiz deprecato da PathwayDetailsView");
//     // router.push(`/quiz/${quizId}/attempt/${attemptId}`); // Non più possibile ottenere attemptId qui
//   } catch (error) {
//     console.error('Errore nell\'avvio del quiz:', error);
//   } finally {
//     isLoading.value = false;
//   }
// };

// Torna alla dashboard
const goToDashboard = () => {
  router.push('/dashboard');
};

// Calcola lo stato di un quiz basandosi sul progresso
const getQuizStatus = (quizOrder: number): { isCompleted: boolean; isAvailable: boolean } => {
  const progress = pathwayStore.currentPathway?.progress;
  const isCompleted = !!progress?.completed_orders?.includes(quizOrder);
  
  // Disponibile se è il primo non completato o se il percorso non è iniziato ed è il primo quiz
  const lastCompletedOrder = progress?.last_completed_quiz_order ?? -1;
  const isAvailable = !isCompleted && (quizOrder === lastCompletedOrder + 1 || (!progress && quizOrder === 0));
  
  return { isCompleted, isAvailable };
};

// Determina la classe CSS per lo stato di un quiz
const getQuizStatusClass = (quizOrder: number) => {
  const { isCompleted, isAvailable } = getQuizStatus(quizOrder);
  if (isCompleted) return 'quiz-completed';
  if (isAvailable) return 'quiz-available';
  return 'quiz-locked';
};

// Genera l'etichetta per lo stato di un quiz
const getQuizStatusLabel = (quizOrder: number) => {
  const { isCompleted, isAvailable } = getQuizStatus(quizOrder);
  if (isCompleted) return 'Completato';
  if (isAvailable) return 'Disponibile';
  return 'Bloccato';
};
</script>

<template>
  <div class="pathway-details-view">
    <header class="pathway-header">
      <div v-if="isLoading" class="loading-header">
        <div class="loading-spinner"></div>
        <p>Caricamento in corso...</p>
      </div>
      
      <div v-else-if="!pathwayStore.currentPathway" class="error-header">
        <h1>Percorso non trovato</h1>
        <p>Il percorso richiesto non esiste o non hai accesso ad esso.</p>
        <button @click="goToDashboard" class="back-button">
          <span class="button-icon">🏠</span> Torna alla Dashboard
        </button>
      </div>
      
      <div v-else class="pathway-info">
        <div class="header-top">
          <h1>{{ pathwayStore.currentPathway.title }}</h1>
          <button @click="goToDashboard" class="back-button">
            <span class="button-icon">🏠</span> Torna alla Dashboard
          </button>
        </div>
        
        <p class="pathway-description">{{ pathwayStore.currentPathway.description }}</p>
        
        <div class="pathway-progress">
          <div class="progress-label">
            <span>Completamento: {{ pathwayStore.completionPercentage }}%</span>
            <span v-if="pathwayStore.isPathwayCompleted" class="completion-badge">
              Percorso Completato
            </span>
          </div>
          
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: `${pathwayStore.completionPercentage}%` }"
            ></div>
          </div>
        </div>
        
        <div v-if="pathwayStore.isPathwayCompleted && pathwayStore.currentPathway.progress?.points_earned" class="points-earned"> <!-- Aggiunto ?. -->
          <span class="points-icon">🏆</span>
          <span class="points-text">
            Hai guadagnato {{ pathwayStore.currentPathway.progress?.points_earned }} punti <!-- Aggiunto ?. -->
            completando questo percorso!
          </span>
        </div>
      </div>
    </header>
    
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Caricamento in corso...</p>
    </div>
    
    <div v-else-if="!pathwayStore.currentPathway" class="error-container">
      <p class="error-message">Impossibile caricare il percorso.</p>
    </div>
    
    <div v-else class="pathway-content">
      <section class="quizzes-section">
        <h2>Quiz in questo Percorso</h2>
        
        <!-- Usa quiz_details -->
        <div v-if="pathwayStore.currentPathway.quiz_details.length === 0" class="empty-quizzes">
          <p>Questo percorso non contiene quiz.</p>
        </div>
        
        <div v-else class="quizzes-list">
          <div 
            <!-- Usa quiz_details -->
            v-for="quiz in pathwayStore.currentPathway.quiz_details"
            :key="quiz.id"
            class="quiz-item"
            <!-- Calcola classe basata sull'ordine -->
            :class="getQuizStatusClass(quiz.order)"
          >
            <div class="quiz-position">{{ quiz.order + 1 }}</div>
            
            <div class="quiz-content">
              <!-- Usa quiz_title, rimuove description -->
              <h3 class="quiz-title">{{ quiz.quiz_title }}</h3>
              <!-- <p class="quiz-description">{{ quiz.description }}</p> -->
              
              <!-- Calcola status basato sull'ordine -->
              <div class="quiz-status">
                <span :class="['status-badge', getQuizStatusClass(quiz.order)]">
                  {{ getQuizStatusLabel(quiz.order) }}
                </span>
              </div>
            </div>
            
            <div class="quiz-action">
              <!-- Pulsante startQuiz commentato perché la funzione è deprecata -->
              <!--
                <button
                  v-if="getQuizStatus(quiz.order).isAvailable && !getQuizStatus(quiz.order).isCompleted"
                  @click="startQuiz(quiz.quiz_id)" // Usa quiz_id
                  class="start-quiz-button"
                  :disabled="isLoading"
                >
                  {{ isLoading ? 'Caricamento...' : 'Inizia Quiz' }}
                </button>
              -->
              <!-- Mostra un messaggio o un link alternativo se necessario -->
              <span v-if="getQuizStatus(quiz.order).isAvailable && !getQuizStatus(quiz.order).isCompleted" class="text-gray-500 text-sm">
                (Avvio quiz da implementare)
              </span>
              
              <button 
                v-else-if="getQuizStatus(quiz.order).isCompleted"
                @click="router.push(`/quiz/${quiz.quiz_id}`)"
                class="view-quiz-button"
              >
                Visualizza Risultati
              </button>
              
              <span v-else class="quiz-locked-message">
                <span class="lock-icon">🔒</span> Completa i quiz precedenti
              </span>
            </div>
          </div>
        </div>
      </section>
      
      <div v-if="pathwayStore.nextAvailableQuiz" class="next-quiz-action">
        <h3>Continua il Percorso</h3>
        <p>Prossimo quiz disponibile: <strong>{{ pathwayStore.nextAvailableQuiz.title }}</strong></p>
        <!-- Pulsante startQuiz commentato perché la funzione è deprecata -->
        <!--
          <button
            @click="startQuiz(pathwayStore.nextAvailableQuiz.id)"
            class="continue-button"
            :disabled="isLoading"
          >
            {{ isLoading ? 'Caricamento...' : 'Continua Percorso' }}
          </button>
        -->
        <p v-if="!isLoading" class="text-gray-500 text-sm">(Funzione "Continua Percorso" da rivedere)</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pathway-details-view {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.pathway-header {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.pathway-header h1 {
  margin: 0;
  color: #333;
}

.pathway-description {
  color: #666;
  margin-bottom: 1.5rem;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.back-button:hover {
  background-color: #1e88e5;
}

.button-icon {
  font-size: 1.1rem;
}

.pathway-progress {
  margin-bottom: 1rem;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #666;
}

.completion-badge {
  background-color: #4caf50;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.progress-bar {
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #4caf50;
  transition: width 0.3s ease;
}

.points-earned {
  margin-top: 1rem;
  background-color: #e8f5e9;
  color: #388e3c;
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.points-icon {
  font-size: 1.5rem;
}

.points-text {
  font-weight: 500;
}

.quizzes-section {
  margin-bottom: 2rem;
}

.quizzes-section h2 {
  margin-bottom: 1.5rem;
  color: #333;
}

.quizzes-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.quiz-item {
  display: flex;
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.quiz-item:hover {
  transform: translateY(-2px);
}

.quiz-position {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 50px;
  background-color: #e0e0e0;
  color: #333;
  font-weight: bold;
  font-size: 1.2rem;
}

.quiz-content {
  flex: 1;
  padding: 1rem;
  border-right: 1px solid #eee;
}

.quiz-title {
  margin-top: 0;
  margin-bottom: 0.5rem;
  color: #333;
}

.quiz-description {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}

.quiz-status {
  display: flex;
  align-items: center;
}

.status-badge {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.quiz-action {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  min-width: 150px;
}

.start-quiz-button, .view-quiz-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.start-quiz-button {
  background-color: #4caf50;
  color: white;
}

.start-quiz-button:hover {
  background-color: #388e3c;
}

.view-quiz-button {
  background-color: #2196f3;
  color: white;
}

.view-quiz-button:hover {
  background-color: #1e88e5;
}

.quiz-locked-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
  font-size: 0.9rem;
}

.lock-icon {
  font-size: 1.1rem;
}

.quiz-completed {
  border-left: 4px solid #4caf50;
}

.quiz-completed .quiz-position {
  background-color: #e8f5e9;
  color: #388e3c;
}

.quiz-available {
  border-left: 4px solid #2196f3;
}

.quiz-available .quiz-position {
  background-color: #e3f2fd;
  color: #1976d2;
}

.quiz-locked {
  border-left: 4px solid #9e9e9e;
  opacity: 0.7;
}

.status-badge.quiz-completed {
  background-color: #e8f5e9;
  color: #388e3c;
  border: none;
}

.status-badge.quiz-available {
  background-color: #e3f2fd;
  color: #1976d2;
  border: none;
}

.status-badge.quiz-locked {
  background-color: #f5f5f5;
  color: #9e9e9e;
  border: none;
}

.next-quiz-action {
  background-color: white;
  border-radius: 8px;
  padding: L.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.next-quiz-action h3 {
  margin-top: 0;
  color: #333;
}

.continue-button {
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.continue-button:hover {
  background-color: #388e3c;
}

.continue-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading-container, .error-container, .loading-header, .error-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
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
  color: #d32f2f;
  font-weight: 500;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .header-top {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .quiz-item {
    flex-direction: column;
  }
  
  .quiz-position {
    width: 100%;
    padding: 0.5rem;
  }
  
  .quiz-action {
    width: 100%;
    border-top: 1px solid #eee;
    padding: 1rem;
  }
}
</style>