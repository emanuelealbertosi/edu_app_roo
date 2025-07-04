<template>
  <div class="delivery-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo -->
      <h1 class="text-2xl font-semibold">Consegna Ricompense</h1> <!-- Rimosso stile individuale -->
    </div>

    <!-- Filtri e Ordinamento -->
    <div class="flex flex-col md:flex-row gap-4 mb-6">
      <div class="flex-grow">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Cerca per nome ricompensa o studente..."
          class="mt-1 block w-full px-3 py-2 bg-white border border-neutral-DEFAULT rounded-md shadow-sm placeholder-neutral-dark focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
        />
      </div>
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento consegne pendenti...</div>
    <div v-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
       <strong class="font-bold">Errore!</strong>
       <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-if="!isLoading && filteredAndSortedDeliveries.length === 0" class="text-center py-10 text-neutral-dark">
      <span v-if="searchQuery">Nessun risultato per "{{ searchQuery }}".</span>
      <span v-else>Nessuna ricompensa in attesa di consegna.</span>
    </div>

    <div v-else class="delivery-list space-y-4">
      <div v-for="purchase in filteredAndSortedDeliveries" :key="purchase.id" class="delivery-item bg-white p-4 rounded-lg shadow-md border border-neutral-DEFAULT">
        <h3 class="text-lg font-semibold mb-2 text-neutral-darkest">{{ purchase.reward_info.name }}</h3>
        <p class="text-sm text-neutral-darker mb-1"><strong class="font-medium text-neutral-darkest">Studente:</strong> {{ purchase.student_info.full_name }} ({{ purchase.student_info.student_code }})</p>
        <p class="text-sm text-neutral-darker mb-1"><strong class="font-medium text-neutral-darkest">Acquistato il:</strong> {{ formatDate(purchase.purchased_at) }}</p>
        <p class="text-sm text-neutral-darker mb-3"><strong class="font-medium text-neutral-darkest">Costo:</strong> {{ purchase.points_spent }} punti</p>
        <div class="delivery-actions mt-3 pt-3 border-t border-neutral-DEFAULT flex flex-col sm:flex-row sm:items-center sm:space-x-3 space-y-2 sm:space-y-0">
          <textarea
            v-model="deliveryNotes[purchase.id]"
            placeholder="Note sulla consegna (opzionale)"
            class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:flex-grow text-sm border-neutral-DEFAULT rounded-md p-2 resize-none h-16 sm:h-auto"
          ></textarea>
          <BaseButton
            variant="success"
            size="sm"
            @click="markAsDelivered(purchase.id)"
            :disabled="isDelivering[purchase.id]"
            class="w-full sm:w-auto flex-shrink-0"
          >
             <span v-if="isDelivering[purchase.id]">
               <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                 <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
               </svg>
               Consegna...
             </span>
             <span v-else>Segna come Consegnato</span>
          </BaseButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue';
import { fetchPendingDeliveries, markRewardAsDelivered, type RewardPurchaseDetails } from '@/api/rewards';
import BaseButton from '@/components/common/BaseButton.vue';

const isLoading = ref(true);
const error = ref<string | null>(null);
const pendingDeliveries = ref<RewardPurchaseDetails[]>([]);
const deliveryNotes = reactive<Record<number, string>>({});
const isDelivering = reactive<Record<number, boolean>>({});
const searchQuery = ref('');
const sortKey = ref('purchased_at');
const sortOrder = ref('desc');

const filteredAndSortedDeliveries = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  const filtered = query
    ? pendingDeliveries.value.filter(p => {
        const rewardName = p.reward_info.name.toLowerCase();
        const studentName = p.student_info.full_name.toLowerCase();
        const studentCode = p.student_info.student_code.toLowerCase();
        return rewardName.includes(query) || studentName.includes(query) || studentCode.includes(query);
      })
    : pendingDeliveries.value;

  return filtered.slice().sort((a, b) => {
    let valA: any;
    let valB: any;

    switch (sortKey.value) {
      case 'reward_name':
        valA = a.reward_info.name.toLowerCase();
        valB = b.reward_info.name.toLowerCase();
        break;
      case 'student_name':
        valA = a.student_info.full_name.toLowerCase();
        valB = b.student_info.full_name.toLowerCase();
        break;
      case 'points_spent':
        valA = a.points_spent;
        valB = b.points_spent;
        break;
      case 'purchased_at':
      default:
        valA = new Date(a.purchased_at).getTime();
        valB = new Date(b.purchased_at).getTime();
        break;
    }

    if (valA < valB) {
      return sortOrder.value === 'asc' ? -1 : 1;
    }
    if (valA > valB) {
      return sortOrder.value === 'asc' ? 1 : -1;
    }
    return 0;
  });
});

onMounted(async () => {
  await loadPendingDeliveries();
});

async function loadPendingDeliveries() {
  isLoading.value = true;
  error.value = null;
  try {
    pendingDeliveries.value = await fetchPendingDeliveries();
    // Inizializza note e stati di caricamento
    pendingDeliveries.value.forEach(p => {
        deliveryNotes[p.id] = '';
        isDelivering[p.id] = false;
    });
  } catch (err: any) {
    console.error("Errore nel caricamento delle consegne pendenti:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore nel caricamento delle consegne.';
  } finally {
    isLoading.value = false;
  }
}

async function markAsDelivered(purchaseId: number) {
  isDelivering[purchaseId] = true;
  error.value = null; // Resetta errore generale prima di provare
  try {
    await markRewardAsDelivered(purchaseId, deliveryNotes[purchaseId] || null);
    // Rimuovi dalla lista locale o ricarica la lista
    pendingDeliveries.value = pendingDeliveries.value.filter(p => p.id !== purchaseId);
    delete deliveryNotes[purchaseId]; // Pulisci note
    delete isDelivering[purchaseId]; // Pulisci stato
    // Mostra notifica successo (opzionale)
  } catch (err: any) {
    console.error(`Errore nel segnare come consegnato l'acquisto ${purchaseId}:`, err);
    // Mostra errore specifico per questo item? O un errore generale?
    error.value = `Errore consegna acquisto ${purchaseId}: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
  } finally {
    // Anche se c'è errore, resetta lo stato di caricamento per permettere nuovo tentativo
     if (isDelivering[purchaseId]) { // Controlla se esiste ancora prima di settare
       isDelivering[purchaseId] = false;
     }
  }
}

function formatDate(dateString: string | null): string {
  if (!dateString) return 'N/D';
  return new Date(dateString).toLocaleString('it-IT');
}
</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
/* Rimosso stile spinner FontAwesome */
</style>