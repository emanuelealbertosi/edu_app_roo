<template>
  <li class="question-editor">
    <div class="question-info">
      <span class="order">({{ question.order }})</span>
      <span class="text">{{ question.text }}</span>
      <span class="type">[{{ question.question_type_display }}]</span>
    </div>
    <div class="question-actions">
      <button @click="editQuestion">Modifica</button>
      <button @click="deleteQuestion" class="delete">Elimina</button>
    </div>
    <!-- Qui potremmo mostrare/gestire le opzioni di risposta in futuro -->
  </li>
</template>

<script setup lang="ts">
import type { Question } from '@/api/questions';
import { defineProps, defineEmits } from 'vue';

const props = defineProps<{
  question: Question;
}>();

const emit = defineEmits(['edit', 'delete']);

const editQuestion = () => {
  emit('edit', props.question.id);
};

const deleteQuestion = () => {
  // Potremmo chiedere conferma qui o nel componente padre
  emit('delete', props.question.id);
};
</script>

<style scoped>
.question-editor {
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

.question-info .order {
  font-weight: bold;
  margin-right: 5px;
}

.question-info .type {
  font-style: italic;
  color: #555;
  margin-left: 5px;
}

.question-actions button {
  margin-left: 5px;
  padding: 3px 8px;
  cursor: pointer;
}

.question-actions button.delete {
    background-color: #f44336; /* Red */
    color: white;
    border: none;
}
.question-actions button.delete:hover {
    background-color: #d32f2f;
}

</style>