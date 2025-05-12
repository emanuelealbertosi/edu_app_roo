<template>
  <div class="uda-template-form-view p-4 md:p-8">
    <h1 class="text-3xl font-bold text-gray-800 mb-6">{{ pageTitle }}</h1>

    <div v-if="loadingInitialData" class="text-center py-10">
      <p class="text-gray-600">Caricamento dati template...</p>
    </div>

    <div v-else-if="initialError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ initialError }}</span>
       <div class="mt-4">
        <RouterLink :to="{ name: 'uda-template-list' }" class="text-indigo-600 hover:text-indigo-800">
          Torna alla lista template
        </RouterLink>
      </div>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="space-y-6 bg-white shadow-lg rounded-lg p-6">
      <!-- Sezione Dati Principali del Template -->
      <div class="bg-gray-50 border border-gray-300 rounded-lg p-6 space-y-6 shadow-sm">
        <h2 class="text-xl font-semibold text-gray-700 mb-4">Dati Principali del Template</h2>
        <div>
          <label for="templateName" class="block text-sm font-medium text-gray-700 mb-1">Nome Template</label>
          <input type="text" id="templateName" v-model="formData.name" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
        </div>

        <div>
          <label for="templateDescription" class="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
          <textarea id="templateDescription" v-model="formData.description" rows="4" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2"></textarea>
        </div>

        <div>
          <label for="subject" class="block text-sm font-medium text-gray-700 mb-1">Materia (Opzionale)</label>
          <select id="subject" v-model="formData.subject" @change="handleSubjectChange" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
            <option :value="null">Nessuna materia selezionata</option>
            <option v-for="subject_item in availableSubjects" :key="subject_item.id" :value="subject_item.id">
              {{ subject_item.name }}
            </option>
          </select>
        </div>

        <div v-if="formData.subject">
          <label for="topics" class="block text-sm font-medium text-gray-700 mb-1">Argomenti (Opzionale)</label>
          <div v-if="topicStore.loading" class="text-sm text-gray-500">Caricamento argomenti...</div>
          <div v-else-if="availableTopicsForSelectedSubject.length === 0" class="text-sm text-gray-500">Nessun argomento disponibile per la materia selezionata.</div>
          <div v-else class="max-h-40 overflow-y-auto border border-gray-300 rounded-md p-2 space-y-1 bg-white">
            <div v-for="topic_item in availableTopicsForSelectedSubject" :key="topic_item.id" class="flex items-center cursor-pointer px-2">
              <input type="checkbox" :id="`topic-${topic_item.id}`" :value="topic_item.id" v-model="selectedTopicIds" class="h-5 w-5 text-indigo-600 border-gray-400 rounded focus:ring-indigo-500 focus:ring-2 focus:ring-offset-0 cursor-pointer">
              <label :for="`topic-${topic_item.id}`" class="ml-3 block text-sm text-gray-900 select-none cursor-pointer">{{ topic_item.name }}</label>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Sezione Contenuti del Template -->
      <div class="bg-gray-50 border border-gray-300 rounded-lg p-6 shadow-sm">
        <h2 class="text-2xl font-semibold text-gray-700 mb-4">Contenuti del Template</h2>
        <UdaContentEditor
          v-model="formData.contents"
          context="template"
          :uda-id="undefined"
        />
      </div>

      <div class="flex justify-end space-x-3 pt-4">
        <RouterLink :to="{ name: 'uda-template-list' }" class="border border-gray-300 hover:bg-gray-100 text-gray-700 font-medium py-2 px-4 rounded-md shadow-sm">
          Annulla
        </RouterLink>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="isSubmitting">Salvataggio...</span>
          <span v-else>{{ submitButtonText }}</span>
        </button>
      </div>
      <div v-if="submitError" class="text-red-600 mt-2 text-sm">{{ submitError }}</div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import { useUdaTemplateStore } from '@/stores/udaTemplateStore';
import { useSubjectStore } from '@/stores/subjectStore';
import { useTopicStore } from '@/stores/topicStore';
import { useUiStore } from '@/stores/ui';
import UdaContentEditor from '@/components/uda/UdaContentEditor.vue';
import type { UDATemplate, UDATemplateContent } from '@/types/uda';
import type { Subject as SubjectType } from '@/types/subject'; // Rinominato per evitare conflitto con variabile 'subject'
import type { Topic as TopicType } from '@/types/topic'; // Rinominato per evitare conflitto

interface TemplateFormData {
  name: string;
  description: string | null;
  subject: number | null;
  topics: number[];
  contents: UDATemplateContent[];
}

// Tipo per il payload da inviare all'API/store
interface UDATemplateApiPayload {
  name: string;
  description?: string | null;
  subject_id?: number | null;
  topic_ids?: number[];
  contents: Omit<UDATemplateContent, 'temp_id'>[];
}


const route = useRoute();
const router = useRouter();
const udaTemplateStore = useUdaTemplateStore();
const subjectStore = useSubjectStore();
const topicStore = useTopicStore();
const uiStore = useUiStore();

const templateId = computed(() => route.params.id ? Number(route.params.id) : null);
const isEditMode = computed(() => templateId.value !== null);

