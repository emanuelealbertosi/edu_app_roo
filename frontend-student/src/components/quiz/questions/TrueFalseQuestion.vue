<script setup lang="ts">
import { ref, watch, defineProps, defineEmits } from 'vue';
import type { Question, TrueFalseAnswer } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: TrueFalseAnswer | null; 
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: TrueFalseAnswer | null): void;
}>();

// State
// Usiamo stringa 'true'/'false' per il v-model dei radio, ma emettiamo booleano
const selectedValue = ref<'true' | 'false' | null>(
  props.initialAnswer === null || props.initialAnswer === undefined ? null : (props.initialAnswer.is_true ? 'true' : 'false')
);

// Watcher per emettere l'evento quando la selezione cambia
watch(selectedValue, (newVal) => {
  if (newVal !== null) {
    emit('update:answer', { is_true: newVal === 'true' });
  } else {
    emit('update:answer', null); // Emette null se nessuna opzione è selezionata
  }
});

// Watcher per resettare la selezione se la domanda cambia
watch(() => props.question.id, () => {
  selectedValue.value = null;
});

</script>

<template>
  <div class="true-false-question mt-4">
    <ul class="options-list grid grid-cols-2 gap-4"> {/* Usa grid per affiancare */}
      <li class="option-item">
        <label
          :class="[
            'block w-full p-6 md:p-8 rounded-lg shadow cursor-pointer transition-all duration-200 text-center font-bold text-xl md:text-2xl',
            'bg-blue-500 text-white', // Colore per Vero
            selectedValue === 'true' ? 'ring-4 ring-offset-2 ring-black' : 'hover:opacity-90 hover:shadow-md'
          ]"
        >
          <input
            type="radio"
            :name="'question_' + question.id"
            value="true"
            v-model="selectedValue"
            class="sr-only"
          />
          <span class="option-text">Vero</span>
        </label>
      </li>
      <li class="option-item">
        <label
          :class="[
            'block w-full p-6 md:p-8 rounded-lg shadow cursor-pointer transition-all duration-200 text-center font-bold text-xl md:text-2xl',
            'bg-red-500 text-white', // Colore per Falso
            selectedValue === 'false' ? 'ring-4 ring-offset-2 ring-black' : 'hover:opacity-90 hover:shadow-md'
          ]"
        >
          <input
            type="radio"
            :name="'question_' + question.id"
            value="false"
            v-model="selectedValue"
            class="sr-only"
          />
          <span class="option-text">Falso</span>
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