<template>
  <div class="uda-detail-view">
    <div v-if="loading" class="loading-message">Caricamento dati UDA...</div>
    <div v-if="error" class="error-message">
      Errore nel caricamento dell'UDA: {{ error }}
    </div>

    <div v-if="uda && !loading && !error" class="uda-details-container">
      <div class="header-actions">
        <h1>{{ uda.title }}</h1>
        <router-link :to="`/udas/${uda.id}/edit`" class="btn btn-secondary">Modifica UDA</router-link>
      </div>
      
      <p v-if="uda.description" class="description">{{ uda.description }}</p>

      <div class="metadata">
        <p><strong>Stato:</strong> {{ uda.status }}</p>
        <p v-if="uda.start_date"><strong>Data Inizio:</strong> {{ formatDate(uda.start_date) }}</p>
        <p v-if="uda.end_date"><strong>Data Fine:</strong> {{ formatDate(uda.end_date) }}</p>
        
        <p v-if="uda.subject">
          <strong>Materia:</strong> 
          <!-- TODO: Recuperare e visualizzare il nome della materia dall'ID -->
          ID Materia: {{ uda.subject }}
        </p>
        
        <div v-if="uda.topics && uda.topics.length > 0">
          <strong>Argomenti:</strong>
          <ul>
            <!-- TODO: Recuperare e visualizzare i nomi degli argomenti dagli ID -->
            <li v-for="topicId in uda.topics" :key="topicId">
              ID Argomento: {{ topicId }}
            </li>
          </ul>
        </div>

        <p v-if="uda.course">
          <strong>Corso di appartenenza:</strong>
          <!-- TODO: Recuperare e visualizzare il nome del corso dall'ID -->
          <router-link :to="`/courses/${uda.course}`">
            Vedi Corso (ID: {{ uda.course }})
          </router-link>
        </p>
      </div>

      <div class="contents-section">
        <h2>Contenuti dell'UDA</h2>
        <div v-if="uda.contents && uda.contents.length > 0" class="contents-list">
          <UdaContentItemRenderer
            v-for="(content, index) in uda.contents"
            :key="content.id || content.temp_id"
            :content="content"
            :uda-id="uda.id"
            context="uda"
            :is-first="index === 0"
            :is-last="index === uda.contents.length - 1"
            @edit="handleEditContent"
            @delete="handleDeleteContent"
            @move="handleMoveContent"
            @update:teacher-marked-completed="handleTeacherMarkedCompletedUpdate"
            @update:activity-completed="handleActivityCompletedUpdate"
          />
          <!-- 
            Event handlers (handleEditContent, etc.) and their logic need to be implemented
            if direct manipulation from detail view is desired.
            For now, they are placeholders.
          -->
        </div>
        <p v-else>Nessun contenuto definito per questa UDA.</p>
      </div>
    </div>
    <div v-if="!uda && !loading && !error" class="no-data-message">
      Nessun dato UDA da visualizzare o UDA non trovata.
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { onMounted, computed } from 'vue';
import { useUdaStore } from '@/stores/udaStore';
import type { UDA, UDAContent } from '@/types/uda'; // Aggiunto UDAContent per handleEditContent
import UdaContentItemRenderer from '@/components/uda/UdaContentItemRenderer.vue';

const route = useRoute();
const router = useRouter(); 
const udaStore = useUdaStore();

const udaId = computed(() => route.params.id as string);

const uda = computed<UDA | null>(() => udaStore.currentUda);
const loading = computed(() => udaStore.loading);
const error = computed(() => udaStore.error);

const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      year: 'numeric', month: 'long', day: 'numeric'
    });
  } catch (e) {
    return dateString; 
  }
};

onMounted(async () => {
  if (udaId.value) {
    const idAsNumber = parseInt(udaId.value, 10);
    if (!isNaN(idAsNumber)) {
      await udaStore.fetchUda(idAsNumber);
    } else {
      console.error("ID UDA non valido fornito nella route:", udaId.value);
    }
  }
});

// TODO: Gestire la visualizzazione del corso di appartenenza (recuperare nome da ID)
// TODO: Gestire la visualizzazione di materia e argomenti (recuperare nomi da ID)

const handleEditContent = (contentItem: UDAContent) => {
  console.log('Edit content:', contentItem);
  alert(`Modifica contenuto (ID: ${contentItem.id || contentItem.temp_id}) - Implementare navigazione/modale`);
};

const handleDeleteContent = (contentId: number | string) => {
  console.log('Delete content ID:', contentId);
  alert(`Elimina contenuto (ID: ${contentId}) - Implementare logica e conferma`);
};

const handleMoveContent = (contentItem: UDAContent, direction: number) => {
  console.log('Move content:', contentItem, 'direction:', direction);
  alert(`Sposta contenuto (ID: ${contentItem.id || contentItem.temp_id}, Direzione: ${direction}) - Implementare logica`);
};

const handleTeacherMarkedCompletedUpdate = (payload: { contentId: number, completed: boolean }) => {
  console.log('Teacher marked completed update:', payload);
};

const handleActivityCompletedUpdate = (payload: { contentId: number, completed: boolean }) => {
  console.log('Activity completed update:', payload);
};
</script>

<style scoped>
.uda-detail-view {
  padding: 20px;
  font-family: sans-serif;
}

.loading-message, .error-message, .no-data-message {
  text-align: center;
  padding: 20px;
  font-size: 1.2em;
}

.error-message {
  color: red;
  background-color: #ffe0e0;
  border: 1px solid red;
  border-radius: 5px;
}

.uda-details-container {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions h1 {
  margin: 0;
  color: #333;
}

.btn {
  padding: 8px 15px;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.9em;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
  border-color: #6c757d;
}
.btn-secondary:hover {
  background-color: #5a6268;
  border-color: #545b62;
}

.description {
  margin-bottom: 20px;
  color: #555;
  line-height: 1.6;
}

.metadata {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border: 1px solid #eee;
  border-radius: 5px;
}

.metadata p, .metadata div {
  margin-bottom: 8px;
}

.metadata strong {
  color: #444;
}

.metadata ul {
  list-style-type: disc;
  padding-left: 20px;
  margin-top: 5px;
}

.contents-section {
  margin-top: 30px;
}

.contents-section h2 {
  border-bottom: 2px solid #eee;
  padding-bottom: 10px;
  margin-bottom: 20px;
  color: #333;
}

.contents-list > div { 
  margin-bottom: 15px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 5px;
}
</style>