import apiClient from './config';
import type { AxiosResponse } from 'axios';

// Interfaccia per le opzioni di risposta (basata su AnswerOptionSerializer)
// Sarà utile quando implementeremo la gestione delle opzioni
export interface AnswerOption {
    id: number;
    text: string;
    is_correct: boolean;
    order: number;
}

// Interfaccia per i dati di una Domanda (basata su QuestionSerializer)
export interface Question {
    id: number;
    quiz: number; // ID del quiz a cui appartiene
    text: string;
    question_type: string; // Es: 'multiple_choice_single', 'true_false', etc.
    question_type_display: string; // Rappresentazione leggibile del tipo
    order: number;
    metadata: Record<string, any> | null;
    answer_options: AnswerOption[]; // Lista delle opzioni (read-only qui)
}

// Interfaccia per i dati inviati durante la creazione/aggiornamento di una Domanda
// Esclude campi read-only come id, quiz, question_type_display, answer_options
export interface QuestionPayload {
    text: string;
    question_type: string;
    order: number;
    metadata?: Record<string, any> | null;
}

// Interfaccia per i dati inviati durante la creazione/aggiornamento di un'Opzione di Risposta
export interface AnswerOptionPayload {
    text: string;
    is_correct: boolean;
    order: number;
}

/**
 * Recupera l'elenco delle domande per un quiz specifico.
 */
export const fetchQuestions = async (quizId: number): Promise<Question[]> => {
    try {
        const response: AxiosResponse<Question[]> = await apiClient.get(`/education/quizzes/${quizId}/questions/`);
        return response.data;
    } catch (error) {
        console.error(`Errore durante il recupero delle domande per il quiz ${quizId}:`, error);
        throw error;
    }
};

/**
 * Recupera i dettagli di una singola domanda.
 */
export const fetchQuestionDetails = async (quizId: number, questionId: number): Promise<Question> => {
    try {
        const response: AxiosResponse<Question> = await apiClient.get(`/education/quizzes/${quizId}/questions/${questionId}/`);
        return response.data;
    } catch (error) {
        console.error(`Errore durante il recupero dei dettagli della domanda ${questionId} per il quiz ${quizId}:`, error);
        throw error;
    }
};

/**
 * Crea una nuova domanda per un quiz specifico.
 */
export const createQuestion = async (quizId: number, payload: QuestionPayload): Promise<Question> => {
    try {
        const response: AxiosResponse<Question> = await apiClient.post(`/education/quizzes/${quizId}/questions/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante la creazione della domanda per il quiz ${quizId}:`, error);
        throw error;
    }
};

/**
 * Aggiorna una domanda esistente (usando PATCH per aggiornamenti parziali).
 */
export const updateQuestion = async (quizId: number, questionId: number, payload: Partial<QuestionPayload>): Promise<Question> => {
    try {
        const response: AxiosResponse<Question> = await apiClient.patch(`/education/quizzes/${quizId}/questions/${questionId}/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'aggiornamento della domanda ${questionId} per il quiz ${quizId}:`, error);
        throw error;
    }
};

/**
 * Elimina una domanda esistente.
 */
export const deleteQuestionApi = async (quizId: number, questionId: number): Promise<void> => {
    try {
        await apiClient.delete(`/education/quizzes/${quizId}/questions/${questionId}/`);
    } catch (error) {
        console.error(`Errore durante l'eliminazione della domanda ${questionId} per il quiz ${quizId}:`, error);
        throw error;
    }
};

// --- Funzioni API per le Opzioni di Risposta ---

/**
 * Recupera l'elenco delle opzioni per una domanda specifica.
 * Nota: Queste sono già incluse in fetchQuestionDetails, ma questa funzione
 * potrebbe essere utile se si vuole ricaricare solo le opzioni.
 */
export const fetchAnswerOptions = async (quizId: number, questionId: number): Promise<AnswerOption[]> => {
    try {
        const response: AxiosResponse<AnswerOption[]> = await apiClient.get(`/education/quizzes/${quizId}/questions/${questionId}/options/`);
        return response.data;
    } catch (error) {
        console.error(`Errore durante il recupero delle opzioni per la domanda ${questionId}:`, error);
        throw error;
    }
};

/**
 * Crea una nuova opzione di risposta per una domanda specifica.
 */
export const createAnswerOption = async (quizId: number, questionId: number, payload: AnswerOptionPayload): Promise<AnswerOption> => {
    try {
        const response: AxiosResponse<AnswerOption> = await apiClient.post(`/education/quizzes/${quizId}/questions/${questionId}/options/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante la creazione dell'opzione per la domanda ${questionId}:`, error);
        throw error;
    }
};

/**
 * Aggiorna un'opzione di risposta esistente.
 */
export const updateAnswerOption = async (quizId: number, questionId: number, optionId: number, payload: Partial<AnswerOptionPayload>): Promise<AnswerOption> => {
    try {
        const response: AxiosResponse<AnswerOption> = await apiClient.patch(`/education/quizzes/${quizId}/questions/${questionId}/options/${optionId}/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'aggiornamento dell'opzione ${optionId} per la domanda ${questionId}:`, error);
        throw error;
    }
};

/**
 * Elimina un'opzione di risposta esistente.
 */
export const deleteAnswerOptionApi = async (quizId: number, questionId: number, optionId: number): Promise<void> => {
    try {
        await apiClient.delete(`/education/quizzes/${quizId}/questions/${questionId}/options/${optionId}/`);
    } catch (error) {
        console.error(`Errore durante l'eliminazione dell'opzione ${optionId} per la domanda ${questionId}:`, error);
        throw error;
    }
};