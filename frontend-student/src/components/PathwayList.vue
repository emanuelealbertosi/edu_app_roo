<script setup lang="ts">
import { computed } from 'vue'; // Import computed
import { useRouter } from 'vue-router';
import type { Pathway } from '@/api/dashboard';
import { watch } from 'vue'; // Import watch

const props = defineProps<{
  pathways: Pathway[];
  title: string;
  emptyMessage: string;
  loading?: boolean;
  showResultLink?: boolean; // Nuova prop
}>();

// Log props when they change
watch(() => props.pathways, (newPathways) => {
  console.log(`[PathwayList] Prop 'pathways' updated for title "${props.title}":`, JSON.stringify(newPathways));
}, { immediate: true, deep: true });


const router = useRouter();

// Formatta la data in un formato più leggibile
const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'N/D';

  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Decide dove navigare quando si clicca su un pulsante del percorso
const navigateToPathwayAction = (pathway: Pathway) => {
  // Se il percorso è completo e dobbiamo mostrare il link ai risultati, naviga lì
  if (props.showResultLink && pathway.latest_progress?.status === 'COMPLETED') {
    router.push({ name: 'PathwayResult', params: { pathwayId: pathway.id } });
  }
  // Se il percorso è in corso o non iniziato, naviga alla vista dettagli/svolgimento
  else if (!pathway.latest_progress || pathway.latest_progress.status === 'IN_PROGRESS') {
    // Naviga alla vista di svolgimento del percorso
    router.push({ name: 'PathwayAttempt', params: { pathwayId: pathway.id } });
  }
};

// Calcola la percentuale di completamento in modo accurato
const calculateCompletionPercentage = (pathway: Pathway): number => {
  if (!pathway.latest_progress || !pathway.quiz_details || pathway.quiz_details.length === 0) {
    return 0;
  }
  // Assicurati che completed_orders sia un array
  const completedOrders = Array.isArray(pathway.latest_progress.completed_orders)
                          ? pathway.latest_progress.completed_orders
                          : [];
  const completedCount = completedOrders.length;
  const totalCount = pathway.quiz_details.length;
  return Math.round((completedCount / totalCount) * 100);
};

// Formatta la percentuale per la visualizzazione
const formatProgressPercentage = (pathway: Pathway): string => {
    if (!pathway.latest_progress) return '0%';
    if (pathway.latest_progress.status === 'COMPLETED') return '100%';
    // Usa la funzione di calcolo accurata
    return `${calculateCompletionPercentage(pathway)}%`;
};


// Genera un'etichetta di stato per il progresso del percorso
const getProgressStatusLabel = (pathway: Pathway): string => {
  // Corretto: usa latest_progress
  if (!pathway.latest_progress) return 'Non iniziato';

  // Corretto: usa latest_progress
  switch (pathway.latest_progress.status) {
    case 'IN_PROGRESS': // Usa stato corretto
      return 'In corso';
    case 'COMPLETED': // Usa stato corretto
      return 'Completato';
    default:
      return pathway.latest_progress.status;
  }
};

// Determina la classe CSS per lo stato del progresso
const getProgressStatusClass = (pathway: Pathway): string => {
  // Corretto: usa latest_progress
  if (!pathway.latest_progress) return 'status-not-started';

  // Corretto: usa latest_progress
  switch (pathway.latest_progress.status) {
    case 'IN_PROGRESS': // Usa stato corretto
      return 'status-in-progress';
    case 'COMPLETED': // Usa stato corretto
      return 'status-completed';
    default:
      return '';
  }
};

// Determina la classe CSS per il BORDO sinistro in base allo stato
const getProgressBorderClass = (pathway: Pathway): string => {
  // Corretto: usa latest_progress
  if (!pathway.latest_progress) return 'border-status-not-started'; // Usa la classe definita nello <style>

  // Corretto: usa latest_progress
  switch (pathway.latest_progress.status) {
    case 'IN_PROGRESS': // Usa stato corretto
      return 'border-status-in-progress';
    case 'COMPLETED': // Usa stato corretto
      return 'border-status-completed';
    default:
      return 'border-status-not-started'; // Default a grigio
  }
};
</script>

