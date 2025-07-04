<template>
  <div class="save-status-indicator text-sm flex items-center">
    <template v-if="status === 'SAVING'">
      <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span class="text-gray-600">Salvataggio...</span>
    </template>
    <template v-else-if="status === 'SAVED'">
      <CheckCircleIcon class="h-5 w-5 text-green-500 mr-1" />
      <span class="text-gray-600">Tutto salvato</span>
    </template>
    <template v-else-if="status === 'DIRTY'">
      <span class="text-gray-600 italic">Modifiche non salvate</span>
    </template>
    <template v-else-if="status === 'ERROR'">
      <ExclamationCircleIcon class="h-5 w-5 text-red-500 mr-1" />
      <span class="text-red-600">Errore salvataggio</span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/vue/24/solid';

type SaveStatus = 'IDLE' | 'DIRTY' | 'SAVING' | 'SAVED' | 'ERROR';

interface Props {
  status: SaveStatus;
}

defineProps<Props>();
</script>