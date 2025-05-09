<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, computed, onMounted } from 'vue';
import type { Question, FillBlankAnswer } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: FillBlankAnswer | null;
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: FillBlankAnswer | null): void;
}>();

// State
// Oggetto per memorizzare le risposte per ogni blank (indice -> risposta)
const blankAnswers = ref<Record<string, string>>({});
// Array per tenere traccia degli indici dei blank trovati nel testo
const blankIndices = ref<string[]>([]);

// Regex per trovare i placeholder come ___1___, ___2___, ecc.
const blankRegex = /___\s*(\d+)\s*___/g;

// Parsa il testo della domanda per trovare i blank e inizializzare lo stato
function initializeBlanks() {
  const indices: string[] = [];
  const initialAnswers: Record<string, string> = {};
  let match;
  // Resetta il regex state
  blankRegex.lastIndex = 0; 

  while ((match = blankRegex.exec(props.question.text)) !== null) {
    const index = match[1]; // L'indice del blank (es. '1', '2')
    if (!indices.includes(index)) {
      indices.push(index);
      // Inizializza la risposta per questo blank (vuota o dal valore iniziale)
      initialAnswers[index] = props.initialAnswer?.answers?.[index] ?? '';
    }
  }
  blankIndices.value = indices.sort((a, b) => parseInt(a) - parseInt(b)); // Ordina gli indici numericamente
  blankAnswers.value = initialAnswers;
}

// Computed property per generare il testo della domanda con gli input
const questionParts = computed(() => {
  const parts: { type: 'text' | 'input'; content: string | number }[] = [];
  let lastIndex = 0;
  // Resetta il regex state
  blankRegex.lastIndex = 0; 

  let match;
  while ((match = blankRegex.exec(props.question.text)) !== null) {
    // Aggiungi il testo prima del match
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: props.question.text.substring(lastIndex, match.index) });
    }
    // Aggiungi l'input per il blank
    const blankIndex = match[1];
    parts.push({ type: 'input', content: Number(blankIndex) });
    lastIndex = match.index + match[0].length;
  }
  // Aggiungi il testo rimanente dopo l'ultimo match
  if (lastIndex < props.question.text.length) {
    parts.push({ type: 'text', content: props.question.text.substring(lastIndex) });
  }
  return parts;
});

// Watcher per emettere l'evento quando una risposta cambia
watch(blankAnswers, (newVal) => {
  // Verifica se tutte le risposte richieste sono state date (anche se vuote)
  const allBlanksAnswered = blankIndices.value.every(index => newVal[index] !== undefined);
  
  if (allBlanksAnswered && blankIndices.value.length > 0) {
     // Emette solo se ci sono blank e sono stati tutti inizializzati (anche se vuoti)
     // Filtra eventuali proprietà extra che potrebbero essere state aggiunte
     const filteredAnswers: Record<string, string> = {};
     blankIndices.value.forEach(index => {
        filteredAnswers[index] = newVal[index] ?? ''; 
     });
    emit('update:answer', { answers: filteredAnswers });
  } else {
    // Se non ci sono blank o non sono ancora stati tutti inizializzati, emette null
    emit('update:answer', null);
  }
}, { deep: true });

// Watcher per reinizializzare se la domanda cambia
watch(() => props.question.id, () => {
  initializeBlanks();
}, { immediate: true }); // Esegui subito all'inizio

</script>

<template>
  <div class="fill-blank-question mt-4">
    <p class="question-text-with-blanks text-lg leading-relaxed">
      <template v-for="(part, index) in questionParts" :key="index">
        <template v-if="part.type === 'text'">
           <span class="align-baseline">{{ part.content }}</span>
        </template>
        <template v-else-if="part.type === 'input'">
           <input
             type="text"
             class="blank-input bg-transparent border-b border-gray-500 focus:border-blue-500 focus:border-b-2 outline-none px-2 py-1 mx-1 text-center text-lg align-baseline w-24 md:w-32"
             v-model="blankAnswers[part.content.toString()]"
             :placeholder="'#' + part.content"
             :aria-label="'Risposta per spazio ' + part.content"
           />
        </template>
      </template>
    </p>
    <!-- Mostra un elenco degli input se il testo è complesso (opzionale) -->
    <!-- 
    <div v-if="blankIndices.length > 1" class="blank-list">
        <div v-for="index in blankIndices" :key="index" class="blank-list-item">
            <label :for="'blank_' + question.id + '_' + index">Spazio #{{ index }}:</label>
            <input 
                :id="'blank_' + question.id + '_' + index"
                type="text" 
                v-model="blankAnswers[index]" 
            />
        </div>
    </div> 
    -->
  </div>
</template>

<style scoped>
/* Stili specifici rimasti o che richiedono override */

/* Assicura che gli input non abbiano sfondi strani in alcuni browser */
.blank-input {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}

/* Stili per l'elenco separato (opzionale) */
.blank-list {
    margin-top: 20px;
    border-top: 1px dashed #ccc;
    padding-top: 15px;
}
.blank-list-item {
    margin-bottom: 10px;
    display: flex;
    align-items: center;
}
.blank-list-item label {
    margin-right: 10px;
    min-width: 80px; /* Allinea le label */
}
.blank-list-item input {
    padding: 5px;
    border: 1px solid #ccc;
    border-radius: 3px;
}

</style>