import apiClient from './config';
import type { AxiosResponse } from 'axios';

// --- Interfacce Basate sui Serializer Backend ---

// Interfaccia per AnswerOptionTemplate (già definita in quizzes.ts? Se sì, importare)
// Se non definita altrove, definirla qui:
export interface AnswerOptionTemplate {
  id: number;
  text: string;
  is_correct: boolean;
  order: number;
}

// Interfaccia per QuestionTemplate (già definita in quizzes.ts? Se sì, importare)
// Se non definita altrove, definirla qui:
export interface QuestionTemplate {
  id: number;
  quiz_template: number; // ID del QuizTemplate padre
  text: string;
  question_type: string; // Es: 'MC_SINGLE', 'TF', etc.
  question_type_display?: string; // Read-only dal backend
  order: number;
  metadata: Record<string, any> | null;
  answer_options?: AnswerOptionTemplate[]; // Opzioni nested (read-only in list/detail?)
}

// Payload per creare/aggiornare QuestionTemplate
export interface QuestionTemplatePayload {
    text: string;
    question_type: string;
    order?: number; // L'ordine viene gestito dal backend su create
    metadata?: Record<string, any> | null;
}

// Payload per creare/aggiornare AnswerOptionTemplate
export interface AnswerOptionTemplatePayload {
    text: string;
    is_correct?: boolean;
    order?: number; // L'ordine viene gestito dal backend su create
}


// --- API Functions ---

// == Question Templates ==

/**
 * Recupera gli ID ordinati delle domande template per un specifico template quiz del docente.
 * Utile per la navigazione sequenziale.
 */
export const fetchQuestionTemplateIdsForQuizTemplate = async (quizTemplateId: number): Promise<number[]> => {
    try {
        // Assumiamo che l'endpoint restituisca un array di ID numerici: [10, 15, 20, 25]
        // Corretto URL per l'azione detail=False nel ViewSet nidificato
        const response: AxiosResponse<number[]> = await apiClient.get(`/education/teacher/quiz-templates/${quizTemplateId}/questions/question-ids/`);
        return response.data;
    } catch (error) {
        console.error(`Errore recupero ID domande template per QuizTemplate ${quizTemplateId}:`, error);
        throw error;
    }
};


/**
 * Recupera le domande template per un specifico template quiz del docente.
 */
export const fetchTeacherQuestionTemplates = async (quizTemplateId: number): Promise<QuestionTemplate[]> => {
    try {
        const response: AxiosResponse<QuestionTemplate[]> = await apiClient.get(`/education/teacher/quiz-templates/${quizTemplateId}/questions/`);
        return response.data;
    } catch (error) {
        console.error(`Errore recupero domande template per QuizTemplate ${quizTemplateId}:`, error);
        throw error;
    }
};

/**
 * Recupera i dettagli di una specifica domanda template.
 */
export const fetchTeacherQuestionTemplateDetails = async (quizTemplateId: number, questionTemplateId: number): Promise<QuestionTemplate> => {
    try {
        const response: AxiosResponse<QuestionTemplate> = await apiClient.get(`/education/teacher/quiz-templates/${quizTemplateId}/questions/${questionTemplateId}/`);
        return response.data;
    } catch (error) {
        console.error(`Errore recupero dettagli domanda template ${questionTemplateId} per QuizTemplate ${quizTemplateId}:`, error);
        throw error;
    }
};

/**
 * Crea una nuova domanda template per un template quiz del docente.
 */
export const createTeacherQuestionTemplate = async (quizTemplateId: number, payload: QuestionTemplatePayload): Promise<QuestionTemplate> => {
    try {
        const response: AxiosResponse<QuestionTemplate> = await apiClient.post(`/education/teacher/quiz-templates/${quizTemplateId}/questions/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore creazione domanda template per QuizTemplate ${quizTemplateId}:`, error);
        throw error;
    }
};

/**
 * Aggiorna una domanda template esistente (PATCH).
 */
export const updateTeacherQuestionTemplate = async (quizTemplateId: number, questionTemplateId: number, payload: Partial<QuestionTemplatePayload>): Promise<QuestionTemplate> => {
    try {
        const response: AxiosResponse<QuestionTemplate> = await apiClient.patch(`/education/teacher/quiz-templates/${quizTemplateId}/questions/${questionTemplateId}/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore aggiornamento domanda template ${questionTemplateId} per QuizTemplate ${quizTemplateId}:`, error);
        throw error;
    }
};

/**
 * Elimina una domanda template.
 */
export const deleteTeacherQuestionTemplate = async (quizTemplateId: number, questionTemplateId: number): Promise<void> => {
    try {
        await apiClient.delete(`/education/teacher/quiz-templates/${quizTemplateId}/questions/${questionTemplateId}/`);
    } catch (error) {
        console.error(`Errore eliminazione domanda template ${questionTemplateId} per QuizTemplate ${quizTemplateId}:`, error);
        throw error;
    }
};


// == Answer Option Templates ==

/**
 * Recupera le opzioni template per una specifica domanda template del docente.
 */
export const fetchTeacherAnswerOptionTemplates = async (quizTemplateId: number, questionTemplateId: number): Promise<AnswerOptionTemplate[]> => {
    try {
        const response: AxiosResponse<AnswerOptionTemplate[]> = await apiClient.get(`/education/teacher/quiz-templates/${quizTemplateId}/questions/${questionTemplateId}/options/`);
        return response.data;
    } catch (error) {
        console.error(`Errore recupero opzioni template per DomandaTemplate ${questionTemplateId}:`, error);
        throw error;
    }
};

/**
 * Crea una nuova opzione template per una domanda template del docente.
 */
export const createTeacherAnswerOptionTemplate = async (quizTemplateId: number, questionTemplateId: number, payload: AnswerOptionTemplatePayload): Promise<AnswerOptionTemplate> => {
    try {
        const response: AxiosResponse<AnswerOptionTemplate> = await apiClient.post(`/education/teacher/quiz-templates/${quizTemplateId}/questions/${questionTemplateId}/options/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore creazione opzione template per DomandaTemplate ${questionTemplateId}:`, error);
        throw error;
    }
};

/**
 * Aggiorna un'opzione template esistente (PATCH).
 */
export const updateTeacherAnswerOptionTemplate = async (quizTemplateId: number, questionTemplateId: number, optionTemplateId: number, payload: Partial<AnswerOptionTemplatePayload>): Promise<AnswerOptionTemplate> => {
    try {
        const response: AxiosResponse<AnswerOptionTemplate> = await apiClient.patch(`/education/teacher/quiz-templates/${quizTemplateId}/questions/${questionTemplateId}/options/${optionTemplateId}/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore aggiornamento opzione template ${optionTemplateId}:`, error);
        throw error;
    }
};

/**
 * Elimina un'opzione template.
 */
export const deleteTeacherAnswerOptionTemplate = async (quizTemplateId: number, questionTemplateId: number, optionTemplateId: number): Promise<void> => {
    try {
        await apiClient.delete(`/education/teacher/quiz-templates/${quizTemplateId}/questions/${questionTemplateId}/options/${optionTemplateId}/`);
    } catch (error) {
        console.error(`Errore eliminazione opzione template ${optionTemplateId}:`, error);
        throw error;
    }
};