import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Topic } from '@/types/topic';
import apiClient from '@/services/apiClient'; // Da decommentare

interface TopicState {
  // Potremmo voler memorizzare gli argomenti in una mappa per materia per efficienza
  // topicsBySubjectId: Record<number, Topic[]>; 
  // Per semplicità ora usiamo un array singolo e filtriamo, 
  // ma per molte materie/argomenti una mappa sarebbe meglio.
  allTopics: Topic[]; // Contiene tutti gli argomenti caricati, da diverse materie
  loading: boolean;
  error: string | null;
}

export const useTopicStore = defineStore('topic', () => {
  const state = ref<TopicState>({
    allTopics: [],
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
    return state.value.allTopics.filter(topic => topic.subject === subjectId);
  }

  function getTopicById(id: number): Topic | undefined {
    return state.value.allTopics.find(topic => topic.id === id);
  }

  // Actions
  async function fetchTopics() { // Rinomina da fetchAllTopics
    if (state.value.allTopics.length > 5 && !state.value.error) { // Evita ricaricamenti se già un buon numero è presente
        // console.log('A sufficient number of topics already loaded or loading.');
        // return;
    }
    console.log('Fetching all topics...');
    state.value.loading = true;
    state.value.error = null;
    try {
      // Simula una chiamata API per tutti gli argomenti
      await new Promise(resolve => setTimeout(resolve, 1200));
      // const response = await apiClient.get('/topics/'); // Esempio endpoint per tutti gli argomenti
      // state.value.allTopics = response.data as Topic[];
      
      // Dati mock estesi per simulare più argomenti da diverse materie
      const mockAllTopics: Topic[] = [
        { id: 101, name: 'Algebra', subject_id: 1 },
        { id: 102, name: 'Geometria', subject_id: 1 },
        { id: 103, name: 'Trigonometria', subject_id: 1 },
        { id: 201, name: 'Storia Antica', subject_id: 2 },
        { id: 202, name: 'Medioevo', subject_id: 2 },
        { id: 203, name: 'Rinascimento', subject_id: 2 },
        { id: 301, name: 'Biologia Cellulare', subject_id: 3 },
        { id: 302, name: 'Chimica Organica', subject_id: 3 },
        { id: 401, name: 'Grammatica Italiana', subject_id: 4 },
        { id: 402, name: 'Letteratura del Novecento', subject_id: 4 },
        { id: 403, name: 'Poesia Ermetica', subject_id: 4},
        { id: 501, name: 'Programmazione Python', subject_id: 5 }, // Materia fittizia
        { id: 502, name: 'Strutture Dati', subject_id: 5 },
      ];
      // Unisci i mock topics con quelli esistenti, evitando duplicati basati su ID
      const existingIds = new Set(state.value.allTopics.map(t => t.id));
      const newTopics = mockAllTopics.filter(t => !existingIds.has(t.id));
      state.value.allTopics.push(...newTopics);

      console.log('All topics fetched/updated:', state.value.allTopics);

    } catch (err) {
      console.error('Error fetching all topics:', err);
      state.value.error = (err as Error).message || 'Failed to fetch all topics';
      // Non resettare allTopics qui, per non perdere quelli già caricati da fetchTopicsBySubject
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
      state.value.allTopics = state.value.allTopics.filter(topic => topic.subject_id !== subjectId);
      // Aggiunge i nuovi argomenti
      state.value.allTopics.push(...fetchedTopics);
      
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
    state.value.allTopics = []; // O potremmo voler pulire solo per una materia specifica
    state.value.error = null;
  }

  return {
    // State (esposto tramite computed o getter)
    loading,
    error,
    // Getters
    getTopicsForSubject,
    getTopicById,
    // Actions
    fetchTopics, // Esponi l'azione rinominata
    fetchTopicsBySubject,
    clearTopics,
  };
});