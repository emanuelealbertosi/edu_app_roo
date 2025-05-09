<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, computed } from 'vue';
import type { Question, TrueFalseAnswer, StudentAnswerResult } from '@/api/quiz';

// Props
const props = defineProps<{
  question: Question;
  initialAnswer?: TrueFalseAnswer | null;
  displayMode?: 'input' | 'result';
  studentAnswerData?: StudentAnswerResult;
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:answer', answer: TrueFalseAnswer | null): void;
}>();

// State
const currentDisplayMode = computed(() => props.displayMode || 'input');
const selectedValue = ref<'true' | 'false' | null>(null);

// Initialize or reset selectedValue based on mode and props
function initializeOrResetSelection() {
  if (currentDisplayMode.value === 'input') {
    selectedValue.value = props.initialAnswer === null || props.initialAnswer === undefined ? null : (props.initialAnswer.is_true ? 'true' : 'false');
  } else {
    // In result mode, selectedValue is not directly used for input,
    // but we can clear it or set based on studentAnswerData if needed for other logic.
    // For now, let's ensure it doesn't carry over from a previous input state if component is reused.
    selectedValue.value = null;
  }
}

watch([() => props.question.id, () => props.initialAnswer, currentDisplayMode], initializeOrResetSelection, { immediate: true });


// Watcher per emettere l'evento quando la selezione cambia (solo in modalità input)
watch(selectedValue, (newVal) => {
  if (currentDisplayMode.value === 'input') {
    if (newVal !== null) {
      emit('update:answer', { is_true: newVal === 'true' });
    } else {
      emit('update:answer', null);
    }
  }
});

// Computed properties per la modalità risultato
const studentAnswerAsBoolean = computed(() => {
  if (currentDisplayMode.value === 'result' && props.studentAnswerData?.selected_answers && typeof (props.studentAnswerData.selected_answers as any).is_true === 'boolean') {
    return (props.studentAnswerData.selected_answers as any).is_true as boolean;
  }
  return null; // o undefined, per indicare che non c'è una risposta valida
});

