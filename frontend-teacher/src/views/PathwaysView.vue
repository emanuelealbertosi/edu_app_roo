<template>
  <div class="container mx-auto p-4">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Gestione Percorsi Educativi</h1>
      <BaseButton @click="createNewPathway" variant="primary" class="flex items-center">
        <PlusCircleIcon class="h-5 w-5 mr-2" />
        Crea Nuovo Percorso
      </BaseButton>
    </div>
    <p class="text-gray-600 mb-6">Qui puoi visualizzare, creare e modificare i tuoi percorsi educativi.</p>

    <GlobalLoadingIndicator :is-loading="isLoading" />

    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-if="!isLoading && pathways.length > 0" class="overflow-x-auto bg-white shadow-md rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titolo</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="pathway in pathways" :key="pathway.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ pathway.title }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ pathway.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ new Date(pathway.created_at).toLocaleDateString('it-IT') }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <BaseButton @click="editPathway(pathway.id)" variant="secondary" size="sm" class="p-2" title="Modifica Percorso">
                <PencilIcon class="h-5 w-5" />
              </BaseButton>
              <BaseButton @click="deletePathway(pathway.id)" variant="danger" size="sm" class="p-2" title="Elimina Percorso">
                <TrashIcon class="h-5 w-5" />
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!isLoading && pathways.length === 0 && !error" class="text-center text-gray-500 mt-6 py-10 bg-gray-50 rounded-md">
      Nessun percorso trovato. Creane uno nuovo!
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { fetchPathways, deletePathwayApi, type Pathway } from '@/api/pathways'; // Importa API e tipo
import BaseButton from '@/components/common/BaseButton.vue';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import { PlusCircleIcon, PencilIcon, TrashIcon } from '@heroicons/vue/24/outline';

const router = useRouter();
const pathways = ref<Pathway[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);

const loadPathways = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    pathways.value = await fetchPathways(); // Usa API reale
  } catch (err: any) {
    console.error("Errore nel recupero dei percorsi:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadPathways);

const createNewPathway = () => {
  router.push({ name: 'pathway-new' }); // Naviga alla rotta di creazione
};

const editPathway = (id: number) => {
  router.push({ name: 'pathway-edit', params: { id: id.toString() } }); // Naviga alla rotta di modifica
};

const deletePathway = async (id: number) => {
  if (!confirm(`Sei sicuro di voler eliminare il percorso con ID ${id}?`)) {
    return;
  }
  try {
    await deletePathwayApi(id); // Usa API reale
    // Aggiorna lista locale
    pathways.value = pathways.value.filter(p => p.id !== id);
    console.log(`Percorso ${id} eliminato.`); // Log di successo
  } catch (err: any) {
    console.error(`Errore eliminazione percorso ${id}:`, err);
    error.value = `Errore eliminazione percorso: ${err.message || 'Errore sconosciuto'}`;
  }
};
</script>

<style scoped>
/* Gli stili specifici sono stati rimossi per fare affidamento su Tailwind CSS e BaseButton */
</style>