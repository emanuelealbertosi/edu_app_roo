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