const correctAnswerAsBoolean = computed(() => {
  if (props.question && props.question.answer_options) {
    // Per True/False, ci aspettiamo due opzioni.
    // Una con testo "Vero" (o simile) e una "Falso" (o simile).
    // La risposta corretta è quella dove answer_option.is_correct è true.
    // Il valore booleano della risposta corretta dipende dal testo di questa opzione corretta.
    const correctOption = props.question.answer_options.find(opt => opt.is_correct);
    if (correctOption) {
      // Assumiamo che le opzioni per Vero/Falso abbiano un testo che possiamo interpretare,
      // o che il backend fornisca un modo più diretto per sapere se 'true' è la risposta corretta.
      // Per ora, una semplice euristica basata su testi comuni.
      // Idealmente, il backend dovrebbe fornire `answer_option.value_boolean` o simile.
      // O, più semplicemente, se l'opzione con testo "Vero" è `is_correct`, allora la risposta corretta è true.
      // E se l'opzione con testo "Falso" è `is_correct`, allora la risposta corretta è false.
      // Questo è più robusto se i testi sono standard.
      // Il modello dati `AnswerOption` ha `text` e `is_correct`.
      // Se `question.answer_options` ha due elementi, uno per Vero e uno per Falso.
      // Troviamo quello con `is_correct: true`. Se il suo testo è "Vero", la risposta è true.
      // Se il testo è "Falso", la risposta è false.
      // Questo presuppone che i testi siano esattamente "Vero" e "Falso".
      // Una soluzione più robusta sarebbe che il backend fornisca direttamente il valore booleano corretto
      // o che le opzioni abbiano un campo `value: boolean`.
      // Data la struttura attuale, se l'opzione con `is_correct: true` ha testo "Vero", allora è true.
      // Se ha testo "Falso", allora è false.
      // Per semplicità, se l'opzione corretta ha testo "Vero" (case-insensitive), è true.
      if (correctOption.text.toLowerCase() === 'vero') return true;
      if (correctOption.text.toLowerCase() === 'falso') return false;
      // Fallback se i testi non sono standard, ma questo è meno ideale.
      // Potremmo assumere che la prima opzione sia "Vero" e la seconda "Falso" se non ci sono testi chiari.
      // Ma questo è rischioso.
      // Per ora, ci fidiamo che `is_correct` sia sull'opzione giusta e il testo sia interpretabile.
      // Se `answer_options` ha due opzioni, una è `is_correct`.
      // Se l'opzione `is_correct` è quella che rappresenta "Vero", allora la risposta corretta è `true`.
      // Se è quella che rappresenta "Falso", allora la risposta corretta è `false`.
      // Il backend dovrebbe popolare `answer_options` per TF in modo che una delle due sia `is_correct`.
      // Esempio: [{id:1, text:"Vero", is_correct:true}, {id:2, text:"Falso", is_correct:false}] -> correctAnswerAsBoolean = true
      // Esempio: [{id:1, text:"Vero", is_correct:false}, {id:2, text:"Falso", is_correct:true}] -> correctAnswerAsBoolean = false
      // Quindi, se l'opzione corretta ha testo "Vero", è true. Altrimenti è false (assumendo solo due opzioni).
      // Questo è ancora un po' fragile.
      // La cosa più sicura è se il backend fornisse direttamente il valore booleano della risposta corretta per la domanda TF.
      // Oppure, se `answer_options` avesse un campo `value: boolean`.
      // Dato che `answer_options` ha `is_correct`, e per TF ci sono due opzioni,
      // una sarà `is_correct: true`. Se questa opzione è quella che semanticamente significa "vero" (es. testo "Vero"),
      // allora la risposta corretta è `true`.
      // Per ora, assumiamo che l'opzione con `is_correct: true` sia quella che definisce la verità della domanda.
      // E che il suo testo sia "Vero" se la risposta corretta è true, e "Falso" se la risposta corretta è false.
      // Questo è un po' circolare.
      // L'approccio più semplice: se l'opzione con `is_correct: true` ha il testo "Vero", allora la risposta corretta è `true`.
      // Se l'opzione con `is_correct: true` ha il testo "Falso", allora la risposta corretta è `false`.
      // Questo è ancora basato sul testo.
      // L'API `Question` ha `answer_options` dove ogni opzione ha `is_correct`.
      // Per una domanda TF, ci saranno due `answer_options`. Una sarà `is_correct: true`.
      // Se l'opzione con `is_correct: true` è quella che rappresenta "Vero" (es. `option.text === 'Vero'`), allora `correctAnswerAsBoolean` è `true`.
      // Se l'opzione con `is_correct: true` è quella che rappresenta "Falso" (es. `option.text === 'Falso'`), allora `correctAnswerAsBoolean` è `false`.
      // Questo è il modo più diretto con la struttura dati attuale.
      const trueOption = props.question.answer_options.find(opt => opt.text.toLowerCase() === 'vero');
      if (trueOption && trueOption.is_correct) return true;
      
      const falseOption = props.question.answer_options.find(opt => opt.text.toLowerCase() === 'falso');
      if (falseOption && falseOption.is_correct) return false;
    }
  }
  return null; // Non dovrebbe accadere se i dati sono corretti
});

</script>

