import apiClient from './config'; // Importa l'istanza axios configurata
import type { AxiosResponse } from 'axios';

// Interfaccia per rappresentare i dati di un Quiz (basata su QuizSerializer)
export interface Quiz {
  id: number;
  teacher: number; // ID del docente
  teacher_username: string;
  source_template: number | null; // ID del template sorgente, se esiste
  title: string;
  description: string | null;
  metadata: Record<string, any> | null; // Oggetto JSON generico
  created_at: string; // Formato ISO 8601
  available_from: string | null; // Formato ISO 8601
  available_until: string | null; // Formato ISO 8601
  // Aggiungere qui altri campi se necessari in futuro (es. questions_count se aggiunto al serializer)
}
// Interfaccia per rappresentare i dati di un Quiz Template
// (basata su QuizTemplateSerializer, ora include teacher)
export interface QuizTemplate {
  id: number;
  admin: number | null; // Può essere null
  admin_username?: string; // Opzionale
  teacher: number | null; // Può essere null
  teacher_username?: string; // Opzionale (da aggiungere al serializer backend se necessario)
  title: string;
  description: string | null;
  metadata: Record<string, any> | null;
  created_at: string; // Formato ISO 8601
}

// Interfaccia per i dati inviati durante la creazione/aggiornamento di un Quiz Template
// (Simile a QuizPayload ma senza campi specifici dell'istanza come available_from/until)
export interface QuizTemplatePayload {
    title: string;
    description?: string | null;
    metadata?: Record<string, any> | null;
    // admin/teacher vengono impostati automaticamente dal backend
}


// Interfaccia per i dati inviati durante la creazione/aggiornamento
// Esclude campi read-only come id, teacher, teacher_username, created_at
export interface QuizPayload {
    title: string;
    description?: string | null;
    source_template?: number | null;
    metadata?: Record<string, any> | null;
    available_from?: string | null; // Formato ISO 8601
    available_until?: string | null; // Formato ISO 8601
}

/**
 * Recupera l'elenco dei quiz associati al docente autenticato.
 * Richiede autenticazione (il token JWT viene aggiunto automaticamente da apiClient).
 */
export const fetchQuizzes = async (): Promise<Quiz[]> => {
  try {
    // L'URL corretto è /education/quizzes/ relativo a baseURL ('/api')
    const response: AxiosResponse<Quiz[]> = await apiClient.get('/education/quizzes/');
    return response.data;
  } catch (error) {
    console.error('Errore durante il recupero dei quiz:', error);
    // Potresti voler rilanciare l'errore o gestirlo in modo più specifico
    throw error;
  }
};
/**
 * Recupera l'elenco dei template di quiz creati dall'ADMIN.
 * Usato principalmente per popolare scelte, non per la gestione diretta del docente.
 */
export const fetchAdminQuizTemplates = async (): Promise<QuizTemplate[]> => {
  try {
    // Endpoint per i template gestiti dall'admin
    const response: AxiosResponse<QuizTemplate[]> = await apiClient.get('/education/quiz-templates/');
    return response.data;
  } catch (error) {
    console.error('Errore durante il recupero dei template di quiz (Admin):', error);
    throw error;
  }
};

// --- API per Teacher Quiz Templates ---

/**
 * Recupera l'elenco dei template di quiz creati dal DOCENTE autenticato.
 */
export const fetchTeacherQuizTemplates = async (): Promise<QuizTemplate[]> => {
  try {
    // Nuovo endpoint per i template del docente
    const response: AxiosResponse<QuizTemplate[]> = await apiClient.get('/education/teacher/quiz-templates/');
    return response.data;
  } catch (error) {
    console.error('Errore durante il recupero dei template di quiz (Docente):', error);
    throw error;
  }
};

/**
 * Recupera i dettagli di un singolo template di quiz del docente.
 */
export const fetchTeacherQuizTemplateDetails = async (templateId: number): Promise<QuizTemplate> => {
    try {
        const response: AxiosResponse<QuizTemplate> = await apiClient.get(`/education/teacher/quiz-templates/${templateId}/`);
        return response.data;
    } catch (error) {
        console.error(`Errore durante il recupero dei dettagli del template quiz ${templateId} (Docente):`, error);
        throw error;
    }
};

/**
 * Crea un nuovo template di quiz per il docente autenticato.
 */
export const createTeacherQuizTemplate = async (payload: QuizTemplatePayload): Promise<QuizTemplate> => {
    try {
        const response: AxiosResponse<QuizTemplate> = await apiClient.post('/education/teacher/quiz-templates/', payload);
        return response.data;
    } catch (error) {
        console.error('Errore durante la creazione del template quiz (Docente):', error);
        throw error;
    }
};

/**
 * Aggiorna un template di quiz esistente del docente (usando PATCH).
 */
export const updateTeacherQuizTemplate = async (templateId: number, payload: Partial<QuizTemplatePayload>): Promise<QuizTemplate> => {
    try {
        const response: AxiosResponse<QuizTemplate> = await apiClient.patch(`/education/teacher/quiz-templates/${templateId}/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'aggiornamento del template quiz ${templateId} (Docente):`, error);
        throw error;
    }
};

