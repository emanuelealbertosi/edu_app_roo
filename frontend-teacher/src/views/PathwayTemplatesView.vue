<template>
  <div class="pathway-templates-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Gestione Template Percorsi</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="opacity-90">Qui puoi visualizzare, creare e modificare i tuoi template di percorsi educativi.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>
    <div class="actions mb-6"> <!-- Margin ok -->
      <BaseButton variant="primary" @click="createNewPathwayTemplate">Crea Nuovo Template</BaseButton> <!-- Usa BaseButton -->
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento template...</div> <!-- Stile loading aggiornato -->
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert"> <!-- Stile errore aggiornato -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento dei template: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="pathwayTemplates.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white"> <!-- Stile tabella aggiornato -->
        <thead class="bg-neutral-lightest"> <!-- Stile thead aggiornato -->
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Titolo</th> <!-- Stile th aggiornato -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT"> <!-- Stile tbody aggiornato -->
          <tr v-for="template in pathwayTemplates" :key="template.id" class="hover:bg-neutral-lightest transition-colors duration-150"> <!-- Stile tr aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ template.title }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ template.description || '-' }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ new Date(template.created_at).toLocaleDateString() }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Spazio ok -->
              <BaseButton variant="warning" size="sm" @click="editPathwayTemplate(template.id)">Modifica</BaseButton> <!-- Usa BaseButton -->
              <BaseButton variant="danger" size="sm" @click="deletePathwayTemplate(template.id)">Elimina</BaseButton> <!-- Usa BaseButton -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark"> <!-- Stile no templates aggiornato -->
      Nessun template di percorso trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa le nuove API e il tipo PathwayTemplate
import { fetchPathwayTemplates, deletePathwayTemplateApi, type PathwayTemplate } from '@/api/pathways';
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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