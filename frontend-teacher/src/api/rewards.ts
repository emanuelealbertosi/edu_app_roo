import apiClient from './config';
import type { AxiosResponse } from 'axios';
// Importa Student se necessario per available_students_info
// import type { Student } from './students';

// Interfaccia per i dati di una Ricompensa (basata su RewardSerializer)
export interface Reward {
    id: number;
    teacher: number;
    teacher_username: string;
    template: number | null;
    name: string;
    description: string | null;
    type: string; // 'DIGITAL' | 'REAL_WORLD'
    type_display?: string; // Opzionale, fornito dal serializer
    cost_points: number;
    availability_type: string; // 'ALL' | 'SPECIFIC'
    availability_type_display?: string; // Opzionale, fornito dal serializer
    metadata: Record<string, any> | null;
    is_active: boolean;
    created_at: string;
    available_to_specific_students?: number[]; // Array di ID studente se availability_type è 'SPECIFIC'
    available_to_specific_groups?: number[];   // NUOVO: Array di ID gruppo se availability_type è 'SPECIFIC'
    // available_students_info?: Student[]; // Se si sceglie di mostrarli
}

// Interfaccia per i dati inviati durante la creazione/aggiornamento di una Ricompensa
export interface RewardPayload {
    template?: number | null;
    name: string;
    description?: string | null;
    type: string; // 'DIGITAL' | 'REAL_WORLD'
    cost_points: number;
    availability_type: string; // 'ALL' | 'SPECIFIC'
    is_active?: boolean;
    metadata?: Record<string, any> | null;
    specific_student_ids?: number[]; // Array di ID studente se availability_type è 'SPECIFIC'
}

// Payload per rendere disponibile una ricompensa a uno studente o gruppo
export interface MakeRewardAvailablePayload {
   student_id?: number; // ID studente (opzionale) - Corretto da 'student'
   group_id?: number;   // ID gruppo (opzionale) - Corretto da 'group'
   // Assicurarsi che almeno uno dei due sia fornito
}

// Payload per revocare la disponibilità di una ricompensa da uno studente o gruppo
export interface RevokeRewardAvailabilityPayload {
   student_id?: number; // ID studente (opzionale) - Coerente con Make...
   group_id?: number;   // ID gruppo (opzionale) - Coerente con Make...
   // Assicurarsi che almeno uno dei due sia fornito
}

// Risposta generica per le operazioni di disponibilità (potrebbe essere vuota o contenere dettagli)
export interface RewardAvailabilityResponse {
   detail?: string;
   // Altri campi se restituiti dall'API
}

// Interfaccia per i dettagli di un acquisto per la vista consegne
export interface RewardPurchaseDetails {
  id: number;
  student: number;
  student_info: { // Assumendo che StudentSerializer sia usato nel backend
      id: number;
      full_name: string; // Assicurati che questo campo sia nel StudentSerializer
      student_code: string;
      // Aggiungere altri campi se necessari
  };
  reward: number;
  reward_info: { // Assumendo che RewardSerializer sia usato nel backend
      id: number;
      name: string;
      // Aggiungere altri campi se necessari
  };
  points_spent: number;
  purchased_at: string;
  status: string; // 'PURCHASED', 'DELIVERED', 'CANCELLED'
  status_display?: string; // Opzionale
  delivered_by?: number | null;
  delivered_by_username?: string | null;
  delivered_at?: string | null;
  delivery_notes?: string | null;
}


/**
 * Recupera l'elenco delle ricompense create dal docente autenticato.
 */
export const fetchRewards = async (): Promise<Reward[]> => {
    try {
        const response: AxiosResponse<Reward[]> = await apiClient.get('/rewards/rewards/');
        return response.data;
    } catch (error) {
        console.error('Errore durante il recupero delle ricompense:', error);
        throw error;
    }
};

/**
 * Recupera i dettagli di una singola ricompensa.
 */
export const fetchRewardDetails = async (rewardId: number): Promise<Reward> => {
    try {
        const response: AxiosResponse<Reward> = await apiClient.get(`/rewards/rewards/${rewardId}/`);
        return response.data;
    } catch (error) {
        console.error(`Errore durante il recupero dei dettagli della ricompensa ${rewardId}:`, error);
        throw error;
    }
};

/**
 * Crea una nuova ricompensa.
 */
export const createReward = async (payload: RewardPayload): Promise<Reward> => {
    try {
        const response: AxiosResponse<Reward> = await apiClient.post('/rewards/rewards/', payload);
        return response.data;
    } catch (error) {
        console.error('Errore durante la creazione della ricompensa:', error);
        throw error;
    }
};

/**
 * Aggiorna una ricompensa esistente (usando PATCH).
 */
