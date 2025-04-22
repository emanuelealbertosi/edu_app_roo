<script setup lang="ts">
import { ref, computed } from 'vue'; // Aggiungere ref e computed
import { useRouter } from 'vue-router';
import type { Quiz } from '@/api/dashboard';
import BaseModal from '@/components/common/BaseModal.vue'; // Importare la modale
import QuizDetailsView from '@/views/QuizDetailsView.vue'; // Importare la vista dettagli
import QuizAttemptView from '@/views/QuizAttemptView.vue'; // Importare la vista tentativo
import QuizResultView from '@/views/QuizResultView.vue'; // Importare la vista risultati
import BaseButton from '@/components/common/BaseButton.vue'; // Importare BaseButton per il footer

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

// Stato per la modale dei dettagli (rinominato per chiarezza)
const selectedQuizIdForDetails = ref<number | null>(null);
const isDetailsModalOpen = ref(false);

// Stato per la modale di tentativo
const quizIdForAttempt = ref<number | null>(null);
const isAttemptModalOpen = ref(false);

// Stato per la modale dei risultati
const attemptIdForResult = ref<number | null>(null);
const isResultModalOpen = ref(false);

// Computed per il titolo della modale dettagli (rinominato per chiarezza)
const selectedQuizForDetails = computed(() => {
  if (!selectedQuizIdForDetails.value) return null;
  return props.quizzes.find(q => q.id === selectedQuizIdForDetails.value);
});

// Funzioni per modale dettagli (rinominate per chiarezza)
const openDetailsModal = (quizId: number) => {
  selectedQuizIdForDetails.value = quizId;
  isDetailsModalOpen.value = true;
};
const closeDetailsModal = () => {
  isDetailsModalOpen.value = false;
  setTimeout(() => { selectedQuizIdForDetails.value = null; }, 300);
};

// Funzioni per modale tentativo
const openAttemptModal = (quizId: number) => {
  quizIdForAttempt.value = quizId;
  isAttemptModalOpen.value = true;
};
const closeAttemptModal = () => {
  isAttemptModalOpen.value = false;
  // Potremmo voler ricaricare i dati della dashboard qui se l'utente chiude a metà
  setTimeout(() => { quizIdForAttempt.value = null; }, 300);
};

// Gestisce l'avvio DALLA MODALE DETTAGLI
const handleStartAttemptFromDetails = (quizId: number) => {
  closeDetailsModal(); // Chiudi la modale dei dettagli
  openAttemptModal(quizId); // Apri la modale di tentativo
};

// Gestisce l'avvio DAL PULSANTE NELLA LISTA
const startQuizAttempt = (quizId: number) => {
  openAttemptModal(quizId); // Apri la modale di tentativo
};

// Gestisce il completamento del tentativo dalla modale
const handleAttemptCompleted = (attemptId: number) => {
  closeAttemptModal(); // Chiudi la modale di tentativo
  // Apri la modale dei risultati invece di navigare
  attemptIdForResult.value = attemptId;
  isResultModalOpen.value = true;
  // Potremmo voler ricaricare i dati della dashboard qui
};

