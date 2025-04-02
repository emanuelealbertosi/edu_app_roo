import apiClient from './config';

// Interfacce per TypeScript
export interface Reward {
  id: number;
  name: string;
  description: string;
  type: 'digital' | 'real_world_tracked';
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
  reward: Reward;
  points_spent: number;
  purchased_at: string;
  status: 'PURCHASED' | 'DELIVERED' | 'CANCELLED'; // Aggiornato per usare i valori del backend
  delivered_at: string | null;
  delivery_notes: string | null;
}

/**
 * Servizio per interagire con le ricompense
 */
const RewardsService = {
  /**
   * Ottiene tutte le ricompense disponibili per lo studente
   */
  async getAvailableRewards(): Promise<Reward[]> {
    try {
      // Ripristinato 'student/' perché il router backend lo include
      // Aggiunto prefisso completo relativo a /api/
      // Corretto percorso completo relativo a /api/
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
      // Ripristinato 'student/' e corretto URL per l'azione 'purchase'
      // Aggiunto prefisso completo relativo a /api/
      // Corretto percorso completo relativo a /api/
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
      // Ripristinato 'student/' perché già nel baseURL
      // Aggiunto prefisso completo relativo a /api/
      // Corretto percorso completo relativo a /api/
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
      // Ripristinato 'student/' perché il router backend lo include
      // Aggiunto prefisso completo relativo a /api/
      // Corretto percorso completo relativo a /api/
      const response = await apiClient.get(`rewards/student/purchases/${purchaseId}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching purchase details for purchase ${purchaseId}:`, error);
      throw error;
    }
  }
};

export default RewardsService;