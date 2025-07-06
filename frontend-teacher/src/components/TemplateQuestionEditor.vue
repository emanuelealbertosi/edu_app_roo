<template>
  <li class="template-question-editor bg-white p-3 md:p-4 rounded-lg shadow border border-neutral-DEFAULT flex justify-between items-center">
    <div class="question-info flex-grow mr-3 md:mr-4">
      <div>
        <span class="order font-semibold text-neutral-dark">({{ question.order }})</span>
        <span class="text ml-2 text-neutral-darkest" v-html="question.text"></span> <!-- Potrebbe essere necessario troncare o gestire l'HTML qui se il testo diventa troppo lungo -->
        <span class="type ml-2 text-xs px-2 py-0.5 rounded-full bg-primary-lightest text-primary-dark font-medium">{{ question.question_type_display || question.question_type }}</span>
      </div>
      <div class="additional-info text-xs text-neutral-medium mt-1 ml-2 flex space-x-3">
        <span v-if="question.num_answer_options !== undefined">Opzioni: {{ question.num_answer_options }}</span>
        <span v-if="question.correct_answers_status && question.correct_answers_status !== 'N/A'">
          Corrette: <span :class="{
            'text-success': question.correct_answers_status === 'OK',
            'text-warning': question.correct_answers_status === 'PARTIAL', // Se implementeremo PARTIAL
            'text-error': question.correct_answers_status === 'MISSING'
          }">{{ question.correct_answers_status }}</span>
        </span>
        <span v-if="question.fill_blank_status && question.fill_blank_status !== 'N/A' && (question.question_type === 'fill_blank' || question.question_type === 'FILL_BLANK')">
          Fill-Blank: <span :class="{
            'text-success': question.fill_blank_status === 'OK',
            'text-error': question.fill_blank_status === 'MISSING'
          }">{{ question.fill_blank_status }}</span>
        </span>
      </div>
    </div>
    <div class="question-actions flex items-center space-x-2 md:space-x-3">
      <button
        @click="editQuestion"
        class="p-1.5 md:p-2 text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 rounded-md transition-colors"
        title="Modifica Domanda"
      >
        <!-- Heroicon: pencil -->
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 md:h-6 md:w-6" viewBox="0 0 20 20" fill="currentColor">
          <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
        </svg>
        <span class="sr-only">Modifica</span>
      </button>
      <button
        v-if="question.question_type === 'fill_blank' || question.question_type === 'FILL_BLANK'"
        @click="configureFillBlank"
        class="p-1.5 md:p-2 text-teal-600 hover:text-teal-800 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-opacity-50 rounded-md transition-colors"
        title="Configura Spazi Vuoti"
      >
        <!-- Heroicon: cog -->
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 md:h-6 md:w-6" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
        </svg>
        <span class="sr-only">Configura Blank</span>
      </button>
      <button
        @click="deleteQuestion"
        class="p-1.5 md:p-2 text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 rounded-md transition-colors"
        title="Elimina Domanda"
      >
        <!-- Heroicon: trash -->
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 md:h-6 md:w-6" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <span class="sr-only">Elimina</span>
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

const emit = defineEmits(['edit', 'delete', 'configure-fill-blank']);

const editQuestion = () => {
  // Emette l'ID della QuestionTemplate
  emit('edit', props.question.id);
};

const deleteQuestion = () => {
  // Emette l'ID della QuestionTemplate
  emit('delete', props.question.id);
};

const configureFillBlank = () => {
  // Assicurati che l'ID sia passato correttamente
  emit('configure-fill-blank', props.question); // Passa l'intera domanda per avere accesso al testo e metadata nella modale
};
</script>

<style scoped>
/* Rimuoviamo gli stili specifici dato che Tailwind è usato nel template.
   Se necessario, si possono aggiungere stili specifici qui.
   Per esempio, se si volesse un minimo di larghezza per le azioni o altro.
*/
.template-question-editor {
  /* Esempio: min-height: 60px; se necessario */
}

/* Gli stili per .question-info, .order, .text, .type sono ora inline con classi Tailwind */
</style>