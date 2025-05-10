<template>
  <div class="fill-blank-question question-fill-blank-display mt-4">
    <p v-if="isLoading && currentDisplayMode === 'input' && !parsedParts.length" class="text-gray-500 dark:text-gray-400">Caricamento domanda...</p>
    <div v-else-if="!question || !question.metadata" class="text-red-500 dark:text-red-400">
      Errore: Dati della domanda mancanti.
    </div>
    <div v-else-if="question.question_type === 'fill_blank' && ((currentDisplayMode === 'input' && !fillBlankMetadataForInput) || (currentDisplayMode === 'result' && !fillBlankMetadataForResults))" class="text-red-500 dark:text-red-400">
      Errore: Metadati specifici per fill-in-the-blank mancanti o malformati.
    </div>

    <!-- Modalità Input -->
    <div v-if="currentDisplayMode === 'input' && fillBlankMetadataForInput" class="prose dark:prose-invert max-w-none">
      <template v-for="(part, index) in parsedParts" :key="`input-${index}`">
        <span v-if="part.type === 'text'" v-html="part.content" class="align-baseline"></span>
        <input
          v-else-if="part.type === 'blank'"
          type="text"
          :aria-label="`Risposta per spazio vuoto ${part.order + 1}`"
          v-model="studentResponses[part.blankId]"
          @input="handleInputChange()"
          class="blank-input mx-1 px-2 py-1 border-b border-gray-500 dark:border-gray-400 focus:border-blue-500 dark:focus:border-blue-400 focus:border-b-2 outline-none text-center text-lg align-baseline w-24 md:w-32 bg-transparent dark:text-gray-200"
        />
      </template>
    </div>

    <!-- Modalità Risultato -->
    <div v-else-if="currentDisplayMode === 'result' && fillBlankMetadataForResults" class="result-display space-y-4">
      <p class="question-text-with-blanks text-lg leading-relaxed dark:text-gray-300 prose dark:prose-invert max-w-none">
        <template v-for="(part, index) in parsedParts" :key="`result-${index}`">
          <span v-if="part.type === 'text'" v-html="part.content" class="align-baseline"></span>
          <span
            v-else-if="part.type === 'blank'"
            class="blank-result-display inline-block px-2 py-1 mx-1 text-center text-lg align-baseline border-b-2 rounded-sm min-w-[6rem] md:min-w-[8rem]"
            :class="getBlankResultClass(part.blankId)"
          >
            <span class="student-answer font-semibold">{{ studentProvidedAnswersForDisplay[part.blankId] || '---' }}</span>
            <span v-if="!isStudentResponseCorrectForBlank(part.blankId) && (fillBlankMetadataForResults?.blanks.find(b => b.id === part.blankId)?.correct_answers?.length ?? 0 > 0)"
                  class="correct-answer-suggestion text-xs block opacity-80">
              (Corretta/e: {{ fillBlankMetadataForResults?.blanks.find(b => b.id === part.blankId)?.correct_answers?.join(' / ') }})
            </span>
          </span>
        </template>
      </p>

      <div v-if="props.studentAnswerData" class="mt-4 p-3 rounded-lg text-center"
        :class="{
            'bg-green-100 dark:bg-green-700 dark:text-green-100 text-green-700': props.studentAnswerData.is_correct === true,
            'bg-red-100 dark:bg-red-700 dark:text-red-100 text-red-700': props.studentAnswerData.is_correct === false,
            'bg-yellow-100 dark:bg-yellow-600 dark:text-yellow-100 text-yellow-700': props.studentAnswerData.is_correct === null || props.studentAnswerData.is_correct === undefined
        }">
        <p class="font-semibold text-lg">
          <span v-if="props.studentAnswerData.is_correct === true">Risposta Complessiva: Corretta! 🎉</span>
          <span v-else-if="props.studentAnswerData.is_correct === false">Risposta Complessiva: Sbagliata.</span>
          <span v-else>In attesa di valutazione.</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import type {
  QuestionMetadataFillBlankDisplay,
  StudentAnswerPayloadFillBlank,
  StudentResponseForBlank,
  BlankDisplayConfig,
  QuestionMetadataFillBlankWithCorrect, // Per i risultati
  BlankWithCorrectAnswer // Per i risultati
} from '@/types/education';
import type { Question as ApiQuestion, StudentAnswerResult as StudentAnswerResultApi } from '@/api/quiz';

