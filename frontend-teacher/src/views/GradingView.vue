<template>
  <div class="grading-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Valutazioni Manuali Pendenti</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="opacity-90">Elenco delle risposte aperte in attesa di valutazione.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento risposte...</div> <!-- Stile loading aggiornato -->
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert"> <!-- Stile errore aggiornato -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento delle risposte: {{ error }}</span>
    </div>
    <!-- Styled List Container -->
    <div v-else-if="pendingAnswers.length > 0" class="answers-list space-y-4"> <!-- Use space-y for gap -->
      <!-- Styled List Item Card -->
      <div v-for="answer in pendingAnswers" :key="answer.id" class="bg-white p-4 rounded-lg shadow-md border border-neutral-DEFAULT flex flex-col md:flex-row md:items-start md:space-x-4"> <!-- Stili card aggiornati -->
        <div class="answer-details flex-grow mb-4 md:mb-0">
          <p class="text-sm text-neutral-dark mb-1">Domanda:</p> <!-- Stile testo aggiornato -->
          <p class="font-medium text-neutral-darkest mb-2">{{ answer.question_text }}</p> <!-- Stile testo aggiornato -->
          <p class="text-sm text-neutral-dark mb-1">Risposta Studente:</p> <!-- Stile testo aggiornato -->
          <pre class="bg-neutral-lightest p-3 rounded border border-neutral-DEFAULT text-sm text-neutral-darker whitespace-pre-wrap break-words mb-2">{{ answer.selected_answers?.answer_text || '(Nessuna risposta fornita)' }}</pre> <!-- Stili pre aggiornati -->
          <p class="text-xs text-neutral-medium">Tentativo ID: {{ answer.quiz_attempt }} | Risposta ID: {{ answer.id }}</p> <!-- Stile testo aggiornato -->
        </div>
        <!-- Styled Actions Area -->
        <div class="grading-actions flex-shrink-0 flex flex-col space-y-2 md:w-40">
          <!-- TODO: Implementare un form più completo per punteggio variabile se necessario -->
          <!-- <p class="text-xs text-neutral-dark mb-2">Valutazione Rapida:</p> -->
          <BaseButton
              variant="success"
              size="sm"
              @click="gradeAnswer(answer.id, true, 1)"
              class="w-full"
          >
              Corretta (1pt)
          </BaseButton>
          <BaseButton
              variant="danger"
              size="sm"
              @click="gradeAnswer(answer.id, false, 0)"
              class="w-full"
          >
              Errata (0pt)
          </BaseButton>
        </div>
      </div>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark"> <!-- Stile no answers aggiornato -->
      Nessuna risposta in attesa di valutazione.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import apiClient from '@/api/config'; // Usa apiClient per chiamate dirette
import type { AxiosResponse } from 'axios';
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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