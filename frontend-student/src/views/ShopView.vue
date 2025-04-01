<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useRewardsStore } from '@/stores/rewards';
import { useDashboardStore } from '@/stores/dashboard';
import type { Reward } from '@/api/rewards';

const authStore = useAuthStore();
const rewardsStore = useRewardsStore();
const dashboardStore = useDashboardStore();
const router = useRouter();

const isLoading = ref(true);
const activeTab = ref('all'); // 'all', 'digital', 'physical'
const successMessage = ref('');
const errorMessage = ref('');

// Punti disponibili dal wallet
const availablePoints = computed(() => dashboardStore.wallet?.current_points || 0);

// Filtra le ricompense in base alla tab attiva
const filteredRewards = computed(() => {
  if (activeTab.value === 'digital') {
    return rewardsStore.digitalRewards;
  } else if (activeTab.value === 'physical') {
    return rewardsStore.realWorldRewards;
  }
  return rewardsStore.availableRewards;
});

// Verifica se l'utente ha abbastanza punti per acquistare una ricompensa
const canAfford = (reward: Reward): boolean => {
  return (dashboardStore.wallet?.current_points || 0) >= reward.cost_points;
};

onMounted(async () => {
  // Verifichiamo che l'utente sia autenticato
  const isAuthenticated = await authStore.checkAuth();
  if (!isAuthenticated) {
    router.push('/login');
    return;
  }
  
  isLoading.value = true;
  
  try {
    // Carichiamo le ricompense disponibili e le informazioni del wallet
    // se non sono già state caricate
    const loadRewardsPromise = rewardsStore.fetchAvailableRewards();
    let loadWalletPromise;
    
    if (!dashboardStore.wallet) {
      loadWalletPromise = dashboardStore.fetchWallet();
    }
    
    await Promise.all([
      loadRewardsPromise, 
      loadWalletPromise
    ].filter(Boolean));
  } catch (error) {
    console.error('Errore nel caricamento dei dati dello shop:', error);
    errorMessage.value = 'Si è verificato un errore nel caricamento dello shop. Riprova più tardi.';
  } finally {
    isLoading.value = false;
  }
});

// Gestisce l'acquisto di una ricompensa
const purchaseReward = async (reward: Reward) => {
  if (!canAfford(reward)) {
    errorMessage.value = 'Non hai abbastanza punti per acquistare questa ricompensa.';
    successMessage.value = '';
    return;
  }
  
  try {
    isLoading.value = true;
    errorMessage.value = '';
    successMessage.value = '';
    
    // Acquista la ricompensa
    await rewardsStore.purchaseReward(reward.id);
    
    // Aggiorna il saldo del wallet
    await dashboardStore.fetchWallet();
    
    successMessage.value = `Hai acquistato con successo "${reward.name}" per ${reward.cost_points} punti!`;
    
    // Se è una ricompensa digitale, mostra eventuali informazioni aggiuntive
    if (reward.type === 'digital' && reward.metadata.link) {
      successMessage.value += ` Puoi accedere alla tua ricompensa qui: ${reward.metadata.link}`;
    }
  } catch (error) {
    console.error('Errore nell\'acquisto della ricompensa:', error);
    
    if (error.response && error.response.status === 400) {
      // Gestisci messaggi di errore specifici dal server
      errorMessage.value = error.response.data.detail || 'Impossibile completare l\'acquisto. Verifica il tuo saldo punti.';
    } else {
      errorMessage.value = 'Si è verificato un errore durante l\'acquisto. Riprova più tardi.';
    }
  } finally {
    isLoading.value = false;
  }
};

// Cambia la tab attiva
const setActiveTab = (tab: string) => {
  activeTab.value = tab;
};

// Torna alla dashboard
const goToDashboard = () => {
  router.push('/dashboard');
};

// Vai alla cronologia acquisti
const goToPurchaseHistory = () => {
  router.push('/purchases');
};
</script>

