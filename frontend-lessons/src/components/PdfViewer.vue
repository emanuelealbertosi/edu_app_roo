<template>
  <div class="pdf-viewer-container border border-gray-300 rounded-md overflow-hidden">
    <vue-pdf-embed :source="source" :page="currentPage" @loaded="handleDocumentLoaded" @loading-failed="handleLoadingError" />
    <div v-if="totalPages > 1" class="pdf-controls flex justify-center items-center p-2 bg-gray-100 border-t border-gray-300">
      <button @click="prevPage" :disabled="currentPage <= 1" class="px-3 py-1 mx-1 bg-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed">
        Precedente
      </button>
      <span class="mx-2">Pagina {{ currentPage }} di {{ totalPages }}</span>
      <button @click="nextPage" :disabled="currentPage >= totalPages" class="px-3 py-1 mx-1 bg-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed">
        Successiva
      </button>
    </div>
    <div v-if="isLoading" class="loading-indicator p-4 text-center">
      Caricamento PDF...
    </div>
     <div v-if="loadError" class="error-indicator p-4 text-center text-red-600">
      Errore durante il caricamento del PDF.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import VuePdfEmbed from 'vue-pdf-embed'

const props = defineProps({
  source: {
    type: String,
    required: true,
  },
})

const currentPage = ref(1)
const totalPages = ref(0)
const isLoading = ref(true)
const loadError = ref(false)

const handleDocumentLoaded = (pdf: any) => {
  totalPages.value = pdf.numPages
  isLoading.value = false
  loadError.value = false
  console.log(`PDF caricato: ${totalPages.value} pagine`)
}

const handleLoadingError = (error: any) => {
  console.error("Errore caricamento PDF:", error);
  isLoading.value = false;
  loadError.value = true;
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

watch(() => props.source, () => {
  currentPage.value = 1
  totalPages.value = 0
  isLoading.value = true
  loadError.value = false
})
</script>

<style scoped>
.pdf-viewer-container {
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}

:deep(.vue-pdf-embed),
:deep(.vue-pdf-embed > div) {
  width: 100% !important;
  height: auto !important;
  overflow-y: auto;
  flex-grow: 1; /* Permette al visualizzatore di occupare lo spazio disponibile */
}

.pdf-controls button {
  transition: background-color 0.2s;
}
.pdf-controls button:hover:not(:disabled) {
  background-color: #cbd5e0; /* gray-400 */
}
</style>