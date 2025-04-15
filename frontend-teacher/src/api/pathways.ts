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
    source_template: number | null; // Aggiunto per fixare errore TS in AssignedPathwaysView
    description: string | null;
    metadata: Record<string, any> | null;
    created_at: string; // Formato ISO 8601
    quiz_details: PathwayQuizDetail[]; // Read-only
}
// --- Template Interfaces ---

// Interfaccia per i dettagli di un quiz template all'interno di un pathway template
export interface PathwayQuizTemplateDetail {
    id: number; // ID della relazione PathwayQuizTemplate
    quiz_template_id: number; // ID del QuizTemplate
    quiz_template_title: string;
    order: number;
}

// Interfaccia per i dati di un Pathway Template (basata su PathwayTemplateSerializer)
export interface PathwayTemplate {
    id: number;
    teacher: number;
    teacher_username: string;
    source_template: number | null; // Aggiunto campo
    title: string;
    description: string | null;
    metadata: Record<string, any> | null;
    created_at: string; // Formato ISO 8601
    quiz_template_details: PathwayQuizTemplateDetail[]; // Read-only
}

// Interfaccia per i dati inviati durante la creazione/aggiornamento di un Pathway Template
export interface PathwayTemplatePayload {
    title: string;
    description?: string | null;
    metadata?: Record<string, any> | null;
    // La gestione dei quiz template avverrà tramite azioni dedicate
}

