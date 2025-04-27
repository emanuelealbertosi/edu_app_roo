<script setup lang="ts">
import { ref, computed } from 'vue'; // Aggiungere ref e computed
import { useRouter } from 'vue-router';
// Importa la nuova interfaccia per i tentativi
import type { QuizAttemptDashboardItem } from '@/api/dashboard';
import BaseModal from '@/components/common/BaseModal.vue'; // Importare la modale
import QuizDetailsView from '@/views/QuizDetailsView.vue'; // Importare la vista dettagli
import QuizAttemptView from '@/views/QuizAttemptView.vue'; // Importare la vista tentativo
import QuizResultView from '@/views/QuizResultView.vue'; // Importare la vista risultati
import BaseButton from '@/components/common/BaseButton.vue'; // Importare BaseButton per il footer

const props = defineProps<{
  // Aggiorna il tipo della prop quizzes
  quizzes: QuizAttemptDashboardItem[];
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
const attemptIdToContinue = ref<number | null>(null); // Nuovo: ID del tentativo da continuare

// Stato per la modale dei risultati
const attemptIdForResult = ref<number | null>(null);
const isResultModalOpen = ref(false);

// Computed per il titolo della modale dettagli (rinominato per chiarezza)
// Computed per trovare il *tentativo* corrispondente all'ID del *quiz* selezionato
// Nota: Questo assume che vogliamo mostrare i dettagli del quiz basandoci sul primo tentativo trovato con quell'ID quiz.
const selectedAttemptForDetails = computed(() => {
  if (!selectedQuizIdForDetails.value) return null;
  // Cerca il primo tentativo nell'array che corrisponde al quiz_id selezionato
  return props.quizzes.find(attempt => attempt.quiz_id === selectedQuizIdForDetails.value);
});

// Funzioni per modale dettagli
// Ora riceve l'ID del *quiz*
const openDetailsModal = (quizId: number) => {
  selectedQuizIdForDetails.value = quizId; // Salva l'ID del quiz
  isDetailsModalOpen.value = true;
};
const closeDetailsModal = () => {
  isDetailsModalOpen.value = false;
  setTimeout(() => { selectedQuizIdForDetails.value = null; }, 300);
};

// Funzioni per modale tentativo (riceve già quizId, corretto)
// Modificato: Accetta anche attemptId opzionale
const openAttemptModal = (quizId: number, attemptId: number | null = null) => {
  quizIdForAttempt.value = quizId;
  attemptIdToContinue.value = attemptId; // Salva l'ID del tentativo se fornito
  isAttemptModalOpen.value = true;
};
const closeAttemptModal = () => {
  isAttemptModalOpen.value = false;
  // Potremmo voler ricaricare i dati della dashboard qui se l'utente chiude a metà
  setTimeout(() => {
    quizIdForAttempt.value = null;
    attemptIdToContinue.value = null; // Resetta anche l'ID del tentativo
  }, 300);
};

// Gestisce l'avvio DALLA MODALE DETTAGLI (riceve già quizId, corretto)
const handleStartAttemptFromDetails = (quizId: number) => {
  closeDetailsModal(); // Chiudi la modale dei dettagli
  openAttemptModal(quizId); // Apri la modale di tentativo
};

// Gestisce l'avvio DAL PULSANTE NELLA LISTA (riceve già quizId, corretto)
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


// Genera un'etichetta di stato per il tentativo
const getAttemptStatusLabel = (attempt: QuizAttemptDashboardItem): string => {
  // Usa direttamente lo stato del tentativo
  switch (attempt.status) {
    case 'IN_PROGRESS': // Usa valori maiuscoli come da backend/serializer
      return 'In corso';
    case 'PENDING_GRADING': // Usa valori maiuscoli
      return 'In attesa di valutazione';
    case 'COMPLETED': // Usa valori maiuscoli
      // Mostra il punteggio se disponibile
      return `Completato (${attempt.score !== null ? Math.round(attempt.score * 100) : '?'}%)`;
    case 'FAILED': // Aggiunto stato FAILED
       return 'Fallito';
    case 'PENDING': // Stato iniziale prima di 'IN_PROGRESS'
       return 'Da iniziare';
    default:
      // Restituisci lo stato grezzo o un default
      return attempt.status || 'Sconosciuto';
  }
};

// Determina la classe CSS per lo stato del tentativo
const getStatusClass = (attempt: QuizAttemptDashboardItem): string => {
  // Usa direttamente lo stato del tentativo
  switch (attempt.status) {
    case 'IN_PROGRESS':
      return 'status-in-progress';
    case 'PENDING_GRADING':
      return 'status-pending';
    case 'COMPLETED':
      return 'status-completed';
    case 'FAILED':
       return 'status-failed'; // Aggiungere stile per failed se necessario
    case 'PENDING':
       return 'status-not-started'; // Usa lo stile 'not-started' per 'PENDING'
    default:
      return 'status-unknown'; // Aggiungere stile per unknown se necessario
  }
};

// Determina la classe CSS per il BORDO sinistro in base allo stato
const getStatusBorderClass = (attempt: QuizAttemptDashboardItem): string => {
  // Usa direttamente lo stato del tentativo
  switch (attempt.status) {
    case 'IN_PROGRESS':
      return 'border-status-in-progress';
    case 'PENDING_GRADING':
      return 'border-status-pending';
    case 'COMPLETED':
      return 'border-status-completed';
    case 'FAILED':
      return 'border-status-failed'; // Aggiungere stile per failed se necessario
    case 'PENDING':
      return 'border-status-not-started'; // Usa lo stile 'not-started' per 'PENDING'
    default:
      return 'border-status-unknown'; // Aggiungere stile per unknown se necessario
  }
};

// Determina se il pulsante "Inizia Quiz" debba essere mostrato per questo tentativo
const shouldShowStartButton = (attempt: QuizAttemptDashboardItem): boolean => {
  const now = new Date();

  // Controlla le date di disponibilità (dal quiz associato)
  if (attempt.available_from && new Date(attempt.available_from) > now) {
    return false; // Non ancora disponibile
  }
  if (attempt.available_until && new Date(attempt.available_until) < now) {
    return false; // Scaduto
  }

  // Controlla lo stato del TENTATIVO corrente
  // Mostra il pulsante solo se lo stato è PENDING (o forse FAILED se si può ritentare?)
  // Nascondi se è COMPLETED, PENDING_GRADING, o IN_PROGRESS
  const status = attempt.status;
  if (status === 'COMPLETED' || status === 'PENDING_GRADING' || status === 'IN_PROGRESS') {
     return false;
  }

  // Mostra per PENDING e FAILED (assumendo che FAILED possa essere ritentato)
  // Se FAILED non può essere ritentato, rimuoverlo da qui.
  if (status === 'PENDING' || status === 'FAILED') {
     return true;
  }

  // Caso di default (stato sconosciuto o non gestito), non mostrare
  return false;
};
</script>

<template>
  <div class="quiz-list-card bg-white rounded-lg shadow-md p-6"> <!-- Stili card base ok -->
    <h2 class="text-xl font-bold text-primary-dark mb-4 flex items-center"><span class="text-2xl mr-2">📝</span> {{ title }}</h2> <!-- Titolo primario scuro -->

    <div v-if="loading" class="loading-indicator text-center py-4 text-neutral-dark"> <!-- Testo loading neutro scuro -->
      <p>Caricamento quiz...</p>
    </div>

    <div v-else-if="quizzes.length === 0" class="empty-message text-center py-4 text-neutral-dark"> <!-- Testo neutro scuro -->
      <p>{{ emptyMessage }}</p>
    </div>
    
    <div v-else class="quiz-list space-y-4">
      <!-- Aggiungere @click qui -->
      <!-- Itera sui tentativi (rinominato quiz -> attempt) -->
      <div
        v-for="attempt in quizzes"
        :key="attempt.attempt_id"
        class="quiz-item bg-neutral-lightest rounded-lg p-4 shadow border-l-4 relative pb-16 hover:shadow-lg transition-shadow duration-200 cursor-pointer"
        :class="getStatusBorderClass(attempt)"
        @click="openDetailsModal(attempt.quiz_id)"
      >
        <!-- Contenuto dell'item (usa 'attempt' invece di 'quiz') -->
        <div class="quiz-header flex justify-between items-center mb-2">
          <h3 class="font-semibold text-lg text-neutral-darkest">{{ attempt.title }}</h3> <!-- Titolo dal tentativo (che lo eredita dal quiz) -->
          <span :class="['quiz-status text-xs font-medium px-3 py-1 rounded-full', getStatusClass(attempt)]">{{ getAttemptStatusLabel(attempt) }}</span>
        </div>

        <p class="quiz-description text-neutral-dark text-sm mb-3 line-clamp-2">{{ attempt.description }}</p> <!-- Descrizione dal tentativo -->

        <div class="quiz-metadata flex flex-wrap gap-2 text-xs mb-3">
          <div v-if="attempt.metadata?.difficulty" class="quiz-difficulty bg-neutral text-neutral-darker px-2 py-1 rounded">
            Difficoltà: {{ attempt.metadata.difficulty }}
          </div>

          <div v-if="attempt.metadata?.subject" class="quiz-subject bg-neutral text-neutral-darker px-2 py-1 rounded">
            Materia: {{ attempt.metadata.subject }}
          </div>

          <div v-if="attempt.metadata?.points_on_completion" class="quiz-points bg-warning/10 text-warning-dark px-2 py-1 rounded">
            Punti: {{ attempt.metadata.points_on_completion }}
          </div>
        </div>

        <!-- Mostra le date se il tentativo non è completato -->
        <div v-if="attempt.status !== 'COMPLETED'" class="quiz-dates flex flex-wrap gap-x-4 gap-y-1 text-xs text-neutral-dark">
          <div v-if="attempt.available_from" class="quiz-available-from">
            <span class="font-medium">Da:</span> {{ formatDate(attempt.available_from) }}
          </div>

          <div v-if="attempt.available_until" class="quiz-available-until">
             <span class="font-medium">Fino a:</span> {{ formatDate(attempt.available_until) }}
          </div>
        </div>

        <!-- Pulsante Inizia Quiz (visibile solo se appropriato per lo stato del TENTATIVO) -->
        <button
          v-if="shouldShowStartButton(attempt)"
          @click.stop="startQuizAttempt(attempt.quiz_id)"
          class="start-quiz-button absolute bottom-4 right-4 bg-primary hover:bg-primary-dark text-white font-bold py-2 px-4 rounded-lg shadow transition-colors duration-200 z-10"
        >
          <!-- Modificato testo pulsante per chiarezza -->
          {{ attempt.status === 'FAILED' ? 'Ritenta Quiz ▶' : 'Inizia Quiz ▶' }}
        </button>
        
        <!-- Pulsante Continua Quiz (visibile solo se IN_PROGRESS) -->
        <button
          v-if="attempt.status === 'IN_PROGRESS'"
          @click.stop="openAttemptModal(attempt.quiz_id, attempt.attempt_id)"
          class="continue-quiz-button absolute bottom-4 right-4 bg-warning hover:bg-warning-dark text-white font-bold py-2 px-4 rounded-lg shadow transition-colors duration-200 z-10"
        >
          Continua Quiz ▶
        </button>
      </div>
    </div>

    <!-- Modale per i Dettagli del Quiz (aggiornare refs) -->
    <BaseModal
      :show="isDetailsModalOpen"
      @close="closeDetailsModal"
      :title="selectedAttemptForDetails?.title || 'Dettagli Quiz'"
    >
      <QuizDetailsView
        v-if="selectedQuizIdForDetails"
        :id="String(selectedQuizIdForDetails)"
      />
       <template #footer>
         <BaseButton variant="secondary" @click="closeDetailsModal">Chiudi</BaseButton>
         <!-- Mostra il pulsante Inizia/Ritenta se appropriato per il *primo* tentativo trovato con quel quiz_id -->
         <BaseButton
            v-if="selectedAttemptForDetails && shouldShowStartButton(selectedAttemptForDetails)"
            variant="success"
            @click="handleStartAttemptFromDetails(selectedAttemptForDetails.quiz_id)"
          >
            {{ selectedAttemptForDetails.status === 'FAILED' ? 'Ritenta Quiz' : 'Inizia Quiz' }}
          </BaseButton>
       </template>
    </BaseModal>

    <!-- Modale per lo Svolgimento del Quiz -->
    <BaseModal
      :show="isAttemptModalOpen"
      @close="closeAttemptModal"
      title="Svolgimento Quiz"
      :maxWidthClass="'w-full lg:w-[90%] h-[85vh]'"
    >
      <!-- Usiamo un div wrapper per il v-if per non rimuovere la modale stessa -->
      <div v-if="quizIdForAttempt">
        <QuizAttemptView
          :quiz-id="quizIdForAttempt"
          :attempt-id="attemptIdToContinue"
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
  @apply bg-neutral text-neutral-darker; /* Badge neutro */
}
.status-in-progress {
  @apply bg-warning/10 text-warning-dark; /* Badge warning (ambra) */
}
.status-pending {
   @apply bg-blue-100 text-blue-800; /* Usiamo info per pending/in attesa - Corretto */
}
.status-completed {
   @apply bg-success/10 text-success-dark; /* Badge success */
}
.status-failed {
    @apply bg-red-100 text-red-800; /* Aggiunto stile per failed - Corretto */
}
.status-unknown {
    @apply bg-neutral text-neutral-darker; /* Stile per stato sconosciuto */
}


/* Classi per il bordo sinistro in base allo stato */
.border-status-not-started { @apply border-l-neutral-medium; } /* Bordo neutro (per PENDING) */
.border-status-in-progress { @apply border-l-warning; } /* Bordo warning (ambra) */
.border-status-pending { @apply border-l-blue-500; } /* Bordo info per pending/in attesa - Corretto */
.border-status-completed { @apply border-l-success; } /* Bordo success */
.border-status-failed { @apply border-l-red-500; } /* Aggiunto bordo per failed - Corretto */
.border-status-unknown { @apply border-l-neutral-dark; } /* Bordo per stato sconosciuto */

/* Stile per troncare la descrizione (alternativa a line-clamp se non supportato ovunque) */
.quiz-description {
  /* display: -webkit-box; */
  /* -webkit-line-clamp: 2; */
  /* -webkit-box-orient: vertical; */
  /* overflow: hidden; */
}
</style>