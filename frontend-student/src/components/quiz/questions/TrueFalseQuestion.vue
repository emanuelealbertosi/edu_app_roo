<script setup lang="ts">
import { ref, watch, defineProps, defineEmits } from 'vue';
import type { Question, TrueFalseAnswer } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: TrueFalseAnswer | null; 
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: TrueFalseAnswer | null): void;
}>();

// State
// Usiamo stringa 'true'/'false' per il v-model dei radio, ma emettiamo booleano
const selectedValue = ref<'true' | 'false' | null>(
  props.initialAnswer === null || props.initialAnswer === undefined ? null : (props.initialAnswer.is_true ? 'true' : 'false')
);

// Watcher per emettere l'evento quando la selezione cambia
watch(selectedValue, (newVal) => {
  if (newVal !== null) {
    emit('update:answer', { is_true: newVal === 'true' });
  } else {
    emit('update:answer', null); // Emette null se nessuna opzione è selezionata
  }
});

// Watcher per resettare la selezione se la domanda cambia
watch(() => props.question.id, () => {
  selectedValue.value = null;
});

</script>

<template>
  <div class="true-false-question">
    <ul class="options-list">
      <li class="option-item">
        <label>
          <input
            type="radio"
            :name="'question_' + question.id"
            value="true"
            v-model="selectedValue"
          />
          <span class="option-text">Vero</span>
        </label>
      </li>
      <li class="option-item">
        <label>
          <input
            type="radio"
            :name="'question_' + question.id"
            value="false"
            v-model="selectedValue"
          />
          <span class="option-text">Falso</span>
        </label>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.true-false-question {
  margin-top: 15px;
}

.options-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex; /* Mette Vero e Falso sulla stessa riga */
  gap: 20px; /* Spazio tra le opzioni */
}

.option-item {
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
  background-color: #fff;
  cursor: pointer;
  transition: background-color 0.2s ease;
  flex: 1; /* Fa occupare lo spazio disponibile */
  text-align: center; /* Centra il testo */
}

.option-item:hover {
  background-color: #f0f0f0;
}

.option-item label {
  display: flex;
  align-items: center;
  justify-content: center; /* Centra input e testo */
  cursor: pointer;
  width: 100%;
}

.option-item input[type="radio"] {
  margin-right: 8px;
  accent-color: #007bff;
}

.option-text {
  font-weight: bold;
}
</style>