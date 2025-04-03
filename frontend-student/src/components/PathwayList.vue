<script setup lang="ts">
import { useRouter } from 'vue-router';
import type { Pathway } from '@/api/dashboard';

const props = defineProps<{
  pathways: Pathway[];
  title: string;
  emptyMessage: string;
  loading?: boolean;
  showResultLink?: boolean; // Nuova prop
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

// Decide dove navigare quando si clicca su un percorso
const navigateToPathway = (pathway: Pathway) => {
  if (props.showResultLink && pathway.progress?.status === 'completed') { // Corretto &amp;&amp; -> &&
    // Se dobbiamo mostrare il link ai risultati e il percorso è completo, naviga ai risultati
    router.push({ name: 'PathwayResult', params: { pathwayId: pathway.id } });
  } else {
    // Altrimenti, naviga ai dettagli del percorso (per continuarlo o visualizzarlo)
    // TODO: Creare la vista PathwayDetailsView se non esiste
    // router.push({ name: 'pathway-details', params: { id: pathway.id } });
    console.warn(`Navigazione a /pathway/${pathway.id} (dettagli) non ancora implementata o necessaria.`);
  }
};

// Calcola e formatta la percentuale di completamento
const calculateProgress = (pathway: Pathway): string => {
  if (!pathway.progress) return '0%';
  
  if (pathway.progress.status === 'completed') {
    return '100%';
  }
  
  // Se abbiamo informazioni sull'ultimo quiz completato, calcoliamo una percentuale approssimativa
  if (pathway.progress.last_completed_quiz_order !== null && pathway.progress.last_completed_quiz_order >= 0) {
    // In un'implementazione reale, dovremmo conoscere il numero totale di quiz nel percorso
    // Qui assumiamo che last_completed_quiz_order sia 0-based e ci siano 5 quiz in totale
    return `${Math.round((pathway.progress.last_completed_quiz_order + 1) * 20)}%`;
  }
  
  return 'In corso';
};

// Genera un'etichetta di stato per il progresso del percorso
const getProgressStatusLabel = (pathway: Pathway): string => {
  if (!pathway.progress) return 'Non iniziato';
  
  switch (pathway.progress.status) {
    case 'in_progress':
      return 'In corso';
    case 'completed':
      return 'Completato';
    default:
      return pathway.progress.status;
  }
};

// Determina la classe CSS per lo stato del progresso
const getProgressStatusClass = (pathway: Pathway): string => {
  if (!pathway.progress) return 'status-not-started';
  
  switch (pathway.progress.status) {
    case 'in_progress':
      return 'status-in-progress';
    case 'completed':
      return 'status-completed';
    default:
      return '';
  }
};

// Determina la classe CSS per il BORDO sinistro in base allo stato
const getProgressBorderClass = (pathway: Pathway): string => {
  if (!pathway.progress) return 'border-status-not-started'; // Usa la classe definita nello <style>

  switch (pathway.progress.status) {
    case 'in_progress':
      return 'border-status-in-progress';
    case 'completed':
      return 'border-status-completed';
    default:
      return 'border-status-not-started'; // Default a grigio
  }
};
</script>

<template>
  <div class="pathway-list-card bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-bold text-teal-700 mb-4 flex items-center"><span class="text-2xl mr-2">🗺️</span> {{ title }}</h2>

    <div v-if="loading" class="loading-indicator text-center py-4 text-gray-500">
      <p>Caricamento percorsi...</p>
    </div>

    <div v-else-if="pathways.length === 0" class="empty-message text-center py-4 text-gray-500">
      <p>{{ emptyMessage }}</p>
    </div>
    
    <div v-else class="pathway-list space-y-4">
      <div v-for="pathway in pathways" :key="pathway.id" class="pathway-item bg-gray-50 rounded-lg p-4 shadow border-l-4 relative pb-16 hover:shadow-lg transition-shadow duration-200 cursor-pointer" :class="getProgressBorderClass(pathway)" @click="navigateToPathway(pathway)">
        <div class="pathway-header flex justify-between items-center mb-2">
          <h3 class="font-semibold text-lg text-gray-800">{{ pathway.title }}</h3>
          <span :class="['pathway-status text-xs font-medium px-3 py-1 rounded-full', getProgressStatusClass(pathway)]">
            {{ getProgressStatusLabel(pathway) }}
          </span>
        </div>
        
        <p class="pathway-description text-gray-600 text-sm mb-3 line-clamp-2">{{ pathway.description }}</p>

        <div class="pathway-progress-container mb-3">
          <div class="pathway-progress-label text-sm font-medium text-gray-700 mb-1">Progresso: {{ calculateProgress(pathway) }}</div>
          <div class="pathway-progress-bar w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
            <div
              class="pathway-progress-fill bg-teal-500 h-2.5 rounded-full transition-all duration-500 ease-out"
              :style="{
                width: pathway.progress && pathway.progress.status === 'completed'
                  ? '100%'
                  : pathway.progress && pathway.progress.last_completed_quiz_order !== null
                    ? `${Math.round((pathway.progress.last_completed_quiz_order + 1) * 20)}%`
                    : '0%'
              }"
            ></div>
          </div>
        </div>
        
        <div class="pathway-metadata flex flex-wrap gap-2 text-xs">
          <div v-if="pathway.metadata.points_on_completion" class="pathway-points bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            Punti: {{ pathway.metadata.points_on_completion }}
          </div>

          <div v-if="pathway.progress && pathway.progress.completed_at" class="pathway-completed-at bg-gray-200 text-gray-700 px-2 py-1 rounded">
            Completato: {{ formatDate(pathway.progress.completed_at) }}
          </div>

          <div v-if="pathway.progress && pathway.progress.points_earned" class="pathway-points-earned bg-green-100 text-green-800 px-2 py-1 rounded">
            Guadagnati: {{ pathway.progress.points_earned }}
          </div>
        </div>
        
        <!-- Link ai Risultati (visibile solo se showResultLink è true e il percorso è completo) -->
        <router-link
          v-if="showResultLink && pathway.progress?.status === 'completed'"
          :to="{ name: 'PathwayResult', params: { pathwayId: pathway.id } }"
          @click.stop
          class="view-results-link absolute bottom-4 right-4 bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-medium py-1.5 px-3 rounded-md shadow transition-colors duration-200"
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
  @apply bg-gray-200 text-gray-700;
}
.status-in-progress {
  @apply bg-yellow-100 text-yellow-800;
}
.status-completed {
   @apply bg-green-100 text-green-800;
}

/* Classi per il bordo sinistro in base allo stato */
.border-status-not-started { @apply border-l-gray-400; }
.border-status-in-progress { @apply border-l-yellow-500; }
.border-status-completed { @apply border-l-green-500; }

/* Stile per troncare la descrizione */
.pathway-description {
  /* display: -webkit-box; */
  /* -webkit-line-clamp: 2; */
  /* -webkit-box-orient: vertical; */
  /* overflow: hidden; */
}
</style>