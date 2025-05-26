<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'; // Aggiungere ref, computed, onMounted
import { useRouter } from 'vue-router';
// Importa la nuova interfaccia per i tentativi
import type { QuizAttemptDashboardItem } from '@/api/dashboard';
import BaseModal from '@/components/common/BaseModal.vue'; // Importare la modale
import QuizDetailsView from '@/views/QuizDetailsView.vue'; // Importare la vista dettagli
import QuizAttemptView from '@/views/QuizAttemptView.vue'; // Importare la vista tentativo
import QuizResultView from '@/views/QuizResultView.vue'; // Importare la vista risultati
import QuizAttemptReviewModal from '@/components/quiz/QuizAttemptReviewModal.vue'; // NUOVO: Importa la modale di revisione
import BaseButton from '@/components/common/BaseButton.vue'; // Importare BaseButton per il footer

const props = defineProps<{
  // Aggiorna il tipo della prop quizzes
  quizzes: QuizAttemptDashboardItem[];
  title: string;
  emptyMessage: string;
  loading?: boolean;
  // displayMode?: 'list' | 'grid'; // Rimosso displayMode
}>();

const router = useRouter();

// const isGridView = computed(() => props.displayMode === 'grid'); // Rimosso isGridView

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
const attemptIdToContinue = ref<number | null>(null); // Ripristinato: ID del tentativo da continuare

// Stato per la modale dei risultati
const attemptIdForResult = ref<number | null>(null);
const isResultModalOpen = ref(false);

// NUOVO: Stato per la modale di revisione
const attemptIdForReview = ref<number | null>(null);
const isReviewModalOpen = ref(false);

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
  selectedQuizIdForDetails.value = null; // Reset immediato
};

// Funzioni per modale tentativo (riceve già quizId, corretto)
// Ripristinato: Accetta anche attemptId opzionale
const openAttemptModal = (quizId: number, attemptId: number | null = null) => {
  quizIdForAttempt.value = quizId;
  attemptIdToContinue.value = attemptId; // Ripristinato: Salva l'ID del tentativo se fornito
  isAttemptModalOpen.value = true;
};
const closeAttemptModal = () => {
  isAttemptModalOpen.value = false;
  // Potremmo voler ricaricare i dati della dashboard qui se l'utente chiude a metà
  quizIdForAttempt.value = null; // Reset immediato
  attemptIdToContinue.value = null; // Ripristinato: Resetta anche l'ID del tentativo // Reset immediato
};

// Gestisce l'avvio DALLA MODALE DETTAGLI (riceve già quizId, corretto)
const handleStartAttemptFromDetails = (quizId: number) => {
  closeDetailsModal(); // Chiudi la modale dei dettagli
  openAttemptModal(quizId); // Apri la modale di tentativo
};

// Ripristinato: Gestisce l'avvio DAL PULSANTE NELLA LISTA
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
  attemptIdForResult.value = null; // Reset immediato
};

// NUOVO: Funzioni per la modale di revisione
const openReviewModal = (attemptId: number) => {
  if (attemptId) { // Assicurati che attemptId sia valido
    attemptIdForReview.value = attemptId;
    isReviewModalOpen.value = true;
  } else {
    console.warn("[QuizList.vue] openReviewModal chiamato senza un attemptId valido.");
  }
};

