<template>
  <div class="grading-attempt-view p-4 md:p-6 lg:p-8">
    <div v-if="isLoading" class="text-center py-10">
      <p class="text-lg text-gray-600">Caricamento dettagli del tentativo...</p>
      <!-- Potremmo aggiungere uno spinner più grande qui -->
    </div>

    <div v-else-if="error" class="text-center py-10">
      <p class="text-xl text-red-600 font-semibold">Errore nel caricamento</p>
      <p class="text-gray-700 mt-2">{{ error }}</p>
      <button @click="router.back()" class="mt-6 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Torna Indietro
      </button>
    </div>

    <div v-else-if="attemptDetails" class="max-w-4xl mx-auto">
      <header class="mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Correzione Quiz: {{ attemptDetails.quiz_title }}</h1>
        <p class="text-lg text-gray-600">Studente: <span class="font-semibold">{{ attemptDetails.student?.first_name }} {{ attemptDetails.student?.last_name }}</span></p>
        <p class="text-sm text-gray-500">Sottomesso il: {{ formatDate(attemptDetails.completed_at) }}</p>
      </header>

      <form @submit.prevent="submitGrading">
        <div v-for="(question, index) in attemptDetails.questions_with_answers" :key="question.id" class="mb-8 p-6 bg-white shadow-lg rounded-lg border border-gray-200">
          <h3 class="text-xl font-semibold text-gray-700 mb-3">Domanda {{ question.order + 1 }}:</h3>
          <p class="text-gray-800 mb-4 whitespace-pre-wrap">{{ question.text }}</p>
          <p class="text-sm text-gray-500 mb-1">Tipo: {{ question.question_type_display }}</p>

          <div v-if="question.student_answer" class="mt-4 p-4 bg-gray-50 rounded-md">
            <h4 class="font-semibold text-gray-700 mb-2">Risposta dello Studente:</h4>
            <p class="text-gray-600 whitespace-pre-wrap mb-3">{{ question.student_answer.selected_answers_text || 'Nessuna risposta testuale fornita (o tipo di domanda diverso).' }}</p>

            <div v-if="question.question_type === 'OPEN_MANUAL'">
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">Valutazione:</label>
                <div class="flex items-center space-x-4">
                  <label class="flex items-center">
                    <input type="radio" :name="'grade-' + question.student_answer.id" :value="true" v-model="grades[question.student_answer.id].is_correct" class="form-radio h-5 w-5 text-green-600">
                    <span class="ml-2 text-green-700">Corretta</span>
                  </label>
                  <label class="flex items-center">
                    <input type="radio" :name="'grade-' + question.student_answer.id" :value="false" v-model="grades[question.student_answer.id].is_correct" class="form-radio h-5 w-5 text-red-600">
                    <span class="ml-2 text-red-700">Sbagliata</span>
                  </label>
                </div>
                 <p v-if="grades[question.student_answer.id].is_correct === null" class="text-xs text-red-500 mt-1">Valutazione richiesta.</p>
              </div>
              <div>
                <label :for="'comment-' + question.student_answer.id" class="block text-sm font-medium text-gray-700 mb-1">Commento del Docente (opzionale):</label>
                <textarea
                  :id="'comment-' + question.student_answer.id"
                  v-model="grades[question.student_answer.id].teacher_comment"
                  rows="3"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="Aggiungi un feedback per lo studente..."
                ></textarea>
              </div>
            </div>
            <div v-else class="mt-2">
              <p class="text-sm">
                <span class="font-semibold">Valutazione Automatica: </span>
                <template v-if="question.student_answer.is_correct !== null">
                  <span :class="question.student_answer.is_correct ? 'text-green-600' : 'text-red-600'">
                    {{ question.student_answer.is_correct ? 'Corretta' : 'Sbagliata' }}
                  </span>
                </template>
                <template v-else-if="attemptDetails && attemptDetails.status === 'PENDING_GRADING'">
                  <span class="text-yellow-600">In attesa di valutazione finale</span>
                </template>
                <template v-else>
                  <span class="text-gray-500">Non valutata</span>
                </template>

                <template v-if="question.student_answer.score !== null">
                  <span class="ml-2 text-gray-600">(Punteggio: {{ question.student_answer.score }})</span>
                </template>
                <template v-else-if="attemptDetails && attemptDetails.status === 'PENDING_GRADING' && question.question_type !== 'OPEN_MANUAL'">
                   <span class="ml-2 text-gray-600">(Punteggio: In attesa)</span>
                </template>
              </p>
              <!-- Mostra opzioni corrette per domande non aperte -->
              <div v-if="question.answer_options && question.answer_options.length > 0 && question.question_type !== 'OPEN_MANUAL'" class="mt-2">
                <p class="text-xs text-gray-500">Opzioni Corrette:</p>
                <ul class="list-disc list-inside text-xs">
                    <li v-for="opt in question.answer_options.filter(o => o.is_correct)" :key="opt.id" class="text-gray-600">{{ opt.text }}</li>
                </ul>
              </div>
            </div>
          </div>
          <div v-else class="mt-4 p-4 bg-yellow-50 rounded-md text-yellow-700">
            Nessuna risposta registrata per questa domanda.
          </div>
          <hr v-if="index < attemptDetails.questions_with_answers.length - 1" class="my-6">
        </div>

        <div class="mt-8 flex justify-end space-x-3">
          <button type="button" @click="router.back()" class="px-6 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
            Annulla
          </button>
          <button
            type="submit"
            :disabled="isSubmitting || !isFormValid"
            class="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
          >
            {{ isSubmitting ? 'Salvataggio...' : 'Salva e Finalizza Correzione' }}
          </button>
        </div>
         <p v-if="submissionError" class="mt-4 text-sm text-red-600 text-center">{{ submissionError }}</p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/api/apiClient';
