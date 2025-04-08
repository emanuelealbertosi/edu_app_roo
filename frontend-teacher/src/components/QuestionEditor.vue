<template>
  <li class="question-editor">
    <div class="question-info">
      <span class="order">({{ question.order }})</span>
      <span class="text">{{ question.text }}</span>
      <span class="type">[{{ question.question_type_display }}]</span>
    </div>
    <!-- Rimosso flex flex-col -->
    <div class="question-actions">
      <!-- Aggiunto block e mb-1 -->
      <button
        @click="editQuestion"
        class="btn btn-warning text-sm mb-1 w-full text-center"
      >
        Modifica
      </button>
      <!-- Aggiunto block -->
      <button
        @click="deleteQuestion"
        class="btn btn-danger text-sm w-full text-center"
      >
        Elimina
      </button>
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
  align-items: center; /* Manteniamo l'allineamento verticale centrato per il blocco azioni */
  margin-bottom: 10px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.question-info {
  flex-grow: 1;
  margin-right: 15px; /* Aumentato margine per dare più spazio ai bottoni */
}

.question-actions {
    flex-shrink: 0; /* Impedisce al contenitore dei bottoni di restringersi */
    width: 80px; /* Larghezza fissa per il contenitore dei bottoni */
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

/* Rimosso stile .question-actions button */
/* .question-actions button { ... } */

/* Rimosso stile .question-actions button.delete */
/* .question-actions button.delete { ... } */
/* .question-actions button.delete:hover { ... } */

</style>