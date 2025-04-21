import apiClient from './apiClient';
// Importa i tipi necessari
import type { AttemptQuestion, SubmitAnswerPayload } from '../types/quiz';

// Tipo per la risposta base da start-attempt (solo ID e info essenziali)
interface StartAttemptResponse {
  id: number; // ID del QuizAttempt
  status: string;
  quiz: {
    id: number;
    title: string;
  };
  // Aggiungere altri campi se utili subito, ma NON le domande
}

/**
 * Inizia un nuovo tentativo per un quiz o recupera un tentativo esistente in corso.
 * Restituisce solo l'ID e le info base del tentativo.
 * @param quizId L'ID del Quiz per cui iniziare/recuperare il tentativo.
 * @returns Le informazioni base del tentativo (incluso l'ID).
 */
export const startOrFetchQuizAttempt = async (quizId: string | number): Promise<StartAttemptResponse> => {
  const apiUrl = `/education/quizzes/${quizId}/attempts/start-attempt/`;
  console.log(`[quizService] Attempting to start/fetch attempt. POST to: ${apiUrl}`);
  try {
    const response = await apiClient.post<StartAttemptResponse>(apiUrl);
    console.log(`[quizService] Received response from start-attempt for quiz ${quizId}:`, response.data);

    // Validazione minima: ci serve almeno l'ID del tentativo
    if (!response?.data?.id) {
       console.error('[quizService] Response data from start-attempt is missing attempt ID.');
       throw new Error('Risposta API non valida da start-attempt (ID mancante).');
    }

    console.log(`[quizService] Successfully started/fetched attempt ID: ${response.data.id} for quiz ID: ${quizId}`);
    return response.data; // Restituisce solo i dati base ricevuti
  } catch (error: any) {
    console.error(`[quizService] Error in startOrFetchQuizAttempt for quiz ID ${quizId}:`, {
      message: error.message,
      responseStatus: error.response?.status,
      responseData: error.response?.data,
      requestConfig: error.config,
      errorObject: error
    });
    throw error;
  }
};

/* COMMENTATO - Non usiamo più /details/ per le domande al momento
import type { QuizAttemptDetails } from '../types/quiz'; // Import necessario se si scommenta
export const fetchAttemptDetails = async (attemptId: string | number): Promise<QuizAttemptDetails> => {
  const apiUrl = `/education/attempts/${attemptId}/details/`;
  console.log(`[quizService] Fetching attempt details. GET from: ${apiUrl}`);
  try {
    const response = await apiClient.get<QuizAttemptDetails>(apiUrl);
    console.log(`[quizService] Received attempt details for attempt ID ${attemptId}:`, response.data);

     // Validazione: ci serve almeno l'ID del tentativo
     if (!response?.data?.id) {
        console.error('[quizService] Response data from attempt details is missing attempt ID.');
        throw new Error('Risposta API non valida da attempt details (ID mancante).');
     }

    return response.data;
  } catch (error: any) {
     console.error(`[quizService] Error fetching attempt details for attempt ID ${attemptId}:`, {
        message: error.message,
        responseStatus: error.response?.status,
        responseData: error.response?.data,
        requestConfig: error.config,
        errorObject: error
      });
      throw error;
   }
};
*/

/**
 * Recupera la domanda corrente per un tentativo di quiz specifico.
 * @param attemptId L'ID del QuizAttempt.
 * @returns La domanda corrente del tentativo.
 */
export const fetchCurrentQuestion = async (attemptId: string | number): Promise<AttemptQuestion> => {
  // Endpoint basato sul vecchio frontend
  const apiUrl = `/education/attempts/${attemptId}/current-question/`;
  console.log(`[quizService] Fetching current question. GET from: ${apiUrl}`);
  try {
    const response = await apiClient.get<AttemptQuestion>(apiUrl);
    console.log(`[quizService] Received current question for attempt ID ${attemptId}:`, response.data);

    // Validazione minima: ci aspettiamo un oggetto con almeno un ID domanda
    if (!response?.data?.id) {
       console.error('[quizService] Response data from current question is missing question ID.');
       throw new Error('Risposta API non valida da current-question (ID domanda mancante).');
    }

    return response.data;
  } catch (error: any) {
     console.error(`[quizService] Error fetching current question for attempt ID ${attemptId}:`, {
       message: error.message,
       responseStatus: error.response?.status,
       responseData: error.response?.data,
       requestConfig: error.config,
       errorObject: error
     });
     throw error;
  }
};

/**
 * Invia la risposta dello studente per una specifica domanda di un tentativo.
 * @param attemptId L'ID del QuizAttempt.
 * @param payload I dati della risposta (question_id, selected_option_id, ecc.).
 * @returns Un oggetto che indica se la risposta è corretta (se valutabile subito) o altri dati.
 */
export const submitAnswer = async (
  attemptId: string | number,
  payload: SubmitAnswerPayload // Usa il tipo definito in types/quiz.ts
): Promise<{ is_correct?: boolean | null; message?: string; next_question_id?: number | null }> => { // Tipo di ritorno più flessibile
  // Endpoint basato sul vecchio frontend
  const apiUrl = `/education/attempts/${attemptId}/submit-answer/`;
  console.log(`[quizService] Submitting answer. POST to: ${apiUrl}`, payload);
  try {
    // Il payload viene inviato direttamente come corpo della richiesta POST
    const response = await apiClient.post(apiUrl, payload);
    console.log(`[quizService] Received response from submit-answer for attempt ID ${attemptId}:`, response.data);
    // Restituisce la risposta del backend (potrebbe contenere info sulla correttezza, punteggio, prossima domanda, ecc.)
    return response.data;
  } catch (error: any) {
     console.error(`[quizService] Error submitting answer for attempt ID ${attemptId}:`, {
       message: error.message,
       responseStatus: error.response?.status,
       responseData: error.response?.data,
       requestConfig: error.config,
       errorObject: error,
       payloadSent: payload // Logga anche il payload inviato per debug
     });
     throw error;
  }
};


// TODO: Aggiungere funzione per completare un tentativo (completeAttempt)