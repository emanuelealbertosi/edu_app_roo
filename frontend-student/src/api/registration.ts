import apiClient from './config'; // Importa l'istanza configurata di axios da config.ts

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

// --- Registrazione specifica con Token di Gruppo ---

export interface GroupTokenRegistrationPayload {
  token: string; // Token specifico del gruppo
  first_name: string;
  last_name: string;
  pin: string;
  // Campi GDPR aggiunti (basati sull'errore del backend e sul payload del FE)
  date_of_birth: string; // Nome atteso dal backend
  accept_privacy_policy: boolean; // Nome atteso dal backend
  accept_terms_of_service: boolean; // Nome atteso dal backend
  parent_email?: string; // Opzionale, aggiunto solo se necessario
}

export interface GroupRegistrationResponse {
  student: StudentRegistrationResponse; // Dati studente creato
  access: string; // Access Token JWT
  refresh: string; // Refresh Token JWT
}

/**
 * Effettua una chiamata API per registrare un nuovo studente utilizzando un token.
 * @param {StudentRegistrationPayload} payload - I dati dello studente e il token.
 * @returns {Promise<StudentRegistrationResponse>} Una Promise che risolve con i dati dello studente registrato.
 */
export const registerStudentWithToken = async (payload: StudentRegistrationPayload): Promise<StudentRegistrationResponse> => {
  try {
    // Effettua una richiesta POST all'endpoint pubblico di registrazione
    // Assicurati che l'URL base in config.ts sia corretto
    const response = await apiClient.post<StudentRegistrationResponse>('/register/student/', payload);
    return response.data;
  } catch (error: any) {
    console.error('Errore durante la registrazione dello studente con token:', error);
    // Rilancia l'errore per permettere alla view di gestirlo
    throw error;
  }
};

/**
 * Effettua una chiamata API per registrare un nuovo studente utilizzando un TOKEN DI GRUPPO.
 * @param {GroupTokenRegistrationPayload} payload - I dati dello studente e il token di gruppo.
 * @returns {Promise<GroupRegistrationResponse>} Una Promise che risolve con i dati dello studente registrato e i token di autenticazione.
 */
export const registerStudentWithGroupToken = async (payload: GroupTokenRegistrationPayload): Promise<GroupRegistrationResponse> => {
  try {
    // Chiama l'endpoint specifico per la registrazione con token di gruppo
    const response = await apiClient.post<GroupRegistrationResponse>('/auth/register-by-token/', payload);
    return response.data;
  } catch (error: any) {
    console.error('Errore durante la registrazione dello studente con token di gruppo:', error);
    throw error;
  }
};