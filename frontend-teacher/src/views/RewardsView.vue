<template>
  <div class="rewards-view">
    <h1>Gestione Ricompense</h1>
    <p>Qui puoi visualizzare, creare e modificare le ricompense disponibili per gli studenti.</p>
    <div class="actions">
      <button @click="createNewReward">Crea Nuova Ricompensa</button>
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
            <th>Disponibilità</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="reward in rewards" :key="reward.id">
            <td>{{ reward.name }}</td>
            <td>{{ reward.description || '-' }}</td>
            <td>{{ reward.cost }}</td>
            <td>{{ reward.is_active ? 'Attiva' : 'Non Attiva' }}</td>
            <td>
              <button @click="editReward(reward.id)">Modifica</button>
              <button @click="deleteReward(reward.id)" class="delete">Elimina</button>
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
.actions button {
  padding: 8px 15px;
  cursor: pointer;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
}
.actions button:hover {
  background-color: #45a049;
}
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
td button {
  margin-right: 5px;
  padding: 3px 8px;
  cursor: pointer;
}
td button.delete {
    background-color: #f44336;
    color: white;
    border: none;
}
td button.delete:hover {
    background-color: #d32f2f;
}
</style>