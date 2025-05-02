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
  return pointsChange >= 0 ? 'text-success bg-success/10' : 'text-error bg-error/10'; // Usa colori success/error con opacità
};

// Formatta il cambiamento di punti con segno
const formatPointsChange = (pointsChange: number): string => {
  return pointsChange >= 0 ? `+${pointsChange}` : `${pointsChange}`;
};
</script>

<template>
  <div class="wallet-card bg-white rounded-lg shadow-md p-6"> <!-- Stili card base -->
    <h2 class="text-xl font-bold text-primary-dark mb-4 flex items-center"><span class="text-2xl mr-2">💰</span> Il tuo Portafoglio</h2> <!-- Titolo primario scuro -->

    <div v-if="loading" class="loading-indicator text-center py-4 text-neutral-dark"> <!-- Testo loading neutro scuro -->
      <p>Caricamento portafoglio...</p>
    </div>
    
    <div v-else-if="!wallet" class="empty-message text-center py-4 text-error"> <!-- Testo errore -->
      <p>Impossibile caricare le informazioni del portafoglio.</p>
    </div>

    <div v-else>
      <div class="wallet-balance bg-neutral-lightest p-6 rounded-lg mb-6 text-center border border-neutral-DEFAULT"> <!-- Sfondo neutro chiaro -->
        <div class="balance-label text-lg text-neutral-dark mb-1">Punti disponibili</div> <!-- Etichetta neutra scura -->
        <div class="balance-value text-5xl font-bold text-primary">{{ wallet.current_points }}</div> <!-- Valore primario -->
      </div>
      
      <div class="wallet-transactions">
        <h3 class="text-lg font-semibold text-neutral-darkest mb-3 pt-4 border-t border-neutral-DEFAULT">Transazioni recenti</h3> <!-- Titolo neutro scuro, bordo neutro -->

        <div v-if="wallet.recent_transactions.length === 0" class="empty-transactions text-center py-4 text-neutral-dark"> <!-- Testo neutro scuro -->
          <p>Nessuna transazione recente.</p>
        </div>
        
        <div v-else class="transactions-list space-y-3">
          <div v-for="transaction in wallet.recent_transactions.slice(0, 3)" :key="transaction.id" class="transaction-item flex justify-between items-center bg-neutral-lightest p-3 rounded-md border-l-4" :class="transaction.points_change >= 0 ? 'border-success' : 'border-error'"> <!-- Sfondo neutro chiaro, bordi success/error -->
            <div class="transaction-info flex-1 mr-2">
              <div class="transaction-reason text-sm font-medium text-neutral-darkest mb-0.5">{{ transaction.reason }}</div> <!-- Testo neutro scuro -->
              <div class="transaction-date text-xs text-neutral-dark">{{ formatDate(transaction.timestamp) }}</div> <!-- Testo neutro scuro -->
            </div>
            <div :class="['transaction-amount text-lg font-bold px-2 py-0.5 rounded', getTransactionClass(transaction.points_change)]">
              {{ formatPointsChange(transaction.points_change) }}
            </div> <!-- Classi aggiornate in getTransactionClass -->
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Rimosse definizioni di stile ridondanti, ora gestite da Tailwind */
.card-icon {
    margin-right: 0.5rem;
    font-size: 1.2em; /* Rende l'icona leggermente più grande del titolo */
    vertical-align: middle; /* Allinea l'icona verticalmente */
}
</style>