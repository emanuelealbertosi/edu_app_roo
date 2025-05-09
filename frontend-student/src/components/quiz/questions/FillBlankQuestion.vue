<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, computed } from 'vue';
import type { Question, FillBlankAnswer, StudentAnswerResult } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: FillBlankAnswer | null;
  displayMode?: 'input' | 'result';
  studentAnswerData?: StudentAnswerResult;
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: FillBlankAnswer | null): void;
}>();

// State
const currentDisplayMode = computed(() => props.displayMode || 'input');
const blankAnswers = ref<Record<string, string>>({}); // Per modalità input
const blankIndices = ref<string[]>([]); // Indici dei blank (es. '1', '2')

const blankRegex = /___\s*(\d+)\s*___/g;

// Parsa il testo della domanda per trovare i blank e inizializzare lo stato (solo per modalità input)
function initializeBlanks() {
  if (currentDisplayMode.value === 'input') {
    const indices: string[] = [];
    const initialInputAnswers: Record<string, string> = {};
    let match;
    blankRegex.lastIndex = 0;

    while ((match = blankRegex.exec(props.question.text)) !== null) {
      const index = match[1];
      if (!indices.includes(index)) {
        indices.push(index);
        initialInputAnswers[index] = props.initialAnswer?.answers?.[index] ?? '';
      }
    }
    blankIndices.value = indices.sort((a, b) => parseInt(a) - parseInt(b));
    blankAnswers.value = initialInputAnswers;
  } else {
    // In modalità risultato, potremmo comunque aver bisogno di blankIndices per il rendering.
    // Li calcoliamo una volta.
    const indices: string[] = [];
    let match;
    blankRegex.lastIndex = 0;
    while ((match = blankRegex.exec(props.question.text)) !== null) {
      const index = match[1];
      if (!indices.includes(index)) {
        indices.push(index);
      }
    }
    blankIndices.value = indices.sort((a, b) => parseInt(a) - parseInt(b));
    blankAnswers.value = {}; // Resetta gli input se si passa da input a result
  }
}

// Computed property per generare le parti della domanda (testo e input/display)
const questionParts = computed(() => {
  const parts: { type: 'text' | 'input'; content: string | number }[] = [];
  let lastIndex = 0;
  // Resetta il regex state
  blankRegex.lastIndex = 0; 

  let match;
  while ((match = blankRegex.exec(props.question.text)) !== null) {
    // Aggiungi il testo prima del match
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: props.question.text.substring(lastIndex, match.index) });
    }
    // Aggiungi l'input per il blank
    const blankIndex = match[1];
    parts.push({ type: 'input', content: Number(blankIndex) });
    lastIndex = match.index + match[0].length;
  }
  // Aggiungi il testo rimanente dopo l'ultimo match
  if (lastIndex < props.question.text.length) {
    parts.push({ type: 'text', content: props.question.text.substring(lastIndex) });
  }
  return parts;
});

// Watcher per emettere l'evento quando una risposta cambia (solo in modalità input)
watch(blankAnswers, (newVal) => {
  if (currentDisplayMode.value === 'input') {
    const allBlanksInitialized = blankIndices.value.every(index => Object.prototype.hasOwnProperty.call(newVal, index));
    
    if (allBlanksInitialized && blankIndices.value.length > 0) {
      const filteredAnswers: Record<string, string> = {};
      blankIndices.value.forEach(index => {
        filteredAnswers[index] = newVal[index] ?? '';
      });
      emit('update:answer', { answers: filteredAnswers });
    } else if (blankIndices.value.length === 0) { // Nessun blank trovato
        emit('update:answer', { answers: {} }); // Emette un oggetto vuoto
    }
     else {
      emit('update:answer', null); // Non tutti i blank sono pronti
    }
  }
}, { deep: true });

// Watcher per reinizializzare se la domanda o la modalità cambiano
watch([() => props.question.id, currentDisplayMode, () => props.initialAnswer], () => {
  initializeBlanks();
}, { immediate: true, deep: true });