<template>
  <div class="pathway-list-card bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-bold text-primary-dark mb-4 flex items-center"><span class="text-2xl mr-2">🗺️</span> {{ title }}</h2>

    <div v-if="loading" class="loading-indicator text-center py-4 text-neutral-dark">
      <p>Caricamento percorsi...</p>
    </div>

    <div v-else-if="pathways.length === 0" class="empty-message text-center py-4 text-neutral-dark">
      <p>{{ emptyMessage }}</p>
    </div>

    <div v-else class="pathway-list space-y-4">
      <!-- Rimosso @click dalla card principale -->
      <div v-for="pathway in pathways" :key="pathway.id" class="pathway-item bg-neutral-lightest rounded-lg p-4 shadow border-l-4 relative pb-16 hover:shadow-lg transition-shadow duration-200" :class="getProgressBorderClass(pathway)">
        <!-- DEBUG LOG: Rendering pathway: {{ JSON.stringify(pathway) }} -->
        <div class="pathway-header flex justify-between items-center mb-2">
          <h3 class="font-semibold text-lg text-neutral-darkest">{{ pathway.title }}</h3>
          <span :class="['pathway-status text-xs font-medium px-3 py-1 rounded-full', getProgressStatusClass(pathway)]">
            {{ getProgressStatusLabel(pathway) }}
          </span>
        </div>

        <p class="pathway-description text-neutral-dark text-sm mb-3 line-clamp-2">{{ pathway.description }}</p>

        <div class="pathway-progress-container mb-3">
          <!-- Usa la funzione formattata -->
          <div class="pathway-progress-label text-sm font-medium text-neutral-darker mb-1">Progresso: {{ formatProgressPercentage(pathway) }}</div>
          <div class="pathway-progress-bar w-full bg-neutral rounded-full h-2.5 overflow-hidden">
            <div
              class="pathway-progress-fill bg-primary h-2.5 rounded-full transition-all duration-500 ease-out"
              :style="{ width: calculateCompletionPercentage(pathway) + '%' }"
              ></div>
          </div>
        </div>
        <div class="pathway-metadata flex flex-wrap gap-x-4 gap-y-2 text-xs"> <!-- Modificato gap per migliore spaziatura -->
          <div v-if="pathway.metadata.points_on_completion" class="pathway-points bg-warning/10 text-warning-dark px-2 py-1 rounded">
            Punti: {{ pathway.metadata.points_on_completion }}
          </div>

          <div v-if="pathway.latest_progress && pathway.latest_progress.completed_at" class="pathway-completed-at bg-neutral text-neutral-darker px-2 py-1 rounded">
            Completato: {{ formatDate(pathway.latest_progress.completed_at) }}
          </div>

          <div v-if="pathway.latest_progress && pathway.latest_progress.points_earned" class="pathway-points-earned bg-success/10 text-success-dark px-2 py-1 rounded">
            Guadagnati: {{ pathway.latest_progress.points_earned }}
          </div>

          <!-- NUOVO: Assegnato da -->
          <div class="pathway-assigned-by text-neutral-dark">
             <span class="font-medium">Assegnato da:</span> {{ pathway.teacher_username }}
          </div>
        </div>

        <!-- Bottone Inizia/Continua -->
        <button
          v-if="!pathway.latest_progress || pathway.latest_progress.status === 'IN_PROGRESS'"
          @click.stop="navigateToPathwayAction(pathway)"
          class="start-continue-link absolute bottom-4 right-4 bg-primary hover:bg-primary-dark text-white text-sm font-medium py-1.5 px-3 rounded-md shadow transition-colors duration-200"
        >
          {{ pathway.latest_progress ? 'Continua Percorso' : 'Inizia Percorso' }}
        </button>

        <!-- Link ai Risultati (visibile solo se showResultLink è true e il percorso è completo) -->
        <router-link
          v-if="showResultLink && pathway.latest_progress?.status === 'COMPLETED'"
          :to="{ name: 'PathwayResult', params: { pathwayId: pathway.id } }"
          @click.stop
          class="view-results-link absolute bottom-4 right-4 bg-secondary hover:bg-secondary-light text-white text-sm font-medium py-1.5 px-3 rounded-md shadow transition-colors duration-200"
        >
          Vedi Risultati
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici rimasti (loading, empty message) o che richiedono override */
.loading-indicator,
.empty-message {
  /* Stili Tailwind applicati direttamente nel template */
}

/* Classi per lo status badge */
.status-not-started {
  @apply bg-neutral text-neutral-darker; /* Badge neutro aggiornato */
}
.status-in-progress {
  @apply bg-warning/10 text-warning-dark; /* Badge warning aggiornato */
}
.status-completed {
   @apply bg-success/10 text-success-dark; /* Badge success aggiornato */
}

/* Classi per il bordo sinistro in base allo stato */
.border-status-not-started { @apply border-l-neutral-medium; } /* Bordo neutro aggiornato */
.border-status-in-progress { @apply border-l-warning; } /* Bordo warning aggiornato */
.border-status-completed { @apply border-l-success; } /* Bordo success aggiornato */

/* Stile per troncare la descrizione */
.pathway-description {
  /* display: -webkit-box; */
  /* -webkit-line-clamp: 2; */
  /* -webkit-box-orient: vertical; */
  /* overflow: hidden; */
}
</style>