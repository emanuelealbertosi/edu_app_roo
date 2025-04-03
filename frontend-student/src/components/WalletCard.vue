<script setup lang="ts">
import type { WalletInfo } from '@/api/dashboard';

const props = defineProps<{
  wallet: WalletInfo | null;
  loading?: boolean;
}>();

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

// Ottiene la classe CSS per la transazione in base al segno (positivo/negativo)
const getTransactionClass = (pointsChange: number): string => {
  // Le classi Tailwind verranno applicate direttamente nel template o nello <style scoped>
  return pointsChange >= 0 ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100';
};

// Formatta il cambiamento di punti con segno
const formatPointsChange = (pointsChange: number): string => {
  return pointsChange >= 0 ? `+${pointsChange}` : `${pointsChange}`;
};
</script>

<template>
  <div class="wallet-card bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-bold text-indigo-700 mb-4 flex items-center"><span class="text-2xl mr-2">💰</span> Il tuo Portafoglio</h2>

    <div v-if="loading" class="loading-indicator text-center py-4 text-gray-500">
      <p>Caricamento portafoglio...</p>
    </div>
    
    <div v-else-if="!wallet" class="empty-message text-center py-4 text-red-500"> {/* Stile errore */}
      <p>Impossibile caricare le informazioni del portafoglio.</p>
    </div>

    <div v-else>
      <div class="wallet-balance bg-indigo-50 p-6 rounded-lg mb-6 text-center border border-indigo-100">
        <div class="balance-label text-lg text-indigo-800 mb-1">Punti disponibili</div>
        <div class="balance-value text-5xl font-bold text-indigo-600">{{ wallet.current_points }}</div>
      </div>
      
      <div class="wallet-transactions">
        <h3 class="text-lg font-semibold text-gray-700 mb-3 pt-4 border-t border-gray-200">Transazioni recenti</h3>

        <div v-if="wallet.recent_transactions.length === 0" class="empty-transactions text-center py-4 text-gray-500">
          <p>Nessuna transazione recente.</p>
        </div>
        
        <div v-else class="transactions-list space-y-3">
          <div v-for="transaction in wallet.recent_transactions" :key="transaction.id" class="transaction-item flex justify-between items-center bg-gray-50 p-3 rounded-md border-l-4" :class="transaction.points_change >= 0 ? 'border-green-400' : 'border-red-400'">
            <div class="transaction-info flex-1 mr-2">
              <div class="transaction-reason text-sm font-medium text-gray-800 mb-0.5">{{ transaction.reason }}</div>
              <div class="transaction-date text-xs text-gray-500">{{ formatDate(transaction.timestamp) }}</div>
            </div>
            <div :class="['transaction-amount text-lg font-bold px-2 py-0.5 rounded', getTransactionClass(transaction.points_change)]">
              {{ formatPointsChange(transaction.points_change) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici rimasti (loading, empty messages) o che richiedono override */
.loading-indicator,
.empty-message,
.empty-transactions {
  /* Stili Tailwind applicati direttamente nel template */
}

/* Definiamo le classi per i colori delle transazioni se vogliamo essere più specifici
   o se le classi Tailwind dirette non bastano.
   Al momento, le classi Tailwind sono applicate direttamente nel template. */
.transaction-positive {
  /* @apply text-green-600 bg-green-100; */
}
.transaction-negative {
  /* @apply text-red-600 bg-red-100; */
}

.loading-indicator,
.empty-message,
.empty-transactions {
  padding: 1rem;
  text-align: center;
  color: #666;
}

.card-icon {
    margin-right: 0.5rem;
    font-size: 1.2em; /* Rende l'icona leggermente più grande del titolo */
    vertical-align: middle; /* Allinea l'icona verticalmente */
}
</style>