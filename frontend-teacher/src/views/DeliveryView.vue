<template>
  <div class="delivery-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-6">Consegna Ricompense</h1> <!-- Styled heading -->

    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento consegne pendenti...</div> <!-- Styled loading -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
       <strong class="font-bold">Errore!</strong>
       <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-if="!isLoading && pendingDeliveries.length === 0" class="text-center py-10 text-gray-500"> <!-- Styled empty message -->
      Nessuna ricompensa in attesa di consegna.
    </div>

    <!-- Styled List Container -->
    <div v-else class="delivery-list space-y-4"> <!-- Use space-y for gap -->
      <!-- Styled List Item Card -->
      <div v-for="purchase in pendingDeliveries" :key="purchase.id" class="delivery-item bg-white p-4 rounded-lg shadow-md border border-gray-200">
        <h3 class="text-lg font-semibold mb-2 text-gray-800">{{ purchase.reward_info.name }}</h3>
        <p class="text-sm text-gray-600 mb-1"><strong class="font-medium text-gray-700">Studente:</strong> {{ purchase.student_info.full_name }} ({{ purchase.student_info.student_code }})</p>
        <p class="text-sm text-gray-600 mb-1"><strong class="font-medium text-gray-700">Acquistato il:</strong> {{ formatDate(purchase.purchased_at) }}</p>
        <p class="text-sm text-gray-600 mb-3"><strong class="font-medium text-gray-700">Costo:</strong> {{ purchase.points_spent }} punti</p>
        <!-- Styled Actions Area -->
        <div class="delivery-actions mt-3 pt-3 border-t border-gray-200 flex flex-col sm:flex-row sm:items-center sm:space-x-3 space-y-2 sm:space-y-0">
          <textarea
            v-model="deliveryNotes[purchase.id]"
            placeholder="Note sulla consegna (opzionale)"
            class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:flex-grow text-sm border-gray-300 rounded-md p-2 resize-none h-16 sm:h-auto"
          ></textarea>
          <button
            @click="markAsDelivered(purchase.id)"
            :disabled="isDelivering[purchase.id]"
            class="btn btn-success btn-sm w-full sm:w-auto flex-shrink-0"
          >
             <span v-if="isDelivering[purchase.id]">
               <i class="fas fa-spinner fa-spin mr-1"></i> Consegna...
             </span>
             <span v-else>Segna come Consegnato</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { fetchPendingDeliveries, markRewardAsDelivered, type RewardPurchaseDetails } from '@/api/rewards'; // Assumendo che le funzioni API esistano

const isLoading = ref(true);
const error = ref<string | null>(null);
const pendingDeliveries = ref<RewardPurchaseDetails[]>([]); // Usa un tipo dettagliato se disponibile
const deliveryNotes = reactive<Record<number, string>>({});
const isDelivering = reactive<Record<number, boolean>>({});

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
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.fa-spinner {
  animation: spin 1s linear infinite;
}
</style>