<template>
  <div class="pathways-view">
    <h1>Gestione Percorsi Educativi</h1>
    <p>Qui puoi visualizzare, creare e modificare i tuoi percorsi educativi.</p>
    <div class="actions">
      <!-- Applicato stile Tailwind -->
      <button @click="createNewPathway" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Crea Nuovo Percorso</button>
    </div>

    <div v-if="isLoading" class="loading">Caricamento percorsi...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento dei percorsi: {{ error }}
    </div>
    <div v-else-if="pathways.length > 0" class="pathways-list">
      <table>
        <thead>
          <tr>
            <th>Titolo</th>
            <th>Descrizione</th>
            <th>Creato il</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pathway in pathways" :key="pathway.id">
            <td>{{ pathway.title }}</td>
            <td>{{ pathway.description || '-' }}</td>
            <td>{{ new Date(pathway.created_at).toLocaleDateString() }}</td>
            <td>
              <!-- Applicato stile Tailwind -->
              <button @click="editPathway(pathway.id)" class="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-1 px-2 rounded text-sm mr-2">Modifica</button>
              <!-- Applicato stile Tailwind -->
              <button @click="deletePathway(pathway.id)" class="delete bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm">Elimina</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="no-pathways">
      Nessun percorso trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { fetchPathways, deletePathwayApi, type Pathway } from '@/api/pathways'; // Importa API e tipo

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
/* Stili simili a QuizzesView */
.pathways-view {
  padding: 20px;
}
.actions {
  margin-bottom: 20px;
}
/* Rimosso stile .actions button */
/* .actions button { ... } */
/* .actions button:hover { ... } */

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
/* Rimosso stile td button */
/* td button { ... } */
/* Rimosso stile td button.delete */
/* td button.delete { ... } */
/* td button.delete:hover { ... } */
</style>