import apiClient from './config';
import axios from 'axios'; // Import axios per type checking
import type { AxiosResponse } from 'axios';

// Interfaccia per i dati di una Ricompensa (basata su RewardSerializer)
export interface Reward {
    id: number;
    teacher: number;
    teacher_username: string;
    template: number | null; // ID del template sorgente, se esiste
    name: string;
    description: string | null;
    type: string; // Es: 'VIRTUAL_ITEM', 'DISCOUNT_CODE'
    type_display: string;
    cost_points: number;
    availability_type: string; // Es: 'ALL', 'SPECIFIC'
    availability_type_display: string;
    metadata: Record<string, any> | null;
    is_active: boolean;
    created_at: string; // Formato ISO 8601
    // available_students_info: any[]; // Potremmo tipizzarlo meglio se necessario
}

// Interfaccia per i dati inviati durante la creazione/aggiornamento di una Ricompensa
// Esclude campi read-only e gestione studenti specifici per ora
export interface RewardPayload {
    template?: number | null; // Opzionale, se si crea da template
    name: string;
    description?: string | null;
    type: string; // Richiesto alla creazione
    cost_points: number;
    availability_type: string; // Es: 'ALL_STUDENTS' o 'SPECIFIC_STUDENTS'
    metadata?: Record<string, any> | null;
    is_active?: boolean;
    // specific_student_ids?: number[]; // Da aggiungere in futuro
}

/**
 * Recupera l'elenco delle ricompense create dal docente autenticato.
 */
export const fetchRewards = async (): Promise<Reward[]> => {
    try {
        // L'endpoint corretto è /rewards/rewards/ relativo a baseURL ('/api')
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
        if (axios.isAxiosError(error) && error.response?.status === 409) { // Type guard per AxiosError
             console.warn(`Impossibile eliminare la ricompensa ${rewardId} perché è stata acquistata.`);
             // Rilancia un errore specifico o gestisci diversamente
             throw new Error(`Impossibile eliminare la ricompensa ${rewardId} perché è stata acquistata.`); // Messaggio più user-friendly
        }
        throw error;
    }
};

// Potrebbero servire API per i RewardTemplate se si vuole permettere la selezione/creazione da template