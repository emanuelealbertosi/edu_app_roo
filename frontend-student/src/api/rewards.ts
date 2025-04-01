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
  status: 'purchased' | 'delivered' | 'cancelled';
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
      const response = await apiClient.get('student/shop/');
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
      const response = await apiClient.post(`student/shop/purchase/${rewardId}/`);
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
      const response = await apiClient.get('student/purchases/');
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
      const response = await apiClient.get(`student/purchases/${purchaseId}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching purchase details for purchase ${purchaseId}:`, error);
      throw error;
    }
  }
};

export default RewardsService;