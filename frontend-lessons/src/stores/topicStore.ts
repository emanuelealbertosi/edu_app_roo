import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Topic } from '@/types/topic';
import apiClient from '@/services/apiClient'; // Da decommentare

interface TopicState {
  topics: Topic[];
  loading: boolean;
  error: string | null;
}

export const useTopicStore = defineStore('topic', () => {
  const state = ref<TopicState>({
    topics: [],
    loading: false,
    error: null,
  });

  // Getters
  const loading = computed(() => state.value.loading);
  const error = computed(() => state.value.error);

  // Getter per ottenere argomenti filtrati per subject_id
  // Questo approccio ricalcola ogni volta, per performance migliori si potrebbe memoizzare
  // o strutturare 'allTopics' come una mappa { subjectId: Topic[] }
  function getTopicsForSubject(subjectId: number): Topic[] {
    return state.value.topics.filter(topic => topic.subject === subjectId);
  }

  function getTopicById(id: number): Topic | undefined {
    return state.value.topics.find(topic => topic.id === id);
  }

  // Actions
  async function fetchTopics() {
    if (state.value.topics.length > 0 && !state.value.error) {
        return;
    }
    console.log('Fetching all topics...');
    state.value.loading = true;
    state.value.error = null;
    try {
      const response = await apiClient.get('/lezioni/topics/');
      state.value.topics = response.data as Topic[];
      console.log('All topics fetched from API:', state.value.topics);
    } catch (err) {
      console.error('Error fetching all topics:', err);
      state.value.error = (err as Error).message || 'Failed to fetch all topics';
    } finally {
      state.value.loading = false;
    }
  }

  async function fetchTopicsBySubject(subjectId: number) {
    // Se abbiamo già caricato argomenti per questa materia e non ci sono errori, potremmo evitare di ricaricare.
    // Tuttavia, la logica qui sotto ricarica sempre per semplicità e per assicurare dati freschi.
    // Una logica più complessa potrebbe controllare se `getTopicsForSubject(subjectId)` ha già elementi.
    
    console.log(`Fetching topics for subject ID: ${subjectId}...`);
    state.value.loading = true;
    state.value.error = null;
    try {
      // Simula una chiamata API
      await new Promise(resolve => setTimeout(resolve, 800));
      const response = await apiClient.get(`/lezioni/topics/?subject_id=${subjectId}`); // Filtra per subject_id
      const fetchedTopics = response.data as Topic[];
      // Rimuove i vecchi argomenti per la stessa materia prima di aggiungere i nuovi
      // per evitare duplicati se questa action viene chiamata più volte per la stessa materia.
      // Unisci i nuovi argomenti a quelli esistenti, evitando duplicati
      const existingIds = new Set(state.value.topics.map(t => t.id));
      const newTopics = fetchedTopics.filter(t => !existingIds.has(t.id));
      state.value.topics.push(...newTopics);

      
      console.log(`Topics fetched for subject ID ${subjectId}:`, fetchedTopics);

    } catch (err) {
      console.error(`Error fetching topics for subject ${subjectId}:`, err);
      state.value.error = (err as Error).message || `Failed to fetch topics for subject ${subjectId}`;
      // Non resettare tutti gli argomenti, solo quelli per la materia fallita (già gestito dal filter sopra)
    } finally {
      state.value.loading = false;
    }
  }

  function clearTopics() {
    // Usato per resettare gli argomenti, ad esempio quando la materia viene deselezionata
    state.value.topics = [];
    state.value.error = null;
  }

  return {
    // State (esposto tramite computed o getter)
    loading,
    error,
    // State esposto direttamente (o tramite computed)
    topics: computed(() => state.value.topics),
    // Getters
    getTopicsForSubject,
    getTopicById,
    // Actions
    fetchTopics, // Esponi l'azione rinominata
    fetchTopicsBySubject,
    clearTopics,
  };
});