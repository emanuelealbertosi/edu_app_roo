<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'; // Aggiunto watch
import { useRouter } from 'vue-router';
import RewardsService, { type Reward } from '@/api/rewards';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
import { useNotificationStore } from '@/stores/notification'; // Importa lo store delle notifiche
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

// State
const router = useRouter();
const authStore = useAuthStore();
const dashboardStore = useDashboardStore(); // Usiamo lo store della dashboard per i punti
const notificationStore = useNotificationStore(); // Istanza dello store notifiche

const availableRewards = ref<Reward[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null); // Errore generale caricamento ricompense
const purchasingRewardId = ref<number | null>(null); // ID della ricompensa in corso di acquisto
const purchaseError = ref<string | null>(null); // Errore specifico dell'acquisto (può essere mostrato in pagina)
// purchaseSuccessMessage non è più necessario per le toast

// Computed property per i punti correnti dello studente
const currentPoints = computed(() => dashboardStore.wallet?.current_points ?? 0);

// Funzioni
async function fetchAvailableRewards() {
  isLoading.value = true;
  error.value = null;
  try {
    const rewardsData = await RewardsService.getAvailableRewards();
    console.log('Ricompense ricevute dall\'API:', rewardsData);
    availableRewards.value = rewardsData;
  } catch (err) {
    console.error('Errore durante il recupero delle ricompense:', err);
    const message = "Impossibile caricare le ricompense disponibili. Riprova più tardi.";
    error.value = message; // Errore generale mostrato in pagina
    notificationStore.addUniformToastNotification({
        title: 'Errore Caricamento Negozio',
        message: message,
        type: 'error',
    });
  } finally {
    isLoading.value = false;
  }
}

async function handlePurchase(reward: Reward) {
  if (purchasingRewardId.value !== null) return; // Evita acquisti multipli contemporanei

  if (currentPoints.value < reward.cost_points) {
      const message = "Non hai abbastanza punti per acquistare questa ricompensa.";
      purchaseError.value = message; // Mostra in pagina
      notificationStore.addUniformToastNotification({
        title: 'Punti Insufficienti',
        message: message,
        type: 'warning', // Usiamo warning per punti insufficienti
      });
      return;
  }

  if (!confirm(`Sei sicuro di voler acquistare "${reward.name}" per ${reward.cost_points} punti?`)) {
      return;
  }

  purchasingRewardId.value = reward.id;
  purchaseError.value = null; // Resetta errore in pagina

  try {
    const purchaseResult = await RewardsService.purchaseReward(reward.id);
    console.log('Acquisto completato:', purchaseResult);
    notificationStore.addUniformToastNotification({
        title: 'Acquisto Riuscito!',
        message: `Ricompensa "${reward.name}" acquistata con successo!`,
        type: 'success',
    });
    
    await dashboardStore.loadDashboard(); 
    await fetchAvailableRewards();

  } catch (err: any) {
    console.error(`Errore durante l'acquisto della ricompensa ${reward.id}:`, err);
    const errorMessage = err.response?.data?.detail || "Errore durante l'acquisto. Riprova.";
    purchaseError.value = errorMessage; // Mostra errore in pagina
    notificationStore.addUniformToastNotification({
        title: 'Errore Acquisto',
        message: errorMessage,
        type: 'error',
    });
  } finally {
    purchasingRewardId.value = null;
  }
}

// Watcher per debug
watch(availableRewards, (newVal) => {
  console.log('Watcher: availableRewards aggiornato:', newVal);
  if (newVal && newVal.length > 0) {
    console.log('Watcher: Numero di ricompense da renderizzare:', newVal.length);
  } else {
    console.log('Watcher: Nessuna ricompensa da renderizzare.');
  }
});

// Lifecycle Hooks
onMounted(() => {
  fetchAvailableRewards();
  if (!dashboardStore.wallet) {
      dashboardStore.fetchWallet();
  }
});

</script>

<template>
  <div class="shop-view px-2 md:px-4 py-8">
    <header class="shop-header bg-accent text-neutral-lightest p-4 rounded-lg shadow-md mb-6 flex justify-between items-center gap-2">
      <h1 class="text-2xl font-semibold flex items-center"><span class="text-3xl mr-3">🛍️</span> Negozio Ricompense</h1>
      <div class="current-points bg-white/20 text-neutral-lightest text-lg font-semibold px-4 py-1 rounded-full shadow-sm">
        Punti: <strong class="text-xl">{{ currentPoints }}</strong> ✨
      </div>
    </header>

    <div class="w-full">
      <div v-if="isLoading" class="loading text-center py-10 text-neutral-dark">
      <p>Caricamento ricompense...</p>
    </div>

    <div v-if="error" class="error-message bg-error/10 border-l-4 border-error text-error p-4 mb-6 rounded" role="alert">
      <p class="font-semibold">{{ error }}</p>
    </div>

    <!-- Messaggio di errore specifico per l'acquisto (se si vuole mantenere in pagina oltre alla toast) -->
    <div v-if="purchaseError" class="error-message purchase-feedback bg-error/10 border-l-4 border-error text-error p-4 mb-6 rounded" role="alert">
      <p class="font-semibold">{{ purchaseError }}</p>
    </div>

    <div v-if="!isLoading && !error">
      <div v-if="availableRewards.length > 0" class="rewards-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div v-for="reward in availableRewards" :key="reward.id" class="reward-card bg-white rounded-lg shadow-lg overflow-hidden flex flex-col border-t-4" :class="reward.type === 'digital' ? 'border-primary' : 'border-success'">
          <template v-if="reward.metadata?.image_url">
            <img
              :src="reward.metadata.image_url"
              :alt="reward.name"
              class="reward-image w-full h-48 object-cover"
            />
          </template>
          <template v-else>
            <div class="reward-image-placeholder w-full h-48 flex items-center justify-center bg-neutral-light text-neutral-dark text-5xl">🎁</div>
          </template>
          <div class="reward-info p-4 flex flex-col flex-grow">
            <h3 class="text-lg font-semibold text-neutral-darkest mb-1">{{ reward.name }}</h3>
            <p class="reward-description text-sm text-neutral-dark mb-3 flex-grow">{{ reward.description }}</p>
            <p class="reward-type text-xs italic text-neutral-dark mb-2">Tipo: {{ reward.type === 'digital' ? 'Digitale' : 'Reale' }}</p>
            <div class="reward-cost text-lg font-bold text-primary mb-3">
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
      <div v-else class="empty-message text-center py-10 text-neutral-dark">
        <p>Non ci sono ricompense disponibili al momento.</p>
      </div>
    </div>
  </div>
</div>
</template>

<style scoped>
/* Rimuoviamo tutti gli stili precedenti */
</style>