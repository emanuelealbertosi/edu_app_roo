<template>
  <div class="uda-template-list-view p-4 md:p-8">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex justify-between items-center">
      <h2 class="text-2xl font-semibold">Elenco Template UDA</h2>
      <!-- Pulsante stile adattato per contrasto -->
      <RouterLink
        :to="{ name: 'uda-template-new' }"
        class="px-4 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-100 transition duration-150 ease-in-out font-medium"
      >
        Nuovo Template UDA
      </RouterLink>
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca template per nome, descrizione, materia, argomenti..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      />
    </div>

    <div v-if="udaTemplateStore.loading" class="text-center py-10">
      <p class="text-gray-600">Caricamento template UDA...</p>
      <!-- Potrebbe essere utile un componente spinner globale -->
    </div>

    <div v-else-if="udaTemplateStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ udaTemplateStore.error }}</span>
    </div>

    <div v-else-if="filteredTemplates.length === 0" class="text-center py-10 bg-gray-50 rounded-md">
       <p class="text-gray-600 text-lg" v-if="searchQuery">Nessun template UDA trovato per "{{ searchQuery }}".</p>
       <p class="text-gray-600 text-lg" v-else>Nessun template UDA trovato.</p>
       <p class="text-gray-500 mt-2" v-if="!searchQuery">Crea il tuo primo template per iniziare a pianificare le tue unità didattiche.</p>
    </div>

    <!-- Tabella Template UDA Filtrati -->
    <div v-else class="shadow-lg overflow-hidden border-b border-gray-200 sm:rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Nome Template
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Descrizione
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Materia
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Argomenti
            </th>
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              Contenuti
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Data Creazione
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Azioni
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="template in filteredTemplates" :key="template.id" class="hover:bg-gray-50 transition-colors duration-150">
          <td class="px-6 py-4 whitespace-nowrap">
            <RouterLink :to="{ name: 'uda-template-edit', params: { id: template.id } }" class="text-sm font-medium text-indigo-700 hover:text-indigo-900">
              {{ template.name }}
            </RouterLink>
          </td>
          <td class="px-6 py-4 text-sm text-gray-500">
            <span :title="template.description" v-if="template.description && template.description.length > 20">
              {{ template.description.substring(0, 20) + '...' }}
            </span>
            <span v-else>{{ template.description || 'Nessuna descrizione.' }}</span>
          </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
              {{ template.subject_details?.name || '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              <span v-if="template.topics_details && template.topics_details.length">
                {{ template.topics_details.map(t => t.name).join(', ') }}
              </span>
              <span v-else>-</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-center">
              {{ template.contents?.length || 0 }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDate(template.created_at) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <RouterLink
                :to="{ name: 'uda-template-edit', params: { id: template.id } }"
                class="text-yellow-600 hover:text-yellow-900 transition duration-150 ease-in-out"
                title="Modifica Template"
              >
                <PencilIcon class="h-5 w-5 inline-block" />
              </RouterLink>
              <button
                @click="confirmDeleteTemplate(template.id)"
                class="text-red-600 hover:text-red-900 transition duration-150 ease-in-out"
                title="Elimina Template"
              >
                <TrashIcon class="h-5 w-5 inline-block" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'; // Aggiunto ref
import { RouterLink } from 'vue-router';
import { useUdaTemplateStore } from '@/stores/udaTemplateStore';
import { useUiStore } from '@/stores/ui';
import { PlusCircleIcon, PencilIcon, TrashIcon } from '@heroicons/vue/24/outline';
import type { UDATemplate } from '@/types/uda';
import { useSubjectStore } from '@/stores/subjectStore'; // Importa lo store delle materie
import { useTopicStore } from '@/stores/topicStore';   // Importa lo store degli argomenti

// TODO: Verificare se questi tipi esistono già e sono più completi in @/types/subject o @/types/topic
interface Subject {
  id: number;
  name: string;
}
interface Topic {
  id: number;
  name: string;
  subject_id?: number; // o subject: number
}

const udaTemplateStore = useUdaTemplateStore();
const uiStore = useUiStore();
const subjectStore = useSubjectStore();
const topicStore = useTopicStore();
const searchQuery = ref('');

const templates = computed(() => {
  return udaTemplateStore.udaTemplates.map(template => {
    const subjectDetails = template.subject ? subjectStore.getSubjectById(template.subject) : null;
    const topicsDetails = template.topics?.map(topicId => topicStore.getTopicById(topicId)).filter(Boolean) as Topic[] | undefined;
    
    return {
      ...template,
      subject_details: subjectDetails,
      topics_details: topicsDetails,
    };
  });
});

const filteredTemplates = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  if (!query) {
    return templates.value;
  }
  return templates.value.filter(template => {
    const name = template.name.toLowerCase();
    const description = template.description?.toLowerCase() || '';
    const subjectName = template.subject_details?.name.toLowerCase() || '';
    const topicNames = template.topics_details?.map(t => t.name.toLowerCase()).join(' ') || '';

    return name.includes(query) ||
           description.includes(query) ||
           subjectName.includes(query) ||
           topicNames.includes(query);
  });
});


onMounted(async () => {
  // Carica in parallelo per efficienza
  await Promise.all([
    udaTemplateStore.fetchUdaTemplates(),
    subjectStore.fetchSubjects(),
    topicStore.fetchTopics()      // Modificato da fetchAllTopics a fetchTopics
  ]);
});

const confirmDeleteTemplate = async (templateId: number) => {
  // TODO: Sostituire con una modale di conferma da uiStore
  const confirmed = window.confirm(`Sei sicuro di voler eliminare questo template UDA (ID: ${templateId})? L'azione non è reversibile.`);
  if (confirmed) {
    uiStore.addNotification({ message: `Eliminazione template ID: ${templateId} in corso...`, type: 'info' });
    try {
      await udaTemplateStore.deleteUdaTemplate(templateId);
      uiStore.addNotification({ message: 'Template UDA eliminato con successo.', type: 'success', duration: 3000 });
      // La lista si aggiornerà automaticamente perché `templates` è una computed property basata sullo store
    } catch (error) {
      console.error(`Errore durante l'eliminazione del template UDA ID ${templateId}:`, error);
      uiStore.addNotification({ message: `Errore durante l'eliminazione: ${(error as Error).message}`, type: 'error' });
    }
  } else {
    uiStore.addNotification({ message: 'Eliminazione template annullata.', type: 'info', duration: 2000 });
  }
};

const formatDate = (dateString?: string) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    year: 'numeric', month: 'long', day: 'numeric'
  });
};

</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #c5c5c5;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #a5a5a5;
}
</style>