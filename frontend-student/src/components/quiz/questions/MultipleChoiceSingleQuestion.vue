<script setup lang="ts">
import { ref, watch, defineProps, defineEmits } from 'vue';
import type { Question, MultipleChoiceSingleAnswer } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  // Potremmo passare un valore iniziale se stiamo riprendendo un tentativo
  initialAnswer?: MultipleChoiceSingleAnswer | null; 
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: MultipleChoiceSingleAnswer | null): void;
}>();

// State
const selectedOptionId = ref<number | null>(props.initialAnswer?.answer_option_id ?? null);

// Watcher per emettere l'evento quando la selezione cambia
watch(selectedOptionId, (newVal) => {
  if (newVal !== null) {
    emit('update:answer', { answer_option_id: newVal });
  } else {
    emit('update:answer', null); // Emette null se nessuna opzione è selezionata
  }
});

// Watcher per resettare la selezione se la domanda cambia
watch(() => props.question.id, () => {
  selectedOptionId.value = null;
});

// Funzione helper per assegnare colori stile Kahoot
const getOptionBgColor = (index: number): string => {
  const colors = [
    'bg-red-500 text-white',
    'bg-blue-500 text-white',
    'bg-yellow-400 text-gray-900', // Giallo richiede testo scuro
    'bg-green-500 text-white',
  ];
  return colors[index % colors.length];
};

</script>

<template>
  <div class="multiple-choice-single-question mt-4">
    <ul class="options-list grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
      <li v-for="(option, index) in question.answer_options" :key="option.id" class="option-item">
        <label
          :class="[
            'block w-full p-4 md:p-6 rounded-lg shadow cursor-pointer transition-all duration-200 text-center font-semibold text-lg md:text-xl',
            getOptionBgColor(index), // Colore di sfondo dinamico
            selectedOptionId === option.id ? 'ring-4 ring-offset-2 ring-black' : 'hover:opacity-90 hover:shadow-md' // Stile selezionato/hover
          ]"
        >
          <input
            type="radio"
            :name="'question_' + question.id"
            :value="option.id"
            v-model="selectedOptionId"
            class="sr-only"
          />
          <span class="option-text">{{ option.text }}</span>
        </label>
      </li>
    </ul>
  </div>
</template>

<style scoped>
/* Stili specifici se necessari, altrimenti Tailwind gestisce tutto */
.option-item label {
  /* Assicura che il testo sia selezionabile */
  user-select: none;
}
</style>