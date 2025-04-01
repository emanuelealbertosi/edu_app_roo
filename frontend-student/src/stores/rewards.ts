import { defineStore } from 'pinia';
import RewardsService from '@/api/rewards';
import axios, { AxiosError } from 'axios';
import type { Reward, RewardPurchase } from '@/api/rewards';

interface RewardsState {
  availableRewards: Reward[];
  purchaseHistory: RewardPurchase[];
  currentPurchase: RewardPurchase | null;
  loading: {
    rewards: boolean;
    purchases: boolean;
    purchase: boolean;
  };
  error: string | null;
  successMessage: string | null;
}

export const useRewardsStore = defineStore('rewards', {
  state: (): RewardsState => ({
    availableRewards: [],
    purchaseHistory: [],
    currentPurchase: null,
    loading: {
      rewards: false,
      purchases: false,
      purchase: false
    },
    error: null,
    successMessage: null
  }),
  
  getters: {
    // Ricompense digitali
    digitalRewards(state): Reward[] {
      return state.availableRewards.filter(reward => reward.type === 'digital');
    },
    
    // Ricompense fisiche
    realWorldRewards(state): Reward[] {
      return state.availableRewards.filter(reward => reward.type === 'real_world_tracked');
    },
    
    // Acquisti in attesa di consegna
    pendingDeliveries(state): RewardPurchase[] {
      return state.purchaseHistory.filter(purchase => 
        purchase.status === 'purchased' && 
        purchase.reward.type === 'real_world_tracked'
      );
    },
    
    // Acquisti già consegnati
    deliveredPurchases(state): RewardPurchase[] {
      return state.purchaseHistory.filter(purchase => 
        purchase.status === 'delivered'
      );
    }
  },
  
  actions: {
    /**
     * Recupera le ricompense disponibili
     */
    async fetchAvailableRewards() {
      this.loading.rewards = true;
      this.error = null;
      
      try {
        this.availableRewards = await RewardsService.getAvailableRewards();
      } catch (error) {
        console.error('Error fetching available rewards:', error);
        this.error = 'Errore nel caricamento delle ricompense disponibili';
      } finally {
        this.loading.rewards = false;
      }
    },
    
    /**
     * Recupera lo storico degli acquisti
     */
    async fetchPurchaseHistory() {
      this.loading.purchases = true;
      this.error = null;
      
      try {
        this.purchaseHistory = await RewardsService.getPurchaseHistory();
      } catch (error) {
        console.error('Error fetching purchase history:', error);
        this.error = 'Errore nel caricamento dello storico acquisti';
      } finally {
        this.loading.purchases = false;
      }
    },
    
    /**
     * Recupera i dettagli di un acquisto specifico
     */
    async fetchPurchaseDetails(purchaseId: number) {
      this.loading.purchase = true;
      this.error = null;
      
      try {
        this.currentPurchase = await RewardsService.getPurchaseDetails(purchaseId);
      } catch (error) {
        console.error(`Error fetching purchase details for purchase ${purchaseId}:`, error);
        this.error = 'Errore nel caricamento dei dettagli dell\'acquisto';
      } finally {
        this.loading.purchase = false;
      }
    },
    
    /**
     * Acquista una ricompensa
     */
    async purchaseReward(rewardId: number) {
      this.loading.purchase = true;
      this.error = null;
      this.successMessage = null;
      
      try {
        const purchase = await RewardsService.purchaseReward(rewardId);
        this.purchaseHistory.unshift(purchase); // Aggiungiamo in cima allo storico
        this.successMessage = 'Ricompensa acquistata con successo!';
        return purchase;
      } catch (error) {
        console.error(`Error purchasing reward ${rewardId}:`, error);
        
        if (axios.isAxiosError(error) && error.response && error.response.status === 400) {
          // Errore specifico, ad esempio punti insufficienti
          this.error = error.response.data.detail || 'Impossibile acquistare la ricompensa.';
        } else {
          this.error = 'Errore nell\'acquisto della ricompensa.';
        }
        
        throw error;
      } finally {
        this.loading.purchase = false;
      }
    }
  }
});