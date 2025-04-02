import apiClient from './config';

// Interfacce per TypeScript
export interface Quiz {
  id: number;
  title: string;
  description: string;
  available_from: string | null;
  available_until: string | null;
  metadata: {
    difficulty?: string;
    subject?: string;
    points_on_completion?: number;
    completion_threshold?: number;
    [key: string]: any;
  };
  attempts_count?: number;
  latest_attempt?: {
    id: number;
    status: string;
    score: number | null;
    started_at: string;
    completed_at: string | null;
  } | null;
}

export interface Pathway {
  id: number;
  title: string;
  description: string;
  metadata: {
    points_on_completion?: number;
    [key: string]: any;
  };
  progress?: {
    status: string;
    last_completed_quiz_order: number | null;
    completed_at: string | null;
    points_earned: number | null;
  } | null;
}

export interface WalletInfo {
  current_points: number;
  recent_transactions: {
    id: number;
    points_change: number;
    reason: string;
    timestamp: string;
  }[];
}

/**
 * Servizio per recuperare i dati della dashboard dello studente
 */
const DashboardService = {
  /**
   * Recupera tutti i quiz assegnati allo studente
   */
  async getAssignedQuizzes(): Promise<Quiz[]> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.get('student/dashboard/quizzes/');
      return response.data;
    } catch (error) {
      console.error('Error fetching assigned quizzes:', error);
      throw error;
    }
  },

  /**
   * Recupera tutti i percorsi assegnati allo studente
   */
  async getAssignedPathways(): Promise<Pathway[]> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.get('student/dashboard/pathways/');
      return response.data;
    } catch (error) {
      console.error('Error fetching assigned pathways:', error);
      throw error;
    }
  },

  /**
   * Recupera le informazioni sul wallet dello studente
   */
  async getWalletInfo(): Promise<WalletInfo> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.get('student/dashboard/wallet/');
      return response.data;
    } catch (error) {
      console.error('Error fetching wallet info:', error);
      throw error;
    }
  }
};

export default DashboardService;