import apiClient from './config';

// --- Interfacce Ricompense ---

export interface Reward {
  id: number;
  name: string;
  description: string;
  type: 'digital' | 'real_world_tracked'; // Aggiornato per matchare backend
  cost_points: number;
  metadata: {
    image_url?: string;
    link?: string;
    [key: string]: any;
  };
  is_active: boolean;
}

export interface RewardPurchase {
  id: number;
  reward: Reward; // Dettagli ricompensa nidificati
  points_spent: number;
  purchased_at: string;
  status: 'PURCHASED' | 'DELIVERED' | 'CANCELLED'; 
  status_display?: string; // Aggiunto opzionale display
  delivered_at: string | null;
  delivery_notes: string | null;
  delivered_by_username?: string | null; // Aggiunto opzionale
}

// --- Interfacce Badge ---

export interface Badge {
  id: number;
  name: string;
  description: string;
  // slug: string; // Rimosso campo slug, non presente nel modello backend
  image_url: string | null;
  trigger_type: string; 
  trigger_type_display?: string; // Reso opzionale
  trigger_condition: { [key: string]: any };
  is_active: boolean;
  created_at: string;
}

export interface EarnedBadge {
  id: number;
  student: number; // ID studente
  badge: Badge; // Dettagli badge nidificati
  earned_at: string;
}

/**
 * Servizio per interagire con le ricompense e i badge
 */
const RewardsService = {
  /**
   * Ottiene tutte le ricompense disponibili per lo studente
   */
  async getAvailableRewards(): Promise<Reward[]> {
    try {
      const response = await apiClient.get('rewards/student/shop/');
      return response.data;
    } catch (error) {
      console.error('Error fetching available rewards:', error);
      throw error;
    }
  },

  /**
   * Acquista una ricompensa
   */
  async purchaseReward(rewardId: number): Promise<RewardPurchase> {
    try {
      const response = await apiClient.post(`rewards/student/shop/${rewardId}/purchase/`);
      return response.data;
    } catch (error) {
      console.error(`Error purchasing reward ${rewardId}:`, error);
      throw error;
    }
  },

  /**
   * Ottiene lo storico degli acquisti dello studente
   */
  async getPurchaseHistory(): Promise<RewardPurchase[]> {
    try {
      const response = await apiClient.get('rewards/student/purchases/');
      return response.data;
    } catch (error) {
      console.error('Error fetching purchase history:', error);
      throw error;
    }
  },

  /**
   * Ottiene i dettagli di un acquisto specifico
   */
  async getPurchaseDetails(purchaseId: number): Promise<RewardPurchase> {
    try {
      const response = await apiClient.get(`rewards/student/purchases/${purchaseId}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching purchase details for purchase ${purchaseId}:`, error);
      throw error;
    }
  },

  // --- Funzioni API per Badge ---

  /**
   * Ottiene tutte le definizioni dei badge attivi
   */
  async getAllBadges(): Promise<Badge[]> {
    try {
      const response = await apiClient.get('rewards/badges/'); // Usa URL registrato
      return response.data;
    } catch (error) {
      console.error('Errore API nel recuperare le definizioni dei badge:', error);
      throw error;
    }
  },

  /**
   * Ottiene i badge guadagnati dallo studente autenticato
   */
  async getEarnedBadges(): Promise<EarnedBadge[]> {
    try {
      const response = await apiClient.get('rewards/student/earned-badges/'); // Usa URL registrato
      return response.data;
    } catch (error) {
      console.error('Errore API nel recuperare i badge guadagnati:', error);
      throw error;
    }
  },
};

export default RewardsService;