import type { QuizAttempt, Question } from '@/types/education'; // Assumendo che Question sia definito qui o importato

// Interfaccia per i dettagli del tentativo come ricevuti dall'API
// (basata su GradingQuizAttemptDetailSerializer)
interface GradingStudentAnswerData {
  id: number;
  question_text: string;
  question_order: number;
  selected_answers_text: string | null;
  is_correct: boolean | null;
  score: number | null;
  teacher_comment: string | null;
}

interface GradingQuestionData extends Pick<Question, 'id' | 'text' | 'question_type' | 'order' | 'metadata'> {
  question_type_display: string;
  student_answer: GradingStudentAnswerData | null;
  answer_options?: { id: number; text: string; is_correct: boolean }[]; // Opzionale, per domande non aperte
}

interface GradingAttemptDetails extends Pick<QuizAttempt, 'id' | 'started_at' | 'completed_at' | 'status'> {
  student: { first_name?: string; last_name?: string; /* altri campi da StudentBasicSerializer */ } | null;
  quiz_title: string;
  quiz_description: string | null;
  questions_with_answers: GradingQuestionData[];
}

// Interfaccia per i dati di correzione da inviare
interface GradeItem {
  student_answer_id: number;
  is_correct: boolean | null; // Può essere null inizialmente
  teacher_comment: string | null;
}

const route = useRoute();
const router = useRouter();

const attemptDetails = ref<GradingAttemptDetails | null>(null);
const isLoading = ref(true);
const error = ref<string | null>(null);
const isSubmitting = ref(false);
const submissionError = ref<string | null>(null);

const grades = ref<Record<number, GradeItem>>({});

const attemptId = computed(() => Number(route.params.attemptId));

const fetchAttemptDetails = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const response = await api.get<GradingAttemptDetails>(`/education/teacher/grading/attempts/${attemptId.value}/details-for-grading/`);
    attemptDetails.value = response.data;
    initializeGrades();
  } catch (err: any) {
    console.error("Errore durante il recupero dei dettagli del tentativo:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore sconosciuto';
  } finally {
    isLoading.value = false;
  }
};

const initializeGrades = () => {
  if (attemptDetails.value) {
    const initialGrades: Record<number, GradeItem> = {};
    attemptDetails.value.questions_with_answers.forEach(q => {
      if (q.student_answer && q.question_type === 'OPEN_MANUAL') {
        initialGrades[q.student_answer.id] = {
          student_answer_id: q.student_answer.id,
          is_correct: q.student_answer.is_correct, // Pre-popola se già valutato (improbabile per PENDING)
          teacher_comment: q.student_answer.teacher_comment || ''
        };
      }
    });
    grades.value = initialGrades;
  }
};

const isFormValid = computed(() => {
  if (!attemptDetails.value) return false;
  // Controlla che tutte le domande OPEN_MANUAL abbiano una valutazione (is_correct non sia null)
  return attemptDetails.value.questions_with_answers.every(q => {
    if (q.question_type === 'OPEN_MANUAL' && q.student_answer) {
      return grades.value[q.student_answer.id]?.is_correct !== null;
    }
    return true; // Le domande non manuali o senza risposta non bloccano la validità del form di correzione
  });
});

const submitGrading = async () => {
  if (!isFormValid.value) {
    submissionError.value = "Per favore, valuta tutte le risposte aperte.";
    return;
  }
  isSubmitting.value = true;
  submissionError.value = null;

  const payloadAnswers = Object.values(grades.value).map(g => ({
    student_answer_id: g.student_answer_id,
    is_correct: g.is_correct as boolean, // Assicurati che sia boolean, la validazione lo garantisce
    teacher_comment: g.teacher_comment || null
  }));

  try {
    await api.post(`/education/teacher/grading/attempts/${attemptId.value}/finalize-grading/`, { answers: payloadAnswers });
    // Successo
    // Potremmo mostrare un messaggio di successo e poi reindirizzare
    // Ad esempio, usando un toast/notifica store
    alert('Correzione salvata con successo!'); // Sostituire con notifica migliore
    router.push({ name: 'GradingDashboard' }); // Torna alla dashboard delle correzioni
  } catch (err: any) {
    console.error("Errore durante il salvataggio della correzione:", err);
    submissionError.value = err.response?.data?.detail || err.message || 'Errore sconosciuto durante il salvataggio.';
  } finally {
    isSubmitting.value = false;
  }
};

const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return 'N/D';
  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

onMounted(() => {
  if (attemptId.value) {
    fetchAttemptDetails();
  } else {
    error.value = "ID del tentativo non fornito.";
    isLoading.value = false;
  }
});

// Watch per reinizializzare i grades se attemptDetails cambia (es. ricaricamento)
watch(attemptDetails, (newDetails) => {
  if (newDetails) {
    initializeGrades();
  }
}, { deep: true });

</script>

<style scoped>
.whitespace-pre-wrap {
  white-space: pre-wrap; /* Per mantenere a capo e spazi nel testo delle domande/risposte */
}
/* Stili per radio button custom se necessario */
</style>