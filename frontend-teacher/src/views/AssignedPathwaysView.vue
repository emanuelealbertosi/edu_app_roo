<template>
  <div class="assigned-pathways-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-4">Percorsi Assegnati (Istanze)</h1> <!-- Styled heading -->
    <p class="text-gray-600 mb-6">Qui puoi visualizzare le istanze concrete dei percorsi che hai assegnato.</p> <!-- Styled paragraph -->

    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento percorsi assegnati...</div> <!-- Styled loading -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento dei percorsi assegnati: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="assignedPathways.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-gray-200 bg-white">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titolo Istanza</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Template Sorgente</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="pathway in assignedPathways" :key="pathway.id" class="hover:bg-gray-50 transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ pathway.title }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ pathway.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ pathway.source_template ? `ID: ${pathway.source_template}` : 'N/D' }}</td> <!-- Simplified display -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ new Date(pathway.created_at).toLocaleDateString() }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Added space-x-2 -->
              <button @click="viewPathwayDetails(pathway.id)" class="btn btn-info btn-sm">Dettagli</button> <!-- Changed style -->
              <!-- <button @click="deleteAssignedPathway(pathway.id)" class="btn btn-danger btn-sm">Elimina Istanza</button> -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-gray-500"> <!-- Styled no pathways -->
      Nessun percorso assegnato trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa API per fetchare le istanze Pathway concrete
import { fetchPathways, deletePathwayApi, type Pathway } from '@/api/pathways'; // Assicurati che Pathway includa source_template

const assignedPathways = ref<Pathway[]>([]); // Usa il tipo Pathway
const isLoading = ref(false);
const router = useRouter();
const error = ref<string | null>(null);

onMounted(async () => {
  isLoading.value = true;
  error.value = null;
  try {
    // Usiamo fetchPathways che dovrebbe restituire le istanze create dal docente
    assignedPathways.value = await fetchPathways();
    // TODO: Verificare se PathwaySerializer nel backend include 'source_template'
  } catch (err: any) {
    console.error("Errore nel recupero dei percorsi assegnati:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
  } finally {
    isLoading.value = false;
  }
});

// Funzione per visualizzare dettagli
const viewPathwayDetails = (id: number) => {
  console.warn(`Visualizzazione dettagli per percorso istanza ${id} non implementata.`);
  // Potrebbe navigare a una vista read-only o alla vista di modifica esistente
  // router.push({ name: 'pathway-edit', params: { id: id.toString() } }); // Riutilizza form esistente?
};

// Funzione eliminazione (commentata)
/*
const deleteAssignedPathway = async (id: number) => {
  if (!confirm(`Sei sicuro di voler eliminare l'istanza percorso con ID ${id}?`)) {
    return;
  }
  try {
    await deletePathwayApi(id);
    assignedPathways.value = assignedPathways.value.filter(p => p.id !== id);
    console.log(`Istanza percorso ${id} eliminata.`);
  } catch (err: any) {
    console.error(`Errore eliminazione istanza percorso ${id}:`, err);
    error.value = `Errore eliminazione istanza percorso: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
  }
};
*/
</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
</style>