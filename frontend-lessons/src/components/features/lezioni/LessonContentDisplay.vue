<template>
  <div class="lesson-content-block border border-gray-200 rounded-lg p-5 bg-white shadow-sm">
    <h4 v-if="content.title" class="text-lg font-semibold text-gray-700 mb-3 pb-2 border-b border-gray-200">{{ content.title }}</h4>

    <!-- Debug output rimosso -->

    <!-- Pulsante per aprire l'HTML in una modale -->
    <div v-if="content.content_type === 'html'">
      <button
        @click="openHtmlInModal"
        class="inline-flex items-center px-4 py-2 bg-teal-100 hover:bg-teal-200 text-teal-700 text-sm font-medium rounded-md border border-teal-200 transition duration-150 ease-in-out"
      >
        Apri Presentazione/Contenuto HTML
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </button>
    </div>

    <div v-else-if="content.content_type === 'pdf' && content.file" class="space-y-3">
      <PdfViewer :source="content.file" />
      <a :href="content.file" target="_blank" rel="noopener noreferrer" download class="inline-block px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-md border border-gray-300 transition duration-150 ease-in-out">
        Scarica PDF
      </a>
    </div>

     <div v-else-if="content.content_type === 'ppt' && content.file" class="file-placeholder border border-dashed border-gray-300 rounded-md p-6 text-center bg-gray-50 space-y-2">
        <span class="text-4xl">📄</span>
        <p class="font-medium text-gray-700">Presentazione PowerPoint</p>
         <a :href="content.file" target="_blank" rel="noopener noreferrer" download class="inline-block px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 text-sm font-medium rounded-md border border-blue-200 transition duration-150 ease-in-out">
            Scarica PPT/PPTX
        </a>
    </div>

    <div v-else-if="content.content_type === 'url' && content.url">
       <a :href="content.url" target="_blank" rel="noopener noreferrer" class="inline-flex items-center px-4 py-2 bg-indigo-100 hover:bg-indigo-200 text-indigo-700 text-sm font-medium rounded-md border border-indigo-200 transition duration-150 ease-in-out">
         Apri Link Esterno
         <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
           <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
         </svg>
       </a>
       <p class="text-xs text-gray-500 mt-1">{{ content.url }}</p>
    </div>

    <!-- Aggiunto blocco per tipo 'file' -->
    <div v-else-if="content.content_type === 'file' && content.file" class="file-placeholder border border-dashed border-gray-300 rounded-md p-6 text-center bg-gray-50 space-y-2">
       <span class="text-4xl">📎</span> <!-- Icona generica per file -->
       <p class="font-medium text-gray-700">{{ content.title || 'File Allegato' }}</p>
        <a :href="content.file" target="_blank" rel="noopener noreferrer" download class="inline-block px-3 py-1 bg-green-100 hover:bg-green-200 text-green-700 text-sm font-medium rounded-md border border-green-200 transition duration-150 ease-in-out">
           Scarica File
       </a>
       <!-- Mostra nome file se disponibile -->
       <p v-if="typeof content.file === 'string'" class="text-xs text-gray-500 mt-1">({{ content.file.split('/').pop() }})</p>
   </div>

    <div v-else class="unknown-content bg-gray-50 text-gray-500 italic p-4 rounded-md border border-gray-200">
        Contenuto non visualizzabile (Tipo: {{ content.content_type }})
    </div>

  </div>
</template>

<script setup lang="ts">
// import { computed } from 'vue'; // Non più necessario
import type { LessonContent } from '@/types/lezioni';
import PdfViewer from '../../PdfViewer.vue';

const emit = defineEmits(['open-html-modal']);

const props = defineProps<{
  content: LessonContent;
}>();

const openHtmlInModal = () => {
  if (props.content.content_type === 'html' && props.content.html_content) {
    // Decodifica l'HTML prima di inviarlo
    const txt = document.createElement("textarea");
    txt.innerHTML = props.content.html_content;
    emit('open-html-modal', txt.value); // Invia l'HTML decodificato
  }
};

// Proprietà calcolata non più necessaria

</script>

<style>
.prose h1, .prose h2, .prose h3 { margin-top: 1.2em; margin-bottom: 0.5em; font-weight: 600; }
.prose p { margin-bottom: 1em; line-height: 1.6; }
.prose a { color: #4f46e5; text-decoration: underline; } /* indigo-600 */
.prose img { max-width: 100%; height: auto; margin-top: 0.5em; margin-bottom: 0.5em; border-radius: 0.375rem; } /* rounded-md */
/* Aggiungere altri stili necessari per .prose */
</style>