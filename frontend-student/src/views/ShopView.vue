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

    // Ricarica le ricompense per aggiornare la lista dopo l'acquisto
    await fetchAvailableRewards();

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
      dashboardStore.fetchWallet(); // Corretto nome azione
  }
});

</script>

<template>
  <div class="shop-view container mx-auto px-4 py-8">
    <header class="shop-header bg-white p-4 md:p-6 rounded-lg shadow-md mb-8 flex flex-col md:flex-row justify-between items-center gap-4">
      <h1 class="text-2xl md:text-3xl font-bold text-purple-800 flex items-center"><span class="text-3xl md:text-4xl mr-3">🛍️</span> Negozio Ricompense</h1>
      <div class="current-points bg-yellow-100 text-yellow-800 text-lg font-semibold px-4 py-2 rounded-full shadow-sm">
        Punti: <strong class="text-xl">{{ currentPoints }}</strong> ✨
      </div>
      <button @click="router.push('/dashboard')" class="back-button bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg shadow transition-colors duration-200">Torna alla Dashboard</button>
    </header>

    <div v-if="isLoading" class="loading text-center py-10 text-gray-500">
      <p>Caricamento ricompense...</p>
      <!-- Spinner TODO rimosso -->
    </div>

    <div v-if="error" class="error-message bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded" role="alert">
      <p>{{ error }}</p>
    </div>
    
    <!-- Messaggio di successo acquisto -->
    <div v-if="purchaseSuccessMessage" class="success-message purchase-feedback bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-6 rounded" role="alert">
      <p>{{ purchaseSuccessMessage }}</p>
    </div>

    <div v-if="purchaseError" class="error-message purchase-feedback bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded" role="alert">
      <p>{{ purchaseError }}</p>
    </div>

    <div v-if="!isLoading && !error" class="rewards-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <div v-for="reward in availableRewards" :key="reward.id" class="reward-card bg-white rounded-lg shadow-lg overflow-hidden flex flex-col border-t-4" :class="reward.type === 'digital' ? 'border-blue-500' : 'border-green-500'">
        <img
          v-if="reward.metadata?.image_url"
          :src="reward.metadata.image_url"
          :alt="reward.name"
          class="reward-image w-full h-48 object-cover"
        />
        <div v-else class="reward-image-placeholder w-full h-48 flex items-center justify-center bg-gray-200 text-gray-400 text-5xl">🎁</div>
        
        <div class="reward-info p-4 flex flex-col flex-grow">
          <h3 class="text-lg font-semibold text-gray-800 mb-1">{{ reward.name }}</h3>
          <p class="reward-description text-sm text-gray-600 mb-3 flex-grow">{{ reward.description }}</p>
          <p class="reward-type text-xs italic text-gray-500 mb-2">Tipo: {{ reward.type === 'digital' ? 'Digitale' : 'Reale' }}</p>
          <div class="reward-cost text-lg font-bold text-indigo-600 mb-3">
            Costo: <strong>{{ reward.cost_points }}</strong> punti
          </div>
        </div>
        
        <button
          @click="handlePurchase(reward)"
          :disabled="purchasingRewardId === reward.id || currentPoints < reward.cost_points"
          class="purchase-button w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white font-bold py-3 px-4 transition-colors duration-200 mt-auto"
          :class="{ 'opacity-50 cursor-not-allowed': purchasingRewardId === reward.id || currentPoints < reward.cost_points }"
        >
          {{ purchasingRewardId === reward.id ? 'Acquisto...' : 'Acquista' }}
        </button>
      </div>
      
      <div v-if="availableRewards.length === 0" class="empty-message col-span-full text-center py-10 text-gray-500">
        <p>Non ci sono ricompense disponibili al momento.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Rimuoviamo tutti gli stili precedenti */
</style>