/**
 * Elimina un template di quiz esistente del docente.
 */
export const deleteTeacherQuizTemplate = async (templateId: number): Promise<void> => {
    try {
        await apiClient.delete(`/education/teacher/quiz-templates/${templateId}/`);
    } catch (error) {
        console.error(`Errore durante l'eliminazione del template quiz ${templateId} (Docente):`, error);
        throw error;
    }
};

/**
 * Carica un file (PDF, DOCX, MD) per creare automaticamente un QuizTemplate.
 * @param file Il file da caricare.
 * @param title Il titolo del nuovo template.
 * @returns I dati del template creato.
 */
export const uploadQuizTemplateFromFile = async (file: File, title: string): Promise<QuizTemplate> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    try {
        // L'URL per l'azione custom è /education/teacher/quiz-templates/upload/
        const response = await apiClient.post<QuizTemplate>('/education/teacher/quiz-templates/upload/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        console.error('Errore API durante l\'upload del template quiz:', error);
        throw error; // Rilancia l'errore per gestirlo nel componente
    }
 };


/**
 * Recupera i dettagli di un singolo quiz.
 */
export const fetchQuizDetails = async (quizId: number): Promise<Quiz> => {
    try {
        const response: AxiosResponse<Quiz> = await apiClient.get(`/education/quizzes/${quizId}/`);
        return response.data;
    } catch (error) {
        console.error(`Errore durante il recupero dei dettagli del quiz ${quizId}:`, error);
        throw error;
    }
};

/**
 * Crea un nuovo quiz.
 */
export const createQuiz = async (payload: QuizPayload): Promise<Quiz> => {
    try {
        const response: AxiosResponse<Quiz> = await apiClient.post('/education/quizzes/', payload);
        return response.data;
    } catch (error) {
        console.error('Errore durante la creazione del quiz:', error);
        throw error;
    }
};

/**
 * Aggiorna un quiz esistente (usando PATCH per aggiornamenti parziali).
 */
export const updateQuiz = async (quizId: number, payload: Partial<QuizPayload>): Promise<Quiz> => {
    try {
        const response: AxiosResponse<Quiz> = await apiClient.patch(`/education/quizzes/${quizId}/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'aggiornamento del quiz ${quizId}:`, error);
        throw error;
    }
};

/**
 * Elimina un quiz esistente.
 */
export const deleteQuizApi = async (quizId: number): Promise<void> => {
    try {
        await apiClient.delete(`/education/quizzes/${quizId}/`);
    } catch (error) {
        console.error(`Errore durante l'eliminazione del quiz ${quizId}:`, error);
        throw error;
    }
};
/**
 * Carica un file (PDF, DOCX, MD) per creare automaticamente un quiz.
 * @param file Il file da caricare.
 * @param title Il titolo del nuovo quiz.
 * @returns I dati del quiz creato.
 */
export const uploadQuiz = async (file: File, title: string): Promise<Quiz> => {
    // Usiamo FormData per inviare il file
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    try {
        // L'URL per l'azione custom è /education/quizzes/upload/
        const response: AxiosResponse<Quiz> = await apiClient.post('/education/quizzes/upload/', formData, {
            headers: {
                // Importante per l'upload di file con axios
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        console.error('Errore durante l\'upload del quiz:', error);
        // Potresti voler gestire errori specifici restituiti dal backend (es. 400 Bad Request)
        throw error;
    }
};
// Interfaccia per i dati di assegnazione Quiz
export interface AssignQuizPayload {
    student: number; // Modificato da student_id a student
    quiz_id?: number | null; // ID del quiz esistente
    quiz_template_id?: number | null; // ID del template da cui creare
    due_date?: string | null; // Data di scadenza opzionale (formato ISO 8601)
}

// Interfaccia per la risposta dell'assegnazione (basata sul serializer)
export interface QuizAssignmentResponse {
    status: string; // Messaggio di stato (es. "Quiz assegnato con successo.")
    assignment: { // Dettagli dell'assegnazione creata/esistente
        id: number;
        student: number;
        student_username: string;
        quiz: number;
        quiz_title: string;
        assigned_at: string;
        due_date: string | null;
        // quiz_template_id non viene restituito dal backend
    };
}


/**
 * Assegna un quiz (esistente o da template) a uno studente.
 */
export const assignQuizToStudent = async (payload: AssignQuizPayload): Promise<QuizAssignmentResponse> => {
    try {
        // L'URL per l'azione custom è /education/quizzes/assign-student/
        const response: AxiosResponse<QuizAssignmentResponse> = await apiClient.post('/education/quizzes/assign-student/', payload);
        return response.data;
    } catch (error) {
        console.error('Errore durante l\'assegnazione del quiz:', error);
        // Potresti voler gestire errori specifici (es. 400, 403, 404)
        throw error;
    }
};
// es. gestione domande, assegnazione studenti, etc.