<template>
  <div class="pathway-templates-view">
    <h1>Gestione Template Percorsi</h1>
    <p>Qui puoi visualizzare, creare e modificare i tuoi template di percorsi educativi.</p>
    <div class="actions">
      <!-- Applicato stile Tailwind -->
      <button @click="createNewPathwayTemplate" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Crea Nuovo Template</button>
    </div>

    <div v-if="isLoading" class="loading">Caricamento template...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento dei template: {{ error }}
    </div>
    <div v-else-if="pathwayTemplates.length > 0" class="pathways-list">
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
          <tr v-for="template in pathwayTemplates" :key="template.id">
            <td>{{ template.title }}</td>
            <td>{{ template.description || '-' }}</td>
            <td>{{ new Date(template.created_at).toLocaleDateString() }}</td>
            <td>
              <!-- Applicato stile Tailwind -->
              <button @click="editPathwayTemplate(template.id)" class="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-1 px-2 rounded text-sm mr-2">Modifica</button>
              <!-- Applicato stile Tailwind -->
              <button @click="deletePathwayTemplate(template.id)" class="delete bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm">Elimina</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="no-pathways">
      Nessun template di percorso trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa le nuove API e il tipo PathwayTemplate
import { fetchPathwayTemplates, deletePathwayTemplateApi, type PathwayTemplate } from '@/api/pathways';

const router = useRouter();
const pathwayTemplates = ref<PathwayTemplate[]>([]); // Usa il tipo PathwayTemplate
const isLoading = ref(false);
const error = ref<string | null>(null);

const loadPathwayTemplates = async () => { // Rinominata funzione
  isLoading.value = true;
  error.value = null;
  try {
    pathwayTemplates.value = await fetchPathwayTemplates(); // Usa la nuova API
  } catch (err: any) {
    console.error("Errore nel recupero dei template di percorso:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadPathwayTemplates); // Chiama la funzione rinominata

const createNewPathwayTemplate = () => { // Rinominata funzione
  // Assicurati che esista una rotta chiamata 'pathway-template-new'
  router.push({ name: 'pathway-template-new' });
};

const editPathwayTemplate = (id: number) => { // Rinominata funzione
  // Assicurati che esista una rotta chiamata 'pathway-template-edit'
  router.push({ name: 'pathway-template-edit', params: { id: id.toString() } });
};

const deletePathwayTemplate = async (id: number) => { // Rinominata funzione
  if (!confirm(`Sei sicuro di voler eliminare il template di percorso con ID ${id}?`)) {
    return;
  }
  try {
    await deletePathwayTemplateApi(id); // Usa la nuova API
    // Aggiorna lista locale
    pathwayTemplates.value = pathwayTemplates.value.filter(p => p.id !== id);
    console.log(`Template di percorso ${id} eliminato.`); // Log aggiornato
  } catch (err: any) {
    console.error(`Errore eliminazione template percorso ${id}:`, err);
    error.value = `Errore eliminazione template percorso: ${err.message || 'Errore sconosciuto'}`;
  }
};
</script>

<style scoped>
/* Stili simili a PathwaysView */
.pathway-templates-view { /* Selettore aggiornato */
  padding: 20px;
}
.actions {
  margin-bottom: 20px;
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