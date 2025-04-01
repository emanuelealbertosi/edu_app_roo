<script setup lang="ts">
import { useRouter } from 'vue-router';
import type { Pathway } from '@/api/dashboard';

const props = defineProps<{
  pathways: Pathway[];
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

// Apre il percorso per visualizzare i dettagli o continuare
const openPathway = (pathwayId: number) => {
  router.push(`/pathway/${pathwayId}`);
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
</script>

<template>
  <div class="pathway-list-card dashboard-card">
    <h2>{{ title }}</h2>
    
    <div v-if="loading" class="loading-indicator">
      <p>Caricamento in corso...</p>
    </div>
    
    <div v-else-if="pathways.length === 0" class="empty-message">
      <p>{{ emptyMessage }}</p>
    </div>
    
    <div v-else class="pathway-list">
      <div v-for="pathway in pathways" :key="pathway.id" class="pathway-item" @click="openPathway(pathway.id)">
        <div class="pathway-header">
          <h3>{{ pathway.title }}</h3>
          <span :class="['pathway-status', getProgressStatusClass(pathway)]">
            {{ getProgressStatusLabel(pathway) }}
          </span>
        </div>
        
        <p class="pathway-description">{{ pathway.description }}</p>
        
        <div class="pathway-progress-container">
          <div class="pathway-progress-label">Progresso: {{ calculateProgress(pathway) }}</div>
          <div class="pathway-progress-bar">
            <div 
              class="pathway-progress-fill" 
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
        
        <div class="pathway-metadata">
          <div v-if="pathway.metadata.points_on_completion" class="pathway-points">
            Punti: {{ pathway.metadata.points_on_completion }}
          </div>
          
          <div v-if="pathway.progress && pathway.progress.completed_at" class="pathway-completed-at">
            Completato il: {{ formatDate(pathway.progress.completed_at) }}
          </div>
          
          <div v-if="pathway.progress && pathway.progress.points_earned" class="pathway-points-earned">
            Punti guadagnati: {{ pathway.progress.points_earned }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pathway-list-card {
  margin-bottom: 1.5rem;
}

.pathway-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pathway-item {
  background-color: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border-left: 4px solid #ddd;
}

.pathway-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.pathway-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.pathway-status {
  font-size: 0.85rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.status-not-started {
  background-color: #e3f2fd;
  color: #1976d2;
}

.status-in-progress {
  background-color: #fff8e1;
  color: #ff8f00;
}

.status-completed {
  background-color: #e8f5e9;
  color: #388e3c;
}

.pathway-description {
  color: #666;
  margin-bottom: 1rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.pathway-progress-container {
  margin: 1rem 0;
}

.pathway-progress-label {
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.pathway-progress-bar {
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.pathway-progress-fill {
  height: 100%;
  background-color: #4caf50;
  border-radius: 4px;
}

.pathway-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

.pathway-metadata > div {
  background-color: #f5f5f5;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.loading-indicator,
.empty-message {
  padding: 1rem;
  text-align: center;
  color: #666;
}
</style>