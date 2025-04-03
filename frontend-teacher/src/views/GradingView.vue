<template>
  <div class="grading-view">
    <h1>Valutazioni Manuali Pendenti</h1>
    <p>Elenco delle risposte aperte in attesa di valutazione.</p>

    <div v-if="isLoading" class="loading">Caricamento risposte...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento delle risposte: {{ error }}
    </div>
    <div v-else-if="pendingAnswers.length > 0" class="answers-list">
      <ul>
        <li v-for="answer in pendingAnswers" :key="answer.id">
          <div class="answer-details">
            <p><strong>Domanda:</strong> {{ answer.question_text }}</p>
            <p><strong>Risposta Studente:</strong></p>
            <pre>{{ answer.selected_answers?.answer_text || '(Nessuna risposta fornita)' }}</pre>
            <p><small>Tentativo ID: {{ answer.quiz_attempt }} | Risposta ID: {{ answer.id }}</small></p>
          </div>
          <div class="grading-actions">
            <!-- Form/pulsanti per assegnare punteggio/correttezza -->
            <p>Form valutazione da implementare</p>
            <!-- Applicato stile Tailwind -->
            <button
                @click="gradeAnswer(answer.id, true, 1)"
                class="bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-2 rounded text-sm mr-2"
            >
                Corretta (1pt)
            </button>
            <!-- Applicato stile Tailwind -->
            <button
                @click="gradeAnswer(answer.id, false, 0)"
                class="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm"
            >
                Errata (0pt)
            </button>
          </div>
        </li>
      </ul>
    </div>
    <div v-else class="no-answers">
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
.grading-view {
  padding: 20px;
}
.loading, .error-message, .no-answers {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
.error-message {
  color: red;
  font-weight: bold;
}
.answers-list {
  margin-top: 20px;
}
.answers-list ul {
  list-style: none;
  padding: 0;
}
.answers-list li {
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 15px;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  gap: 20px;
}
.answer-details {
  flex-grow: 1;
}
.answer-details pre {
    background-color: #f8f8f8;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 3px;
    white-space: pre-wrap; /* Va a capo automaticamente */
    word-wrap: break-word;
}
.grading-actions {
    min-width: 150px;
    text-align: right;
}
/* Rimosso stile .grading-actions button */
/* .grading-actions button { ... } */

</style>