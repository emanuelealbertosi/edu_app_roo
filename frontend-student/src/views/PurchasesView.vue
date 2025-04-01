<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useRewardsStore } from '@/stores/rewards';
import type { RewardPurchase } from '@/api/rewards';

const authStore = useAuthStore();
const rewardsStore = useRewardsStore();
const router = useRouter();

const isLoading = ref(true);
const activeTab = ref('all'); // 'all', 'pending', 'delivered'

onMounted(async () => {
  // Verifichiamo che l'utente sia autenticato
  const isAuthenticated = await authStore.checkAuth();
  if (!isAuthenticated) {
    router.push('/login');
    return;
  }
  
  isLoading.value = true;
  
  try {
    // Carichiamo lo storico degli acquisti
    await rewardsStore.fetchPurchaseHistory();
  } catch (error) {
    console.error('Errore nel caricamento dello storico acquisti:', error);
  } finally {
    isLoading.value = false;
  }
});

// Filtra gli acquisti in base alla tab attiva
const filteredPurchases = computed(() => {
  if (activeTab.value === 'pending') {
    return rewardsStore.pendingDeliveries;
  } else if (activeTab.value === 'delivered') {
    return rewardsStore.deliveredPurchases;
  }
  return rewardsStore.purchaseHistory;
});

// Formatta la data in un formato più leggibile
const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Cambia la tab attiva
const setActiveTab = (tab: string) => {
  activeTab.value = tab;
};

// Torna allo shop
const goToShop = () => {
  router.push('/shop');
};

// Torna alla dashboard
const goToDashboard = () => {
  router.push('/dashboard');
};

// Ottiene la classe CSS per lo stato dell'acquisto
const getStatusClass = (status: string): string => {
  switch (status) {
    case 'purchased':
      return 'status-purchased';
    case 'delivered':
      return 'status-delivered';
    case 'cancelled':
      return 'status-cancelled';
    default:
      return '';
  }
};

// Ottiene l'etichetta leggibile per lo stato dell'acquisto
const getStatusLabel = (status: string): string => {
  switch (status) {
    case 'purchased':
      return 'Acquistato';
    case 'delivered':
      return 'Consegnato';
    case 'cancelled':
      return 'Annullato';
    default:
      return status;
  }
};
</script>

<template>
  <div class="purchases-view">
    <header class="purchases-header">
      <div class="header-content">
        <h1>Cronologia Acquisti</h1>
        <div class="header-actions">
          <button @click="goToShop" class="shop-button">
            <span class="button-icon">🛒</span> Torna allo Shop
          </button>
          <button @click="goToDashboard" class="dashboard-button">
            <span class="button-icon">🏠</span> Dashboard
          </button>
        </div>
      </div>
    </header>
    
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Caricamento in corso...</p>
    </div>
    
    <div v-else class="purchases-content">
      <!-- Filtri per stato dell'acquisto -->
      <div class="purchase-filters">
        <button 
          @click="setActiveTab('all')" 
          :class="['filter-button', { active: activeTab === 'all' }]"
        >
          Tutti
        </button>
        <button 
          @click="setActiveTab('pending')" 
          :class="['filter-button', { active: activeTab === 'pending' }]"
        >
          In attesa di consegna
        </button>
        <button 
          @click="setActiveTab('delivered')" 
          :class="['filter-button', { active: activeTab === 'delivered' }]"
        >
          Consegnati
        </button>
      </div>
      
      <!-- Lista acquisti -->
      <div v-if="filteredPurchases.length === 0" class="empty-purchases">
        <p>Non hai ancora effettuato acquisti in questa categoria.</p>
      </div>
      
      <div v-else class="purchases-list">
        <div 
          v-for="purchase in filteredPurchases" 
          :key="purchase.id" 
          class="purchase-card"
        >
          <div class="purchase-header">
            <h3>{{ purchase.reward.name }}</h3>
            <span :class="['purchase-status', getStatusClass(purchase.status)]">
              {{ getStatusLabel(purchase.status) }}
            </span>
          </div>
          
          <div class="purchase-details">
            <div class="reward-info">
              <p class="reward-description">{{ purchase.reward.description }}</p>
              <div class="reward-type">
                <span class="reward-type-badge" :class="`type-${purchase.reward.type}`">
                  {{ purchase.reward.type === 'digital' ? 'Digitale' : 'Fisica' }}
                </span>
              </div>
            </div>
            
            <div class="purchase-info">
              <div class="purchase-date">
                <span class="info-label">Data acquisto:</span>
                <span class="info-value">{{ formatDate(purchase.purchased_at) }}</span>
              </div>
              
              <div class="purchase-cost">
                <span class="info-label">Punti spesi:</span>
                <span class="info-value">{{ purchase.points_spent }}</span>
              </div>
              
              <div v-if="purchase.status === 'delivered'" class="delivery-info">
                <div class="delivery-date">
                  <span class="info-label">Data consegna:</span>
                  <span class="info-value">{{ formatDate(purchase.delivered_at) }}</span>
                </div>
                
                <div v-if="purchase.delivery_notes" class="delivery-notes">
                  <span class="info-label">Note:</span>
                  <span class="info-value">{{ purchase.delivery_notes }}</span>
                </div>
              </div>
              
              <div v-if="purchase.status === 'purchased' && purchase.reward.type === 'digital'" class="digital-info">
                <p class="digital-access-info">
                  Accedi alla tua ricompensa digitale:
                  <a 
                    v-if="purchase.reward.metadata.link" 
                    :href="purchase.reward.metadata.link" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    class="digital-link"
                  >
                    {{ purchase.reward.metadata.link }}
                  </a>
                  <span v-else>Nessun link disponibile.</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.purchases-view {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.purchases-header {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
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

.shop-button, .dashboard-button {
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

.shop-button {
  background-color: #4caf50;
}

.dashboard-button {
  background-color: #2196f3;
}

.button-icon {
  font-size: 1.2rem;
}

.purchase-filters {
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

.purchases-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.purchase-card {
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.purchase-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.purchase-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.purchase-status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-purchased {
  background-color: #fff8e1;
  color: #ff8f00;
}

.status-delivered {
  background-color: #e8f5e9;
  color: #388e3c;
}

.status-cancelled {
  background-color: #ffebee;
  color: #d32f2f;
}

.purchase-details {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.reward-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.reward-description {
  margin: 0;
  color: #666;
}

.reward-type-badge {
  display: inline-block;
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

.purchase-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  border-top: 1px solid #eee;
  padding-top: 1rem;
}

.purchase-date, .purchase-cost, .delivery-date, .delivery-notes {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  color: #666;
  font-size: 0.9rem;
}

.info-value {
  font-weight: 500;
}

.delivery-info {
  background-color: #f8f9fa;
  padding: 0.75rem;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.digital-info {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background-color: #e3f2fd;
  border-radius: 4px;
}

.digital-link {
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
}

.digital-link:hover {
  text-decoration: underline;
}

.loading-container, .empty-purchases {
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
  
  .purchase-filters {
    flex-wrap: wrap;
  }
  
  .filter-button {
    flex: 1;
    min-width: 100px;
  }
}
</style>