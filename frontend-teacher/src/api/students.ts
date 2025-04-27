// frontend-teacher/src/api/students.ts
import apiClient from './apiClient';
import type { Student } from '@/types/users'; // Assumendo che il tipo Student sia definito qui

/**
 * Recupera l'elenco degli studenti associati al docente autenticato.
 */
export const getMyStudents = (): Promise<{ data: Student[] }> => {
  // L'endpoint esatto potrebbe variare, ma /api/students/ è comune per DRF ViewSet
  return apiClient.get('/students/');
};