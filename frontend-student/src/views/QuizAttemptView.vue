<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useQuizStore } from '@/stores/quiz';
import type { Answer } from '@/api/quiz';

const props = defineProps<{
  quizId: string;
  attemptId: string;
}>();

const authStore = useAuthStore();
const quizStore = useQuizStore();
const router = useRouter();

// Converte i parametri da string a number
const quizIdNum = computed(() => parseInt(props.quizId));
const attemptIdNum = computed(() => parseInt(props.attemptId));

const isLoading = ref(true);
const error = ref('');
const selectedAnswers = ref<any>(null);
const showSubmitConfirmation = ref(false);
const countdownTimer = ref<number | null>(null);
const timeLeft = ref<number>(0);

// Per le domande fill_blank
const blankAnswers = ref<Record<string, string>>({});

// Stati calcolati
const currentQuestionIndex = computed(() => {
  if (!quizStore.attemptDetails || !quizStore.currentQuestion) return -1;
  
  return quizStore.attemptDetails.questions.findIndex(
    q => q.id === quizStore.currentQuestion?.id
  );
});

const totalQuestions = computed(() => {
  return quizStore.attemptDetails?.questions.length || 0;
});

const isLastQuestion = computed(() => {
  return currentQuestionIndex.value === totalQuestions.value - 1;
});

// All'avvio del componente, verifichiamo lo stato dell'autenticazione e carichiamo l'attempt
onMounted(async () => {
  const isAuthenticated = await authStore.checkAuth();
  if (!isAuthenticated) {
    router.push('/login');
    return;
  }
  
  isLoading.value = true;
  error.value = '';
  
  try {
    // Verifichiamo che l'attempt esista e appartenga all'utente corrente
    await loadAttemptAndQuestion();
  } catch (err) {
    console.error('Errore nel caricamento del tentativo:', err);
    error.value = 'Si è verificato un errore nel caricamento del tentativo. Riprova più tardi.';
  } finally {
    isLoading.value = false;
  }
});

// Carica i dettagli del tentativo e la domanda corrente
const loadAttemptAndQuestion = async () => {
  if (!quizStore.currentAttempt || quizStore.currentAttempt.id !== attemptIdNum.value) {
    // Se non abbiamo l'attempt corrente, lo dobbiamo caricare
    try {
      await quizStore.loadAttemptDetails();
    } catch (error) {
      console.error('Errore nel caricamento dei dettagli del tentativo:', error);
      throw new Error('Impossibile caricare i dettagli del tentativo');
    }
  }
  
  // Carichiamo la domanda corrente
  if (!quizStore.currentQuestion) {
    try {
      await quizStore.loadCurrentQuestion();
    } catch (error) {
      console.error('Errore nel caricamento della domanda corrente:', error);
      throw new Error('Impossibile caricare la domanda corrente');
    }
  }
  
  // Resettiamo le risposte selezionate
  resetSelectedAnswers();
};

// Resetta le risposte selezionate in base al tipo di domanda
const resetSelectedAnswers = () => {
  if (!quizStore.currentQuestion) return;
  
  switch (quizStore.currentQuestion.question_type) {
    case 'multiple_choice_single':
      selectedAnswers.value = null;
      break;
    case 'multiple_choice_multiple':
      selectedAnswers.value = [];
      break;
    case 'true_false':
      selectedAnswers.value = null;
      break;
    case 'fill_blank':
      blankAnswers.value = {};
      break;
    case 'open_answer_manual':
      selectedAnswers.value = '';
      break;
  }
};

// Quando cambia la domanda corrente, resetta le risposte selezionate
watch(() => quizStore.currentQuestion, (newQuestion) => {
  if (newQuestion) {
    resetSelectedAnswers();
  }
});

