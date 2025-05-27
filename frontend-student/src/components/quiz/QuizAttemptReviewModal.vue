<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { useQuizStore } from '@/stores/quiz';
import type { QuizAttemptReviewData, QuestionReview, AnswerOptionReview } from '@/types/education'; // Importa i tipi necessari
import BaseModal from '@/components/common/BaseModal.vue'; // Assumendo che BaseModal sia qui
import BaseButton from '@/components/common/BaseButton.vue';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/vue/24/solid'; // Icone per correttezza

const props = defineProps<{
  attemptId: number | null;
  show: boolean;
}>();

const emit = defineEmits(['close']);

const quizStore = useQuizStore();
const isLoading = ref(false);
const error = ref<string | null>(null);
const attemptReviewData = ref<QuizAttemptReviewData | null>(null);
const expandedQuestions = ref<Record<number, boolean>>({});

// Calcola il titolo della modale dinamicamente
const modalTitle = computed(() => {
  if (attemptReviewData.value?.quiz_title) {
    return `Revisione: ${attemptReviewData.value.quiz_title}`;
  }
  return 'Revisione Tentativo';
});

const toggleQuestionExpansion = (questionId: number) => {
  expandedQuestions.value[questionId] = !expandedQuestions.value[questionId];
};

watch(() => props.attemptId, async (newAttemptId) => {
  if (newAttemptId && props.show) {
    expandedQuestions.value = {}; // Resetta lo stato di espansione
    isLoading.value = true;
    error.value = null;
    attemptReviewData.value = null;
    await quizStore.loadAttemptForReview(newAttemptId);
    if (quizStore.attemptReviewError) {
      error.value = quizStore.attemptReviewError;
    } else {
      attemptReviewData.value = quizStore.currentAttemptReviewData;
      if (attemptReviewData.value?.questions) {
        attemptReviewData.value.questions.forEach(q => {
          expandedQuestions.value[q.id] = false; // Chiudi tutte per default
        });
      }
    }
    isLoading.value = false;
  }
}, { immediate: true });

watch(() => props.show, (newShowState, oldShowState) => {
  if (newShowState && !oldShowState && props.attemptId) {
    // Se la modale viene mostrata e non era mostrata prima, e c'è un attemptId
    isLoading.value = true;
    error.value = null;
    attemptReviewData.value = null; // Pulisci i dati vecchi
    expandedQuestions.value = {}; // Resetta espansione
    quizStore.loadAttemptForReview(props.attemptId).then(() => {
      if (quizStore.attemptReviewError) {
        error.value = quizStore.attemptReviewError;
      } else {
        attemptReviewData.value = quizStore.currentAttemptReviewData;
        if (attemptReviewData.value?.questions) {
          attemptReviewData.value.questions.forEach(q => {
            expandedQuestions.value[q.id] = false; // Chiudi tutte per default
          });
        }
      }
      isLoading.value = false;
    });
  } else if (!newShowState) {
    // Quando la modale viene chiusa, resetta i dati per evitare flash di contenuto vecchio
    attemptReviewData.value = null;
    error.value = null;
    expandedQuestions.value = {};
  }
});


const closeModal = () => {
  emit('close');
};