interface Props {
  question: ApiQuestion;
  initialAnswer?: StudentAnswerPayloadFillBlank | null; // Per modalità input
  displayMode?: 'input' | 'result'; // 'input' per svolgimento, 'result' per visualizzazione risultati
  studentAnswerData?: StudentAnswerResultApi | null; // Dati della risposta dello studente per modalità 'result'
}

const props = withDefaults(defineProps<Props>(), {
  displayMode: 'input',
});

const emit = defineEmits<{
  (e: 'update:answer', payload: StudentAnswerPayloadFillBlank | null): void;
}>();

const studentResponses = ref<Record<string, string>>({});
const parsedParts = ref<ParsedPart[]>([]);
const isLoading = ref(true);
const currentDisplayMode = computed(() => props.displayMode);

// Metadati per la modalità INPUT (non contiene correct_answers)
const fillBlankMetadataForInput = computed(() => {
  if (props.question.question_type === 'fill_blank' && props.question.metadata) {
    // text_with_placeholders e blanks (senza correct_answers) sono attesi
    return props.question.metadata as unknown as QuestionMetadataFillBlankDisplay;
  }
  return null;
});

// Metadati per la modalità RISULTATO (contiene correct_answers e case_sensitive)
const fillBlankMetadataForResults = computed(() => {
  if (props.question.question_type === 'fill_blank' && props.question.metadata) {
    // Qui ci aspettiamo la struttura completa con correct_answers
    return props.question.metadata as unknown as QuestionMetadataFillBlankWithCorrect;
  }
  return null;
});


interface TextPart {
  type: 'text';
  content: string;
}

interface BlankPart {
  type: 'blank';
  blankId: string;
  order: number;
}

type ParsedPart = TextPart | BlankPart;

