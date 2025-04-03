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

// Potresti aggiungere qui altre funzioni API relative ai quiz in futuro
// es. gestione domande, assegnazione studenti, etc.
// es. gestione domande, assegnazione studenti, etc.