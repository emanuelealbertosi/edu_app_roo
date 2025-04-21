<template>
  <div class="pathway-templates-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-4">Gestione Template Percorsi</h1> <!-- Styled heading -->
    <p class="text-gray-600 mb-6">Qui puoi visualizzare, creare e modificare i tuoi template di percorsi educativi.</p> <!-- Styled paragraph -->
    <div class="actions mb-6"> <!-- Added margin -->
      <button @click="createNewPathwayTemplate" class="btn btn-primary">Crea Nuovo Template</button>
    </div>

    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento template...</div> <!-- Styled loading -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento dei template: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="pathwayTemplates.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-gray-200 bg-white">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titolo</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="template in pathwayTemplates" :key="template.id" class="hover:bg-gray-50 transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ template.title }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ template.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ new Date(template.created_at).toLocaleDateString() }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Added space-x-2 -->
              <button @click="editPathwayTemplate(template.id)" class="btn btn-warning btn-sm">Modifica</button> <!-- Added btn-sm -->
              <button @click="deletePathwayTemplate(template.id)" class="btn btn-danger btn-sm">Elimina</button> <!-- Added btn-sm -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-gray-500"> <!-- Styled no templates -->
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
/* Stili specifici rimossi in favore di Tailwind */
</style>