const pageTitle = computed(() => isEditMode.value ? 'Modifica Template UDA' : 'Crea Nuovo Template UDA');
const submitButtonText = computed(() => isEditMode.value ? 'Salva Modifiche' : 'Crea Template');

const loadingInitialData = ref(false);
const initialError = ref<string | null>(null);
const isSubmitting = ref(false);
const submitError = ref<string | null>(null);

const formData = ref<TemplateFormData>({
  name: '',
  description: null,
  subject: null,
  topics: [],
  contents: []
});

// Per la checkbox list degli argomenti
const selectedTopicIds = ref<number[]>([]);

const availableSubjects = computed(() => subjectStore.subjects as SubjectType[]); // Cast a SubjectType[]
const availableTopicsForSelectedSubject = computed(() => {
  if (formData.value.subject) {
    return topicStore.getTopicsForSubject(formData.value.subject) as TopicType[]; // Cast a TopicType[]
  }
  return [];
});

watch(() => formData.value.subject, (newSubjectId) => {
  selectedTopicIds.value = []; // Resetta gli argomenti selezionati quando cambia la materia
  if (newSubjectId) {
    topicStore.fetchTopicsBySubject(newSubjectId);
  }
});

// Sincronizza selectedTopicIds con formData.topics
watch(selectedTopicIds, (newVal) => {
  formData.value.topics = [...newVal];
});
watch(() => formData.value.topics, (newVal) => {
  if (JSON.stringify(newVal) !== JSON.stringify(selectedTopicIds.value)) {
    selectedTopicIds.value = [...newVal];
  }
}, { deep: true });


onMounted(async () => {
  loadingInitialData.value = true;
  initialError.value = null;
  try {
    await subjectStore.fetchSubjects();
    // Non carichiamo tutti gli argomenti subito, ma solo quelli per la materia selezionata (se in edit mode)

    if (isEditMode.value && templateId.value) {
      await udaTemplateStore.fetchUdaTemplate(templateId.value);
      const templateToEdit = udaTemplateStore.currentUdaTemplate;
      if (templateToEdit) {
        formData.value.name = templateToEdit.name;
        formData.value.description = templateToEdit.description || null;
        formData.value.subject = templateToEdit.subject || null;
        formData.value.topics = templateToEdit.topics ? [...templateToEdit.topics] : [];
        formData.value.contents = templateToEdit.contents ? JSON.parse(JSON.stringify(templateToEdit.contents)) : [];
        
        if (formData.value.subject) {
          await topicStore.fetchTopicsBySubject(formData.value.subject);
        }
        selectedTopicIds.value = [...formData.value.topics]; // Inizializza checkbox
      } else {
        initialError.value = `Template UDA con ID ${templateId.value} non trovato.`;
      }
    }
  } catch (error) {
    console.error("Errore caricamento dati form template UDA:", error);
    initialError.value = (error as Error).message || "Errore sconosciuto durante il caricamento.";
  } finally {
    loadingInitialData.value = false;
  }
});

const handleSubjectChange = () => {
  // selectedTopicIds e formData.topics vengono resettati dal watcher su formData.subject
  // La fetch degli argomenti è gestita anch'essa dal watcher
};

const handleSubmit = async () => {
  isSubmitting.value = true;
  submitError.value = null;

  // Prepara il payload, assicurandosi che subject sia null se non selezionato
  const payload: UDATemplateApiPayload = {
    name: formData.value.name,
    description: formData.value.description || undefined, // Invia undefined se null per non sovrascrivere con null se non voluto
    subject_id: formData.value.subject || undefined,
    topic_ids: formData.value.topics,
    contents: formData.value.contents.map(c => {
      const { temp_id, ...contentToSave } = c; // Rimuovi temp_id
      return contentToSave as Omit<UDATemplateContent, 'temp_id'>; // Cast per sicurezza di tipo
    })
  };
  
  // Rimuovi chiavi undefined dal payload per PATCH, così da non sovrascrivere campi non modificati con null/undefined
  // Per POST (creazione) questo non è strettamente necessario ma non fa male.
  Object.keys(payload).forEach(keyStr => {
    const key = keyStr as keyof UDATemplateApiPayload;
    if (payload[key] === undefined) {
      delete payload[key];
    }
  });


  try {
    if (isEditMode.value && templateId.value) {
      // Per l'update, passiamo solo i campi che potrebbero essere cambiati.
      // Se un campo non è nel payload, non verrà aggiornato.
      await udaTemplateStore.updateUdaTemplate(templateId.value, payload);
      uiStore.addNotification({ message: 'Template UDA aggiornato con successo!', type: 'success' });
    } else {
      await udaTemplateStore.createUdaTemplate(payload);
      uiStore.addNotification({ message: 'Template UDA creato con successo!', type: 'success' });
    }
    router.push({ name: 'uda-template-list' });
  } catch (error) {
    console.error("Errore durante il salvataggio del template UDA:", error);
    submitError.value = (error as Error).message || "Errore sconosciuto durante il salvataggio.";
    uiStore.addNotification({ message: `Errore: ${submitError.value}`, type: 'error' });
  } finally {
    isSubmitting.value = false;
  }
};

</script>

<style scoped>
/* Stili aggiuntivi se necessari */
</style>