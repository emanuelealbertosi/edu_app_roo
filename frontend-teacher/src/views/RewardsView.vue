<template>
  <div class="rewards-view">
    <h1>Gestione Ricompense</h1>
    <p>Qui puoi visualizzare, creare e modificare le ricompense disponibili per gli studenti.</p>
    <div class="actions">
      <!-- Applicato stile Tailwind -->
      <button @click="createNewReward" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Crea Nuova Ricompensa</button>
    </div>

    <div v-if="isLoading" class="loading">Caricamento ricompense...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento delle ricompense: {{ error }}
    </div>
    <div v-else-if="rewards.length > 0" class="rewards-list">
      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Descrizione</th>
            <th>Costo (Punti)</th>
            <th>Stato</th> <!-- Modificato da Disponibilità -->
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="reward in rewards" :key="reward.id">
            <td>{{ reward.name }}</td>
            <td>{{ reward.description || '-' }}</td>
            <!-- Corretto: usa cost_points invece di cost -->
            <td>{{ reward.cost_points }}</td>
            <td>{{ reward.is_active ? 'Attiva' : 'Non Attiva' }}</td>
            <td>
              <!-- Applicato stile Tailwind -->
              <button @click="editReward(reward.id)" class="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-1 px-2 rounded text-sm mr-2">Modifica</button>
              <!-- Applicato stile Tailwind -->
              <button @click="deleteReward(reward.id)" class="delete bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm">Elimina</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="no-rewards">
      Nessuna ricompensa trovata.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { fetchRewards, deleteRewardApi, type Reward } from '@/api/rewards'; // Importa API e tipo

const router = useRouter();
const rewards = ref<Reward[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);

const loadRewards = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    rewards.value = await fetchRewards(); // Usa API reale
  } catch (err: any) {
    console.error("Errore nel recupero delle ricompense:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadRewards);

const createNewReward = () => {
  router.push({ name: 'reward-new' }); // Naviga alla rotta di creazione
};

const editReward = (id: number) => {
  router.push({ name: 'reward-edit', params: { id: id.toString() } }); // Naviga alla rotta di modifica
};

const deleteReward = async (id: number) => {
  if (!confirm(`Sei sicuro di voler eliminare la ricompensa con ID ${id}?`)) {
    return;
  }
  error.value = null; // Resetta errore precedente
  try {
    await deleteRewardApi(id); // Usa API reale
    // Aggiorna lista locale
    rewards.value = rewards.value.filter(r => r.id !== id);
    console.log(`Ricompensa ${id} eliminata.`); // Log di successo
  } catch (err: any) {
    console.error(`Errore eliminazione ricompensa ${id}:`, err);
    // Usa il messaggio specifico dall'errore lanciato da deleteRewardApi se disponibile
    error.value = `Errore eliminazione ricompensa: ${err.message || 'Errore sconosciuto'}`;
    // Attenzione: potrebbe essere un ProtectedError (409) se già acquistata
  }
};
</script>

<style scoped>
/* Stili simili a QuizzesView/PathwaysView */
.rewards-view {
  padding: 20px;
}
.actions {
  margin-bottom: 20px;
}
/* Rimosso stile .actions button */
/* .actions button { ... } */
/* .actions button:hover { ... } */

.loading, .error-message, .no-rewards {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
.error-message {
  color: red;
  font-weight: bold;
}
.rewards-list {
  margin-top: 20px;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
th {
  background-color: #f2f2f2;
}
/* Rimosso stile td button */
/* td button { ... } */
/* Rimosso stile td button.delete */
/* td button.delete { ... } */
/* td button.delete:hover { ... } */
</style>