import apiClient from './config';

// Interfacce per TypeScript
export interface QuizDetails {
  id: number;
  title: string;
  description: string;
  metadata: {
    [key: string]: any;
  };
}

export interface Question {
  id: number;
  text: string;
  // Aggiornato per usare i valori effettivi del backend (come in models.py)
  question_type: 'MC_SINGLE' | 'MC_MULTI' | 'TF' | 'FILL_BLANK' | 'OPEN_MANUAL';
  question_type_display?: string | null; // Aggiunto campo display opzionale
  order: number;
  metadata: {
    points?: number;
    fill_blank_correct_answers?: string[];
    [key: string]: any;
  };
  answer_options?: {
    id: number;
    text: string;
    order: number;
  }[];
}

export interface QuizAttempt {
  id: number;
  quiz: QuizDetails;
  started_at: string;
  completed_at: string | null;
  score: number | null;
  points_earned: number | null;
  status: 'IN_PROGRESS' | 'PENDING_GRADING' | 'COMPLETED' | 'FAILED'; // Usa valori backend (uppercase)
}

// Interfaccia per una singola risposta data dallo studente
export interface StudentAnswerResult {
  id: number;
  quiz_attempt: number;
  question: number; // ID della domanda
  question_text?: string; // Opzionale, potrebbe non essere sempre incluso
  // Aggiornato per usare i valori effettivi del backend
  question_type?: 'MC_SINGLE' | 'MC_MULTI' | 'TF' | 'FILL_BLANK' | 'OPEN_MANUAL'; // Opzionale
  selected_answers: any; // Formato dipende dal tipo di domanda
  is_correct: boolean | null;
  score: number | null;
  answered_at: string;
}

// Interfaccia per i dati base di un Badge (come da SimpleBadgeSerializer)
export interface SimpleBadge {
  id: number;
  name: string;
  image_url: string | null; // Può essere null se non c'è immagine
  description?: string; // Opzionale
}

export interface AttemptDetails extends QuizAttempt {
  questions: Question[]; // Lista delle domande del quiz
  given_answers: StudentAnswerResult[]; // Lista delle risposte date dallo studente
  // Nuovi campi dal backend
  status_display: string | null; // Campo display per lo stato
  completion_threshold: number | null; // Percentuale
  total_questions: number | null;
  correct_answers_count: number | null;
  newly_earned_badges?: SimpleBadge[]; // Aggiunto campo opzionale per i badge
}

// Tipi per le risposte alle domande
export interface MultipleChoiceSingleAnswer {
  answer_option_id: number;
}

export interface MultipleChoiceMultipleAnswer {
  answer_option_ids: number[];
}

export interface TrueFalseAnswer {
  is_true: boolean;
}

export interface FillBlankAnswer {
  answers: {
    [key: string]: string; // Indice -> valore risposta
  };
}

export interface OpenAnswerManualAnswer {
  text: string;
}

export type Answer = 
  | MultipleChoiceSingleAnswer 
  | MultipleChoiceMultipleAnswer 
  | TrueFalseAnswer 
  | FillBlankAnswer 
  | OpenAnswerManualAnswer;

/**
 * Servizio per interagire con i quiz
 */
const QuizService = {
  /**
   * Ottiene i dettagli di un quiz
   */
  async getQuizDetails(quizId: number): Promise<QuizDetails> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.get(`student/quizzes/${quizId}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching quiz details for quiz ${quizId}:`, error);
      throw error;
    }
  },

  /**
   * Inizia un nuovo tentativo per un quiz
   */
  async startAttempt(quizId: number): Promise<QuizAttempt> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.post(`student/quizzes/${quizId}/attempts/start-attempt/`);
      return response.data;
    } catch (error) {
      console.error(`Error starting attempt for quiz ${quizId}:`, error);
      throw error;
    }
  },

  /**
   * Ottiene i dettagli di un tentativo
   */
  async getAttemptDetails(attemptId: number): Promise<AttemptDetails> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.get(`student/attempts/${attemptId}/details/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching attempt details for attempt ${attemptId}:`, error);
      throw error;
    }
  },

  /**
   * Ottiene la domanda corrente/successiva per un tentativo
   */
  async getCurrentQuestion(attemptId: number): Promise<Question> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.get(`student/attempts/${attemptId}/current-question/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching current question for attempt ${attemptId}:`, error);
      throw error;
    }
  },

  /**
   * Invia una risposta per una domanda
   */
  async submitAnswer(
    attemptId: number, 
    questionId: number, 
    answer: Answer
  ): Promise<{ is_correct: boolean | null; message?: string }> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.post(`student/attempts/${attemptId}/submit-answer/`, {
        question_id: questionId,
        selected_answers: answer
      });
      return response.data;
    } catch (error) {
      console.error(`Error submitting answer for question ${questionId}:`, error);
      throw error;
    }
  },

  /**
   * Completa un tentativo
   */
  async completeAttempt(attemptId: number): Promise<AttemptDetails> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.post(`student/attempts/${attemptId}/complete/`);
      return response.data;
    } catch (error) {
      console.error(`Error completing attempt ${attemptId}:`, error);
      throw error;
    }
  }
};

export default QuizService;