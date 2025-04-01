import apiClient from './config';
import type { Quiz } from './dashboard';

// Interfacce per TypeScript
export interface PathwayDetails {
  id: number;
  title: string;
  description: string;
  metadata: {
    points_on_completion?: number;
    [key: string]: any;
  };
  progress: {
    status: string;
    last_completed_quiz_order: number | null;
    completed_at: string | null;
    points_earned: number | null;
  } | null;
  quizzes: {
    id: number;
    title: string;
    description: string;
    order: number;
    is_available: boolean;
    is_completed: boolean;
    attempt_id?: number;
  }[];
}

/**
 * Servizio per interagire con i percorsi formativi
 */
const PathwayService = {
  /**
   * Ottiene i dettagli di un percorso formativo specifico
   */
  async getPathwayDetails(pathwayId: number): Promise<PathwayDetails> {
    try {
      const response = await apiClient.get(`student/pathways/${pathwayId}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching pathway details for pathway ${pathwayId}:`, error);
      throw error;
    }
  },

  /**
   * Avvia un quiz all'interno di un percorso
   */
  async startQuizInPathway(pathwayId: number, quizId: number): Promise<{ attempt_id: number }> {
    try {
      const response = await apiClient.post(`student/pathways/${pathwayId}/start-quiz/${quizId}/`);
      return response.data;
    } catch (error) {
      console.error(`Error starting quiz ${quizId} in pathway ${pathwayId}:`, error);
      throw error;
    }
  }
};

export default PathwayService;