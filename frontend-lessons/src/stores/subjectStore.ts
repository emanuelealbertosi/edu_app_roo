import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Subject } from '@/types/subject';
import apiClient from '@/services/apiClient'; // Da decommentare quando il servizio API è pronto

interface SubjectState {
  subjects: Subject[];
  loading: boolean;
  error: string | null;
}

export const useSubjectStore = defineStore('subject', () => {
  const state = ref<SubjectState>({
    subjects: [],
    loading: false,
    error: null,
  });

  // Getters
  const subjects = computed(() => state.value.subjects);
  const loading = computed(() => state.value.loading);
  const error = computed(() => state.value.error);

  // Actions
  async function fetchSubjects() {
    if (state.value.subjects.length > 0 && !state.value.error) {
      // Non ricaricare se già presenti e non c'è stato errore precedente
      // console.log('Subjects already loaded');
      // return;
    }
    console.log('Fetching subjects...');
    state.value.loading = true;
    state.value.error = null;
    try {
      // Simula una chiamata API
      await new Promise(resolve => setTimeout(resolve, 1000));
      const response = await apiClient.get('/lezioni/subjects/'); // Esempio con apiClient
      state.value.subjects = response.data;
      
      // Dati mock per ora, in attesa dell'API reale
      // const mockSubjects: Subject[] = [
      //   { id: 1, name: 'Matematica', color_placeholder: '#FF5733' },
      //   { id: 2, name: 'Storia', color_placeholder: '#33FF57' },
      //   { id: 3, name: 'Scienze', color_placeholder: '#3357FF' },
      //   { id: 4, name: 'Italiano', color_placeholder: '#F3FF33'},
      // ];
      // state.value.subjects = mockSubjects;
      console.log('Subjects fetched:', state.value.subjects);

    } catch (err) {
      console.error('Error fetching subjects:', err);
      state.value.error = (err as Error).message || 'Failed to fetch subjects';
      state.value.subjects = []; // Resetta in caso di errore
    } finally {
      state.value.loading = false;
    }
  }

  function clearSubjects() {
    state.value.subjects = [];
    state.value.error = null;
    // Non resettare loading qui, fetchSubjects lo gestirà
  }


  function getSubjectById(id: number): Subject | undefined {
    return state.value.subjects.find(subject => subject.id === id);
  }

  return {
    // State (esposto tramite computed)
    subjects,
    loading,
    error,
    // Actions
    fetchSubjects,
    clearSubjects,
    // Getters
    getSubjectById,
  };
});