import apiClient from './apiClient'; // Importa l'istanza configurata di axios

// Definisce la struttura della risposta attesa dall'API quando si crea un token
export interface RegistrationTokenResponse {
  token: string; // UUID del token
  teacher: number; // ID del docente
  teacher_username: string;
  created_at: string; // ISO date string
  expires_at: string; // ISO date string
  used_at: string | null; // ISO date string or null
  student: number | null; // ID dello studente registrato or null
  is_valid: boolean;
  registration_link: string; // URL completo per la registrazione
}

/**
 * Effettua una chiamata API per creare un nuovo token di registrazione per il docente autenticato.
 * @returns {Promise<RegistrationTokenResponse>} Una Promise che risolve con i dati del token creato.
 */
export const createRegistrationToken = async (): Promise<RegistrationTokenResponse> => {
  try {
    // Effettua una richiesta POST all'endpoint corretto. Non servono dati nel body.
    const response = await apiClient.post<RegistrationTokenResponse>('/teacher/registration-tokens/');
    return response.data;
  } catch (error) {
    console.error('Errore durante la creazione del token di registrazione:', error);
    // Rilancia l'errore per permettere al chiamante di gestirlo (es. mostrare un messaggio all'utente)
    throw error;
  }
};

// Potremmo aggiungere qui altre funzioni API relative ai token se necessario,
// ad esempio per listare i token esistenti (anche se la view attuale non lo fa).
// export const fetchRegistrationTokens = async (): Promise<RegistrationTokenResponse[]> => {
//   try {
//     const response = await apiClient.get<RegistrationTokenResponse[]>('/teacher/registration-tokens/');
//     return response.data;
//   } catch (error) {
//     console.error('Errore durante il recupero dei token di registrazione:', error);
//     throw error;
//   }
// };