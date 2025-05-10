<template>
  <div class="question-fill-blank-display">
    <p v-if="!parsedParts.length">Caricamento domanda...</p>
    <div v-else class="prose dark:prose-invert max-w-none">
      <template v-for="(part, index) in parsedParts" :key="index">
        <span v-if="part.type === 'text'" v-html="part.content"></span>
        <input
          v-else-if="part.type === 'blank'"
          type="text"
          :aria-label="`Risposta per spazio vuoto ${part.order + 1}`"
          v-model="studentResponses[part.blankId]"
          @input="handleInputChange(part.blankId, ($event.target as HTMLInputElement).value)"
          class="blank-input mx-1 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
          :placeholder="`___`"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import type {
  QuestionFillBlankDisplay,
  StudentAnswerPayloadFillBlank,
  StudentResponseForBlank
} from '@/types/education'; // Assicurati che il percorso sia corretto @ è src/

interface Props {
  question: QuestionFillBlankDisplay;
  initialAnswers?: StudentResponseForBlank[]; // Per pre-compilare se necessario (es. ripresa quiz)
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'update:answer', payload: StudentAnswerPayloadFillBlank): void;
}>();

// Struttura per memorizzare le risposte dello studente: { blank_id_0: "risposta1", blank_id_1: "risposta2" }
const studentResponses = ref<Record<string, string>>({});

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

const parsedParts = ref<ParsedPart[]>([]);

const initializeResponses = () => {
  const initialResponsesMap: Record<string, string> = {};
  if (props.question && props.question.metadata && props.question.metadata.blanks) {
    props.question.metadata.blanks.forEach(blank => {
      const existingAnswer = props.initialAnswers?.find(ans => ans.blank_id === blank.id);
      initialResponsesMap[blank.id] = existingAnswer ? existingAnswer.student_response : '';
    });
  }
  studentResponses.value = initialResponsesMap;
};

const parseTextWithPlaceholders = () => {
  if (!props.question || !props.question.metadata || !props.question.metadata.text_with_placeholders || !props.question.metadata.blanks) {
    parsedParts.value = [];
    return;
  }
  const { text_with_placeholders, blanks } = props.question.metadata;

  const sortedBlanks = [...blanks].sort((a, b) => a.order - b.order);
  
  const parts: ParsedPart[] = [];
  const placeholderRegex = /\{([\w-]+)\}/g;
  let lastIndex = 0;
  let match;

  while ((match = placeholderRegex.exec(text_with_placeholders)) !== null) {
    const placeholderContent = match[0]; 
    const blankIdInPlaceholder = match[1]; 

    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text_with_placeholders.substring(lastIndex, match.index) });
    }

    const blankConfig = sortedBlanks.find(b => b.id === blankIdInPlaceholder);

    if (blankConfig) {
      parts.push({ type: 'blank', blankId: blankConfig.id, order: blankConfig.order });
    } else {
      parts.push({ type: 'text', content: placeholderContent });
      console.warn(`Placeholder ${placeholderContent} non trovato nei metadati dei blank.`);
    }
    lastIndex = placeholderRegex.lastIndex;
  }

  if (lastIndex < text_with_placeholders.length) {
    parts.push({ type: 'text', content: text_with_placeholders.substring(lastIndex) });
  }
  
  parsedParts.value = parts;
  initializeResponses(); // Inizializza/Re-inizializza le risposte dopo il parsing
};


onMounted(() => {
  parseTextWithPlaceholders();
  emitUpdate(); // Emetti lo stato iniziale
});

watch(() => props.question, () => {
  parseTextWithPlaceholders();
  // emitUpdate() qui è ridondante se parseTextWithPlaceholders chiama initializeResponses e poi si emette
  // Tuttavia, per sicurezza, se la domanda cambia radicalmente, è bene emettere.
  // Ma initializeResponses dovrebbe già aver resettato studentResponses, e il watch su studentResponses emetterà.
  // Per ora, lo lascio commentato per evitare doppie emissioni, affidandomi al watch su studentResponses.
  // Se si verificano problemi, si può decommentare.
  // emitUpdate(); 
}, { deep: true });

watch(() => props.initialAnswers, (newInitialAnswers) => {
  if (newInitialAnswers && newInitialAnswers.length > 0) {
    const newResponsesState: Record<string, string> = { ...studentResponses.value };
    let changed = false;
    newInitialAnswers.forEach(ans => {
      if (props.question?.metadata?.blanks.some(b => b.id === ans.blank_id)) {
        if (newResponsesState[ans.blank_id] !== ans.student_response) {
          newResponsesState[ans.blank_id] = ans.student_response;
          changed = true;
        }
      }
    });
    if (changed) {
      studentResponses.value = newResponsesState;
      // L'emissione avverrà tramite il watch su studentResponses
    }
  } else if (newInitialAnswers === undefined || newInitialAnswers.length === 0) {
    // Se initialAnswers viene rimosso o svuotato, resetta le risposte ai valori di default (vuoti)
    // a meno che non ci siano già valori in studentResponses (es. l'utente ha iniziato a scrivere)
    // Questa logica potrebbe necessitare di affinamento a seconda del comportamento desiderato
    // per ora, parseTextWithPlaceholders() dovrebbe gestire il reset se la domanda non cambia.
  }
}, { deep: true });


const handleInputChange = (blankId: string, value: string) => {
  // studentResponses.value[blankId] = value; // Questo è già gestito da v-model
  // L'emissione avverrà tramite il watch su studentResponses
};

const emitUpdate = () => {
  if (props.question && props.question.metadata && props.question.metadata.blanks) {
    const answersForPayload: StudentResponseForBlank[] = props.question.metadata.blanks.map(blank => ({
      blank_id: blank.id,
      student_response: studentResponses.value[blank.id] || ''
    }));
    emit('update:answer', { answers: answersForPayload });
  }
};

// Watch combinato per studentResponses per emettere l'aggiornamento
watch(studentResponses, () => {
  emitUpdate();
}, { deep: true });

</script>

<style scoped>
.question-fill-blank-display {
  margin-bottom: 1.5rem;
}

.blank-input {
  min-width: 80px; 
  max-width: 200px; 
  text-align: center;
}
</style>