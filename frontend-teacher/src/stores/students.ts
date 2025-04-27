// frontend-teacher/src/stores/students.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Student } from '@/types/users';
import { getMyStudents } from '@/api/students'; // Importa la funzione API

export const useStudentStore = defineStore('students', () => {
  // --- State ---
  const students = ref<Student[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // --- Getters ---
  const allStudents = computed(() => students.value);
  const studentCount = computed(() => students.value.length);

  // --- Actions ---

  /**
   * Recupera l'elenco degli studenti del docente dall'API e aggiorna lo stato.
   */
  async function fetchStudents() {
    if (students.value.length > 0) {
      // Non ricaricare se abbiamo già i dati (potremmo aggiungere logica di invalidazione)
      // console.log('Studenti già caricati.');
      // return;
    }
    isLoading.value = true;
    error.value = null;
    try {
      const response = await getMyStudents();
      students.value = response.data;
      // console.log('Studenti caricati:', students.value);
    } catch (err) {
      console.error('Errore durante il recupero degli studenti:', err);
      // Gestione sicura del tipo 'unknown'
      let errorMessage = 'Errore sconosciuto durante il recupero degli studenti.';
      if (typeof err === 'object' && err !== null) {
        // Tentativo di accedere alle proprietà comuni degli errori Axios/HTTP
        const axiosError = err as { response?: { data?: { detail?: string } }, message?: string };
        errorMessage = axiosError.response?.data?.detail || axiosError.message || errorMessage;
      } else if (err instanceof Error) {
         errorMessage = err.message;
      } else if (typeof err === 'string') {
         errorMessage = err;
      }
      error.value = errorMessage;
      students.value = []; // Resetta in caso di errore
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Restituisce uno studente per ID dallo store locale.
   * @param studentId L'ID dello studente da cercare.
   */
  function getStudentById(studentId: number): Student | undefined {
    return students.value.find(s => s.id === studentId);
  }


  return {
    // State
    students,
    isLoading,
    error,
    // Getters
    allStudents,
    studentCount,
    // Actions
    fetchStudents,
    getStudentById,
  };
});