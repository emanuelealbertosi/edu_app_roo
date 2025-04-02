import apiClient from './config'; // Importa l'istanza axios configurata
import type { AxiosResponse } from 'axios';

// Interfaccia per rappresentare i dati di uno studente (basata su StudentSerializer)
// Assicurati che corrisponda ai campi restituiti dal backend
export interface Student {
  id: number;
  user_id: number; // ID dell'oggetto User associato (se necessario)
  username: string; // Username dell'oggetto User associato
  first_name: string;
  last_name: string;
  student_code: string;
  // Aggiungi altri campi se presenti nel serializer e necessari nel frontend
  // email?: string; // Esempio
  // date_joined?: string; // Esempio
  teacher?: number; // ID del docente associato (potrebbe essere utile)
}

/**
 * Recupera l'elenco degli studenti associati al docente autenticato.
 * Richiede autenticazione (il token JWT viene aggiunto automaticamente da apiClient).
 */
export const fetchStudents = async (): Promise<Student[]> => {
  try {
    // Corretto: il percorso è relativo a baseURL ('/api')
    const response: AxiosResponse<Student[]> = await apiClient.get('/students/');
    return response.data;
  } catch (error) {
    console.error('Errore durante il recupero degli studenti:', error);
    // Potresti voler rilanciare l'errore o gestirlo in modo più specifico
    throw error;
  }
};

// Potresti aggiungere qui altre funzioni API relative agli studenti in futuro
// es. createStudent, updateStudent, deleteStudent