// Computed properties per la modalità risultato
const studentProvidedAnswers = computed(() => {
  if (currentDisplayMode.value === 'result' && props.studentAnswerData?.selected_answers && typeof (props.studentAnswerData.selected_answers as any).answers === 'object') {
    return (props.studentAnswerData.selected_answers as any).answers as Record<string, string>;
  }
  return {};
});

const correctAnswersForBlanks = computed(() => {
  const correct: Record<string, string> = {};
  const correctAnswersArray = props.question.metadata?.fill_blank_correct_answers;
  if (Array.isArray(correctAnswersArray)) {
    blankIndices.value.forEach((blankIndex, arrayPos) => {
      if (arrayPos < correctAnswersArray.length) {
        correct[blankIndex] = correctAnswersArray[arrayPos];
      }
    });
  }
  return correct;
});

// Determina se la risposta per un singolo blank è corretta
function isSingleBlankCorrect(blankIndexKey: string): boolean {
  const studentAnswer = studentProvidedAnswers.value[blankIndexKey];
  const correctAnswer = correctAnswersForBlanks.value[blankIndexKey];
  if (studentAnswer === undefined || correctAnswer === undefined) {
    return false; // O considera non risposto/non specificato
  }
  // Confronto case-insensitive e trim
  return studentAnswer.trim().toLowerCase() === correctAnswer.trim().toLowerCase();
}

</script>

<template>
  <div class="fill-blank-question mt-4">
    <!-- Modalità Input -->
    <div v-if="currentDisplayMode === 'input'">
      <p class="question-text-with-blanks text-lg leading-relaxed dark:text-gray-300">
        <template v-for="(part, pIndex) in questionParts" :key="`input-${pIndex}`">
          <template v-if="part.type === 'text'">
            <span class="align-baseline">{{ part.content }}</span>
          </template>
          <template v-else-if="part.type === 'input'">
            <input
              type="text"
              class="blank-input bg-transparent border-b border-gray-500 dark:border-gray-400 focus:border-blue-500 dark:focus:border-blue-400 focus:border-b-2 outline-none px-2 py-1 mx-1 text-center text-lg align-baseline w-24 md:w-32 dark:text-gray-200"
              v-model="blankAnswers[part.content.toString()]"
              :placeholder="'#' + part.content"
              :aria-label="'Risposta per spazio ' + part.content"
            />
          </template>
        </template>
      </p>
    </div>

    <!-- Modalità Risultato -->
    <div v-else-if="currentDisplayMode === 'result'" class="result-display space-y-4">
      <p class="question-text-with-blanks text-lg leading-relaxed dark:text-gray-300">
        <template v-for="(part, pIndex) in questionParts" :key="`result-${pIndex}`">
          <template v-if="part.type === 'text'">
            <span class="align-baseline">{{ part.content }}</span>
          </template>
          <template v-else-if="part.type === 'input'">
            <span
              class="blank-result-display inline-block px-2 py-1 mx-1 text-center text-lg align-baseline border-b-2 rounded-sm min-w-[6rem] md:min-w-[8rem]"
              :class="{
                'bg-green-100 border-green-500 text-green-700 dark:bg-green-800 dark:border-green-600 dark:text-green-200': isSingleBlankCorrect(part.content.toString()),
                'bg-red-100 border-red-500 text-red-700 dark:bg-red-800 dark:border-red-600 dark:text-red-200': !isSingleBlankCorrect(part.content.toString()) && studentProvidedAnswers[part.content.toString()] !== undefined,
                'bg-gray-100 border-gray-400 text-gray-600 dark:bg-gray-700 dark:border-gray-500 dark:text-gray-400': studentProvidedAnswers[part.content.toString()] === undefined // Non risposto
              }"
            >
              <span class="student-answer font-semibold">{{ studentProvidedAnswers[part.content.toString()] || '---' }}</span>
              <span v-if="!isSingleBlankCorrect(part.content.toString()) && correctAnswersForBlanks[part.content.toString()]"
                    class="correct-answer-suggestion text-xs block opacity-80">
                (Corretta: {{ correctAnswersForBlanks[part.content.toString()] }})
              </span>
            </span>
          </template>
        </template>
      </p>

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
.blank-input {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}
.blank-result-display {
  /* Stili per i box di visualizzazione dei risultati dei blank */
}
</style>