const initializeAndParse = () => {
  isLoading.value = true;
  const currentMeta = currentDisplayMode.value === 'input' ? fillBlankMetadataForInput.value : fillBlankMetadataForResults.value;

  // DEBUG LOGS
  console.log('[FillBlankQuestion DEBUG] initializeAndParse called. Mode:', currentDisplayMode.value);
  console.log('[FillBlankQuestion DEBUG] props.question.metadata:', JSON.parse(JSON.stringify(props.question.metadata)));
  console.log('[FillBlankQuestion DEBUG] fillBlankMetadataForInput.value:', JSON.parse(JSON.stringify(fillBlankMetadataForInput.value)));
  console.log('[FillBlankQuestion DEBUG] fillBlankMetadataForResults.value:', JSON.parse(JSON.stringify(fillBlankMetadataForResults.value)));
  console.log('[FillBlankQuestion DEBUG] currentMeta:', JSON.parse(JSON.stringify(currentMeta)));

  if (currentMeta) {
    console.log('[FillBlankQuestion DEBUG] currentMeta.text_with_placeholders:', currentMeta.text_with_placeholders);
    console.log('[FillBlankQuestion DEBUG] currentMeta.blanks:', JSON.parse(JSON.stringify(currentMeta.blanks)));
    console.log('[FillBlankQuestion DEBUG] Condition check: !currentMeta:', !currentMeta);
    console.log('[FillBlankQuestion DEBUG] Condition check: !currentMeta.text_with_placeholders:', !currentMeta.text_with_placeholders);
    console.log('[FillBlankQuestion DEBUG] Condition check: !currentMeta.blanks:', !currentMeta.blanks);
     // More specific check for blanks array
    if (Array.isArray(currentMeta.blanks)) {
      console.log('[FillBlankQuestion DEBUG] Condition check: currentMeta.blanks.length === 0:', currentMeta.blanks.length === 0);
    } else {
      console.log('[FillBlankQuestion DEBUG] currentMeta.blanks is not an array.');
    }
  } else {
    console.log('[FillBlankQuestion DEBUG] currentMeta is null or undefined.');
  }
  // END DEBUG LOGS

  if (!currentMeta || !currentMeta.text_with_placeholders || !currentMeta.blanks || (Array.isArray(currentMeta.blanks) && currentMeta.blanks.length === 0) ) {
    console.error('Metadati fill_blank (modalità:', currentDisplayMode.value, ') mancanti o malformati. props.question:', JSON.parse(JSON.stringify(props.question)));
    parsedParts.value = [];
    studentResponses.value = {}; // Per modalità input
    isLoading.value = false;
    if (currentDisplayMode.value === 'input') {
      emit('update:answer', null);
    }
    return;
  }

  const { text_with_placeholders, blanks } = currentMeta;
  const sortedBlanks = [...blanks].sort((a, b) => a.order - b.order);
  const parts: ParsedPart[] = [];
  const placeholderRegex = /\{([\w-]+)\}/g;
  let lastIndex = 0;
  let match;

  while ((match = placeholderRegex.exec(text_with_placeholders)) !== null) {
    const placeholderId = match[1];
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text_with_placeholders.substring(lastIndex, match.index) });
    }
    const blankConfig = sortedBlanks.find(b => b.id === placeholderId);
    if (blankConfig) {
      parts.push({ type: 'blank', blankId: blankConfig.id, order: blankConfig.order });
    } else {
      parts.push({ type: 'text', content: match[0] });
      console.warn(`Placeholder ${match[0]} non trovato nei metadati dei blank.`);
    }
    lastIndex = placeholderRegex.lastIndex;
  }

  if (lastIndex < text_with_placeholders.length) {
    parts.push({ type: 'text', content: text_with_placeholders.substring(lastIndex) });
  }
  parsedParts.value = parts;

  if (currentDisplayMode.value === 'input') {
    const initialResponsesMap: Record<string, string> = {};
    currentMeta.blanks.forEach(blank => {
      const existingAnswer = props.initialAnswer?.answers?.find(ans => ans.blank_id === blank.id);
      initialResponsesMap[blank.id] = existingAnswer ? existingAnswer.student_response : '';
    });
    studentResponses.value = initialResponsesMap;
    emitUpdate(); // Emetti stato iniziale per input mode
  }
  isLoading.value = false;
};

const studentProvidedAnswersForDisplay = computed(() => {
  const answers: Record<string, string> = {};
  if (currentDisplayMode.value === 'result' && props.studentAnswerData?.selected_answers) {
    const selected = props.studentAnswerData.selected_answers as StudentAnswerPayloadFillBlank;
    if (selected.answers && Array.isArray(selected.answers)) {
      selected.answers.forEach(ans => {
        answers[ans.blank_id] = ans.student_response;
      });
    }
  }
  return answers;
});

function isStudentResponseCorrectForBlank(blankId: string): boolean {
  if (currentDisplayMode.value !== 'result' || !fillBlankMetadataForResults.value) return false;

  const studentAnswer = studentProvidedAnswersForDisplay.value[blankId];
  if (studentAnswer === undefined) return false; // Non risposto non è corretto

  const blankDef = fillBlankMetadataForResults.value.blanks.find(b => b.id === blankId);
  if (!blankDef || !blankDef.correct_answers || blankDef.correct_answers.length === 0) return false; // Nessuna risposta corretta definita

  const caseSensitive = fillBlankMetadataForResults.value.case_sensitive ?? false;
  const responseToCompare = caseSensitive ? studentAnswer : studentAnswer.toLowerCase();

  return blankDef.correct_answers.some(correct => {
    const correctToCompare = caseSensitive ? correct : correct.toLowerCase();
    return responseToCompare === correctToCompare;
  });
}