<template>
  <div class="shop-view">
    <header class="shop-header">
      <div class="header-content">
        <h1>Shop Ricompense</h1>
        <div class="header-actions">
          <button @click="goToDashboard" class="back-button">
            <span class="button-icon">🏠</span> Torna alla Dashboard
          </button>
          <button @click="goToPurchaseHistory" class="history-button">
            <span class="button-icon">📋</span> Cronologia Acquisti
          </button>
        </div>
      </div>
      
      <div class="points-display">
        <span class="points-label">Punti Disponibili:</span>
        <span class="points-value">{{ availablePoints }}</span>
      </div>
    </header>
    
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Caricamento in corso...</p>
    </div>
    
    <div v-else class="shop-content">
      <!-- Messaggi di successo o errore -->
      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>
      
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      
      <!-- Filtri per tipo di ricompensa -->
      <div class="reward-filters">
        <button 
          @click="setActiveTab('all')" 
          :class="['filter-button', { active: activeTab === 'all' }]"
        >
          Tutte
        </button>
        <button 
          @click="setActiveTab('digital')" 
          :class="['filter-button', { active: activeTab === 'digital' }]"
        >
          Digitali
        </button>
        <button 
          @click="setActiveTab('physical')" 
          :class="['filter-button', { active: activeTab === 'physical' }]"
        >
          Fisiche
        </button>
      </div>
      
      <!-- Lista ricompense -->
      <div v-if="filteredRewards.length === 0" class="empty-rewards">
        <p>Non ci sono ricompense disponibili in questa categoria al momento.</p>
      </div>
      
      <div v-else class="rewards-grid">
        <div 
          v-for="reward in filteredRewards" 
          :key="reward.id" 
          class="reward-card"
          :class="{ 'not-affordable': !canAfford(reward) }"
        >
          <div class="reward-header">
            <h3>{{ reward.name }}</h3>
            <span class="reward-type-badge" :class="`type-${reward.type}`">
              {{ reward.type === 'digital' ? 'Digitale' : 'Fisica' }}
            </span>
          </div>
          
          <div v-if="reward.metadata.image_url" class="reward-image">
            <img :src="reward.metadata.image_url" :alt="reward.name">
          </div>
          
          <p class="reward-description">{{ reward.description }}</p>
          
          <div class="reward-footer">
            <div class="reward-cost">
              <span class="cost-label">Costo:</span>
              <span class="cost-value">{{ reward.cost_points }} punti</span>
            </div>
            
            <button 
              @click="purchaseReward(reward)" 
              class="purchase-button"
              :disabled="!canAfford(reward) || isLoading"
            >
              {{ canAfford(reward) ? 'Acquista' : 'Punti insufficienti' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shop-view {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.shop-header {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.points-display {
  background-color: #4caf50;
  color: white;
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.points-label {
  font-size: 1.2rem;
  margin-right: 0.5rem;
}

.points-value {
  font-size: 1.5rem;
  font-weight: bold;
}

.back-button, .history-button {
  padding: 0.75rem 1.5rem;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.back-button {
  background-color: #2196f3; /* Blu */
}

.history-button {
  background-color: #9c27b0; /* Viola */
}

.button-icon {
  font-size: 1.2rem;
}

.reward-filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filter-button {
  padding: 0.5rem 1.5rem;
  background-color: #f5f5f5;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.filter-button.active {
  background-color: var(--vt-c-indigo);
  color: white;
}

.rewards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.reward-card {
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
}

.reward-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.reward-card.not-affordable {
  opacity: 0.7;
}

.reward-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.reward-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.reward-type-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.type-digital {
  background-color: #e3f2fd;
  color: #1976d2;
}

.type-real_world_tracked {
  background-color: #fff8e1;
  color: #ff8f00;
}

.reward-image {
  width: 100%;
  height: 180px;
  overflow: hidden;
}

.reward-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.reward-description {
  padding: 1rem;
  flex-grow: 1;
  color: #666;
}

.reward-footer {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  border-top: 1px solid #eee;
}

.reward-cost {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cost-label {
  color: #666;
}

.cost-value {
  font-weight: bold;
  color: #4caf50;
}

.purchase-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.purchase-button:hover:not(:disabled) {
  background-color: #388e3c;
}

.purchase-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.success-message {
  background-color: #e8f5e9;
  color: #388e3c;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
  border-left: 4px solid #4caf50;
}

.error-message {
  background-color: #ffebee;
  color: #d32f2f;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
  border-left: 4px solid #f44336;
}

.loading-container, .empty-rewards {
  padding: 3rem;
  text-align: center;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: var(--vt-c-indigo);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    flex-direction: column;
  }
  
  .reward-filters {
    flex-wrap: wrap;
  }
  
  .filter-button {
    flex: 1;
    min-width: 100px;
  }
}
</style>