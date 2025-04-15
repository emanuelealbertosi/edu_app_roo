import apiClient from './config';
import type { AxiosResponse } from 'axios';

// Interfaccia per rappresentare i dati di uno studente (basata su StudentSerializer)
// Usata sia per le risposte API che per il tipo nello store/componenti
export interface Student {
  id: number;
  first_name: string;
  last_name: string;
  student_code: string;
  teacher: number; // ID del docente associato
  teacher_username: string;
  group_id: number | null; // ID del gruppo (può essere null)
  group_name: string | null; // Nome del gruppo (può essere null)
  full_name: string; // Proprietà calcolata dal backend
  is_active: boolean;
  created_at: string;
  // Aggiungere altri campi se necessario (es. wallet_balance se restituito qui)
}

// Interfaccia per il payload dell'aggiornamento del PIN
interface UpdatePinPayload {
  new_pin: string;
  current_pin?: string; // Potrebbe essere richiesto per verifica, dipende dall'API
}

/**
 * Aggiorna il PIN dello studente autenticato.
 * Richiede autenticazione studente.
 * @param payload Oggetto contenente il nuovo PIN (e opzionalmente quello attuale).
 */
export const updateStudentPin = async (payload: UpdatePinPayload): Promise<void> => {
  try {
    // Assumiamo un endpoint dedicato per la modifica del PIN, es. /student/profile/set-pin/
    // Se non esiste, questa chiamata fallirà e dovrà essere adattata all'API reale.
    await apiClient.post('/student/profile/set-pin/', payload);
  } catch (error) {
    console.error('Errore durante l\'aggiornamento del PIN:', error);
    throw error;
  }
};

// Potremmo aggiungere altre funzioni API specifiche per lo studente qui,
// ad esempio per recuperare il profilo completo o altre informazioni.