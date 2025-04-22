<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import RewardsService, { type RewardPurchase } from '@/api/rewards';
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

// State
const router = useRouter();
const purchaseHistory = ref<RewardPurchase[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

// Funzioni
async function fetchPurchaseHistory() {
  isLoading.value = true;
  error.value = null;
  try {
    purchaseHistory.value = await RewardsService.getPurchaseHistory();
  } catch (err: any) { // Aggiunto :any
    console.error('Errore durante il recupero dello storico acquisti:', err);
     if (err.response?.data?.detail) {
        error.value = `Errore caricamento storico: ${err.response.data.detail}`;
    } else {
        error.value = "Impossibile caricare lo storico degli acquisti. Controlla la connessione o riprova.";
    }
    // Non impostiamo un timeout qui, l'utente può riprovare manualmente
  } finally {
    isLoading.value = false;
  }
}

// Formatta la data
const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'N/D';
  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
};

// Funzioni getStatusLabel e getStatusClass rimosse perché sostituite da icone

// Lifecycle Hooks
onMounted(() => {
  fetchPurchaseHistory();
});

</script>

<template>
  <div class="purchases-view container mx-auto px-4 py-8">
    <header class="purchases-header mb-8 flex justify-between items-center"> <!-- Aggiunto flex per allineare bottone -->
      <h1 class="text-3xl font-bold text-kahoot-purple flex items-center"><span class="text-4xl mr-3">📜</span> Storico Acquisti</h1> <!-- Colore titolo aggiornato -->
      <BaseButton variant="secondary" @click="router.push('/dashboard')">Torna alla Dashboard</BaseButton> <!-- Bottone spostato qui -->
    </header>

    <div v-if="isLoading" class="loading text-center py-10 text-brand-gray-dark"> <!-- Colore testo aggiornato -->
      <p>Caricamento storico...</p>
    </div>

    <div v-if="error" class="error-message bg-kahoot-red-light border-l-4 border-kahoot-red text-kahoot-red-dark p-4 mb-6 rounded flex justify-between items-center" role="alert"> <!-- Colori errore aggiornati -->
      <p class="font-semibold">{{ error }}</p>
      <BaseButton variant="danger" size="sm" @click="fetchPurchaseHistory">Riprova</BaseButton> <!-- Usa BaseButton -->
    </div>

    <div v-if="!isLoading && !error" class="purchases-list-container bg-white p-6 rounded-lg shadow-md">
      <table v-if="purchaseHistory.length > 0" class="purchases-table w-full">
        <thead class="hidden md:table-header-group">
          <tr class="bg-brand-gray-light"> <!-- Colore sfondo header aggiornato -->
            <th class="px-4 py-3 text-left text-xs font-medium text-brand-gray-dark uppercase tracking-wider">Ricompensa</th> <!-- Colore testo header aggiornato -->
            <th class="px-4 py-3 text-left text-xs font-medium text-brand-gray-dark uppercase tracking-wider">Descrizione</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-brand-gray-dark uppercase tracking-wider">Costo (Punti)</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-brand-gray-dark uppercase tracking-wider">Data Acquisto</th>
            <th class="px-4 py-3 text-center text-xs font-medium text-brand-gray-dark uppercase tracking-wider">Stato</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-brand-gray-dark uppercase tracking-wider">Data Consegna</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-brand-gray-dark uppercase tracking-wider">Note Consegna</th>
          </tr>
        </thead>
        <tbody class="text-sm text-brand-gray-dark"> <!-- Colore testo body aggiornato -->
          <tr v-for="purchase in purchaseHistory" :key="purchase.id" class="border-b border-brand-gray-light md:border-none"> <!-- Colore bordo aggiornato -->
            <td data-label="Ricompensa" class="px-4 py-3 whitespace-nowrap font-semibold">{{ purchase.reward_info.name }}</td>
            <td data-label="Descrizione" class="px-4 py-3">{{ purchase.reward_info.description || '-' }}</td>
            <td data-label="Costo" class="points-spent px-4 py-3 whitespace-nowrap font-semibold text-kahoot-purple">{{ purchase.points_spent }}</td> <!-- Colore punti spesi -->
            <td data-label="Data Acquisto" class="px-4 py-3 whitespace-nowrap">{{ formatDate(purchase.purchased_at) }}</td>
            <td data-label="Stato" class="status-cell px-4 py-3 text-center">
              <span v-if="purchase.status === 'PURCHASED'" title="Acquistato (In attesa di consegna)" class="text-2xl">⏳</span>
              <span v-else-if="purchase.status === 'DELIVERED'" title="Consegnato" class="text-2xl">✅</span>
              <span v-else-if="purchase.status === 'CANCELLED'" title="Annullato" class="text-2xl">❌</span>
              <span v-else class="text-xs italic">{{ purchase.status }}</span>
            </td>
            <td data-label="Data Consegna" class="px-4 py-3 whitespace-nowrap">{{ formatDate(purchase.delivered_at) }}</td>
            <td data-label="Note Consegna" class="px-4 py-3">{{ purchase.delivery_notes || '-' }}</td>
          </tr>
        </tbody>
      </table>
      
      <div v-else class="empty-message text-center py-10 text-brand-gray-dark"> <!-- Colore testo aggiornato -->
        <p class="mb-4">Non hai ancora effettuato nessun acquisto.</p>
        <BaseButton variant="info" @click="router.push('/shop')">Vai allo Shop</BaseButton> <!-- Usa BaseButton -->
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici rimasti (loading, error, empty) o che richiedono override */
.loading, .error-message, .empty-message {
  /* Stili Tailwind applicati direttamente nel template */
}
/* Rimossi stili .retry-button e .go-to-shop-link */

/* Manteniamo gli stili per la tabella responsiva */

/* Responsive Table Styles */
@media (max-width: 768px) {
  .purchases-table thead {
    display: none; /* Nasconde l'header su schermi piccoli */
  }
  .purchases-table, .purchases-table tbody, .purchases-table tr, .purchases-table td {
    display: block;
    width: 100%;
  }
  .purchases-table tr {
    margin-bottom: 15px;
    border: 1px solid #ddd;
    border-radius: 5px;
    overflow: hidden;
  }
  .purchases-table td {
    text-align: right; /* Allinea il valore a destra */
    padding-left: 50%; /* Crea spazio per l'etichetta */
    position: relative;
    border-bottom: none; /* Rimuove la linea inferiore di default */
    padding-top: 8px;
    padding-bottom: 8px;
    /* Aggiunto per gestire meglio il wrap della descrizione */
    white-space: normal; 
    word-break: break-word;
  }
   .purchases-table td:last-child {
       border-bottom: 0; /* Nessun bordo per l'ultimo elemento */
   }
  .purchases-table td::before {
    content: attr(data-label); /* Usa l'attributo data-label come etichetta */
    position: absolute;
    left: 15px; /* Allinea l'etichetta a sinistra */
    width: calc(50% - 30px); /* Larghezza dell'etichetta */
    padding-right: 10px;
    white-space: nowrap;
    text-align: left;
    font-weight: bold;
    color: #555;
  }
}

</style>