<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, computed } from 'vue';
import type { Question, MultipleChoiceMultipleAnswer } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: MultipleChoiceMultipleAnswer | null; 
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: MultipleChoiceMultipleAnswer | null): void;
}>();

// State
// Usiamo un oggetto per tenere traccia dello stato selezionato di ogni opzione
const selectedOptions = ref<Record<number, boolean>>({});

// Inizializza lo stato basato sulla risposta iniziale (se presente)
function initializeSelection() {
  const initialSelection: Record<number, boolean> = {};
  props.question.answer_options?.forEach(option => {
    initialSelection[option.id] = props.initialAnswer?.answer_option_ids?.includes(option.id) ?? false;
  });
  selectedOptions.value = initialSelection;
}

// Calcola l'array di ID selezionati da emettere
const selectedOptionIds = computed(() => {
  return Object.entries(selectedOptions.value)
    .filter(([, isSelected]) => isSelected)
    .map(([id]) => Number(id));
});

// Watcher per emettere l'evento quando la selezione cambia
watch(selectedOptionIds, (newVal) => {
  if (newVal.length > 0) {
    emit('update:answer', { answer_option_ids: newVal });
  } else {
    emit('update:answer', null); // Emette null se nessuna opzione è selezionata
  }
}, { deep: true }); // Deep watch necessario per l'oggetto selectedOptions

// Watcher per resettare la selezione se la domanda cambia
watch(() => props.question.id, () => {
  initializeSelection(); // Re-inizializza quando la domanda cambia
}, { immediate: true }); // Esegui subito all'inizio

// Funzione helper per assegnare colori stile Kahoot (riutilizzata)
const getOptionBgColor = (index: number): string => {
  const colors = [
    'bg-red-500 text-white',
    'bg-blue-500 text-white',
    'bg-yellow-400 text-gray-900',
    'bg-green-500 text-white',
  ];
  return colors[index % colors.length];
};

</script>

<template>
  <div class="multiple-choice-multiple-question mt-4">
    <p class="instruction text-sm text-gray-600 mb-3 text-center md:text-left">(Seleziona tutte le risposte corrette)</p>
    <ul class="options-list grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
      <li v-for="(option, index) in question.answer_options" :key="option.id" class="option-item">
        <label
          :class="[
            'block w-full p-4 md:p-6 rounded-lg shadow cursor-pointer transition-all duration-200 text-center font-semibold text-lg md:text-xl relative', // Aggiunto relative per l'icona
            getOptionBgColor(index),
            selectedOptions[option.id] ? 'ring-4 ring-offset-2 ring-black shadow-inner' : 'hover:opacity-90 hover:shadow-md' // Stile selezionato/hover
          ]"
        >
          {/* Icona di spunta per indicare la selezione */}
          <span v-if="selectedOptions[option.id]" class="absolute top-2 right-2 text-white bg-black bg-opacity-50 rounded-full p-1">
             <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
             </svg>
          </span>
          <input
            type="checkbox"
            :value="option.id"
            v-model="selectedOptions[option.id]"
            class="sr-only"
          />
          <span class="option-text">{{ option.text }}</span>
        </label>
      </li>
    </ul>
  </div>
</template>

<style scoped>
/* Stili specifici se necessari */
.option-item label {
  user-select: none;
}
</style>