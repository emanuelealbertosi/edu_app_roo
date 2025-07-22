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
  async function fetchSubjects(params: { course_id?: number } = {}) {
    const { course_id } = params;
    const cacheKey = course_id ? `course_${course_id}` : 'all';

    // Semplifichiamo la logica di caching per ora, ricaricando sempre.
    // In futuro, si potrebbe implementare una cache più sofisticata se necessario.
    
    console.log(`Fetching subjects for ${cacheKey}...`);
    state.value.loading = true;
    state.value.error = null;
    
    try {
      const url = course_id
        ? `/lezioni/subjects/?course_id=${course_id}`
        : '/lezioni/subjects/';
        
      const response = await apiClient.get(url);
      state.value.subjects = response.data;
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