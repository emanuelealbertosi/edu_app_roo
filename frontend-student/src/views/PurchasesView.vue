<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import RewardsService, { type RewardPurchase } from '@/api/rewards';

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

// Ottiene un'etichetta leggibile per lo stato dell'acquisto
const getStatusLabel = (status: RewardPurchase['status']): string => {
    switch (status) {
        case 'purchased': return 'Acquistato (In attesa)';
        case 'delivered': return 'Consegnato';
        case 'cancelled': return 'Annullato';
        default: return status;
    }
};

// Ottiene una classe CSS per lo stato
const getStatusClass = (status: RewardPurchase['status']): string => {
    switch (status) {
        case 'purchased': return 'status-purchased';
        case 'delivered': return 'status-delivered';
        case 'cancelled': return 'status-cancelled';
        default: return '';
    }
};


// Lifecycle Hooks
onMounted(() => {
  fetchPurchaseHistory();
});

</script>

<template>
  <div class="purchases-view">
    <header class="purchases-header">
      <h1>📜 Storico Acquisti</h1>
      <!-- Il pulsante indietro è ora nella navbar principale in App.vue -->
      <!-- <button @click="router.push('/dashboard')" class="back-button">Torna alla Dashboard</button> -->
    </header>

    <div v-if="isLoading" class="loading">
      <p>Caricamento storico...</p>
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="fetchPurchaseHistory" class="retry-button">Riprova</button>
    </div>

    <div v-if="!isLoading &amp;&amp; !error" class="purchases-list-container">
      <table v-if="purchaseHistory.length > 0" class="purchases-table">
        <thead>
          <tr>
            <th>Ricompensa</th>
            <th>Costo (Punti)</th>
            <th>Data Acquisto</th>
            <th>Stato</th>
            <th>Data Consegna</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="purchase in purchaseHistory" :key="purchase.id">
            <td data-label="Ricompensa">{{ purchase.reward.name }}</td>
            <td data-label="Costo" class="points-spent">{{ purchase.points_spent }}</td>
            <td data-label="Data Acquisto">{{ formatDate(purchase.purchased_at) }}</td>
            <td data-label="Stato">
              <span :class="['status-badge', getStatusClass(purchase.status)]">
                {{ getStatusLabel(purchase.status) }}
              </span>
            </td>
            <td data-label="Data Consegna">{{ formatDate(purchase.delivered_at) }}</td>
          </tr>
        </tbody>
      </table>
      
      <div v-else class="empty-message">
        <p>Non hai ancora effettuato nessun acquisto.</p>
        <router-link to="/shop" class="go-to-shop-link">Vai allo Shop</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.purchases-view {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.purchases-header {
  display: flex;
  justify-content: space-between; /* Sposta il titolo a sinistra */
  align-items: center;
  margin-bottom: 2rem;
  /* Rimuoviamo lo sfondo qui se la navbar è globale */
  /* background-color: #f8f9fa; */
  /* padding: 1rem 1.5rem; */
  /* border-radius: 8px; */
  /* box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); */
}

.purchases-header h1 {
  margin: 0;
  font-size: 1.8em;
  color: #333;
}

/* Stile rimosso per il back-button, ora è nella navbar */

.loading, .error-message, .empty-message {
  margin-top: 20px;
  padding: 15px;
  border-radius: 5px;
  text-align: center;
}

.loading {
  background-color: #e0e0e0;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.retry-button {
    margin-top: 10px;
    padding: 5px 15px;
    font-size: 0.9em;
    cursor: pointer;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 3px;
}
.retry-button:hover {
    background-color: #5a6268;
}

.empty-message {
    background-color: #e9ecef;
    color: #6c757d;
}

.purchases-list-container {
    margin-top: 1.5rem;
    background-color: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.purchases-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.purchases-table th,
.purchases-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.purchases-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #333;
}

.purchases-table tbody tr:hover {
  background-color: #f5f5f5;
}

.points-spent {
    font-weight: bold;
    color: #dc3545; /* Rosso per i punti spesi */
}

.status-badge {
    padding: 4px 8px;
    border-radius: 12px; /* Più arrotondato */
    font-size: 0.85em;
    font-weight: 500;
    white-space: nowrap;
}

.status-purchased {
    background-color: #fff3cd; /* Giallo chiaro */
    color: #856404; /* Giallo scuro */
    border: 1px solid #ffeeba;
}
.status-delivered {
    background-color: #d4edda; /* Verde chiaro */
    color: #155724; /* Verde scuro */
    border: 1px solid #c3e6cb;
}
.status-cancelled {
    background-color: #f8d7da; /* Rosso chiaro */
    color: #721c24; /* Rosso scuro */
    border: 1px solid #f5c6cb;
}

.go-to-shop-link {
    display: inline-block;
    margin-top: 1rem;
    padding: 0.6rem 1.2rem;
    background-color: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.2s;
}
.go-to-shop-link:hover {
    background-color: #0056b3;
}

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