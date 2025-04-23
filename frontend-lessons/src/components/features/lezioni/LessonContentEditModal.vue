<template>
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex justify-center items-center z-50" @click.self="close">
    <div class="relative mx-auto p-6 border w-full max-w-2xl shadow-lg rounded-md bg-white">
      <h3 class="text-xl font-semibold text-center mb-4 text-gray-700">Modifica Contenuto Lezione</h3>
      <form @submit.prevent="submitForm" v-if="editableContent" class="space-y-4">

        <div class="bg-gray-100 p-3 rounded-md">
          <label class="block text-sm font-medium text-gray-500">Tipo Contenuto:</label>
          <span class="text-lg font-semibold text-gray-800">{{ editableContent.content_type.toUpperCase() }}</span>
        </div>

        <div>
          <label for="edit-content-title" class="block text-sm font-medium text-gray-600 mb-1">Titolo (opzionale):</label>
          <input type="text" id="edit-content-title" v-model="editableContent.title" placeholder="Es: Introduzione al Capitolo" class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
        </div>

        <!-- Usa Textarea per HTML grezzo -->
        <div v-if="editableContent.content_type === 'html'">
           <label for="edit-content-html" class="block text-sm font-medium text-gray-600 mb-1">Contenuto HTML (incluso codice &lt;script&gt;):</label>
           <textarea
             id="edit-content-html"
             v-model="editableContent.html_content"
             rows="15"
             class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
             placeholder="Inserisci qui il tuo codice HTML..."
           ></textarea>
           <small class="text-xs text-gray-500 mt-1">Attenzione: Il codice inserito verrà visualizzato senza sanitizzazione.</small>
        </div>
        <!-- Mantieni input file per PDF/PPT -->
        <div v-if="editableContent.content_type === 'pdf' || editableContent.content_type === 'ppt'">
            <label for="edit-content-file" class="block text-sm font-medium text-gray-600 mb-1">Sostituisci File (opzionale):</label>
            <input type="file" id="edit-content-file" @change="handleFileChange" :accept="fileAcceptType" class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100">
            <div v-if="currentFileName" class="mt-2 text-sm text-gray-500 italic">Attuale: {{ currentFileName }}</div>
            <div v-if="selectedFile" class="mt-1 text-sm text-indigo-600 italic">Nuovo: {{ selectedFile.name }}</div>
            <small class="text-xs text-gray-500 mt-1">Se non selezioni un nuovo file, quello attuale verrà mantenuto.</small>
        </div>
         <div v-if="editableContent.content_type === 'url'">
            <label for="edit-content-url" class="block text-sm font-medium text-gray-600 mb-1">URL Esterno:</label>
            <input type="url" id="edit-content-url" v-model="editableContent.url" placeholder="https://esempio.com/risorsa" required class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
        </div>

         <div>
            <label for="edit-content-order" class="block text-sm font-medium text-gray-600 mb-1">Ordine:</label>
            <input type="number" id="edit-content-order" v-model.number="editableContent.order" min="0" class="w-20 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            <small class="text-xs text-gray-500 ml-2">Numero per ordinare i contenuti (0, 1, 2...).</small>
         </div>


        <div v-if="formError" class="text-red-500 text-sm mt-2">{{ formError }}</div>

        <div class="pt-4 flex justify-end space-x-3 border-t border-gray-200 mt-6">
          <button type="button" @click="close" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition duration-150 ease-in-out">Annulla</button>
          <button type="submit" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition duration-150 ease-in-out" :disabled="isSaving">
            {{ isSaving ? 'Salvataggio...' : 'Salva Modifiche' }}
          </button>
        </div>
      </form>
       <div v-else class="text-center text-gray-500 py-10">Caricamento dati contenuto...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
// Importa il tipo LessonContent
import type { LessonContent } from '@/types/lezioni';
// Importa l'editor WYSIWYG con percorso relativo - NON PIU' USATO PER HTML
// import WysiwygEditor from '../../WysiwygEditor.vue';

const props = defineProps<{
  content: LessonContent | null;
  lessonId: number;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', contentId: number, data: FormData | object): void;
}>();

const editableContent = ref<LessonContent | null>(null);
const formError = ref<string | null>(null);
const isSaving = ref(false);
const currentFileName = ref<string | null>(null);
const selectedFile = ref<File | null>(null);

watch(() => props.content, (newContent) => {
  if (newContent) {
    editableContent.value = { ...newContent };
    selectedFile.value = null;
    if ((newContent.content_type === 'pdf' || newContent.content_type === 'ppt') && typeof newContent.file === 'string') {
        currentFileName.value = newContent.file.split('/').pop() || null;
    } else {
        currentFileName.value = null;
    }
  } else {
    editableContent.value = null;
  }
  formError.value = null;
}, { immediate: true, deep: true });


const fileAcceptType = computed(() => {
    if (!editableContent.value) return '*/*';
    if (editableContent.value.content_type === 'pdf') return '.pdf,application/pdf';
    if (editableContent.value.content_type === 'ppt') return '.ppt,.pptx,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation';
    return '*/*';
});

const handleFileChange = (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files[0]) {
        selectedFile.value = target.files[0]; // Aggiorna solo lo stato separato
    } else {
        selectedFile.value = null;
    }
};


const close = () => {
  emit('close');
};

const submitForm = () => {
  if (!editableContent.value) return;
  formError.value = null;

  if (editableContent.value.content_type === 'url' && !editableContent.value.url) {
      formError.value = "L'URL è obbligatorio per il tipo Link Esterno."; return;
  }
   if (editableContent.value.content_type === 'html' && !editableContent.value.html_content) {
      formError.value = "Il contenuto HTML è obbligatorio."; return;
  }
   if (editableContent.value.order === null || editableContent.value.order < 0) {
       formError.value = "L'ordine deve essere un numero non negativo."; return;
   }


  isSaving.value = true;

  let dataToSend: FormData | object;
  const needsFormData = selectedFile.value instanceof File;

  if (needsFormData) {
      const formData = new FormData();
      dataToSend = formData;
      if (editableContent.value.title) formData.append('title', editableContent.value.title);
      formData.append('order', editableContent.value.order.toString());
      if (selectedFile.value) {
          formData.append('file', selectedFile.value);
      }
  } else {
      dataToSend = {
          title: editableContent.value.title || undefined,
          order: editableContent.value.order,
          html_content: editableContent.value.content_type === 'html' ? editableContent.value.html_content : undefined,
          url: editableContent.value.content_type === 'url' ? editableContent.value.url : undefined,
      };
  }


  emit('save', editableContent.value.id, dataToSend);
};

</script>
