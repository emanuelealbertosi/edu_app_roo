import apiClient from './config';
import type { StudentAnswerPayloadFillBlank, BlankDisplayConfig } from '../types/education'; // Import per FillBlank

// Interfacce per TypeScript
export interface QuizDetails {
  id: number;
  title: string;
  description: string;
  metadata: {
    [key: string]: any; // Mantenuto generico per altri usi, ma FillBlank avrà una struttura specifica
  };
}

// Definiamo una struttura più specifica per i blank come da FILL_BLANK_PLAN.md
// da usare in QuestionMetadataFillBlank
export interface QuestionBlankDefinitionApi extends BlankDisplayConfig {
  // correct_answers NON viene inviato allo studente durante lo svolgimento
  // ma potrebbe essere presente nei metadati completi per la visualizzazione dei risultati
  correct_answers?: string[];
}

export interface QuestionMetadataFillBlankApi {
  text_with_placeholders: string;
  blanks: QuestionBlankDefinitionApi[];
  case_sensitive?: boolean; // Opzionale durante lo svolgimento, presente nei risultati
  points?: number;
}

export interface Question {
  id: number;
  text: string;
  question_type: 'MC_SINGLE' | 'MC_MULTI' | 'TF' | 'fill_blank' | 'OPEN_MANUAL';
  question_type_display?: string | null;
  order: number;
  metadata: { // Questo metadata è un oggetto generico
    points?: number;
    // fill_blank_correct_answers?: string[]; // OBSOLETO, usare la struttura in QuestionMetadataFillBlankApi
    // Per FILL_BLANK, ci aspettiamo che metadata contenga QuestionMetadataFillBlankApi
    // Per gli altri tipi, potrebbe avere altre strutture.
    // Si potrebbe usare un tipo unione discriminata qui se si volessero tipizzare tutti i metadata.
    text_with_placeholders?: string; // Aggiunto per FILL_BLANK
    blanks?: QuestionBlankDefinitionApi[]; // Aggiunto per FILL_BLANK
    case_sensitive?: boolean; // Aggiunto per FILL_BLANK (per risultati)
    [key: string]: any; // Per retrocompatibilità e altri tipi di domande
  };
  answer_options?: {
    id: number;
    text: string;
    order: number;
    is_correct: boolean;
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

// FillBlankAnswer ora userà la struttura da StudentAnswerPayloadFillBlank
// export interface FillBlankAnswer { // OBSOLETO
//   answers: {
//     [key: string]: string; // Indice -> valore risposta
//   };
// }
// Al suo posto, usiamo direttamente StudentAnswerPayloadFillBlank importato

// Nuovo tipo per il payload API specifico per fill_blank
export interface FillBlankApiPayload {
  answers: string[]; // Lista ordinata di stringhe di risposta
}

export interface OpenAnswerManualAnswer {
  text: string;
}

export type Answer =
  | MultipleChoiceSingleAnswer
  | MultipleChoiceMultipleAnswer
  | TrueFalseAnswer
  | FillBlankApiPayload // Aggiornato per usare il nuovo tipo per l'API
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