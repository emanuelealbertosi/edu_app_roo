import apiClient from './config';
import type { AxiosResponse } from 'axios';

// Interfaccia per i dettagli di un quiz all'interno di un percorso
export interface PathwayQuizDetail {
    id: number; // ID della relazione PathwayQuiz
    quiz: number; // ID del Quiz
    quiz_title: string;
    order: number;
}

// Interfaccia per i dati di un Percorso (basata su PathwaySerializer)
export interface Pathway {
    id: number;
    teacher: number;
    teacher_username: string;
    title: string;
    description: string | null;
    metadata: Record<string, any> | null;
    created_at: string; // Formato ISO 8601
    quiz_details: PathwayQuizDetail[]; // Read-only
}

// Interfaccia per i dati inviati durante la creazione/aggiornamento di un Percorso
// Esclude campi read-only
export interface PathwayPayload {
    title: string;
    description?: string | null;
    metadata?: Record<string, any> | null;
    // La gestione dei quiz (aggiunta/rimozione/ordine) avverrà tramite azioni dedicate
}

/**
 * Recupera l'elenco dei percorsi associati al docente autenticato.
 */
export const fetchPathways = async (): Promise<Pathway[]> => {
    try {
        const response: AxiosResponse<Pathway[]> = await apiClient.get('/education/pathways/');
        return response.data;
    } catch (error) {
        console.error('Errore durante il recupero dei percorsi:', error);
        throw error;
    }
};

/**
 * Recupera i dettagli di un singolo percorso.
 */
export const fetchPathwayDetails = async (pathwayId: number): Promise<Pathway> => {
    try {
        const response: AxiosResponse<Pathway> = await apiClient.get(`/education/pathways/${pathwayId}/`);
        return response.data;
    } catch (error) {
        console.error(`Errore durante il recupero dei dettagli del percorso ${pathwayId}:`, error);
        throw error;
    }
};

/**
 * Crea un nuovo percorso.
 */
export const createPathway = async (payload: PathwayPayload): Promise<Pathway> => {
    try {
        const response: AxiosResponse<Pathway> = await apiClient.post('/education/pathways/', payload);
        return response.data;
    } catch (error) {
        console.error('Errore durante la creazione del percorso:', error);
        throw error;
    }
};

/**
 * Aggiorna un percorso esistente (usando PATCH).
 */
export const updatePathway = async (pathwayId: number, payload: Partial<PathwayPayload>): Promise<Pathway> => {
    try {
        const response: AxiosResponse<Pathway> = await apiClient.patch(`/education/pathways/${pathwayId}/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'aggiornamento del percorso ${pathwayId}:`, error);
        throw error;
    }
};

/**
 * Elimina un percorso esistente.
 */
export const deletePathwayApi = async (pathwayId: number): Promise<void> => {
    try {
        await apiClient.delete(`/education/pathways/${pathwayId}/`);
    } catch (error) {
        console.error(`Errore durante l'eliminazione del percorso ${pathwayId}:`, error);
        throw error;
    }
};

// --- API per gestire i Quiz all'interno di un Percorso ---

/**
 * Aggiunge un quiz a un percorso o ne aggiorna l'ordine.
 */
export const addQuizToPathway = async (pathwayId: number, quizId: number, order: number): Promise<PathwayQuizDetail> => {
    try {
        const payload = { quiz_id: quizId, order: order };
        // L'endpoint è un'azione custom sul PathwayViewSet
        const response: AxiosResponse<PathwayQuizDetail> = await apiClient.post(`/education/pathways/${pathwayId}/add-quiz/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'aggiunta/aggiornamento del quiz ${quizId} al percorso ${pathwayId}:`, error);
        throw error;
    }
};

/**
 * Rimuove un quiz da un percorso.
 * Nota: L'API DRF standard per le relazioni M2M 'through' non espone direttamente
 * un endpoint DELETE sulla relazione stessa tramite il router nested standard.
 * Potrebbe essere necessario implementare un'azione custom nel backend
 * o gestire la rimozione modificando l'intero set di quiz del percorso.
 * Per ora, assumiamo che serva un'azione custom (da creare nel backend se non esiste).
 * Se l'azione custom non esiste, questa funzione fallirà.
 */
export const removeQuizFromPathway = async (pathwayId: number, pathwayQuizId: number): Promise<void> => {
     // pathwayQuizId è l'ID della relazione M2M (PathwayQuiz), non del Quiz stesso.
    try {
        // Assumiamo un'azione custom 'remove-quiz' che accetta l'ID della relazione M2M
        // await apiClient.post(`/education/pathways/${pathwayId}/remove-quiz/`, { pathway_quiz_id: pathwayQuizId });
        // OPPURE, se l'API permette DELETE sull'endpoint della relazione (non standard con nested routers):
        // await apiClient.delete(`/education/pathways/${pathwayId}/quizzes/${pathwayQuizId}/`); // Questo probabilmente non funziona
        console.warn(`API per rimuovere quiz da percorso (relazione ID ${pathwayQuizId}) non implementata o endpoint non standard.`);
        throw new Error("API per rimuovere quiz da percorso non implementata.");
    } catch (error) {
        console.error(`Errore durante la rimozione del quiz (relazione ID ${pathwayQuizId}) dal percorso ${pathwayId}:`, error);
        throw error;
    }
};