// Invia la risposta alla domanda corrente
const submitAnswer = async () => {
  if (!quizStore.currentQuestion) return;
  
  isLoading.value = true;
  error.value = '';
  
  try {
    // Prepara la risposta in base al tipo di domanda
    let answer: Answer;
    
    switch (quizStore.currentQuestion.question_type) {
      case 'multiple_choice_single':
        answer = { answer_option_id: selectedAnswers.value };
        break;
      case 'multiple_choice_multiple':
        answer = { answer_option_ids: selectedAnswers.value };
        break;
      case 'true_false':
        answer = { is_true: selectedAnswers.value };
        break;
      case 'fill_blank':
        answer = { answers: blankAnswers.value };
        break;
      case 'open_answer_manual':
        answer = { text: selectedAnswers.value };
        break;
      default:
        throw new Error('Tipo di domanda non supportato');
    }
    
    // Invia la risposta
    await quizStore.submitAnswer(quizStore.currentQuestion.id, answer);
    
    // Se non ci sono più domande o era l'ultima domanda, offriamo di completare il tentativo
    if (!quizStore.currentQuestion || isLastQuestion.value) {
      showSubmitConfirmation.value = true;
    }
  } catch (err) {
    console.error('Errore nell\'invio della risposta:', err);
    error.value = 'Si è verificato un errore nell\'invio della risposta. Riprova.';
  } finally {
    isLoading.value = false;
  }
};

// Completa il tentativo
const completeAttempt = async () => {
  if (!quizStore.currentAttempt) return;
  
  isLoading.value = true;
  error.value = '';
  
  try {
    await quizStore.completeAttempt();
    // Navighiamo alla pagina dei risultati (in questo caso torniamo ai dettagli del quiz)
    router.push(`/quiz/${quizIdNum.value}`);
  } catch (err) {
    console.error('Errore nel completamento del tentativo:', err);
    error.value = 'Si è verificato un errore nel completamento del tentativo. Riprova.';
    isLoading.value = false;
  }
};

// Controlla se la risposta è valida e può essere inviata
const isValidAnswer = computed(() => {
  if (!quizStore.currentQuestion) return false;
  
  switch (quizStore.currentQuestion.question_type) {
    case 'multiple_choice_single':
      return selectedAnswers.value !== null;
    case 'multiple_choice_multiple':
      return selectedAnswers.value && selectedAnswers.value.length > 0;
    case 'true_false':
      return selectedAnswers.value !== null;
    case 'fill_blank':
      // Verifichiamo che tutti i campi richiesti siano compilati
      const requiredBlankKeys = Object.keys(blankAnswers.value);
      return requiredBlankKeys.length > 0 && requiredBlankKeys.every(key => blankAnswers.value[key].trim() !== '');
    case 'open_answer_manual':
      return selectedAnswers.value && selectedAnswers.value.trim() !== '';
    default:
      return false;
  }
});

// Torna alla dashboard
const goToDashboard = () => {
  quizStore.resetStore();
  router.push('/dashboard');
};

// Sostituisce i segnaposti con campi di input nelle domande fill_blank
const renderFillBlankQuestion = (text: string) => {
  // Assumendo che i segnaposti sono nel formato __blank_N__ dove N è un indice
  const regex = /__blank_(\d+)__/g;
  let match;
  let result = text;
  
  while ((match = regex.exec(text)) !== null) {
    const placeholder = match[0];
    const index = match[1];
    const inputHtml = `<input 
      type="text" 
      class="blank-input" 
      placeholder="Inserisci la risposta" 
      v-model="blankAnswers.${index}"
    />`;
    
    result = result.replace(placeholder, inputHtml);
  }
  
  return result;
};
</script>

