<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import RewardsService, { type Reward } from '@/api/rewards';
import { useAuthStore } from '@/stores/auth'; // Per info utente o punti?
import { useDashboardStore } from '@/stores/dashboard'; // Per aggiornare i punti dopo l'acquisto

// State
const router = useRouter();
const authStore = useAuthStore();
const dashboardStore = useDashboardStore(); // Usiamo lo store della dashboard per i punti

const availableRewards = ref<Reward[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);
const purchasingRewardId = ref<number | null>(null); // ID della ricompensa in corso di acquisto
const purchaseError = ref<string | null>(null); // Errore specifico dell'acquisto
const purchaseSuccessMessage = ref<string | null>(null); // Messaggio di successo per l'acquisto

// Computed property per i punti correnti dello studente
const currentPoints = computed(() => dashboardStore.wallet?.current_points ?? 0);

// Funzioni
async function fetchAvailableRewards() {
  isLoading.value = true;
  error.value = null;
  try {
    availableRewards.value = await RewardsService.getAvailableRewards();
  } catch (err) {
    console.error('Errore durante il recupero delle ricompense:', err);
    error.value = "Impossibile caricare le ricompense disponibili. Riprova più tardi.";
  } finally {
    isLoading.value = false;
  }
}

async function handlePurchase(reward: Reward) {
  if (purchasingRewardId.value !== null) return; // Evita acquisti multipli contemporanei

  if (currentPoints.value < reward.cost_points) {
      purchaseError.value = "Non hai abbastanza punti per acquistare questa ricompensa.";
      return;
  }

  // Chiedi conferma (opzionale ma consigliato)
  if (!confirm(`Sei sicuro di voler acquistare "${reward.name}" per ${reward.cost_points} punti?`)) {
      return;
  }

  purchasingRewardId.value = reward.id;
  purchaseError.value = null; // Resetta errori/successi precedenti
  purchaseSuccessMessage.value = null;
  try {
    const purchaseResult = await RewardsService.purchaseReward(reward.id);
    console.log('Acquisto completato:', purchaseResult);
    // Mostra un messaggio di successo integrato
    purchaseSuccessMessage.value = `Ricompensa "${reward.name}" acquistata con successo!`;
    // Cancella il messaggio dopo 5 secondi
    setTimeout(() => { purchaseSuccessMessage.value = null; }, 5000);
    
    // Aggiorna i dati della dashboard (in particolare i punti nel wallet)
    // Potrebbe essere ottimizzato aggiornando solo il wallet
    await dashboardStore.loadDashboard(); 

    // Opzionale: ricarica le ricompense se la disponibilità potrebbe cambiare dopo l'acquisto
    // await fetchAvailableRewards(); 

  } catch (err: any) {
    console.error(`Errore durante l'acquisto della ricompensa ${reward.id}:`, err);
    // Mostra un errore specifico se possibile (es. punti insufficienti dal backend)
    if (err.response && err.response.data && err.response.data.detail) { // Corretto &amp;&amp;
        purchaseError.value = err.response.data.detail;
    } else {
        purchaseError.value = "Errore durante l'acquisto. Riprova.";
    }
    // Cancella il messaggio di errore dopo 7 secondi
    setTimeout(() => { purchaseError.value = null; }, 7000);
  } finally {
    purchasingRewardId.value = null;
  }
}

// Lifecycle Hooks
onMounted(() => {
  fetchAvailableRewards();
  // Assicurati che i dati del wallet siano caricati se non lo sono già
  if (!dashboardStore.wallet) {
      dashboardStore.loadWallet();
  }
});

</script>

