<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, computed } from 'vue';
import type { Question, MultipleChoiceSingleAnswer, StudentAnswerResult } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: MultipleChoiceSingleAnswer | null; // Usato in modalità input
  displayMode?: 'input' | 'result'; // Per distinguere la modalità
  studentAnswerData?: StudentAnswerResult; // Dati per la modalità risultato
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: MultipleChoiceSingleAnswer | null): void;
}>();

// State
const selectedOptionId = ref<number | null>(props.initialAnswer?.answer_option_id ?? null);

const currentDisplayMode = computed(() => props.displayMode || 'input');

// Watcher per emettere l'evento quando la selezione cambia (solo in modalità input)
watch(selectedOptionId, (newVal) => {
  if (currentDisplayMode.value === 'input') {
    if (newVal !== null) {
      emit('update:answer', { answer_option_id: newVal });
    } else {
      emit('update:answer', null);
    }
  }
});

// Watcher per resettare la selezione se la domanda cambia (solo in modalità input)
watch(() => props.question.id, () => {
  if (currentDisplayMode.value === 'input') {
    selectedOptionId.value = props.initialAnswer?.answer_option_id ?? null;
  }
});

// Computed properties per la modalità risultato
const studentSelectedOptionId = computed(() => {
  if (currentDisplayMode.value === 'result' && props.studentAnswerData?.selected_answers && typeof props.studentAnswerData.selected_answers === 'object' && 'answer_option_id' in props.studentAnswerData.selected_answers) {
    return (props.studentAnswerData.selected_answers as { answer_option_id?: number }).answer_option_id ?? null;
  }
  return null;
});

const correctAnswerOptionId = computed(() => {
  if (currentDisplayMode.value === 'result') {
    const correctOption = props.question.answer_options?.find(opt => opt.is_correct);
    return correctOption?.id ?? null;
  }
  return null;
});


// Funzione helper per assegnare colori stile Kahoot (solo per modalità input)
const getOptionBgColorInput = (index: number): string => {
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
  <div class="multiple-choice-single-question mt-4">
    <!-- Modalità Input -->
    <div v-if="currentDisplayMode === 'input'">
      <ul class="options-list grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
        <li v-for="(option, index) in question.answer_options" :key="option.id" class="option-item">
          <label
            :class="[
              'block w-full p-4 md:p-6 rounded-lg shadow cursor-pointer transition-all duration-200 text-center font-semibold text-lg md:text-xl',
              getOptionBgColorInput(index),
              selectedOptionId === option.id ? 'ring-4 ring-offset-2 ring-black dark:ring-gray-400' : 'hover:opacity-90 hover:shadow-md'
            ]"
          >
            <input
              type="radio"
              :name="'question_' + question.id"
              :value="option.id"
              v-model="selectedOptionId"
              class="sr-only"
              :aria-label="option.text"
            />
            <span class="option-text">{{ option.text }}</span>
          </label>
        </li>
      </ul>
    </div>

    <!-- Modalità Risultato -->
    <div v-else-if="currentDisplayMode === 'result'" class="result-display space-y-4">
      <ul class="options-list grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
        <li v-for="option in question.answer_options" :key="`result-${option.id}`" class="option-item-result">
          <div
            :class="[
              'block w-full p-4 md:p-6 rounded-lg shadow text-center font-semibold text-lg md:text-xl',
              option.id === correctAnswerOptionId ? 'bg-green-200 border-2 border-green-500 text-green-800' : 'bg-gray-100 dark:bg-gray-700',
              option.id === studentSelectedOptionId && option.id !== correctAnswerOptionId ? 'bg-red-200 border-2 border-red-500 text-red-800' : '',
              option.id === studentSelectedOptionId && option.id === correctAnswerOptionId ? 'border-2 border-green-700' : '' // Rafforza il bordo se scelta e corretta
            ]"
          >
            <span class="option-text">{{ option.text }}</span>
            <div class="mt-2 text-sm">
              <span v-if="option.id === studentSelectedOptionId" class="font-bold text-blue-600 dark:text-blue-400 block">(La tua risposta)</span>
              <span v-if="option.id === correctAnswerOptionId && option.id !== studentSelectedOptionId" class="font-bold text-green-600 dark:text-green-400 block">(Risposta corretta)</span>
            </div>
          </div>
        </li>
      </ul>

      <div v-if="studentAnswerData" class="mt-4 p-3 rounded-lg"
        :class="{
            'bg-green-100 dark:bg-green-800 dark:text-green-200 text-green-700': studentAnswerData.is_correct === true,
            'bg-red-100 dark:bg-red-800 dark:text-red-200 text-red-700': studentAnswerData.is_correct === false,
            'bg-yellow-100 dark:bg-yellow-700 dark:text-yellow-200 text-yellow-700': studentAnswerData.is_correct === null || studentAnswerData.is_correct === undefined
        }">
        <p class="font-semibold text-center text-lg">
          <span v-if="studentAnswerData.is_correct === true">Corretta! 🎉</span>
          <span v-else-if="studentAnswerData.is_correct === false">Sbagliata.</span>
          <span v-else>In attesa di valutazione.</span>
        </p>
      </div>
       <p v-if="!studentAnswerData && currentDisplayMode === 'result'" class="text-gray-500 italic text-center">
        Informazioni sulla risposta non disponibili.
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici se necessari, altrimenti Tailwind gestisce tutto */
.option-item label {
  user-select: none;
}
.option-item-result div {
  user-select: none;
}
</style>