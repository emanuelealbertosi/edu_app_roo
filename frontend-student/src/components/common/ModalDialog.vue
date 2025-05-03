<template>
  <!-- Overlay -->
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 z-40 flex justify-center items-center p-4"
    @click.self="$emit('close')"
  >
    <!-- Contenitore Modale -->
    <div class="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
      <!-- Header Modale -->
      <div class="flex justify-between items-center p-4 border-b border-neutral-light">
        <h3 class="text-xl font-semibold text-neutral-darkest">{{ title }}</h3>
        <button
          @click="$emit('close')"
          class="text-neutral-dark hover:text-neutral-darker p-1 rounded-full hover:bg-neutral-lightest focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Chiudi modale"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Corpo Modale (Scrollabile) -->
      <div class="p-6 overflow-y-auto flex-grow">
        <div class="prose max-w-none" v-html="contentHtml"></div>
      </div>

      <!-- Footer Modale (Opzionale, qui solo per il pulsante Chiudi) -->
      <div class="flex justify-end p-4 border-t border-neutral-light">
        <button
          @click="$emit('close')"
          class="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
        >
          Chiudi
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';

// Props per titolo, contenuto HTML e visibilità
defineProps<{
  show: boolean;
  title: string;
  contentHtml: string;
}>();

// Evento per notificare la chiusura
defineEmits<{
  (e: 'close'): void;
}>();
</script>

<style scoped>
/* Stili specifici per la modale se necessario */
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3) {
  margin-bottom: 0.5em;
  margin-top: 1em;
}

.prose :deep(ul) {
  list-style-type: disc;
  margin-left: 1.5em;
}

.prose :deep(p) {
    margin-bottom: 0.75em;
}

.prose :deep(a) {
    color: #2563eb; /* Blu Tailwind */
    text-decoration: underline;
}

.prose :deep(a:hover) {
    color: #1d4ed8; /* Blu Tailwind più scuro */
}
</style>