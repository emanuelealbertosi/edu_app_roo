<template>
  <div class="grading-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-4">Valutazioni Manuali Pendenti</h1> <!-- Styled heading -->
    <p class="text-gray-600 mb-6">Elenco delle risposte aperte in attesa di valutazione.</p> <!-- Styled paragraph -->

    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento risposte...</div> <!-- Styled loading -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento delle risposte: {{ error }}</span>
    </div>
    <!-- Styled List Container -->
    <div v-else-if="pendingAnswers.length > 0" class="answers-list space-y-4"> <!-- Use space-y for gap -->
      <!-- Styled List Item Card -->
      <div v-for="answer in pendingAnswers" :key="answer.id" class="bg-white p-4 rounded-lg shadow-md border border-gray-200 flex flex-col md:flex-row md:items-start md:space-x-4">
        <div class="answer-details flex-grow mb-4 md:mb-0">
          <p class="text-sm text-gray-500 mb-1">Domanda:</p>
          <p class="font-medium text-gray-800 mb-2">{{ answer.question_text }}</p>
          <p class="text-sm text-gray-500 mb-1">Risposta Studente:</p>
          <pre class="bg-gray-50 p-3 rounded border border-gray-200 text-sm text-gray-700 whitespace-pre-wrap break-words mb-2">{{ answer.selected_answers?.answer_text || '(Nessuna risposta fornita)' }}</pre>
          <p class="text-xs text-gray-400">Tentativo ID: {{ answer.quiz_attempt }} | Risposta ID: {{ answer.id }}</p>
        </div>
        <!-- Styled Actions Area -->
        <div class="grading-actions flex-shrink-0 flex flex-col space-y-2 md:w-40">
          <!-- TODO: Implementare un form più completo per punteggio variabile se necessario -->
          <!-- <p class="text-xs text-gray-500 mb-2">Valutazione Rapida:</p> -->
          <button
              @click="gradeAnswer(answer.id, true, 1)"
              class="btn btn-success btn-sm w-full"
          >
              Corretta (1pt)
          </button>
          <button
              @click="gradeAnswer(answer.id, false, 0)"
              class="btn btn-danger btn-sm w-full"
          >
              Errata (0pt)
          </button>
        </div>
      </div>
    </div>
    <div v-else class="text-center py-10 text-gray-500"> <!-- Styled no answers -->
      Nessuna risposta in attesa di valutazione.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import apiClient from '@/api/config'; // Usa apiClient per chiamate dirette
import type { AxiosResponse } from 'axios';

// Interfaccia basata su StudentAnswerSerializer
interface PendingAnswer {
  id: number;
  quiz_attempt: number;
  question: number;
  question_text: string;
  question_type: string;
  selected_answers: { answer_text?: string } | null; // Il contenuto di selected_answers per OPEN_MANUAL
  is_correct: boolean | null;
  score: number | null;
  answered_at: string;
}

const pendingAnswers = ref<PendingAnswer[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);

const loadPendingAnswers = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const response: AxiosResponse<PendingAnswer[]> = await apiClient.get('/education/teacher/grading/pending/');
    pendingAnswers.value = response.data;
  } catch (err: any) {
    console.error("Errore nel caricamento delle risposte pendenti:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore caricamento risposte.';
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadPendingAnswers);

const gradeAnswer = async (answerId: number, isCorrect: boolean, score: number | null) => {
    // Trova l'indice della risposta per aggiornare lo stato di caricamento/errore specifico
    const answerIndex = pendingAnswers.value.findIndex(a => a.id === answerId);
    // TODO: Aggiungere uno stato di caricamento per riga se necessario

    error.value = null; // Resetta errore generale prima di provare
    try {
        await apiClient.post(`/education/teacher/grading/${answerId}/grade/`, {
            is_correct: isCorrect,
            score: score // Invia null se necessario
        });
        // Rimuovi dalla lista dopo successo
        pendingAnswers.value.splice(answerIndex, 1);
        console.log(`Risposta ${answerId} valutata con successo.`);
        // Mostra notifica successo (opzionale)
    } catch (err: any) {
        console.error(`Errore valutazione risposta ${answerId}:`, err);
        // Mostra errore specifico per questa riga o un errore generale
        error.value = `Errore valutazione risposta ${answerId}: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    } finally {
        // TODO: Resetta stato caricamento per riga se implementato
    }
};

</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
pre { /* Assicura che il font monospace sia applicato */
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
</style>