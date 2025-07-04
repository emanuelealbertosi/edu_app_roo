<template>
  <div class="rewards-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Gestione Ricompense</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="opacity-90">Qui puoi visualizzare, creare e modificare le ricompense disponibili per gli studenti.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>
    <div class="actions mb-6"> <!-- Margin ok -->
      <BaseButton variant="primary" @click="createNewReward" class="flex items-center">
        <PlusCircleIcon class="h-5 w-5 mr-2" />
        Crea Nuova Ricompensa
      </BaseButton>
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca ricompense per nome, descrizione..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-neutral-DEFAULT rounded-md shadow-sm placeholder-neutral-dark focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
      />
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento ricompense...</div>
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento delle ricompense: {{ error }}</span>
    </div>
    
    <div v-else-if="filteredAndSortedRewards.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white">
        <thead class="bg-neutral-lightest">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('name')">
              Nome
              <span v-if="sortKey === 'name'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('description')">
              Descrizione
              <span v-if="sortKey === 'description'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('cost_points')">
              Costo (Punti)
              <span v-if="sortKey === 'cost_points'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('is_active')">
              Stato
              <span v-if="sortKey === 'is_active'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('availability_type')">
              Disponibilità
              <span v-if="sortKey === 'availability_type'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT">
          <tr v-for="reward in filteredAndSortedRewards" :key="reward.id" class="hover:bg-neutral-lightest transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ reward.name }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ reward.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ reward.cost_points }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <span :class="reward.is_active ? 'text-success-dark' : 'text-error'">
                {{ reward.is_active ? 'Attiva' : 'Non Attiva' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">
               {{ reward.availability_type === 'ALL' ? 'Tutti' : 'Specifica' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
              <BaseButton variant="warning" size="sm" @click="editReward(reward.id)" class="p-2" title="Modifica Ricompensa">
                <PencilIcon class="h-5 w-5" />
              </BaseButton>
              <BaseButton
                  v-if="reward.availability_type === 'SPECIFIC'"
                  variant="info"
                  size="sm"
                  @click="openAvailabilityModal(reward)"
                  class="p-2"
                  title="Gestisci Disponibilità"
              >
                  <UsersIcon class="h-5 w-5" />
              </BaseButton>
              <BaseButton variant="danger" size="sm" @click="deleteReward(reward.id)" class="p-2" title="Elimina Ricompensa">
                <TrashIcon class="h-5 w-5" />
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark">
      <span v-if="searchQuery">Nessuna ricompensa trovata per "{{ searchQuery }}".</span>
      <span v-else>Nessuna ricompensa trovata.</span>
    </div>
  </div>

  <!-- Modale per Creare Nuova Ricompensa -->
  <RewardCreateModal
    :show="isCreateModalOpen"
    @close="closeCreateModal"
    @created="handleRewardCreated"
  />

  <!-- Modale per Gestire Disponibilità -->
  <RewardAvailabilityModal
     :show="isAvailabilityModalOpen"
     :reward="selectedRewardForAvailability"
     @close="closeAvailabilityModal"
     @updated="handleAvailabilityUpdate"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { fetchRewards, deleteRewardApi, type Reward } from '@/api/rewards';
import BaseButton from '@/components/common/BaseButton.vue';
// Importa le modali
import RewardAvailabilityModal from '@/components/features/rewards/RewardAvailabilityModal.vue';
import RewardCreateModal from '@/components/features/rewards/RewardCreateModal.vue'; // Importa la modale di creazione
import { PlusCircleIcon, PencilIcon, UsersIcon, TrashIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';

const router = useRouter();
const rewards = ref<Reward[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const searchQuery = ref('');
const sortKey = ref('name');
const sortOrder = ref('asc');

// Stato per la modale di creazione
const isCreateModalOpen = ref(false);

// Stato per la modale di disponibilità
const isAvailabilityModalOpen = ref(false);
const selectedRewardForAvailability = ref<Reward | null>(null);

const filteredAndSortedRewards = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  const filtered = query
    ? rewards.value.filter(reward => {
        const name = reward.name.toLowerCase();
        const description = reward.description ? reward.description.toLowerCase() : '';
        return name.includes(query) || description.includes(query);
      })
    : rewards.value;

  return filtered.slice().sort((a, b) => {
    let valA: any = a[sortKey.value as keyof Reward];
    let valB: any = b[sortKey.value as keyof Reward];

    if (typeof valA === 'string' && typeof valB === 'string') {
      valA = valA.toLowerCase();
      valB = valB.toLowerCase();
    }
    
    if (valA < valB) {
      return sortOrder.value === 'asc' ? -1 : 1;
    }
    if (valA > valB) {
      return sortOrder.value === 'asc' ? 1 : -1;
    }
    return 0;
  });
});

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

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

// --- Gestione Modale Creazione ---
const createNewReward = () => {
  // router.push({ name: 'reward-new' }); // Non naviga più
  isCreateModalOpen.value = true; // Apre la modale
};

const closeCreateModal = () => {
  isCreateModalOpen.value = false;
};

const handleRewardCreated = () => {
  closeCreateModal(); // Chiude la modale
  loadRewards(); // Ricarica l'elenco delle ricompense
  // Potresti aggiungere un messaggio di successo qui (es. con un toast)
};
// --- Fine Gestione Modale Creazione ---

const editReward = (id: number) => {
  router.push({ name: 'reward-edit', params: { id: id.toString() } }); // Naviga alla rotta di modifica (usa RewardFormView)
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
    error.value = `Errore eliminazione ricompensa: ${err.message || 'Errore sconosciuto'}`;
  }
};

// --- Gestione Modale Disponibilità ---
const openAvailabilityModal = (reward: Reward) => {
  selectedRewardForAvailability.value = reward;
  isAvailabilityModalOpen.value = true;
};

const closeAvailabilityModal = () => {
  isAvailabilityModalOpen.value = false;
  selectedRewardForAvailability.value = null;
};

const handleAvailabilityUpdate = () => {
   closeAvailabilityModal();
   loadRewards(); // Ricarica l'elenco per vedere l'aggiornamento (es. tipo disponibilità)
   console.log("Disponibilità aggiornata, chiusura modale.");
};
// --- Fine Gestione Modale Disponibilità ---

</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
</style>