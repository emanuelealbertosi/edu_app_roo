import apiClient from './apiClient'; // Importa l'istanza axios configurata
import type { AxiosResponse } from 'axios';

// Interfaccia per i dati di assegnazione Quiz (da Template a Studente)
// Presa da frontend-teacher/src/api/quizzes.ts
export interface AssignQuizPayload {
    student: number; // ID dello studente (user_id)
    due_date?: string | null; // Data di scadenza opzionale (formato ISO 8601)
}

// Interfaccia per la risposta dell'assegnazione (basata sul serializer)
// Presa da frontend-teacher/src/api/quizzes.ts
export interface QuizAssignmentResponse {
    status: string;
    assignment: {
        id: number;
        student: number;
        student_username: string;
        quiz: number; // Questo sarà l'ID dell'istanza Quiz creata, non del template
        quiz_title: string;
        assigned_at: string;
        due_date: string | null;
    };
}

// Interfaccia per i dati di assegnazione Quiz Template a Gruppo
// Presa da frontend-teacher/src/api/quizzes.ts
export interface AssignQuizTemplateToGroupPayload {
    group: number; // ID del gruppo
    due_date?: string | null; // Data di scadenza opzionale (formato ISO 8601)
}

// Interfaccia per la risposta dell'assegnazione a gruppo
// Presa da frontend-teacher/src/api/quizzes.ts
export interface GroupAssignmentResponse {
    status: string;
    // Potrebbe includere dettagli sugli assignment creati se l'API li restituisce
    // Ad esempio, un array di QuizAssignmentResponse per ogni studente nel gruppo
    assignments?: QuizAssignmentResponse[]; // Ipotizzando una struttura
    message?: string; // O un messaggio generico
}

/**
 * Assegna un template quiz a uno studente singolo.
 * @param templateId L'ID del template quiz da assegnare.
 * @param payload Contiene l'ID dello studente e la data di scadenza opzionale.
 */
export const assignQuizToStudent = async (templateId: number, payload: AssignQuizPayload): Promise<QuizAssignmentResponse> => {
    const finalPayload = {
        student: payload.student,
        due_date: payload.due_date || null
    };

    try {
        // L'endpoint dovrebbe essere lo stesso usato da frontend-teacher se il backend è condiviso
        // e l'azione è definita sul QuizTemplateViewSet del docente.
        const url = `/education/teacher/quiz-templates/${templateId}/assign-student/`;
        const response: AxiosResponse<QuizAssignmentResponse> = await apiClient.post(url, finalPayload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'assegnazione del template quiz ${templateId} allo studente ${payload.student}:`, error);
        throw error;
    }
};

/**
 * Assegna un template quiz a un gruppo.
 * @param templateId L'ID del template quiz da assegnare.
 * @param payload Contiene l'ID del gruppo e la data di scadenza.
 */
export const assignQuizTemplateToGroup = async (templateId: number, payload: AssignQuizTemplateToGroupPayload): Promise<GroupAssignmentResponse> => {
    try {
        // L'endpoint dovrebbe essere lo stesso.
        const url = `/education/teacher/quiz-templates/${templateId}/assign-group/`;
        const response: AxiosResponse<GroupAssignmentResponse> = await apiClient.post(url, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'assegnazione del template quiz ${templateId} al gruppo ${payload.group}:`, error);
        throw error;
    }
};