<template>
  <div class="quiz-attempt-view">
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Caricamento in corso...</p>
    </div>
    
    <div v-else-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
      <button @click="goToDashboard" class="back-button">Torna alla Dashboard</button>
    </div>
    
    <div v-else-if="!quizStore.currentQuestion && !showSubmitConfirmation" class="error-container">
      <p>Nessuna domanda disponibile o tentativo completato.</p>
      <button @click="goToDashboard" class="back-button">Torna alla Dashboard</button>
    </div>
    
    <div v-else-if="showSubmitConfirmation" class="quiz-complete-container">
      <div class="confirmation-card">
        <h2>Completare il tentativo?</h2>
        <p>Hai risposto a tutte le domande. Sei sicuro di voler completare il tentativo?</p>
        <div class="confirmation-actions">
          <button @click="completeAttempt" class="confirm-button" :disabled="isLoading">
            {{ isLoading ? 'Completamento in corso...' : 'Completa tentativo' }}
          </button>
          <button @click="showSubmitConfirmation = false" class="cancel-button">
            Rivedi le risposte
          </button>
        </div>
      </div>
    </div>
    
    <div v-else class="quiz-content">
      <header class="quiz-header">
        <div class="quiz-progress">
          <span class="question-counter">
            Domanda {{ currentQuestionIndex + 1 }} di {{ totalQuestions }}
          </span>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: `${((currentQuestionIndex + 1) / totalQuestions) * 100}%` }"
            ></div>
          </div>
        </div>
        
        <button @click="goToDashboard" class="exit-button">
          <span class="button-icon">✕</span> Esci
        </button>
      </header>
      
      <div class="question-card">
        <h2>{{ quizStore.currentQuestion.text }}</h2>
        
        <!-- Diverse visualizzazioni in base al tipo di domanda -->
        <div v-if="quizStore.currentQuestion.question_type === 'multiple_choice_single'" class="answer-options">
          <div 
            v-for="option in quizStore.currentQuestion.answer_options" 
            :key="option.id"
            class="option-item"
            :class="{ selected: selectedAnswers === option.id }"
            @click="selectedAnswers = option.id"
          >
            <div class="option-selector">
              <div class="radio-button"></div>
            </div>
            <div class="option-text">{{ option.text }}</div>
          </div>
        </div>
        
        <div v-else-if="quizStore.currentQuestion.question_type === 'multiple_choice_multiple'" class="answer-options">
          <div 
            v-for="option in quizStore.currentQuestion.answer_options" 
            :key="option.id"
            class="option-item"
            :class="{ selected: selectedAnswers && selectedAnswers.includes(option.id) }"
            @click="selectedAnswers = selectedAnswers ? 
              (selectedAnswers.includes(option.id) ? 
                selectedAnswers.filter(id => id !== option.id) : 
                [...selectedAnswers, option.id]) : 
              [option.id]"
          >
            <div class="option-selector">
              <div class="checkbox"></div>
            </div>
            <div class="option-text">{{ option.text }}</div>
          </div>
        </div>
        
        <div v-else-if="quizStore.currentQuestion.question_type === 'true_false'" class="true-false-options">
          <div 
            class="option-item"
            :class="{ selected: selectedAnswers === true }"
            @click="selectedAnswers = true"
          >
            <div class="option-selector">
              <div class="radio-button"></div>
            </div>
            <div class="option-text">Vero</div>
          </div>
          
          <div 
            class="option-item"
            :class="{ selected: selectedAnswers === false }"
            @click="selectedAnswers = false"
          >
            <div class="option-selector">
              <div class="radio-button"></div>
            </div>
            <div class="option-text">Falso</div>
          </div>
        </div>
        
        <div v-else-if="quizStore.currentQuestion.question_type === 'fill_blank'" class="fill-blank-container">
          <!-- Al posto di renderFillBlankQuestion che era un approccio non funzionale con Vue,
               creiamo markup basato sui segnaposti -->
          <template v-for="(part, index) in quizStore.currentQuestion.text.split(/(__blank_\d+__)/)" :key="index">
            <template v-if="part.match(/^__blank_(\d+)__$/)">
              <input 
                type="text" 
                class="blank-input" 
                placeholder="Inserisci la risposta" 
                v-model="blankAnswers[part.match(/^__blank_(\d+)__$/)[1]]"
              />
            </template>
            <template v-else>
              {{ part }}
            </template>
          </template>
        </div>
        
        <div v-else-if="quizStore.currentQuestion.question_type === 'open_answer_manual'" class="open-answer-container">
          <textarea 
            v-model="selectedAnswers"
            class="open-answer-input"
            placeholder="Inserisci la tua risposta..."
            rows="6"
          ></textarea>
        </div>
      </div>
      
      <div class="question-actions">
        <div v-if="quizStore.lastAnswerResult" class="answer-feedback">
          <div 
            v-if="quizStore.lastAnswerResult.is_correct !== null"
            :class="['feedback-message', quizStore.lastAnswerResult.is_correct ? 'correct' : 'incorrect']"
          >
            {{ quizStore.lastAnswerResult.is_correct ? 'Risposta corretta!' : 'Risposta errata.' }}
            <span v-if="quizStore.lastAnswerResult.message">{{ quizStore.lastAnswerResult.message }}</span>
          </div>
          <div v-else class="feedback-message manual">
            La tua risposta sarà valutata manualmente.
          </div>
        </div>
        
        <div class="action-buttons">
          <button 
            @click="submitAnswer" 
            class="submit-button"
            :disabled="!isValidAnswer || isLoading"
          >
            {{ isLoading ? 'Invio in corso...' : 
              isLastQuestion ? 'Invia e completa' : 'Invia e continua' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quiz-attempt-view {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.quiz-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.quiz-progress {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 70%;
}

.question-counter {
  font-size: 0.9rem;
  color: #666;
}

.progress-bar {
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--vt-c-indigo);
  transition: width 0.3s ease;
}

.exit-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.exit-button:hover {
  background-color: #e0e0e0;
}

.question-card {
  background-color: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.question-card h2 {
  margin-top: 0;
  margin-bottom: 2rem;
  color: #333;
}

.answer-options, .true-false-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-item:hover {
  background-color: #f5f5f5;
}

.option-item.selected {
  border-color: var(--vt-c-indigo);
  background-color: rgba(70, 60, 190, 0.05);
}

.option-selector {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 24px;
  height: 24px;
}

.radio-button {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #ccc;
  position: relative;
}

.option-item.selected .radio-button {
  border-color: var(--vt-c-indigo);
}

.option-item.selected .radio-button::after {
  content: '';
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--vt-c-indigo);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #ccc;
  border-radius: 4px;
  position: relative;
}

.option-item.selected .checkbox {
  border-color: var(--vt-c-indigo);
  background-color: var(--vt-c-indigo);
}

.option-item.selected .checkbox::after {
  content: '✓';
  position: absolute;
  color: white;
  font-size: 14px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.option-text {
  flex: 1;
}

.fill-blank-container {
  line-height: 2;
}

.blank-input {
  display: inline-block;
  min-width: 150px;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  margin: 0 0.25rem;
  transition: border-color 0.2s;
}

.blank-input:focus {
  border-color: var(--vt-c-indigo);
  outline: none;
}

.open-answer-container {
  width: 100%;
}

.open-answer-input {
  width: 100%;
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: inherit;
  font-size: inherit;
  resize: vertical;
  transition: border-color 0.2s;
}

.open-answer-input:focus {
  border-color: var(--vt-c-indigo);
  outline: none;
}

.question-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.answer-feedback {
  padding: 1rem;
  border-radius: 8px;
}

.feedback-message {
  padding: 1rem;
  border-radius: 8px;
}

.feedback-message.correct {
  background-color: #e8f5e9;
  color: #388e3c;
  border-left: 4px solid #4caf50;
}

.feedback-message.incorrect {
  background-color: #ffebee;
  color: #d32f2f;
  border-left: 4px solid #f44336;
}

.feedback-message.manual {
  background-color: #e8eaf6;
  color: #3f51b5;
  border-left: 4px solid #3f51b5;
}

.action-buttons {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.submit-button {
  padding: 0.75rem 2rem;
  background-color: var(--vt-c-indigo);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.submit-button:hover:not(:disabled) {
  opacity: 0.9;
}

.submit-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
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

.quiz-complete-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
}

.confirmation-card {
  background-color: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  text-align: center;
}

.confirmation-card h2 {
  margin-top: 0;
  color: #333;
}

.confirmation-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .quiz-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .quiz-progress {
    width: 100%;
  }
  
  .confirmation-actions {
    flex-direction: column;
  }
}
</style>