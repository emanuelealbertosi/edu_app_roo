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
  <div class="open-answer-manual-question">
    <textarea
      v-model="answerText"
      class="answer-textarea"
      placeholder="Scrivi qui la tua risposta..."
      rows="5"
      :aria-label="'Risposta per la domanda: ' + question.text"
    ></textarea>
  </div>
</template>

<style scoped>
.open-answer-manual-question {
  margin-top: 15px;
}

.answer-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
  line-height: 1.5;
  resize: vertical; /* Permette il ridimensionamento verticale */
}

.answer-textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}
</style>