function getBlankResultClass(blankId: string): string[] {
  const classes: string[] = [];
  if (currentDisplayMode.value === 'result') {
    const isCorrect = isStudentResponseCorrectForBlank(blankId);
    const studentAnswer = studentProvidedAnswersForDisplay.value[blankId];

    if (studentAnswer === undefined || studentAnswer.trim() === '') {
      classes.push('bg-gray-100 dark:bg-gray-700 border-gray-400 dark:border-gray-500 text-gray-600 dark:text-gray-400'); // Non risposto
    } else if (isCorrect) {
      classes.push('bg-green-100 dark:bg-green-700 border-green-500 dark:border-green-600 text-green-700 dark:text-green-200');
    } else {
      classes.push('bg-red-100 dark:bg-red-700 border-red-500 dark:border-red-600 text-red-700 dark:text-red-200');
    }
  }
  return classes;
}


const handleInputChange = () => {
  // Gestito da v-model e watcher su studentResponses
};

const emitUpdate = () => {
  if (currentDisplayMode.value !== 'input' || !fillBlankMetadataForInput.value || !fillBlankMetadataForInput.value.blanks) {
    // Non emettere se non in modalità input o se i metadati non sono validi
    return;
  }
  const metadata = fillBlankMetadataForInput.value;
  const answersForPayload: StudentResponseForBlank[] = metadata.blanks.map(blank => {
    const response = studentResponses.value[blank.id] || '';
    return {
      blank_id: blank.id,
      student_response: response.trim() // Applica .trim() qui
    };
  });
  // DEBUG LOG
  console.log('[FillBlankQuestion DEBUG] emitUpdate called. studentResponses:', JSON.parse(JSON.stringify(studentResponses.value)));
  console.log('[FillBlankQuestion DEBUG] emitUpdate called. answersForPayload:', JSON.parse(JSON.stringify(answersForPayload)));
  // END DEBUG LOG
  emit('update:answer', { answers: answersForPayload });
};

onMounted(() => {
  initializeAndParse();
});

watch(() => [props.question.id, props.displayMode], () => {
  initializeAndParse();
}, { immediate: false });

watch(() => props.initialAnswer, (newVal, oldVal) => {
  if (currentDisplayMode.value === 'input' && JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
     initializeAndParse(); // Re-inizializza se initialAnswer cambia
  }
}, { deep: true });

watch(studentResponses, (newVal, oldVal) => {
  console.log(`[FillBlankQuestion DEBUG] Watcher triggered. Mode: ${currentDisplayMode.value}`);
  console.log(`[FillBlankQuestion DEBUG] Watcher newVal: ${JSON.stringify(newVal)}`);
  // Con { deep: true }, il watcher si attiva solo su modifiche effettive al contenuto dell'oggetto.
  // Non è strettamente necessario confrontare newVal e oldVal di nuovo, ma lo manteniamo per chiarezza
  // e per assicurarci che non ci siano chiamate ridondanti se Vue dovesse attivare il watcher in modo imprevisto.
  // La causa più probabile del problema precedente era che i log di emitUpdate non venivano visualizzati.
  
  if (currentDisplayMode.value === 'input') {
    // Verifichiamo esplicitamente se c'è stata una modifica per evitare chiamate multiple se il watcher si comporta in modo strano.
    // Tuttavia, con deep:true, questo dovrebbe essere già gestito.
    // La modifica principale qui è assicurarsi che emitUpdate sia chiamato.
    // if (JSON.stringify(newVal) !== JSON.stringify(oldVal)) { // Rimuoviamo temporaneamente per forzare la chiamata
      console.log('[FillBlankQuestion DEBUG] Watcher: Mode is input. Calling emitUpdate() due to change in studentResponses.');
      emitUpdate();
    // } else {
    //   console.log('[FillBlankQuestion DEBUG] Watcher: Values did not change according to stringify.');
    // }
  } else {
    console.log('[FillBlankQuestion DEBUG] Watcher: Mode is NOT input. Not calling emitUpdate.');
  }
}, { deep: true });

</script>

<style scoped>
.fill-blank-question {
  /* styles */
}
.blank-input {
  /* styles */
}
.blank-result-display {
  /* styles */
}
</style>