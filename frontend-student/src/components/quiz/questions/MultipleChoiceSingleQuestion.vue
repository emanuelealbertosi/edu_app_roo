<script setup lang="ts">
import { ref, watch, defineProps, defineEmits } from 'vue';
import type { Question, MultipleChoiceSingleAnswer } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  // Potremmo passare un valore iniziale se stiamo riprendendo un tentativo
  initialAnswer?: MultipleChoiceSingleAnswer | null; 
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: MultipleChoiceSingleAnswer | null): void;
}>();

// State
const selectedOptionId = ref<number | null>(props.initialAnswer?.answer_option_id ?? null);

// Watcher per emettere l'evento quando la selezione cambia
watch(selectedOptionId, (newVal) => {
  if (newVal !== null) {
    emit('update:answer', { answer_option_id: newVal });
  } else {
    emit('update:answer', null); // Emette null se nessuna opzione è selezionata
  }
});

// Watcher per resettare la selezione se la domanda cambia
watch(() => props.question.id, () => {
  selectedOptionId.value = null;
});

</script>

<template>
  <div class="multiple-choice-single-question">
    <ul class="options-list">
      <li v-for="option in question.answer_options" :key="option.id" class="option-item">
        <label>
          <input
            type="radio"
            :name="'question_' + question.id"
            :value="option.id"
            v-model="selectedOptionId"
          />
          <span class="option-text">{{ option.text }}</span>
        </label>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.multiple-choice-single-question {
  margin-top: 15px;
}

.options-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.option-item {
  margin-bottom: 10px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
  background-color: #fff;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.option-item:hover {
  background-color: #f0f0f0;
}

.option-item label {
  display: flex;
  align-items: center;
  cursor: pointer;
  width: 100%;
}

.option-item input[type="radio"] {
  margin-right: 10px;
  accent-color: #007bff; /* Colora il radio button */
}

.option-text {
  flex-grow: 1;
}
</style>