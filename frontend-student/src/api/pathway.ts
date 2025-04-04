import apiClient from './config';
import type { Quiz } from './dashboard'; // Potrebbe servire per NextQuiz

// Interfacce per TypeScript

// Interfaccia per il progresso (basata su PathwayProgressSerializer)
export interface PathwayProgressData {
  id: number;
  student_info: any; // O un'interfaccia StudentInfo più specifica
  pathway: number;
  pathway_title: string;
  last_completed_quiz_order: number | null;
  completed_orders: number[]; // Aggiunto: lista degli ordini completati
  started_at: string;
  completed_at: string | null;
  status: string; // 'IN_PROGRESS', 'COMPLETED'
  status_display: string;
  points_earned: number | null; // Aggiunto da SimplePathwayProgressSerializer
}

// Interfaccia per il prossimo quiz (basata su NextPathwayQuizSerializer)
export interface NextQuizInfo {
  id: number;
  title: string;
  description: string | null;
}

// Interfaccia aggiornata per i dettagli del tentativo del percorso
export interface PathwayAttemptDetails {
  id: number;
  teacher: number;
  teacher_username: string;
  title: string;
  description: string | null;
  metadata: {
    points_on_completion?: number;
    [key: string]: any;
  };
  created_at: string;
  quiz_details: { // Dettagli dei quiz nel percorso (da PathwayQuizSerializer)
      id: number;
      quiz_id: number;
      quiz_title: string;
      order: number;
  }[];
  progress: PathwayProgressData | null; // Dettagli del progresso attuale
  next_quiz: NextQuizInfo | null; // Dettagli del prossimo quiz da fare
}


/**
 * Servizio per interagire con i percorsi formativi
 */
const PathwayService = {
  /**
   * Ottiene i dettagli di un percorso formativo specifico (vista generica)
   * NOTA: Questo potrebbe non essere più necessario o restituire dati diversi
   *       dall'endpoint specifico per il tentativo.
   */
  // async getPathwayDetails(pathwayId: number): Promise<PathwayDetails> {
  //   try {
  //     const response = await apiClient.get(`education/pathways/${pathwayId}/`); // Aggiornato URL base
  //     return response.data;
  //   } catch (error) {
  //     console.error(`Error fetching pathway details for pathway ${pathwayId}:`, error);
  //     throw error;
  //   }
  // },

  /**
   * Ottiene i dettagli specifici per iniziare o continuare un tentativo di percorso.
   * Chiama il nuovo endpoint /api/education/pathways/{pk}/attempt/
   */
  async getPathwayAttemptDetails(pathwayId: number): Promise<PathwayAttemptDetails> {
    try {
      // Usa il nuovo URL specifico per il tentativo dello studente
      // Il prefisso /api/education/ è gestito da apiClient
      const response = await apiClient.get(`education/pathways/${pathwayId}/attempt/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching pathway attempt details for pathway ${pathwayId}:`, error);
      // Potrebbe essere utile gestire errori specifici (es. 403 Forbidden se non assegnato)
      throw error;
    }
  },


  /**
   * Avvia un quiz all'interno di un percorso
   * NOTA: La logica di avvio quiz potrebbe ora essere gestita diversamente,
   *       magari direttamente dalla vista QuizAttemptView.
   */
  // async startQuizInPathway(pathwayId: number, quizId: number): Promise<{ attempt_id: number }> {
  //   try {
  //     // Questo endpoint potrebbe non esistere più o essere cambiato
  //     const response = await apiClient.post(`education/pathways/${pathwayId}/start-quiz/${quizId}/`);
  //     return response.data;
  //   } catch (error) {
  //     console.error(`Error starting quiz ${quizId} in pathway ${pathwayId}:`, error);
  //     throw error;
  //   }
  // }
};

export default PathwayService;