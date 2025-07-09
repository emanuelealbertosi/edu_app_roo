<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
      <h3 class="text-xl font-semibold mb-4">{{ existingGroup ? 'Rinomina Gruppo' : 'Crea Nuovo Gruppo' }}</h3>
      
      <div class="mb-4">
        <label for="group-name" class="block text-sm font-medium text-gray-700">Nome del Gruppo</label>
        <input 
          type="text" 
          id="group-name" 
          v-model="groupName"
          class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          placeholder="Es. Corsi di Sviluppo Web"
          @keyup.enter="handleSave"
        />
      </div>

      <div class="flex justify-end space-x-3">
        <button @click="$emit('close')" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">Annulla</button>
        <button @click="handleSave" class="px-4 py-2 bg-blue-600 text-white rounded-md shadow-sm hover:bg-blue-700">Salva</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { CourseGroup } from '@/types/uda';

const props = defineProps<{
  show: boolean;
  existingGroup?: CourseGroup | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', name: string): void;
}>();

const groupName = ref('');

watch(() => props.show, (newVal) => {
  if (newVal) {
    groupName.value = props.existingGroup ? props.existingGroup.name : '';
  }
});

const handleSave = () => {
  if (groupName.value.trim()) {
    emit('save', groupName.value.trim());
  }
};
</script>