import apiClient from './apiClient'; // Importa l'istanza configurata di axios

// Definisce la struttura dei dati da inviare per la registrazione
export interface StudentRegistrationPayload {
  token: string; // UUID del token dalla URL
  first_name: string;
  last_name: string;
  pin: string; // PIN in chiaro (il backend lo hasherà)
}

// Definisce la struttura della risposta attesa dall'API dopo la registrazione
// (corrisponde a StudentSerializer nel backend)
export interface StudentRegistrationResponse {
  id: number;
  teacher: number;
  teacher_username: string;
  first_name: string;
  last_name: string;
  student_code: string;
  is_active: boolean;
  created_at: string; // ISO date string
  full_name: string;
}

/**
 * Effettua una chiamata API per registrare un nuovo studente utilizzando un token.
 * @param {StudentRegistrationPayload} payload - I dati dello studente e il token.
 * @returns {Promise<StudentRegistrationResponse>} Una Promise che risolve con i dati dello studente registrato.
 */
export const registerStudentWithToken = async (payload: StudentRegistrationPayload): Promise<StudentRegistrationResponse> => {
  try {
    // Effettua una richiesta POST all'endpoint pubblico di registrazione
    const response = await apiClient.post<StudentRegistrationResponse>('/register/student/', payload);
    return response.data;
  } catch (error: any) {
    console.error('Errore durante la registrazione dello studente con token:', error);
    // Rilancia l'errore per permettere alla view di gestirlo (es. mostrare un messaggio all'utente)
    // Potrebbe contenere messaggi specifici dal backend (es. token non valido, PIN troppo corto)
    throw error;
  }
};