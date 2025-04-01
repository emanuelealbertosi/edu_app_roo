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
  question_type: 'multiple_choice_single' | 'multiple_choice_multiple' | 'true_false' | 'fill_blank' | 'open_answer_manual';
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
  status: 'in_progress' | 'pending_manual_grading' | 'completed';
}

export interface AttemptDetails extends QuizAttempt {
  questions: Question[];
  student_answers: {
    question_id: number;
    selected_answers: any; // Formato dipende dal tipo di domanda
    is_correct: boolean | null;
    score: number | null;
    answered_at: string;
  }[];
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
      const response = await apiClient.get(`quizzes/${quizId}/`);
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
      const response = await apiClient.post(`quizzes/${quizId}/start-attempt/`);
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
      const response = await apiClient.get(`attempts/${attemptId}/details/`);
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
      const response = await apiClient.get(`attempts/${attemptId}/current-question/`);
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
      const response = await apiClient.post(`attempts/${attemptId}/submit-answer/`, {
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
      const response = await apiClient.post(`attempts/${attemptId}/complete/`);
      return response.data;
    } catch (error) {
      console.error(`Error completing attempt ${attemptId}:`, error);
      throw error;
    }
  }
};

export default QuizService;