// Funzione helper per visualizzare la risposta dello studente in modo leggibile
const getFormattedStudentAnswer = (question: QuestionReview): string => {
  if (!question.student_answer || question.student_answer.selected_answers === null || question.student_answer.selected_answers === undefined) {
    return 'Nessuna risposta data.';
  }

  const studentResp = question.student_answer.selected_answers;
  const normalizedQuestionType = question.question_type ? question.question_type.toLowerCase() : '';

  switch (normalizedQuestionType) {
    case 'mc_single': // multiple_choice_single è già gestito da toLowerCase
      // Trova il testo dell'opzione selezionata
      const selectedOptionId = studentResp.answer_option_id;
      const selectedOption = question.answer_options?.find(opt => opt.id === selectedOptionId);
      return selectedOption ? selectedOption.text : 'Opzione non trovata.';
    case 'mc_multi': // multiple_choice_multiple è già gestito da toLowerCase
      const selectedOptionIds = studentResp.answer_option_ids || [];
      const selectedOptionsText = question.answer_options
        ?.filter(opt => selectedOptionIds.includes(opt.id))
        .map(opt => opt.text)
        .join(', ');
      return selectedOptionsText || 'Nessuna opzione selezionata.';
    case 'tf': // true_false è già gestito da toLowerCase
      return studentResp.is_true ? 'Vero' : 'Falso';
    case 'fill_blank':
      let filledTextFb = question.metadata?.text_with_placeholders || '';
      // La struttura corretta, come da feedback, è studentResp.answers che è un array di stringhe
      const studentResponsesArray = studentResp.answers as string[] | undefined;

      if (question.metadata?.blanks) {
        const blanksArrayConfig = (Array.isArray(question.metadata.blanks) ? [...question.metadata.blanks] : [])
            .sort((a, b) => (a.order || 0) - (b.order || 0)); // Assicura l'ordine

        blanksArrayConfig.forEach((blankConf: { id: string, order: number }, index: number) => {
          const rawStudentResponse = Array.isArray(studentResponsesArray) ? studentResponsesArray[index] : undefined;
          let answerTextForDisplay: string;

          if (typeof rawStudentResponse === 'string') { // Include stringa vuota
            answerTextForDisplay = rawStudentResponse;
          } else { // null, undefined, o se l'array di risposte è più corto dei blanks
            answerTextForDisplay = ''; // Visualizza come vuoto
          }
          filledTextFb = filledTextFb.replace(`{${blankConf.id}}`, `[${answerTextForDisplay}]`);
        });
      }
      return filledTextFb;
    case 'open_manual': // open_answer_manual è già gestito da toLowerCase
      return studentResp.text || 'Nessuna risposta data.';
    default:
      try {
        return JSON.stringify(studentResp);
      } catch (e) {
        return 'Risposta non visualizzabile';
      }
  }
};

// Funzione helper per ottenere le risposte ai singoli blank per la visualizzazione
const getIndividualBlankAnswers = (question: QuestionReview): Array<{ id: string, response: string, order: number }> => {
  const normalizedQuestionType = question.question_type ? question.question_type.toLowerCase() : '';
  if (normalizedQuestionType === 'fill_blank') {
    // La struttura corretta, come da feedback, è student_answer.selected_answers.answers che è un array di stringhe
    const studentSelectedAnswersContainer = question.student_answer?.selected_answers;
    const studentResponsesArray = studentSelectedAnswersContainer?.answers as string[] | undefined;

    if (question.metadata?.blanks) {
      const result: Array<{ id: string, response: string, order: number }> = [];
      
      const blankConfigs = (Array.isArray(question.metadata.blanks) ? [...question.metadata.blanks] : [])
        .sort((a, b) => (a.order || 0) - (b.order || 0)); // Assicura l'ordine

      blankConfigs.forEach((blankConf: { id: string, order: number }, index: number) => {
        const rawStudentResponse = Array.isArray(studentResponsesArray) ? studentResponsesArray[index] : undefined;
        let individualAnswerText: string;

        if (typeof rawStudentResponse === 'string') { // Include stringa vuota
          individualAnswerText = rawStudentResponse;
        } else { // null, undefined, o se l'array di risposte è più corto dei blanks
          individualAnswerText = ''; // Visualizza come vuoto
        }
        
        result.push({
          id: blankConf.id,
          response: individualAnswerText,
          order: blankConf.order !== undefined ? blankConf.order : -1
        });
      });
      return result;
    }
  }
  return [];
};

</script>