const closeReviewModal = () => {
  isReviewModalOpen.value = false;
  attemptIdForReview.value = null;
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
      return `Completato (${attempt.score !== null ? Math.round(attempt.score) : '?'}%)`;
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

// Rimosso getStatusBorderClass perché non più utilizzato

// Ripristinato: Determina se il pulsante "Inizia Quiz" debba essere mostrato per questo tentativo
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

const getButtonLabel = (attempt: QuizAttemptDashboardItem): string => {
  switch (attempt.status) {
    case 'PENDING':
      return 'Inizia Quiz';
    case 'IN_PROGRESS':
      return 'Continua Quiz';
    case 'FAILED':
      return 'Ritenta Quiz';
    case 'COMPLETED':
    case 'PENDING_GRADING':
      return 'Visualizza Risultati';
    default:
      return 'Visualizza Dettagli';
  }
};

const getButtonDisabledState = (attempt: QuizAttemptDashboardItem): boolean => {
  const now = new Date();
  if (attempt.status === 'PENDING' || attempt.status === 'FAILED') {
    if (attempt.available_from && new Date(attempt.available_from) > now) {
      return true; // Non ancora disponibile
    }
    if (attempt.available_until && new Date(attempt.available_until) < now) {
      return true; // Scaduto
    }
  }
  // Per COMPLETED o PENDING_GRADING, il pulsante è sempre abilitato se c'è un attempt_id
  if ((attempt.status === 'COMPLETED' || attempt.status === 'PENDING_GRADING') && !attempt.attempt_id) {
      return true; // Non può visualizzare risultati senza un ID tentativo
  }
  return false;
};

const handleQuizAction = (attempt: QuizAttemptDashboardItem): void => {
  if (getButtonDisabledState(attempt)) return;

  switch (attempt.status) {
    case 'PENDING':
      openAttemptModal(attempt.quiz_id);
      break;
    case 'IN_PROGRESS':
      openAttemptModal(attempt.quiz_id, attempt.attempt_id);
      break;
    case 'FAILED':
      // Assumiamo che ritentare apra la modale per un nuovo tentativo sullo stesso quiz_id
      openAttemptModal(attempt.quiz_id);
      break;
    case 'COMPLETED':
    case 'PENDING_GRADING':
      if (attempt.attempt_id) {
        attemptIdForResult.value = attempt.attempt_id;
        isResultModalOpen.value = true;
      } else {
        // Fallback o errore: non dovrebbe succedere se il pulsante non è disabilitato
        openDetailsModal(attempt.quiz_id);
      }
      break;
    default:
      openDetailsModal(attempt.quiz_id);
      break;
  }
};


onMounted(() => {
  // Logga i dati dei quiz quando il componente viene montato e ogni volta che le props cambiano (se la reattività lo permette)
  // Questo ci aiuterà a vedere se subject_name, topic_name, etc., arrivano al componente.
  console.log('[QuizList.vue] Props quizzes ricevute:', JSON.parse(JSON.stringify(props.quizzes)));
});

// Rimosse lightenColor e getContrastingTextColor perché non più utilizzate con stili fissi

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
    
    <div v-else class="quiz-list grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"> <!-- Layout a griglia -->
      <div
        v-for="attempt in quizzes"
        :key="attempt.attempt_id"
        class="quiz-item bg-white rounded-lg shadow-md overflow-hidden flex flex-col"
      >
        <!-- Contenuto principale della card -->
        <div class="p-5 flex-grow relative">
          <!-- Sfondo colorato limitato a quest'area -->
          <div
            v-if="attempt.card_background_color"
            class="absolute inset-0 opacity-20"
            :style="{ backgroundColor: attempt.card_background_color }"
          ></div>
          <!-- Wrapper per il contenuto testuale per z-index -->
          <div class="relative z-10">
            <h3 class="text-lg font-semibold text-gray-800 mb-2">{{ attempt.title }}</h3>
            
            <!-- Metadati: Materia, Argomento, Docente -->
            <div class="text-sm text-gray-600 mb-2">
              <p v-if="attempt.subject_name"><strong>Materia:</strong> {{ attempt.subject_name }}</p>
              <p v-if="attempt.topic_name"><strong>Argomento:</strong> {{ attempt.topic_name }}</p>
              <p>
                  <strong>Docente:</strong>
                  {{ attempt.teacher_first_name || '' }} {{ attempt.teacher_last_name || '' }}
                  <span v-if="!attempt.teacher_first_name && !attempt.teacher_last_name">{{ attempt.teacher_username || 'N/D' }}</span>
              </p>
              <p v-if="attempt.metadata?.difficulty"><strong>Difficoltà:</strong> {{ attempt.metadata.difficulty }}</p>
              <p v-if="attempt.metadata?.points_on_completion"><strong>Punti:</strong> {{ attempt.metadata.points_on_completion }}</p>
            </div>

            <!-- Date e Stato -->
            <p class="text-xs text-gray-500 mb-3">
              <span v-if="attempt.available_from">Disponibile dal: {{ formatDate(attempt.available_from) }} <br /></span>
              <span v-if="attempt.available_until && attempt.status !== 'COMPLETED'">Scade il: {{ formatDate(attempt.available_until) }} <br /></span>
              Stato: <span :class="['font-medium', getStatusClass(attempt)]">{{ getAttemptStatusLabel(attempt) }}</span>
              <span v-if="attempt.status === 'COMPLETED' && attempt.completed_at"> il {{ formatDate(attempt.completed_at) }}</span>
            </p>
          </div>
        </div>

        <!-- Footer della card con pulsante di azione -->
        <div class="bg-gray-50 px-5 py-3 mt-auto space-y-2">
          <button
            @click="handleQuizAction(attempt)"
            class="w-full text-center px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-sm font-medium rounded-md shadow-sm transition duration-150 ease-in-out"
            :disabled="getButtonDisabledState(attempt)"
          >
            {{ getButtonLabel(attempt) }}
          </button>
          
          <!-- NUOVO: Pulsante "Rivedi Domande" -->
          <button
            v-if="(attempt.status === 'COMPLETED' || attempt.status === 'FAILED') && attempt.attempt_id"
            @click="openReviewModal(attempt.attempt_id)"
            class="w-full text-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium rounded-md shadow-sm transition duration-150 ease-in-out"
          >
            Rivedi Domande
          </button>
        </div>
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
         <!-- Rimosso pulsante Inizia/Ritenta dal footer della modale dettagli -->
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
          :attempt-id="attemptIdToContinue"  # Ripristinato prop
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

    <!-- NUOVO: Modale per la Revisione del Tentativo -->
    <QuizAttemptReviewModal
      :show="isReviewModalOpen"
      :attempt-id="attemptIdForReview"
      @close="closeReviewModal"
    />

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
  @apply bg-yellow-200 text-yellow-800;
}
.status-pending {
   @apply bg-blue-200 text-blue-800;
}
.status-completed {
   @apply bg-green-200 text-green-800;
}
.status-failed {
    @apply bg-red-200 text-red-800;
}
.status-unknown {
    @apply bg-gray-200 text-gray-700;
}

/* Rimosse classi border-status-* perché il bordo colorato non è più usato */

/* Stile per troncare la descrizione (alternativa a line-clamp se non supportato ovunque) */
.quiz-description {
  /* display: -webkit-box; */
  /* -webkit-line-clamp: 2; */
  /* -webkit-box-orient: vertical; */
  /* overflow: hidden; */
}
</style>