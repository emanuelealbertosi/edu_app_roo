import apiClient from './config';
import type { AxiosResponse } from 'axios';

// Interfaccia per i dati restituiti dall'endpoint della dashboard del docente
export interface TeacherDashboardData {
  student_count: number;
  quiz_template_count: number;
  pathway_template_count: number;
  pending_manual_answers_count: number;
  // Aggiungere altri campi se verranno implementati nel backend
}

/**
 * Recupera i dati aggregati per la dashboard del docente autenticato.
 */
export const fetchTeacherDashboardData = async (): Promise<TeacherDashboardData> => {
  try {
    // L'URL è relativo a baseURL ('/api') e punta all'endpoint creato in apps.users.urls
    const response: AxiosResponse<TeacherDashboardData> = await apiClient.get('/teacher/dashboard-data/');
    return response.data;
  } catch (error) {
    console.error('Errore durante il recupero dei dati della dashboard docente:', error);
    throw error;
  }
};