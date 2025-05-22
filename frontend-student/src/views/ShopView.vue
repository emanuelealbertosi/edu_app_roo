<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'; // Aggiunto watch
import { useRouter } from 'vue-router';
import RewardsService, { type Reward } from '@/api/rewards';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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
    const rewardsData = await RewardsService.getAvailableRewards();
    console.log('Ricompense ricevute dall\'API:', rewardsData); // LOG 1: Dati grezzi API
    availableRewards.value = rewardsData;
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
    if (err.response && err.response.data && err.response.data.detail) { // Corretto &&
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

// Watcher per debug
watch(availableRewards, (newVal) => {
  console.log('Watcher: availableRewards aggiornato:', newVal); // LOG 2: Dati nello state
  if (newVal && newVal.length > 0) {
    console.log('Watcher: Numero di ricompense da renderizzare:', newVal.length);
  } else {
    console.log('Watcher: Nessuna ricompensa da renderizzare.');
  }
});

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
  <div class="shop-view px-4 md:px-8 py-8"> <!-- Rimosso container mx-auto, aggiunto padding laterale -->
    <header class="shop-header bg-accent text-neutral-lightest p-4 rounded-lg shadow-md mb-6 flex justify-between items-center gap-2"> <!-- Ripristinate flex, ridotto gap -->
      <h1 class="text-2xl font-semibold flex items-center"><span class="text-3xl mr-3">🛍️</span> Negozio Ricompense</h1>
      <div class="current-points bg-white/20 text-neutral-lightest text-lg font-semibold px-4 py-1 rounded-full shadow-sm"> <!-- Rimosso posizionamento assoluto, ridotto py -->
        Punti: <strong class="text-xl">{{ currentPoints }}</strong> ✨
      </div>
      <!-- Pulsante "Torna alla Dashboard" rimosso -->
    </header>

    <div class="container mx-auto"> <!-- Contenuto principale avvolto in container -->
      <div v-if="isLoading" class="loading text-center py-10 text-neutral-dark">
      <p>Caricamento ricompense...</p>
      <!-- Spinner TODO rimosso -->
    </div>

    <div v-if="error" class="error-message bg-error/10 border-l-4 border-error text-error p-4 mb-6 rounded" role="alert"> <!-- Colori errore aggiornati -->
      <p class="font-semibold">{{ error }}</p>
    </div>

    <!-- Messaggio di successo acquisto -->
    <div v-if="purchaseSuccessMessage" class="success-message purchase-feedback bg-success/10 border-l-4 border-success text-success-dark p-4 mb-6 rounded" role="alert"> <!-- Colori successo aggiornati -->
      <p class="font-semibold">{{ purchaseSuccessMessage }}</p>
    </div>

    <div v-if="purchaseError" class="error-message purchase-feedback bg-error/10 border-l-4 border-error text-error p-4 mb-6 rounded" role="alert"> <!-- Colori errore aggiornati -->
      <p class="font-semibold">{{ purchaseError }}</p>
    </div>

    <div v-if="!isLoading && !error">
      <!-- Mostra la griglia solo se ci sono ricompense -->
      <div v-if="availableRewards.length > 0" class="rewards-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div v-for="reward in availableRewards" :key="reward.id" class="reward-card bg-white rounded-lg shadow-lg overflow-hidden flex flex-col border-t-4" :class="reward.type === 'digital' ? 'border-primary' : 'border-success'"> <!-- Colori bordo aggiornati -->
          <!-- Test: Decommento solo div info e nome -->
          <!-- Reward ID: {{ reward.id }} --> <!-- Commento l'ID ora -->
          <template v-if="reward.metadata?.image_url">
            <img
              :src="reward.metadata.image_url"
              :alt="reward.name"
              class="reward-image w-full h-48 object-cover"
            />
          </template>
          <template v-else>
            <div class="reward-image-placeholder w-full h-48 flex items-center justify-center bg-neutral-light text-neutral-dark text-5xl">🎁</div> <!-- Colori placeholder aggiornati -->
          </template>
          <div class="reward-info p-4 flex flex-col flex-grow">
            <h3 class="text-lg font-semibold text-neutral-darkest mb-1">{{ reward.name }}</h3> <!-- Colore testo aggiornato -->
            <p class="reward-description text-sm text-neutral-dark mb-3 flex-grow">{{ reward.description }}</p> <!-- Colore testo aggiornato -->
            <p class="reward-type text-xs italic text-neutral-dark mb-2">Tipo: {{ reward.type === 'digital' ? 'Digitale' : 'Reale' }}</p> <!-- Colore testo aggiornato -->
            <div class="reward-cost text-lg font-bold text-primary mb-3"> <!-- Colore testo aggiornato -->
              Costo: <strong>{{ reward.cost_points }}</strong> punti
            </div>
          </div>
          <BaseButton
            variant="primary"
            @click="handlePurchase(reward)"
            :disabled="purchasingRewardId === reward.id || currentPoints < reward.cost_points"
            class="w-full rounded-t-none"
          >
            {{ purchasingRewardId === reward.id ? 'Acquisto...' : 'Acquista' }}
          </BaseButton>
        </div>
      </div>
      <!-- Mostra il messaggio se non ci sono ricompense -->
      <div v-else class="empty-message text-center py-10 text-neutral-dark"> <!-- Colore testo aggiornato -->
        <p>Non ci sono ricompense disponibili al momento.</p>
      </div>
    </div>
  </div> <!-- Chiusura del div container mx-auto -->
</div> <!-- Chiusura del div shop-view principale -->
</template>

<style scoped>
/* Rimuoviamo tutti gli stili precedenti */
</style>