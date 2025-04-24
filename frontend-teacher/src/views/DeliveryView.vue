<template>
  <div class="delivery-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo -->
      <h1 class="text-2xl font-semibold">Consegna Ricompense</h1> <!-- Rimosso stile individuale -->
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento consegne pendenti...</div> <!-- Stile loading aggiornato -->
    <div v-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert"> <!-- Stile errore aggiornato -->
       <strong class="font-bold">Errore!</strong>
       <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-if="!isLoading && pendingDeliveries.length === 0" class="text-center py-10 text-neutral-dark"> <!-- Stile empty message aggiornato -->
      Nessuna ricompensa in attesa di consegna.
    </div>

    <!-- Styled List Container -->
    <div v-else class="delivery-list space-y-4"> <!-- Use space-y for gap -->
      <!-- Styled List Item Card -->
      <div v-for="purchase in pendingDeliveries" :key="purchase.id" class="delivery-item bg-white p-4 rounded-lg shadow-md border border-neutral-DEFAULT"> <!-- Stili card aggiornati -->
        <h3 class="text-lg font-semibold mb-2 text-neutral-darkest">{{ purchase.reward_info.name }}</h3> <!-- Stile testo aggiornato -->
        <p class="text-sm text-neutral-darker mb-1"><strong class="font-medium text-neutral-darkest">Studente:</strong> {{ purchase.student_info.full_name }} ({{ purchase.student_info.student_code }})</p> <!-- Stili testo aggiornati -->
        <p class="text-sm text-neutral-darker mb-1"><strong class="font-medium text-neutral-darkest">Acquistato il:</strong> {{ formatDate(purchase.purchased_at) }}</p> <!-- Stili testo aggiornati -->
        <p class="text-sm text-neutral-darker mb-3"><strong class="font-medium text-neutral-darkest">Costo:</strong> {{ purchase.points_spent }} punti</p> <!-- Stili testo aggiornati -->
        <!-- Styled Actions Area -->
        <div class="delivery-actions mt-3 pt-3 border-t border-neutral-DEFAULT flex flex-col sm:flex-row sm:items-center sm:space-x-3 space-y-2 sm:space-y-0"> <!-- Stile bordo aggiornato -->
          <textarea
            v-model="deliveryNotes[purchase.id]"
            placeholder="Note sulla consegna (opzionale)"
            class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:flex-grow text-sm border-neutral-DEFAULT rounded-md p-2 resize-none h-16 sm:h-auto"
          ></textarea> <!-- Stili textarea aggiornati -->
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
import { ref, onMounted, reactive } from 'vue';
import { fetchPendingDeliveries, markRewardAsDelivered, type RewardPurchaseDetails } from '@/api/rewards'; // Assumendo che le funzioni API esistano
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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
/* Rimosso stile spinner FontAwesome */
</style>