<template>
  <div class="delivery-view">
    <h1>Consegna Ricompense</h1>

    <div v-if="isLoading" class="loading">Caricamento consegne pendenti...</div>
    <div v-if="error" class="error-message">{{ error }}</div>

    <div v-if="!isLoading &amp;&amp; pendingDeliveries.length === 0" class="empty-message">
      Nessuna ricompensa in attesa di consegna.
    </div>

    <div v-else class="delivery-list">
      <div v-for="purchase in pendingDeliveries" :key="purchase.id" class="delivery-item">
        <h3>{{ purchase.reward_info.name }}</h3>
        <p><strong>Studente:</strong> {{ purchase.student_info.full_name }} ({{ purchase.student_info.student_code }})</p>
        <p><strong>Acquistato il:</strong> {{ formatDate(purchase.purchased_at) }}</p>
        <p><strong>Costo:</strong> {{ purchase.points_spent }} punti</p>
        <div class="delivery-actions">
          <textarea v-model="deliveryNotes[purchase.id]" placeholder="Note sulla consegna (opzionale)"></textarea>
          <button @click="markAsDelivered(purchase.id)" :disabled="isDelivering[purchase.id]">
            {{ isDelivering[purchase.id] ? 'Consegna...' : 'Segna come Consegnato' }}
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
  error.value = null; // Resetta errore precedente specifico per questa azione?
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
.delivery-view {
  padding: 20px;
}
.loading, .error-message, .empty-message {
  margin-top: 15px;
  padding: 10px;
  border-radius: 4px;
}
.error-message {
  color: red;
  background-color: #fdd;
}
.empty-message {
  color: #666;
}
.delivery-list {
  margin-top: 20px;
  display: grid;
  gap: 20px;
}
.delivery-item {
  border: 1px solid #ccc;
  padding: 15px;
  border-radius: 5px;
  background-color: #f9f9f9;
}
.delivery-item h3 {
  margin-top: 0;
}
.delivery-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  align-items: center;
}
.delivery-actions textarea {
  flex-grow: 1;
  min-height: 40px;
  resize: vertical;
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 3px;
}
.delivery-actions button {
  padding: 8px 12px;
  cursor: pointer;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
}
.delivery-actions button:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}
</style>