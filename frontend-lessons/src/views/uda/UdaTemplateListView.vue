<template>
  <div class="uda-template-list-view p-4 md:p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-gray-800">Elenco Template UDA</h1>
      <RouterLink
        :to="{ name: 'uda-template-new' }"
        class="bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
      >
        <PlusCircleIcon class="h-5 w-5 mr-2" />
        Nuovo Template UDA
      </RouterLink>
    </div>

    <div v-if="udaTemplateStore.loading" class="text-center py-10">
      <p class="text-gray-600">Caricamento template UDA...</p>
      <!-- Potrebbe essere utile un componente spinner globale -->
    </div>

    <div v-else-if="udaTemplateStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ udaTemplateStore.error }}</span>
    </div>

    <div v-else-if="templates.length === 0" class="text-center py-10 bg-gray-50 rounded-md">
      <p class="text-gray-600 text-lg">Nessun template UDA trovato.</p>
      <p class="text-gray-500 mt-2">Crea il tuo primo template per iniziare a pianificare le tue unità didattiche.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="template in templates"
        :key="template.id"
        class="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-lg transition-shadow duration-200 overflow-hidden flex flex-col"
      >
        <div class="p-5 flex-grow">
          <h2 class="text-xl font-semibold text-indigo-700 mb-2">{{ template.name }}</h2>
          <p class="text-gray-600 text-sm mb-3 h-20 overflow-y-auto custom-scrollbar">
            {{ template.description || 'Nessuna descrizione.' }}
          </p>
          <div class="text-xs text-gray-500">
            <p v-if="template.subject_details">Materia: <span class="font-medium text-gray-700">{{ template.subject_details.name }}</span></p>
            <p v-if="template.topics_details && template.topics_details.length">
              Argomenti:
              <span
                v-for="(topic, index) in template.topics_details"
                :key="topic.id"
                class="inline-block bg-gray-200 rounded-full px-2 py-0.5 text-xs font-semibold text-gray-700 mr-1 mb-1"
              >
                {{ topic.name }}
              </span>
            </p>
            <p>Contenuti: {{ template.contents?.length || 0 }}</p>
            <p>Creato il: {{ formatDate(template.created_at) }}</p>
          </div>
        </div>
        <div class="bg-gray-50 p-4 border-t border-gray-200 flex justify-end space-x-2">
          <RouterLink
            :to="{ name: 'uda-template-edit', params: { id: template.id } }"
            class="text-sm bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-1.5 px-3 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
            title="Modifica Template"
          >
            <PencilIcon class="h-4 w-4 mr-1" /> Modifica
          </RouterLink>
          <button
            @click="confirmDeleteTemplate(template.id)"
            class="text-sm bg-red-500 hover:bg-red-600 text-white font-medium py-1.5 px-3 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
            title="Elimina Template"
          >
            <TrashIcon class="h-4 w-4 mr-1" /> Elimina
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
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