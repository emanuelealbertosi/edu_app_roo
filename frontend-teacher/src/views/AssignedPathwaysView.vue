<template>
  <div class="assigned-pathways-view">
    <h1>Percorsi Assegnati (Istanze)</h1>
    <p>Qui puoi visualizzare le istanze concrete dei percorsi che hai assegnato.</p>

    <div v-if="isLoading" class="loading">Caricamento percorsi assegnati...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento dei percorsi assegnati: {{ error }}
    </div>
    <div v-else-if="assignedPathways.length > 0" class="pathways-list">
      <table>
        <thead>
          <tr>
            <th>Titolo Istanza</th>
            <th>Descrizione</th>
            <th>Template Sorgente</th>
            <th>Creato il</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pathway in assignedPathways" :key="pathway.id">
            <td>{{ pathway.title }}</td>
            <td>{{ pathway.description || '-' }}</td>
            <td>{{ pathway.source_template ? `ID: ${pathway.source_template}` : 'Nessuno (Creato manualmente)' }}</td> <!-- Assumendo che source_template sia aggiunto al serializer Pathway -->
            <td>{{ new Date(pathway.created_at).toLocaleDateString() }}</td>
            <td>
              <button @click="viewPathwayDetails(pathway.id)" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded text-sm mr-2">Dettagli</button>
              <!-- <button @click="deleteAssignedPathway(pathway.id)" class="delete bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm">Elimina Istanza</button> -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="no-pathways">
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
/* Stili simili a PathwayTemplatesView */
.assigned-pathways-view {
  padding: 20px;
}
.loading, .error-message, .no-pathways {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
.error-message {
  color: red;
  font-weight: bold;
}
.pathways-list {
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
</style>