// Funzione per chiudere la modale dei risultati
const closeResultModal = () => {
  isResultModalOpen.value = false;
  setTimeout(() => { attemptIdForResult.value = null; }, 300); // Ritarda reset per animazione
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

// Determina la classe CSS per il BORDO sinistro in base allo stato
const getStatusBorderClass = (quiz: Quiz): string => {
  if (!quiz.latest_attempt) return 'border-status-not-started'; // Usa la classe definita nello <style>

  switch (quiz.latest_attempt.status) {
    case 'in_progress':
      return 'border-status-in-progress';
    case 'pending_manual_grading':
      return 'border-status-pending';
    case 'completed':
      return 'border-status-completed';
    default:
      return 'border-status-not-started'; // Default a grigio
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
  <div class="quiz-list-card bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-bold text-purple-700 mb-4 flex items-center"><span class="text-2xl mr-2">📝</span> {{ title }}</h2>

    <div v-if="loading" class="loading-indicator text-center py-4 text-gray-500">
      <p>Caricamento quiz...</p>
    </div>

    <div v-else-if="quizzes.length === 0" class="empty-message text-center py-4 text-gray-500">
      <p>{{ emptyMessage }}</p>
    </div>
    
    <div v-else class="quiz-list space-y-4">
      <!-- Aggiungere @click qui -->
      <div
        v-for="quiz in quizzes"
        :key="quiz.id"
        class="quiz-item bg-gray-50 rounded-lg p-4 shadow border-l-4 relative pb-16 hover:shadow-lg transition-shadow duration-200 cursor-pointer"
        :class="getStatusBorderClass(quiz)"
        @click="openDetailsModal(quiz.id)"
      >
        <!-- Contenuto dell'item (invariato, tranne il pulsante sotto) -->
        <div class="quiz-header flex justify-between items-center mb-2">
          <h3 class="font-semibold text-lg text-gray-800">{{ quiz.title }}</h3>
          <span :class="['quiz-status text-xs font-medium px-3 py-1 rounded-full', getStatusClass(quiz)]">{{ getAttemptStatusLabel(quiz) }}</span>
        </div>
        
        <p class="quiz-description text-gray-600 text-sm mb-3 line-clamp-2">{{ quiz.description }}</p>

        <div class="quiz-metadata flex flex-wrap gap-2 text-xs mb-3">
          <div v-if="quiz.metadata.difficulty" class="quiz-difficulty bg-gray-200 text-gray-700 px-2 py-1 rounded">
            Difficoltà: {{ quiz.metadata.difficulty }}
          </div>

          <div v-if="quiz.metadata.subject" class="quiz-subject bg-gray-200 text-gray-700 px-2 py-1 rounded">
            Materia: {{ quiz.metadata.subject }}
          </div>

          <div v-if="quiz.metadata.points_on_completion" class="quiz-points bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            Punti: {{ quiz.metadata.points_on_completion }}
          </div>
        </div>
        
        <!-- Nascondi le date se il quiz è completato -->
        <div v-if="quiz.latest_attempt?.status !== 'COMPLETED'" class="quiz-dates flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
          <div v-if="quiz.available_from" class="quiz-available-from">
            <span class="font-medium">Da:</span> {{ formatDate(quiz.available_from) }}
          </div>

          <div v-if="quiz.available_until" class="quiz-available-until">
             <span class="font-medium">Fino a:</span> {{ formatDate(quiz.available_until) }}
          </div>
        </div>
        
        <!-- Pulsante Inizia Quiz (visibile solo se showStartButton è true) -->
        <button
          v-if="shouldShowStartButton(quiz)"
          @click.stop="startQuizAttempt(quiz.id)"
          class="start-quiz-button absolute bottom-4 right-4 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg shadow transition-colors duration-200 z-10"
        >
          Inizia Quiz ▶
        </button>
      </div>
    </div>

    <!-- Modale per i Dettagli del Quiz (aggiornare refs) -->
    <BaseModal
      :show="isDetailsModalOpen"
      @close="closeDetailsModal"
      :title="selectedQuizForDetails?.title || 'Dettagli Quiz'"
    >
      <QuizDetailsView
        v-if="selectedQuizIdForDetails"
        :id="String(selectedQuizIdForDetails)"
      />
       <template #footer>
         <BaseButton variant="secondary" @click="closeDetailsModal">Chiudi</BaseButton>
         <!-- Aggiungiamo un pulsante Inizia qui, che chiama la nostra funzione -->
         <BaseButton
            v-if="selectedQuizIdForDetails && shouldShowStartButton(selectedQuizForDetails!)"
            variant="success"
            @click="handleStartAttemptFromDetails(selectedQuizIdForDetails!)"
          >
            Inizia Quiz
          </BaseButton>
       </template>
    </BaseModal>

    <!-- Modale per lo Svolgimento del Quiz -->
    <BaseModal
      :show="isAttemptModalOpen"
      @close="closeAttemptModal"
      title="Svolgimento Quiz"
    >
      <!-- Usiamo un div wrapper per il v-if per non rimuovere la modale stessa -->
      <div v-if="quizIdForAttempt">
        <QuizAttemptView
          :quiz-id="quizIdForAttempt"
          @close="closeAttemptModal"
          @completed="handleAttemptCompleted"
        />
      </div>
       <!-- Nascondiamo il footer di default per questa modale -->
       <!-- <template #footer>
         <BaseButton variant="danger" @click="closeAttemptModal">Annulla Tentativo</BaseButton>
       </template> -->
    </BaseModal>

    <!-- Nuova Modale per i Risultati del Quiz -->
    <BaseModal
      :show="isResultModalOpen"
      @close="closeResultModal"
      title="Risultati Quiz"
    >
      <!-- Usiamo un div wrapper per il v-if per non rimuovere la modale stessa -->
      <div v-if="attemptIdForResult">
        <QuizResultView
          :attempt-id="attemptIdForResult"
          @close="closeResultModal"
        />
      </div>
      <!-- Nascondiamo il footer di default per questa modale -->
      <!-- <template #footer>
        <BaseButton variant="primary" @click="closeResultModal">Chiudi</BaseButton>
      </template> -->
    </BaseModal>

  </div>
</template>

<style scoped>
/* Stili specifici rimasti (loading, empty message) o che richiedono override */
.loading-indicator,
.empty-message {
  /* Stili Tailwind applicati direttamente nel template */
}

/* Aggiungiamo classi Tailwind direttamente nel template per gli stati,
   ma potremmo definire colori specifici qui se necessario */
.status-not-started {
  @apply bg-gray-200 text-gray-700;
}
.status-in-progress {
  @apply bg-yellow-100 text-yellow-800;
}
.status-pending {
   @apply bg-orange-100 text-orange-800; /* Colore diverso per pending */
}
.status-completed {
   @apply bg-green-100 text-green-800;
}

/* Classi per il bordo sinistro in base allo stato */
.border-status-not-started { @apply border-l-gray-400; }
.border-status-in-progress { @apply border-l-yellow-500; }
.border-status-pending { @apply border-l-orange-500; }
.border-status-completed { @apply border-l-green-500; }

/* Stile per troncare la descrizione (alternativa a line-clamp se non supportato ovunque) */
.quiz-description {
  /* display: -webkit-box; */
  /* -webkit-line-clamp: 2; */
  /* -webkit-box-orient: vertical; */
  /* overflow: hidden; */
}
</style>