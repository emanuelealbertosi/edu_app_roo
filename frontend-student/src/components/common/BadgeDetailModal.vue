<template>
  <div v-if="show" 
       class="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4"
       @click.self="$emit('close')">
    <div class="badge-detail-modal p-6 bg-white rounded-lg shadow-xl w-full max-w-4xl md:max-w-5xl lg:max-w-6xl transform transition-all">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold text-gray-800">{{ badge.name }}</h3>
        <button @click="$emit('close')" class="text-gray-500 hover:text-gray-700">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="media-container w-full h-auto max-h-[70vh] md:max-h-[80vh] flex justify-center items-center overflow-hidden rounded">
        <video
          v-if="badge.mediaType === 'VIDEO_MP4' && badge.fileUrl"
          :src="badge.fileUrl"
          class="max-w-full max-h-full object-contain"
          autoplay
          loop
          playsinline
          :aria-label="badge.name"
        ></video>
        <img
          v-else-if="(badge.mediaType === 'IMAGE_STATIC' || badge.mediaType === 'IMAGE_GIF') && badge.fileUrl"
          :src="badge.fileUrl"
          :alt="badge.name"
          class="max-w-full max-h-full object-contain"
        />
        <div v-else class="text-gray-500">
          Anteprima non disponibile.
        </div>
      </div>

      <p v-if="badge.description" class="mt-4 text-sm text-gray-600">{{ badge.description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
// Rimosso import BaseModal from './BaseModal.vue';
import type { Badge } from '@/api/rewards'; // Importa il tipo Badge corretto
import { onMounted, onUnmounted } from 'vue';

const props = defineProps<{
  show: boolean;
  badge: Badge; // Usa il tipo Badge importato
}>();

const emit = defineEmits(['close']);

// Gestione chiusura con tasto Esc
const handleEsc = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.show) {
    emit('close');
  }
};

onMounted(() => {
  document.addEventListener('keydown', handleEsc);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleEsc);
});

</script>

<style scoped>
.badge-detail-modal {
  /* Stili aggiuntivi se necessario */
}
.media-container video,
.media-container img {
  display: block;
  margin: auto;
}
</style>