<template>
  <div class="true-false-question mt-4">
    <!-- Modalità Input -->
    <div v-if="currentDisplayMode === 'input'">
      <ul class="options-list grid grid-cols-2 gap-4">
        <li class="option-item">
          <label
            :class="[
              'block w-full p-6 md:p-8 rounded-lg shadow cursor-pointer transition-all duration-200 text-center font-bold text-xl md:text-2xl',
              'bg-blue-500 hover:bg-blue-600 text-white',
              selectedValue === 'true' ? 'ring-4 ring-offset-2 ring-black dark:ring-gray-400' : 'hover:opacity-90 hover:shadow-md'
            ]"
          >
            <input
              type="radio"
              :name="'question_' + question.id"
              value="true"
              v-model="selectedValue"
              class="sr-only"
              aria-label="Vero"
            />
            <span class="option-text">Vero</span>
          </label>
        </li>
        <li class="option-item">
          <label
            :class="[
              'block w-full p-6 md:p-8 rounded-lg shadow cursor-pointer transition-all duration-200 text-center font-bold text-xl md:text-2xl',
              'bg-red-500 hover:bg-red-600 text-white',
              selectedValue === 'false' ? 'ring-4 ring-offset-2 ring-black dark:ring-gray-400' : 'hover:opacity-90 hover:shadow-md'
            ]"
          >
            <input
              type="radio"
              :name="'question_' + question.id"
              value="false"
              v-model="selectedValue"
              class="sr-only"
              aria-label="Falso"
            />
            <span class="option-text">Falso</span>
          </label>
        </li>
      </ul>
    </div>

    <!-- Modalità Risultato -->
    <div v-else-if="currentDisplayMode === 'result'" class="result-display space-y-4">
      <ul class="options-list grid grid-cols-2 gap-4">
        <!-- Opzione Vero -->
        <li class="option-item-result">
          <div
            :class="[
              'block w-full p-6 md:p-8 rounded-lg shadow text-center font-bold text-xl md:text-2xl',
              correctAnswerAsBoolean === true ? 'bg-green-200 border-2 border-green-500 text-green-800 dark:bg-green-700 dark:border-green-400 dark:text-green-100' : 'bg-gray-100 dark:bg-gray-700 dark:text-gray-300',
              studentAnswerAsBoolean === true && correctAnswerAsBoolean !== true ? 'bg-red-200 border-2 border-red-500 text-red-800 dark:bg-red-700 dark:border-red-400 dark:text-red-100' : '',
              studentAnswerAsBoolean === true && correctAnswerAsBoolean === true ? 'border-2 border-green-700 dark:border-green-300' : ''
            ]"
          >
            Vero
            <div class="mt-2 text-sm font-normal">
              <span v-if="studentAnswerAsBoolean === true" class="font-bold text-blue-600 dark:text-blue-400 block">(La tua risposta)</span>
              <span v-if="correctAnswerAsBoolean === true && studentAnswerAsBoolean !== true" class="font-bold text-green-600 dark:text-green-400 block">(Risposta corretta)</span>
            </div>
          </div>
        </li>
        <!-- Opzione Falso -->
        <li class="option-item-result">
          <div
            :class="[
              'block w-full p-6 md:p-8 rounded-lg shadow text-center font-bold text-xl md:text-2xl',
              correctAnswerAsBoolean === false ? 'bg-green-200 border-2 border-green-500 text-green-800 dark:bg-green-700 dark:border-green-400 dark:text-green-100' : 'bg-gray-100 dark:bg-gray-700 dark:text-gray-300',
              studentAnswerAsBoolean === false && correctAnswerAsBoolean !== false ? 'bg-red-200 border-2 border-red-500 text-red-800 dark:bg-red-700 dark:border-red-400 dark:text-red-100' : '',
              studentAnswerAsBoolean === false && correctAnswerAsBoolean === false ? 'border-2 border-green-700 dark:border-green-300' : ''
            ]"
          >
            Falso
             <div class="mt-2 text-sm font-normal">
              <span v-if="studentAnswerAsBoolean === false" class="font-bold text-blue-600 dark:text-blue-400 block">(La tua risposta)</span>
              <span v-if="correctAnswerAsBoolean === false && studentAnswerAsBoolean !== false" class="font-bold text-green-600 dark:text-green-400 block">(Risposta corretta)</span>
            </div>
          </div>
        </li>
      </ul>

      <div v-if="studentAnswerData" class="mt-4 p-3 rounded-lg"
        :class="{
            'bg-green-100 dark:bg-green-800 dark:text-green-200 text-green-700': studentAnswerData.is_correct === true,
            'bg-red-100 dark:bg-red-800 dark:text-red-200 text-red-700': studentAnswerData.is_correct === false,
            'bg-yellow-100 dark:bg-yellow-700 dark:text-yellow-200 text-yellow-700': studentAnswerData.is_correct === null || studentAnswerData.is_correct === undefined
        }">
        <p class="font-semibold text-center text-lg">
          <span v-if="studentAnswerData.is_correct === true">Corretta! 🎉</span>
          <span v-else-if="studentAnswerData.is_correct === false">Sbagliata.</span>
          <span v-else>In attesa di valutazione.</span>
        </p>
      </div>
       <p v-if="!studentAnswerData && currentDisplayMode === 'result'" class="text-gray-500 italic text-center">
        Informazioni sulla risposta non disponibili.
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici se necessari */
.option-item label, .option-item-result div {
  user-select: none;
}
</style>