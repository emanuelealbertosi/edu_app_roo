<template>
  <div class="pathways-view">
    <h1>Gestione Percorsi Educativi</h1>
    <p>Qui puoi visualizzare, creare e modificare i tuoi percorsi educativi.</p>
    <div class="actions">
      <button @click="createNewPathway">Crea Nuovo Percorso</button>
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
              <button @click="editPathway(pathway.id)">Modifica</button>
              <button @click="deletePathway(pathway.id)" class="delete">Elimina</button>
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