// Interfaccia per aggiungere un QuizTemplate a un PathwayTemplate
export interface AddQuizTemplatePayload {
    quiz_template_id: number;
    order: number;
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
// --- API per Pathway Templates ---

/**
 * Recupera l'elenco dei template di percorso associati al docente autenticato.
 */
export const fetchPathwayTemplates = async (): Promise<PathwayTemplate[]> => {
    try {
        const response: AxiosResponse<PathwayTemplate[]> = await apiClient.get('/education/pathway-templates/');
        return response.data;
    } catch (error) {
        console.error('Errore durante il recupero dei template di percorso:', error);
        throw error;
    }
};

/**
 * Recupera i dettagli di un singolo template di percorso.
 */
export const fetchPathwayTemplateDetails = async (templateId: number): Promise<PathwayTemplate> => {
    try {
        const response: AxiosResponse<PathwayTemplate> = await apiClient.get(`/education/pathway-templates/${templateId}/`);
        return response.data;
    } catch (error) {
        console.error(`Errore durante il recupero dei dettagli del template di percorso ${templateId}:`, error);
        throw error;
    }
};

/**
 * Crea un nuovo template di percorso.
 */
export const createPathwayTemplate = async (payload: PathwayTemplatePayload): Promise<PathwayTemplate> => {
    try {
        const response: AxiosResponse<PathwayTemplate> = await apiClient.post('/education/pathway-templates/', payload);
        return response.data;
    } catch (error) {
        console.error('Errore durante la creazione del template di percorso:', error);
        throw error;
    }
};

/**
 * Aggiorna un template di percorso esistente (usando PATCH).
 */
export const updatePathwayTemplate = async (templateId: number, payload: Partial<PathwayTemplatePayload>): Promise<PathwayTemplate> => {
    try {
        const response: AxiosResponse<PathwayTemplate> = await apiClient.patch(`/education/pathway-templates/${templateId}/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'aggiornamento del template di percorso ${templateId}:`, error);
        throw error;
    }
};

/**
 * Elimina un template di percorso esistente.
 */
export const deletePathwayTemplateApi = async (templateId: number): Promise<void> => {
    try {
        await apiClient.delete(`/education/pathway-templates/${templateId}/`);
    } catch (error) {
        console.error(`Errore durante l'eliminazione del template di percorso ${templateId}:`, error);
        throw error;
    }
};

// --- API per gestire i Quiz Templates all'interno di un Pathway Template ---

/**
 * Recupera l'elenco dei quiz template associati a un pathway template.
 */
export const fetchQuizTemplatesForPathwayTemplate = async (pathwayTemplateId: number): Promise<PathwayQuizTemplateDetail[]> => {
    try {
        const response: AxiosResponse<PathwayQuizTemplateDetail[]> = await apiClient.get(`/education/pathway-templates/${pathwayTemplateId}/quiz-templates/`);
        return response.data;
    } catch (error) {
        console.error(`Errore durante il recupero dei quiz template per il pathway template ${pathwayTemplateId}:`, error);
        throw error;
    }
};


/**
 * Aggiunge un quiz template a un pathway template.
 */
export const addQuizTemplateToPathwayTemplate = async (pathwayTemplateId: number, payload: AddQuizTemplatePayload): Promise<PathwayQuizTemplateDetail> => {
    try {
        const response: AxiosResponse<PathwayQuizTemplateDetail> = await apiClient.post(`/education/pathway-templates/${pathwayTemplateId}/quiz-templates/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'aggiunta del quiz template al pathway template ${pathwayTemplateId}:`, error);
        throw error;
    }
};

/**
 * Rimuove un quiz template da un pathway template.
 * @param pathwayTemplateId L'ID del pathway template.
 * @param pathwayQuizTemplateId L'ID della relazione M2M (PathwayQuizTemplate).
 */
export const removeQuizTemplateFromPathwayTemplate = async (pathwayTemplateId: number, pathwayQuizTemplateId: number): Promise<void> => {
    try {
        // L'URL è /api/education/pathway-templates/{pathwayTemplateId}/quiz-templates/{pathwayQuizTemplateId}/
        await apiClient.delete(`/education/pathway-templates/${pathwayTemplateId}/quiz-templates/${pathwayQuizTemplateId}/`);
    } catch (error) {
        console.error(`Errore durante la rimozione del quiz template (relazione ID ${pathwayQuizTemplateId}) dal pathway template ${pathwayTemplateId}:`, error);
        throw error;
    }
};

// --- API per Assegnazione Percorsi ---

// Interfaccia per i dati inviati all'azione assign_student_pathway
export interface AssignPathwayPayload {
    student: number; // ID dello studente a cui assegnare
    due_date?: string | null; // Data di scadenza opzionale (formato ISO 8601)
}

// Interfaccia per la risposta dell'assegnazione (basata su PathwayAssignmentSerializer)
// Assumiamo che il backend restituisca direttamente i dati dell'assegnazione
export interface PathwayAssignment {
    id: number;
    student: number;
    student_username: string; // Potrebbe essere aggiunto dal serializer
    pathway: number;
    pathway_title: string; // Potrebbe essere aggiunto dal serializer
    assigned_by: number;
    assigned_by_username: string; // Potrebbe essere aggiunto dal serializer
    assigned_at: string;
    due_date: string | null;
}

/**
 * Assegna un percorso a uno studente, creandolo da un template.
 * @param pathwayTemplateId L'ID del PathwayTemplate da cui creare e assegnare.
 * @param payload Oggetto contenente 'student' (ID studente) e opzionalmente 'due_date'.
 */
export const assignPathwayToStudent = async (pathwayTemplateId: number, payload: AssignPathwayPayload): Promise<PathwayAssignment> => {
    try {
        // L'URL corretto è sull'endpoint del template
        const url = `/education/pathway-templates/${pathwayTemplateId}/assign-student/`;
        console.log(`[api/pathways] Assegnazione percorso da template ${pathwayTemplateId} a studente ${payload.student}. URL: ${url}`);
        const response: AxiosResponse<PathwayAssignment> = await apiClient.post(url, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'assegnazione del percorso dal template ${pathwayTemplateId}:`, error);
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
        // Chiama l'azione custom 'remove_quiz' implementata nel backend
        // L'URL è /api/education/pathways/{pathwayId}/remove-quiz/{pathwayQuizId}/
        await apiClient.delete(`/education/pathways/${pathwayId}/remove-quiz/${pathwayQuizId}/`);
    } catch (error) {
        console.error(`Errore durante la rimozione del quiz (relazione ID ${pathwayQuizId}) dal percorso ${pathwayId}:`, error);
        throw error; // Rilancia l'errore per gestirlo nel componente Vue
    }
};
// Interfaccia per i dettagli di un'assegnazione specifica di un percorso
// (basata su PathwayAssignmentDetailSerializer)
export interface PathwayAssignmentDetail {
  id: number; // ID dell'assegnazione
  student_id: number; // ID dello studente (CORRETTO)
  student_username: string;
  student_full_name: string;
  assigned_at: string;
}

// Interfaccia per le statistiche aggregate delle assegnazioni di un percorso
export interface PathwayAssignmentStats {
  assigned_count: number;
  started_count: number;
  completed_count: number;
}

// Interfaccia per la risposta completa dell'endpoint assignments per percorsi
export interface PathwayAssignmentsResponse {
  assignments: PathwayAssignmentDetail[];
  stats: PathwayAssignmentStats;
}

/**
 * Recupera l'elenco degli studenti a cui è stata assegnata una specifica istanza di percorso
 * e le statistiche aggregate.
 * @param pathwayId L'ID del percorso.
 */
export const fetchPathwayAssignments = async (pathwayId: number): Promise<PathwayAssignmentsResponse> => {
  try {
    // L'URL per l'azione custom è /education/pathways/{pathway_pk}/assignments/
    const response: AxiosResponse<PathwayAssignmentsResponse> = await apiClient.get(`/education/pathways/${pathwayId}/assignments/`);
    return response.data;
  } catch (error) {
    console.error(`Errore durante il recupero delle assegnazioni per il percorso ${pathwayId}:`, error);
    throw error;
  }
};

/**
 * Disassegna un percorso da uno studente eliminando l'assegnazione.
 * @param assignmentId L'ID dell'oggetto PathwayAssignment da eliminare.
 */
export const unassignPathwayFromStudent = async (assignmentId: number): Promise<void> => {
    try {
        // L'URL per l'azione custom è /education/pathways/unassign-student/{assignment_pk}/
        await apiClient.delete(`/education/pathways/unassign-student/${assignmentId}/`);
    } catch (error) {
        console.error(`Errore durante la disassegnazione del percorso (Assignment ID: ${assignmentId}):`, error);
        // Potresti voler gestire errori specifici (es. 403, 404)
        throw error;
    }
};