<template>
  <BaseModal :show="show" @close="closeModal">
    <template #header>
      <div class="bg-primary-600 text-white p-4 rounded-t-lg">
        <h2 class="text-xl font-semibold">{{ modalTitle }}</h2>
      </div>
    </template>
    <div v-if="isLoading" class="p-6 text-center">
      <p>Caricamento revisione...</p>
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mt-2"></div>
    </div>
    <div v-else-if="error" class="p-6 text-center text-red-600">
      <p>Errore nel caricamento della revisione: {{ error }}</p>
    </div>
    <div v-else-if="attemptReviewData && attemptReviewData.questions" class="p-4 md:p-6 space-y-6 max-h-[70vh] overflow-y-auto">
      <div class="text-sm text-gray-600">
        <p><strong>Studente:</strong> {{ attemptReviewData.student.first_name }} {{ attemptReviewData.student.last_name }}</p>
        <p><strong>Punteggio:</strong> {{ attemptReviewData.score !== null ? `${attemptReviewData.score}%` : 'N/D' }}</p>
        <p><strong>Completato il:</strong> {{ attemptReviewData.completed_at ? new Date(attemptReviewData.completed_at).toLocaleString('it-IT') : 'N/D' }}</p>
      </div>
      <hr/>
      <div v-for="(question, index) in attemptReviewData.questions" :key="question.id" class="question-review-item border-b border-gray-200 last:border-b-0 pb-4 mb-4 last:mb-0 last:pb-0">
        <div @click="toggleQuestionExpansion(question.id)" class="cursor-pointer p-2 hover:bg-gray-50 rounded">
          <h3 class="text-md font-semibold mb-1 flex justify-between items-center">
            <div class="flex items-center">
              <CheckCircleIcon v-if="question.student_answer?.is_correct === true" class="h-5 w-5 mr-2 text-green-500 shrink-0"/>
              <XCircleIcon v-else-if="question.student_answer?.is_correct === false" class="h-5 w-5 mr-2 text-red-500 shrink-0"/>
              <span v-else class="h-5 w-5 mr-2 shrink-0"></span> <!-- Spazio per allineamento se non ancora valutata -->
              <span>Domanda {{ index + 1 }} ({{ question.question_type_display }})</span>
            </div>
            <span class="text-sm transition-transform duration-200" :class="{'rotate-180': expandedQuestions[question.id]}">▼</span>
          </h3>
        </div>

        <div v-if="expandedQuestions[question.id]" class="mt-1 pl-4 pr-2 pb-2 border-l-2 border-gray-200 ml-2 space-y-3">
          <p class="text-gray-800 mb-2 whitespace-pre-wrap">{{ question.text }}</p>
          
          <!-- La Sezione Opzioni (per MC, TF) è stata rimossa per mostrare solo la risposta data dallo studente -->

          <!-- Sezione Risposta Data -->
          <div class="my-2">
            <p class="font-medium text-sm text-gray-700">Risposta data:</p>
            <!-- Caso specifico per FILL_BLANK nella sezione "Risposta data" -->
            <div v-if="question.question_type && question.question_type.toLowerCase() === 'fill_blank'">
              <ul v-if="getIndividualBlankAnswers(question).length > 0" class="list-disc list-inside pl-4 mt-1 space-y-1">
                <li v-for="blankAnswer in getIndividualBlankAnswers(question)" :key="blankAnswer.id" class="text-sm">
                  <!-- Rimosso: <span class="font-mono text-xs bg-gray-100 px-1 rounded">{{ blankAnswer.id }} (ordine {{ blankAnswer.order }}):</span> -->
                  <span class="text-gray-800 font-semibold">{{ blankAnswer.response }}</span>
                </li>
              </ul>
              <p v-else class="text-gray-600 text-sm italic">Nessuna risposta fornita per i singoli blank.</p>
            </div>
            <!-- Caso per altri tipi di domanda -->
            <div v-else class="flex items-center">
              <p class="text-gray-800 font-semibold whitespace-pre-wrap mr-2">{{ getFormattedStudentAnswer(question) }}</p>
              <CheckCircleIcon v-if="question.student_answer?.is_correct === true" class="h-6 w-6 text-green-500"/>
              <XCircleIcon v-else-if="question.student_answer?.is_correct === false" class="h-6 w-6 text-red-500"/>
            </div>
          </div>
          
          <!-- Caso specifico per FILL_BLANK per mostrare il testo completo con le risposte e la correttezza generale -->
          <div v-if="question.question_type && question.question_type.toLowerCase() === 'fill_blank'" class="my-2 p-3 bg-gray-50 rounded">
            <p class="font-medium text-sm text-gray-700">Testo con risposte inserite:</p>
            <p class="text-gray-800 whitespace-pre-wrap">{{ getFormattedStudentAnswer(question) }}</p>
             <!-- Mostra correttezza generale per fill_blank -->
            <div v-if="question.student_answer" class="mt-1 flex items-center">
                <span class="text-xs mr-1">Valutazione:</span>
                <CheckCircleIcon v-if="question.student_answer.is_correct === true" class="h-4 w-4 text-green-500"/>
                <XCircleIcon v-else-if="question.student_answer.is_correct === false" class="h-4 w-4 text-red-500"/>
                <span v-else class="text-xs text-gray-500">Non valutata</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="p-6 text-center">
      <p>Nessun dato disponibile per la revisione.</p>
    </div>

    <template #footer>
      <BaseButton @click="closeModal" variant="secondary">Chiudi</BaseButton>
    </template>
  </BaseModal>
</template>

<style scoped>
.question-review-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}
.whitespace-pre-wrap {
  white-space: pre-wrap; /* Per mantenere a capo e spazi multipli nel testo della domanda/risposta */
}
</style>