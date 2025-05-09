<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, computed } from 'vue';
import type { Question, OpenAnswerManualAnswer, StudentAnswerResult } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: OpenAnswerManualAnswer | null; // Usato in modalità input
  displayMode?: 'input' | 'result'; // Per distinguere la modalità
  studentAnswerData?: StudentAnswerResult & { teacher_comment?: string | null }; // Usa StudentAnswerResult e aggiunge teacher_comment opzionale
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: OpenAnswerManualAnswer | null): void;
}>();

// State
const answerText = ref<string>(props.initialAnswer?.text ?? '');

const currentDisplayMode = computed(() => props.displayMode || 'input');

// Watcher per emettere l'evento quando il testo cambia (solo in modalità input)
watch(answerText, (newVal) => {
  if (currentDisplayMode.value === 'input') {
    if (newVal.trim()) {
      emit('update:answer', { text: newVal });
    } else {
      emit('update:answer', null);
    }
  }
});

// Watcher per resettare il testo se la domanda cambia (solo in modalità input)
watch(() => props.question.id, () => {
  if (currentDisplayMode.value === 'input') {
    answerText.value = props.initialAnswer?.text ?? ''; // Resetta all'initialAnswer o vuoto
  }
});

// Valore per la visualizzazione in modalità risultato
const studentProvidedAnswerText = computed(() => {
  if (currentDisplayMode.value === 'result' && props.studentAnswerData?.selected_answers && typeof props.studentAnswerData.selected_answers === 'object' && 'text' in props.studentAnswerData.selected_answers) {
    return (props.studentAnswerData.selected_answers as { text?: string }).text || '';
  }
  return '';
});

</script>

<template>
  <div class="open-answer-manual-question mt-4">
    <!-- Modalità Input -->
    <div v-if="currentDisplayMode === 'input'">
      <textarea
        v-model="answerText"
        class="answer-textarea w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-150 ease-in-out text-base"
        placeholder="Scrivi qui la tua risposta..."
        rows="5"
        :aria-label="'Risposta per la domanda: ' + question.text"
      ></textarea>
    </div>

    <!-- Modalità Risultato -->
    <div v-else-if="currentDisplayMode === 'result'" class="result-display space-y-3">
      <div>
        <p class="font-semibold text-gray-700">La tua risposta:</p>
        <p v-if="studentProvidedAnswerText" class="text-gray-800 bg-gray-50 p-3 rounded-md whitespace-pre-wrap">{{ studentProvidedAnswerText }}</p>
        <p v-else class="text-gray-500 italic bg-gray-50 p-3 rounded-md">Nessuna risposta fornita.</p>
      </div>

      <div v-if="props.studentAnswerData?.is_correct !== null && props.studentAnswerData?.is_correct !== undefined">
        <p class="font-semibold text-gray-700">Valutazione:</p>
        <span
          :class="{
            'bg-green-100 text-green-700': props.studentAnswerData?.is_correct === true,
            'bg-red-100 text-red-700': props.studentAnswerData?.is_correct === false,
          }"
          class="px-3 py-1 rounded-full text-sm font-medium"
        >
          {{ props.studentAnswerData?.is_correct === true ? 'Corretta' : 'Sbagliata' }}
        </span>
      </div>
      <div v-else>
         <p class="font-semibold text-gray-700">Valutazione:</p>
         <span class="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-sm font-medium">
            In attesa di correzione
         </span>
      </div>


      <div v-if="props.studentAnswerData?.teacher_comment">
        <p class="font-semibold text-gray-700">Commento del docente:</p>
        <p class="text-gray-800 bg-blue-50 p-3 rounded-md whitespace-pre-wrap">{{ props.studentAnswerData.teacher_comment }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici se necessari */
.answer-textarea {
  resize: vertical; /* Manteniamo il resize verticale */
}
</style>