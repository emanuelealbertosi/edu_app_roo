<template>
  <div class="rewards-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Gestione Ricompense</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="opacity-90">Qui puoi visualizzare, creare e modificare le ricompense disponibili per gli studenti.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>
    <div class="actions mb-6"> <!-- Margin ok -->
      <BaseButton variant="primary" @click="createNewReward">Crea Nuova Ricompensa</BaseButton> <!-- Usa BaseButton -->
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento ricompense...</div> <!-- Stile loading aggiornato -->
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert"> <!-- Stile errore aggiornato -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento delle ricompense: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="rewards.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white"> <!-- Stile tabella aggiornato -->
        <thead class="bg-neutral-lightest"> <!-- Stile thead aggiornato -->
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Nome</th> <!-- Stile th aggiornato -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Costo (Punti)</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Stato</th> <!-- Modificato da Disponibilità -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT"> <!-- Stile tbody aggiornato -->
          <tr v-for="reward in rewards" :key="reward.id" class="hover:bg-neutral-lightest transition-colors duration-150"> <!-- Stile tr aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ reward.name }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ reward.description || '-' }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ reward.cost_points }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <span :class="reward.is_active ? 'text-success-dark' : 'text-error'"> <!-- Colori stato aggiornati -->
                {{ reward.is_active ? 'Attiva' : 'Non Attiva' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Spazio ok -->
              <BaseButton variant="warning" size="sm" @click="editReward(reward.id)">Modifica</BaseButton> <!-- Usa BaseButton -->
              <BaseButton variant="danger" size="sm" @click="deleteReward(reward.id)">Elimina</BaseButton> <!-- Usa BaseButton -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark"> <!-- Stile no rewards aggiornato -->
      Nessuna ricompensa trovata.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { fetchRewards, deleteRewardApi, type Reward } from '@/api/rewards'; // Importa API e tipo
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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