<template>
  <div class="shop-view">
    <header class="shop-header">
      <h1><span class="card-icon">🛍️</span> Negozio Ricompense</h1>
      <div class="current-points">
        Punti disponibili: <strong>{{ currentPoints }}</strong> ✨
      </div>
      <button @click="router.push('/dashboard')" class="back-button">Torna alla Dashboard</button>
    </header>

    <div v-if="isLoading" class="loading">
      <p>Caricamento ricompense...</p>
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>
    
    <!-- Messaggio di successo acquisto -->
    <div v-if="purchaseSuccessMessage" class="success-message purchase-feedback">
      <p>{{ purchaseSuccessMessage }}</p>
    </div>

    <!-- Messaggio di errore acquisto -->
    <div v-if="purchaseError" class="error-message purchase-feedback">
      <p>{{ purchaseError }}</p>
    </div>

    <div v-if="!isLoading &amp;&amp; !error" class="rewards-grid">
      <div v-for="reward in availableRewards" :key="reward.id" class="reward-card">
        <img 
          v-if="reward.metadata?.image_url" 
          :src="reward.metadata.image_url" 
          :alt="reward.name" 
          class="reward-image"
        />
        <div v-else class="reward-image-placeholder">🎁</div>
        
        <div class="reward-info">
          <h3>{{ reward.name }}</h3>
          <p class="reward-description">{{ reward.description }}</p>
          <p class="reward-type">Tipo: {{ reward.type === 'digital' ? 'Digitale' : 'Reale' }}</p>
          <div class="reward-cost">
            Costo: <strong>{{ reward.cost_points }}</strong> punti
          </div>
        </div>
        
        <button 
          @click="handlePurchase(reward)" 
          :disabled="purchasingRewardId === reward.id || currentPoints < reward.cost_points"
          class="purchase-button"
        >
          {{ purchasingRewardId === reward.id ? 'Acquisto...' : 'Acquista' }}
        </button>
      </div>
      
      <div v-if="availableRewards.length === 0" class="empty-message">
        <p>Non ci sono ricompense disponibili al momento.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shop-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.shop-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  background-color: #f8f9fa;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.shop-header h1 {
  margin: 0;
  font-size: 1.8em;
  color: #333;
}

.current-points {
  font-size: 1.1em;
  background-color: #fff8e1;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  color: #ff8f00;
  font-weight: 500;
}

.back-button {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}
.back-button:hover {
  background-color: #5a6268;
}


.loading, .error-message {
  margin-top: 20px;
  padding: 15px;
  border-radius: 5px;
  text-align: center;
}

.loading {
  background-color: #e0e0e0;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.success-message {
  background-color: #d4edda; /* Verde chiaro */
  color: #155724; /* Verde scuro */
  border: 1px solid #c3e6cb;
}

.purchase-feedback {
    margin-bottom: 1.5rem; /* Spazio sotto i messaggi di feedback */
    /* Animazione fade-in/out potrebbe essere aggiunta qui */
}

.rewards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.reward-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08); /* Ombra più leggera */
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border-left: 4px solid; /* Aggiunto per colore tipo */
  border-color: var(--reward-border-color, #ddd); /* Colore default */
}
/* Definisci colori per tipo */
.reward-card[data-reward-type="digital"] {
    --reward-border-color: #007bff; /* Blu */
}
.reward-card[data-reward-type="real_world_tracked"] {
     --reward-border-color: #28a745; /* Verde */
}
.reward-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.reward-image {
  width: 100%;
  height: 180px;
  object-fit: cover; /* Copre l'area senza distorcere */
  background-color: #eee; /* Placeholder color */
}
.reward-image-placeholder {
    width: 100%;
    height: 180px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 4rem;
    background-color: #f0f0f0;
    color: #ccc;
}

.reward-info {
  padding: 1rem 1rem 0.5rem 1rem; /* Ridotto padding inferiore */
  flex-grow: 1; /* Fa espandere questa sezione */
  display: flex;
  flex-direction: column;
}

.reward-info h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.reward-description {
  font-size: 0.9em;
  color: #666;
  margin-bottom: 0.8rem;
  flex-grow: 1; /* Spinge il costo e il pulsante in basso */
}

.reward-type {
    font-size: 0.8em;
    color: #888;
    margin-bottom: 0.5rem;
    font-style: italic;
}

.reward-cost {
  font-size: 1.1em;
  color: #007bff;
  margin-bottom: 1rem;
}

.purchase-button {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 0.8rem;
  border-bottom-left-radius: 8px; /* Arrotonda solo gli angoli inferiori */
  border-bottom-right-radius: 8px;
  cursor: pointer;
  font-size: 1em;
  font-weight: bold;
  transition: background-color 0.2s ease;
  margin-top: 0.5rem; /* Ridotto margine sopra il pulsante */
}

.purchase-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.purchase-button:hover:not(:disabled) {
  background-color: #0056b3;
}

.empty-message {
  grid-column: 1 / -1; /* Occupa tutta la larghezza della griglia */
  text-align: center;
  padding: 2rem;
  color: #666;
}

.card-icon {
    margin-right: 0.5rem;
    font-size: 1em;
    vertical-align: baseline;
}
</style>