<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, computed } from 'vue';
import type { Question, MultipleChoiceMultipleAnswer, StudentAnswerResult } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: MultipleChoiceMultipleAnswer | null;
  displayMode?: 'input' | 'result';
  studentAnswerData?: StudentAnswerResult;
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: MultipleChoiceMultipleAnswer | null): void;
}>();

// State
const selectedOptions = ref<Record<number, boolean>>({});
const currentDisplayMode = computed(() => props.displayMode || 'input');

// Inizializza lo stato basato sulla risposta iniziale (solo in modalità input)
function initializeSelection() {
  if (currentDisplayMode.value === 'input') {
    const initialSelection: Record<number, boolean> = {};
    props.question.answer_options?.forEach(option => {
      initialSelection[option.id] = props.initialAnswer?.answer_option_ids?.includes(option.id) ?? false;
    });
    selectedOptions.value = initialSelection;
  }
}

// Calcola l'array di ID selezionati da emettere (solo in modalità input)
const selectedOptionIdsForEmit = computed(() => {
  if (currentDisplayMode.value === 'input') {
    return Object.entries(selectedOptions.value)
      .filter(([, isSelected]) => isSelected)
      .map(([id]) => Number(id));
  }
  return [];
});

// Watcher per emettere l'evento quando la selezione cambia (solo in modalità input)
watch(selectedOptionIdsForEmit, (newVal) => {
  if (currentDisplayMode.value === 'input') {
    if (newVal.length > 0) {
      emit('update:answer', { answer_option_ids: newVal });
    } else {
      emit('update:answer', null);
    }
  }
}, { deep: true });

// Watcher per resettare la selezione se la domanda cambia (solo in modalità input)
watch(() => props.question.id, () => {
  if (currentDisplayMode.value === 'input') {
    initializeSelection();
  }
}, { immediate: true });


// Computed properties per la modalità risultato
const studentSelectedOptionIdsArray = computed(() => {
  if (currentDisplayMode.value === 'result' && props.studentAnswerData?.selected_answers && Array.isArray((props.studentAnswerData.selected_answers as any).answer_option_ids)) {
    return (props.studentAnswerData.selected_answers as any).answer_option_ids as number[];
  }
  return [];
});

const correctOptionIdsArray = computed(() => {
  if (currentDisplayMode.value === 'result' || currentDisplayMode.value === 'input') { // Utile anche in input per riferimento futuro, ma principalmente per result
    return props.question.answer_options?.filter(opt => opt.is_correct).map(opt => opt.id) ?? [];
  }
  return [];
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
  <div class="multiple-choice-multiple-question mt-4">
    <!-- Modalità Input -->
    <div v-if="currentDisplayMode === 'input'">
      <p class="instruction text-sm text-gray-600 dark:text-gray-400 mb-3 text-center md:text-left">(Seleziona tutte le risposte corrette)</p>
      <ul class="options-list grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
        <li v-for="(option, index) in question.answer_options" :key="option.id" class="option-item">
          <label
            :class="[
              'block w-full p-4 md:p-6 rounded-lg shadow cursor-pointer transition-all duration-200 text-center font-semibold text-lg md:text-xl relative',
              getOptionBgColorInput(index),
              selectedOptions[option.id] ? 'ring-4 ring-offset-2 ring-black dark:ring-gray-400 shadow-inner' : 'hover:opacity-90 hover:shadow-md'
            ]"
          >
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
              :aria-label="option.text"
            />
            <span class="option-text">{{ option.text }}</span>
          </label>
        </li>
      </ul>
    </div>

    <!-- Modalità Risultato -->
    <div v-else-if="currentDisplayMode === 'result'" class="result-display space-y-4">
      <p class="instruction text-sm text-gray-600 dark:text-gray-400 mb-3 text-center md:text-left">(Risultato domanda multipla)</p>
      <ul class="options-list grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
        <li v-for="option in question.answer_options" :key="`result-${option.id}`" class="option-item-result">
          <div
            :class="[
              'block w-full p-4 md:p-6 rounded-lg shadow text-center font-semibold text-lg md:text-xl relative',
              // Logica degli stili per la modalità risultato:
              // Opzione corretta e selezionata dallo studente
              (correctOptionIdsArray.includes(option.id) && studentSelectedOptionIdsArray.includes(option.id)) ? 'bg-green-200 border-2 border-green-500 text-green-800 dark:bg-green-700 dark:border-green-400 dark:text-green-100' : '',
              // Opzione corretta ma NON selezionata dallo studente
              (correctOptionIdsArray.includes(option.id) && !studentSelectedOptionIdsArray.includes(option.id)) ? 'bg-green-100 border-2 border-green-300 text-green-700 dark:bg-green-600 dark:border-green-500 dark:text-green-200 opacity-75' : '',
              // Opzione sbagliata ma selezionata dallo studente
              (!correctOptionIdsArray.includes(option.id) && studentSelectedOptionIdsArray.includes(option.id)) ? 'bg-red-200 border-2 border-red-500 text-red-800 dark:bg-red-700 dark:border-red-400 dark:text-red-100' : '',
              // Opzione sbagliata e NON selezionata (stile neutro/default)
              (!correctOptionIdsArray.includes(option.id) && !studentSelectedOptionIdsArray.includes(option.id)) ? 'bg-gray-100 dark:bg-gray-700 dark:text-gray-300' : ''
            ]"
          >
            <span class="option-text">{{ option.text }}</span>
            
            <div class="absolute top-1 right-1 text-xs">
              <span v-if="correctOptionIdsArray.includes(option.id) && studentSelectedOptionIdsArray.includes(option.id)"
                    class="inline-block bg-green-500 text-white p-1 rounded-full leading-none" title="Corretta e da te selezionata">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
              </span>
              <span v-if="correctOptionIdsArray.includes(option.id) && !studentSelectedOptionIdsArray.includes(option.id)"
                    class="inline-block bg-green-400 text-white p-1 rounded-full leading-none" title="Corretta (non selezionata)">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
              </span>
              <span v-if="!correctOptionIdsArray.includes(option.id) && studentSelectedOptionIdsArray.includes(option.id)"
                    class="inline-block bg-red-500 text-white p-1 rounded-full leading-none" title="Sbagliata e da te selezionata">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12" /></svg>
              </span>
            </div>

            <div class="mt-1 text-xs font-normal">
              <span v-if="studentSelectedOptionIdsArray.includes(option.id)" class="text-blue-600 dark:text-blue-400 block">(Tua scelta)</span>
              <span v-if="correctOptionIdsArray.includes(option.id) && !studentSelectedOptionIdsArray.includes(option.id)" class="text-green-600 dark:text-green-400 block">(Era corretta)</span>
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
          <span v-if="studentAnswerData.is_correct === true">Risposta Complessiva: Corretta! 🎉</span>
          <span v-else-if="studentAnswerData.is_correct === false">Risposta Complessiva: Sbagliata.</span>
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
/* Stili specifici se necessari */
.option-item label, .option-item-result div {
  user-select: none;
}
</style>