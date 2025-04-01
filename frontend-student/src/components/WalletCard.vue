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
  return pointsChange >= 0 ? 'transaction-positive' : 'transaction-negative';
};

// Formatta il cambiamento di punti con segno
const formatPointsChange = (pointsChange: number): string => {
  return pointsChange >= 0 ? `+${pointsChange}` : `${pointsChange}`;
};
</script>

<template>
  <div class="wallet-card dashboard-card">
    <h2>Il tuo Portafoglio</h2>
    
    <div v-if="loading" class="loading-indicator">
      <p>Caricamento in corso...</p>
    </div>
    
    <div v-else-if="!wallet" class="empty-message">
      <p>Impossibile caricare le informazioni del portafoglio.</p>
    </div>
    
    <div v-else>
      <div class="wallet-balance">
        <div class="balance-label">Punti disponibili:</div>
        <div class="balance-value">{{ wallet.current_points }}</div>
      </div>
      
      <div class="wallet-transactions">
        <h3>Transazioni recenti</h3>
        
        <div v-if="wallet.recent_transactions.length === 0" class="empty-transactions">
          <p>Nessuna transazione recente.</p>
        </div>
        
        <div v-else class="transactions-list">
          <div v-for="transaction in wallet.recent_transactions" :key="transaction.id" class="transaction-item">
            <div class="transaction-info">
              <div class="transaction-reason">{{ transaction.reason }}</div>
              <div class="transaction-date">{{ formatDate(transaction.timestamp) }}</div>
            </div>
            <div :class="['transaction-amount', getTransactionClass(transaction.points_change)]">
              {{ formatPointsChange(transaction.points_change) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wallet-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.wallet-balance {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  margin-bottom: 1.5rem;
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
}

.balance-label {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.balance-value {
  font-size: 3rem;
  font-weight: bold;
  color: #4caf50;
}

.wallet-transactions h3 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: #333;
}

.transactions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.transaction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background-color: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #ddd;
}

.transaction-info {
  flex: 1;
}

.transaction-reason {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.transaction-date {
  font-size: 0.8rem;
  color: #666;
}

.transaction-amount {
  font-weight: bold;
  font-size: 1.1rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.transaction-positive {
  color: #4caf50;
  background-color: rgba(76, 175, 80, 0.1);
}

.transaction-negative {
  color: #f44336;
  background-color: rgba(244, 67, 54, 0.1);
}

.loading-indicator,
.empty-message,
.empty-transactions {
  padding: 1rem;
  text-align: center;
  color: #666;
}
</style>