export const updateReward = async (rewardId: number, payload: Partial<RewardPayload>): Promise<Reward> => {
    try {
        const response: AxiosResponse<Reward> = await apiClient.patch(`/rewards/rewards/${rewardId}/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Errore durante l'aggiornamento della ricompensa ${rewardId}:`, error);
        throw error;
    }
};

/**
 * Elimina una ricompensa esistente.
 */
export const deleteRewardApi = async (rewardId: number): Promise<void> => {
    try {
        await apiClient.delete(`/rewards/rewards/${rewardId}/`);
    } catch (error: unknown) { // Specifica tipo unknown
        console.error(`Errore durante l'eliminazione della ricompensa ${rewardId}:`, error);
        // Gestire specificamente 409 Conflict se necessario
        // Importa axios per usare isAxiosError
        // import axios from 'axios';
        // if (axios.isAxiosError(error) && error.response?.status === 409) {
        //      console.warn(`Impossibile eliminare la ricompensa ${rewardId} perché è stata acquistata.`);
        //      throw new Error(`Impossibile eliminare la ricompensa ${rewardId} perché è stata acquistata.`);
        // }
        throw error;
    }
};

/**
* Rende una ricompensa disponibile per uno studente o un gruppo specifico.
* @param rewardId L'ID della ricompensa.
* @param payload Contiene l'ID dello studente o del gruppo.
*/
export const makeRewardAvailable = async (rewardId: number, payload: MakeRewardAvailablePayload): Promise<RewardAvailabilityResponse> => {
   if (!payload.student_id && !payload.group_id) { // Corretto: student -> student_id, group -> group_id
       throw new Error("È necessario specificare un ID studente o un ID gruppo.");
   }
   try {
       // Assumendo un'azione 'make-available' sul ViewSet Reward
       const response = await apiClient.post<RewardAvailabilityResponse>(`/rewards/rewards/${rewardId}/make-available/`, payload); // Corretto: make_available -> make-available
       return response.data;
   } catch (error) {
       const targetType = payload.student_id ? 'studente' : 'gruppo'; // Corretto: student -> student_id
       const targetId = payload.student_id ?? payload.group_id; // Corretto: student -> student_id, group -> group_id
       console.error(`Errore nel rendere disponibile la ricompensa ${rewardId} per ${targetType} ${targetId}:`, error);
       throw error;
   }
};

/**
* Revoca la disponibilità di una ricompensa per uno studente o un gruppo specifico.
* @param rewardId L'ID della ricompensa.
* @param payload Contiene l'ID dello studente o del gruppo.
*/
export const revokeRewardAvailability = async (rewardId: number, payload: RevokeRewardAvailabilityPayload): Promise<RewardAvailabilityResponse> => {
    if (!payload.student_id && !payload.group_id) { // Usa i nomi corretti
       throw new Error("È necessario specificare un ID studente o un ID gruppo.");
   }
   try {
       // Assumendo un'azione 'revoke_availability' sul ViewSet Reward
       // Usiamo POST anche per la revoca se l'azione è definita così nel backend,
       // altrimenti potrebbe essere DELETE o un altro metodo HTTP.
       const response = await apiClient.post<RewardAvailabilityResponse>(`/rewards/rewards/${rewardId}/revoke_availability/`, payload);
       return response.data;
   } catch (error) {
       const targetType = payload.student_id ? 'studente' : 'gruppo'; // Usa i nomi corretti
       const targetId = payload.student_id ?? payload.group_id; // Usa i nomi corretti
       console.error(`Errore nel revocare la disponibilità della ricompensa ${rewardId} per ${targetType} ${targetId}:`, error);
       throw error;
   }
};

/**
 * Recupera la lista delle ricompense in attesa di consegna per il docente loggato.
 */
export async function fetchPendingDeliveries(): Promise<RewardPurchaseDetails[]> {
    try {
        // L'URL corretto dovrebbe essere relativo alla baseURL ('/api')
        const response = await apiClient.get<RewardPurchaseDetails[]>('/rewards/teacher/delivery/pending-delivery/');
        return response.data;
    } catch (error) {
        console.error('Error fetching pending deliveries:', error);
        throw error; // Rilancia per gestione nell'UI
    }
}

/**
 * Segna una ricompensa come consegnata.
 */
export async function markRewardAsDelivered(purchaseId: number, deliveryNotes: string | null): Promise<RewardPurchaseDetails> {
    try {
        const payload: { delivery_notes?: string } = {};
        if (deliveryNotes) {
            payload.delivery_notes = deliveryNotes;
        }
        // L'URL corretto dovrebbe essere relativo alla baseURL ('/api')
        const response = await apiClient.post<RewardPurchaseDetails>(`/rewards/teacher/delivery/${purchaseId}/mark-delivered/`, payload);
        return response.data;
    } catch (error) {
        console.error(`Error marking reward purchase ${purchaseId} as delivered:`, error);
        throw error; // Rilancia per gestione nell'UI
    }
}