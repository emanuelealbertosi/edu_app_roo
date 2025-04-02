<script setup lang="ts">
import { useRouter } from 'vue-router';
import type { Quiz } from '@/api/dashboard';

const props = defineProps<{
  quizzes: Quiz[];
  title: string;
  emptyMessage: string;
  loading?: boolean;
}>();

const router = useRouter();

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

// Inizia un nuovo tentativo per il quiz
const startQuizAttempt = (quizId: number) => {
  // Reindirizza alla rotta specifica per iniziare un tentativo
  router.push({ name: 'quiz-start-attempt', params: { quizId } });
};

// Genera un'etichetta di stato per il tentativo più recente
const getAttemptStatusLabel = (quiz: Quiz): string => {
  if (!quiz.latest_attempt) return 'Non iniziato';
  
  switch (quiz.latest_attempt.status) {
    case 'in_progress':
      return 'In corso';
    case 'pending_manual_grading':
      return 'In attesa di valutazione';
    case 'completed':
      return `Completato (${quiz.latest_attempt.score !== null ? Math.round(quiz.latest_attempt.score * 100) : '?'}%)`;
    default:
      return quiz.latest_attempt.status;
  }
};

// Determina la classe CSS per lo stato del tentativo
const getStatusClass = (quiz: Quiz): string => {
  if (!quiz.latest_attempt) return 'status-not-started';
  
  switch (quiz.latest_attempt.status) {
    case 'in_progress':
      return 'status-in-progress';
    case 'pending_manual_grading':
      return 'status-pending';
    case 'completed':
      return 'status-completed';
    default:
      return '';
  }
};

// Determina se il pulsante "Inizia Quiz" debba essere mostrato
const shouldShowStartButton = (quiz: Quiz): boolean => {
  const now = new Date();

  // Controlla le date di disponibilità
  if (quiz.available_from && new Date(quiz.available_from) > now) {
    return false; // Non ancora disponibile
  }
  if (quiz.available_until && new Date(quiz.available_until) < now) {
    return false; // Scaduto
  }

  // Controlla lo stato dell'ultimo tentativo
  // Non mostrare se è completato o in attesa di valutazione
  if (quiz.latest_attempt) {
    const status = quiz.latest_attempt.status;
    // Corretto per usare i valori di stato maiuscoli dal backend
    if (status === 'COMPLETED' || status === 'PENDING_GRADING') {
       // Potremmo aggiungere logica qui per permettere nuovi tentativi se consentito
       return false;
    }
    // Potremmo anche voler nascondere il pulsante se è 'in_progress'
    // if (status === 'in_progress') return false;
  }

  // Se tutti i controlli passano, mostra il pulsante
  return true;
};
</script>

<template>
  <div class="quiz-list-card dashboard-card">
    <h2><span class="card-icon">📝</span> {{ title }}</h2>
    
    <div v-if="loading" class="loading-indicator">
      <p>Caricamento in corso...</p>
    </div>
    
    <div v-else-if="quizzes.length === 0" class="empty-message">
      <p>{{ emptyMessage }}</p>
    </div>
    
    <div v-else class="quiz-list">
      <div v-for="quiz in quizzes" :key="quiz.id" class="quiz-item">
        <div class="quiz-header">
          <h3>{{ quiz.title }}</h3>
          <span :class="['quiz-status', getStatusClass(quiz)]">{{ getAttemptStatusLabel(quiz) }}</span>
        </div>
        
        <p class="quiz-description">{{ quiz.description }}</p>
        
        <div class="quiz-metadata">
          <div v-if="quiz.metadata.difficulty" class="quiz-difficulty">
            Difficoltà: {{ quiz.metadata.difficulty }}
          </div>
          
          <div v-if="quiz.metadata.subject" class="quiz-subject">
            Materia: {{ quiz.metadata.subject }}
          </div>
          
          <div v-if="quiz.metadata.points_on_completion" class="quiz-points">
            Punti: {{ quiz.metadata.points_on_completion }}
          </div>
        </div>
        
        <!-- Nascondi le date se il quiz è completato -->
        <div v-if="quiz.latest_attempt?.status !== 'COMPLETED'" class="quiz-dates">
          <div v-if="quiz.available_from" class="quiz-available-from">
            Disponibile da: {{ formatDate(quiz.available_from) }}
          </div>
          
          <div v-if="quiz.available_until" class="quiz-available-until">
            Disponibile fino a: {{ formatDate(quiz.available_until) }}
          </div>
        </div>
        
        <!-- Pulsante Inizia Quiz (visibile solo se showStartButton è true) -->
        <button
          v-if="shouldShowStartButton(quiz)"
          @click.stop="startQuizAttempt(quiz.id)"
          class="start-quiz-button"
        >
          Inizia Quiz
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quiz-list-card {
  /* margin-bottom: 1.5rem; */ /* Rimosso: gestito dal gap del parent */
}

.quiz-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.quiz-item {
  background-color: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  /* Rimuovi cursor: pointer se non vuoi che l'intero item sia cliccabile */
  /* cursor: pointer; */
  transition: transform 0.2s, box-shadow 0.2s;
  border-left: 4px solid #ddd;
  position: relative; /* Necessario per posizionare il pulsante se si usa absolute */
  padding-bottom: 4rem; /* Aggiungi spazio per il pulsante */
}

.quiz-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.quiz-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.quiz-status {
  font-size: 0.85rem;
  padding: 0.25rem 0.6rem; /* Leggermente più padding orizzontale */
  border-radius: 12px; /* Più arrotondato */
  font-weight: 500;
}

.status-not-started {
  background-color: #e3f2fd;
  color: #1976d2;
  border: 1px solid #bbdefb; /* Bordo leggero */
}

.status-in-progress {
  background-color: #fff8e1;
  color: #ff8f00;
  border: 1px solid #ffecb3; /* Bordo leggero */
}

.status-pending {
  background-color: #fff3e0; /* Leggermente diverso per pending */
  color: #ef6c00;
  border: 1px solid #ffe0b2; /* Bordo leggero */
}

.status-completed {
  background-color: #e8f5e9;
  color: #388e3c;
  border: 1px solid #c8e6c9; /* Bordo leggero */
}

.quiz-description {
  color: #666;
  margin-bottom: 1rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.quiz-metadata {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.quiz-metadata > div {
  background-color: #f5f5f5;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.quiz-dates {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #666;
}

.loading-indicator,
.empty-message {
  padding: 1rem;
  text-align: center;
  color: #666;
}

.start-quiz-button {
  position: absolute; /* O usa flexbox/grid sul container .quiz-item */
  bottom: 1rem;
  right: 1rem;
  padding: 0.5rem 1rem;
  background-color: var(--vt-c-indigo); /* Usa il colore primario */
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.start-quiz-button:hover {
  background-color: #2c3e50; /* Scurisce leggermente all'hover */
}

.card-icon {
    margin-right: 0.5rem;
    font-size: 1em; /* Dimensione simile al titolo */
    vertical-align: baseline;
}
</style>