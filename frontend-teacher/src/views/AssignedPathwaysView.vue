<template>
  <div class="assigned-pathways-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Percorsi Assegnati (Istanze)</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="opacity-90">Qui puoi visualizzare le istanze concrete dei percorsi che hai assegnato.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento percorsi assegnati...</div> <!-- Stile loading aggiornato -->
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert"> <!-- Stile errore aggiornato -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento dei percorsi assegnati: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="assignedPathways.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white"> <!-- Stile tabella aggiornato -->
        <thead class="bg-neutral-lightest"> <!-- Stile thead aggiornato -->
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Titolo Istanza</th> <!-- Stile th aggiornato -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Template Sorgente</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT"> <!-- Stile tbody aggiornato -->
          <tr v-for="pathway in assignedPathways" :key="pathway.id" class="hover:bg-neutral-lightest transition-colors duration-150"> <!-- Stile tr aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ pathway.title }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ pathway.description || '-' }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ pathway.source_template ? `ID: ${pathway.source_template}` : 'N/D' }}</td> <!-- Simplified display, stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ new Date(pathway.created_at).toLocaleDateString() }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Spazio ok -->
              <BaseButton variant="info" size="sm" @click="viewPathwayDetails(pathway.id)">Dettagli</BaseButton> <!-- Usa BaseButton -->
              <!-- <BaseButton variant="danger" size="sm" @click="deleteAssignedPathway(pathway.id)">Elimina Istanza</BaseButton> -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark"> <!-- Stile no pathways aggiornato -->
      Nessun percorso assegnato trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa API per fetchare le istanze Pathway concrete
import { fetchPathways, deletePathwayApi, type Pathway } from '@/api/pathways'; // Assicurati che Pathway includa source_template
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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