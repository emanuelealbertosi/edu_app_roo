<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" @click.self="$emit('close')">
    <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
      <h3 class="text-xl font-semibold mb-4">Crea Nuovo Gruppo per Template</h3>
      
      <div class="mb-4">
        <label for="group-name" class="block text-sm font-medium text-gray-700">Nome del Gruppo</label>
        <input 
          type="text" 
          id="group-name" 
          v-model="groupName"
          class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
          placeholder="Es. Template di Storia - Classe 3B"
          @keyup.enter="handleSave"
        />
        <p v-if="errorMessage" class="text-sm text-error mt-1">{{ errorMessage }}</p>
      </div>

      <div class="flex justify-end space-x-3">
        <BaseButton variant="secondary" @click="$emit('close')">Annulla</BaseButton>
        <BaseButton @click="handleSave" :disabled="!groupName.trim()">Salva Gruppo</BaseButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import BaseButton from '@/components/common/BaseButton.vue';

const props = defineProps<{
  show: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', name: string): void;
}>();

const groupName = ref('');
const errorMessage = ref('');

watch(() => props.show, (newVal) => {
  if (newVal) {
    groupName.value = '';
    errorMessage.value = '';
  }
});

const handleSave = () => {
  if (groupName.value.trim()) {
    // Qui in futuro si potrebbe aggiungere validazione
    emit('save', groupName.value.trim());
  } else {
    errorMessage.value = 'Il nome del gruppo non può essere vuoto.';
  }
};
</script>