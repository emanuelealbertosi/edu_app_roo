<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, computed } from 'vue';
import type { Question, MultipleChoiceMultipleAnswer } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: MultipleChoiceMultipleAnswer | null; 
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: MultipleChoiceMultipleAnswer | null): void;
}>();

// State
// Usiamo un oggetto per tenere traccia dello stato selezionato di ogni opzione
const selectedOptions = ref<Record<number, boolean>>({});

// Inizializza lo stato basato sulla risposta iniziale (se presente)
function initializeSelection() {
  const initialSelection: Record<number, boolean> = {};
  props.question.answer_options?.forEach(option => {
    initialSelection[option.id] = props.initialAnswer?.answer_option_ids?.includes(option.id) ?? false;
  });
  selectedOptions.value = initialSelection;
}

// Calcola l'array di ID selezionati da emettere
const selectedOptionIds = computed(() => {
  return Object.entries(selectedOptions.value)
    .filter(([, isSelected]) => isSelected)
    .map(([id]) => Number(id));
});

// Watcher per emettere l'evento quando la selezione cambia
watch(selectedOptionIds, (newVal) => {
  if (newVal.length > 0) {
    emit('update:answer', { answer_option_ids: newVal });
  } else {
    emit('update:answer', null); // Emette null se nessuna opzione è selezionata
  }
}, { deep: true }); // Deep watch necessario per l'oggetto selectedOptions

// Watcher per resettare la selezione se la domanda cambia
watch(() => props.question.id, () => {
  initializeSelection(); // Re-inizializza quando la domanda cambia
}, { immediate: true }); // Esegui subito all'inizio

</script>

<template>
  <div class="multiple-choice-multiple-question">
    <p class="instruction">(Seleziona tutte le risposte corrette)</p>
    <ul class="options-list">
      <li v-for="option in question.answer_options" :key="option.id" class="option-item">
        <label>
          <input
            type="checkbox"
            :value="option.id"
            v-model="selectedOptions[option.id]"
          />
          <span class="option-text">{{ option.text }}</span>
        </label>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.multiple-choice-multiple-question {
  margin-top: 15px;
}

.instruction {
    font-size: 0.9em;
    color: #666;
    margin-bottom: 10px;
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

.option-item input[type="checkbox"] {
  margin-right: 10px;
  accent-color: #007bff; /* Colora la checkbox */
}

.option-text {
  flex-grow: 1;
}
</style>