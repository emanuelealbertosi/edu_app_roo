<script setup lang="ts">
import { ref, watch, defineProps, defineEmits } from 'vue';
import type { Question, OpenAnswerManualAnswer } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: OpenAnswerManualAnswer | null; 
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: OpenAnswerManualAnswer | null): void;
}>();

// State
const answerText = ref<string>(props.initialAnswer?.text ?? '');

// Watcher per emettere l'evento quando il testo cambia
watch(answerText, (newVal) => {
  // Emette la risposta solo se c'è del testo, altrimenti null
  if (newVal.trim()) {
    emit('update:answer', { text: newVal });
  } else {
    emit('update:answer', null); 
  }
});

// Watcher per resettare il testo se la domanda cambia
watch(() => props.question.id, () => {
  answerText.value = '';
});

</script>

<template>
  <div class="open-answer-manual-question mt-4">
    <textarea
      v-model="answerText"
      class="answer-textarea w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-150 ease-in-out text-base"
      placeholder="Scrivi qui la tua risposta..."
      rows="5"
      :aria-label="'Risposta per la domanda: ' + question.text"
    ></textarea>
  </div>
</template>

<style scoped>
/* Stili specifici se necessari */
.answer-textarea {
  resize: vertical; /* Manteniamo il resize verticale */
}
</style>