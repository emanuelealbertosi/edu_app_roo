<template>
  <li class="template-question-editor"> <!-- Selettore CSS aggiornato -->
    <div class="question-info">
      <span class="order">({{ question.order }})</span>
      <span class="text">{{ question.text }}</span>
      <span class="type">[{{ question.question_type_display || question.question_type }}]</span> <!-- Usa display se disponibile -->
    </div>
    <div class="question-actions">
      <button
        @click="editQuestion"
        class="btn btn-warning text-sm mb-1 w-full text-center"
      >
        Modifica
      </button>
      <button
        @click="deleteQuestion"
        class="btn btn-danger text-sm w-full text-center"
      >
        Elimina
      </button>
    </div>
    <!-- TODO: Aggiungere sezione per visualizzare/modificare AnswerOptionTemplate -->
  </li>
</template>

<script setup lang="ts">
// Importa il tipo QuestionTemplate dal nuovo file API
import type { QuestionTemplate } from '@/api/templateQuestions';
import { defineProps, defineEmits } from 'vue';

const props = defineProps<{
  question: QuestionTemplate; // Usa il tipo QuestionTemplate
}>();

const emit = defineEmits(['edit', 'delete']);

const editQuestion = () => {
  // Emette l'ID della QuestionTemplate
  emit('edit', props.question.id);
};

const deleteQuestion = () => {
  // Emette l'ID della QuestionTemplate
  emit('delete', props.question.id);
};
</script>

<style scoped>
/* Stili identici a QuestionEditor, ma con selettore aggiornato */
.template-question-editor {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.question-info {
  flex-grow: 1;
  margin-right: 15px;
}

.question-actions {
    flex-shrink: 0;
    width: 80px;
}

.question-info .order {
  font-weight: bold;
  margin-right: 5px;
}

.question-info .type {
  font-style: italic;
  color: #555;
  margin-left: 5px;
}
</style>