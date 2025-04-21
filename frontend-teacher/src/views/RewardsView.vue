<template>
  <div class="rewards-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-4">Gestione Ricompense</h1> <!-- Styled heading -->
    <p class="text-gray-600 mb-6">Qui puoi visualizzare, creare e modificare le ricompense disponibili per gli studenti.</p> <!-- Styled paragraph -->
    <div class="actions mb-6"> <!-- Added margin -->
      <button @click="createNewReward" class="btn btn-primary">Crea Nuova Ricompensa</button>
    </div>

    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento ricompense...</div> <!-- Styled loading -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento delle ricompense: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="rewards.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-gray-200 bg-white">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Costo (Punti)</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stato</th> <!-- Modificato da Disponibilità -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="reward in rewards" :key="reward.id" class="hover:bg-gray-50 transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ reward.name }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ reward.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ reward.cost_points }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <span :class="reward.is_active ? 'text-green-600' : 'text-red-600'">
                {{ reward.is_active ? 'Attiva' : 'Non Attiva' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Added space-x-2 -->
              <button @click="editReward(reward.id)" class="btn btn-warning btn-sm">Modifica</button> <!-- Added btn-sm -->
              <button @click="deleteReward(reward.id)" class="btn btn-danger btn-sm">Elimina</button> <!-- Added btn-sm -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-gray-500"> <!-- Styled no rewards -->
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
/* Stili specifici rimossi in favore di Tailwind */
</style>