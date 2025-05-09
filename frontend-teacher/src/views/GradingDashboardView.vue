<template>
  <div class="grading-dashboard-view p-4">
    <h1 class="text-2xl font-semibold mb-6">Quiz da Correggere</h1>

    <div v-if="isLoading" class="text-center">
      <p>Caricamento tentativi in attesa di correzione...</p>
      <!-- Potremmo aggiungere uno spinner qui -->
    </div>

    <div v-else-if="error" class="text-center text-red-500">
      <p>Errore nel caricamento dei tentativi: {{ error }}</p>
    </div>

    <div v-else-if="pendingAttempts.length === 0" class="text-center text-gray-500">
      <p>Nessun quiz in attesa di correzione al momento.</p>
    </div>

    <div v-else class="overflow-x-auto">
      <table class="min-w-full bg-white shadow-md rounded-lg">
        <thead class="bg-gray-200">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Studente</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quiz</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inviato il</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="attempt in pendingAttempts" :key="attempt.id">
            <td class="px-6 py-4 whitespace-nowrap">{{ attempt.student_name }}</td>
            <td class="px-6 py-4 whitespace-nowrap">{{ attempt.quiz_title }}</td>
            <td class="px-6 py-4 whitespace-nowrap">{{ formatDate(attempt.completed_at || attempt.started_at) }}</td>
            <td class="px-6 py-4 whitespace-nowrap">
              <button
                @click="goToGrading(attempt.id)"
                class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
              >
                Correggi
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api/apiClient'; // Corretto percorso al servizio API
import type { QuizAttempt } from '@/types/education'; // Importa dal nuovo file

// Interfaccia specifica per i dati attesi dall'endpoint pending-attempts
interface PendingAttemptItem extends Pick<QuizAttempt, 'id' | 'status' | 'started_at' | 'completed_at'> {
  student_name: string;
  quiz_title: string;
}

const router = useRouter();
const pendingAttempts = ref<PendingAttemptItem[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

const fetchPendingAttempts = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    // L'endpoint corretto è /api/education/teacher/grading/pending-attempts/
    // ma il servizio api dovrebbe gestire il prefisso /api/education/
    const response = await api.get<PendingAttemptItem[]>('/education/teacher/grading/pending-attempts/');
    pendingAttempts.value = response.data;
  } catch (err: any) {
    console.error("Errore durante il recupero dei tentativi in attesa:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore sconosciuto';
  } finally {
    isLoading.value = false;
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

const goToGrading = (attemptId: number) => {
  // Naviga a una nuova vista per la correzione del singolo tentativo
  // Questa vista dovrà essere creata, es. GradingAttemptView.vue
  router.push({ name: 'GradingAttemptView', params: { attemptId } });
};

onMounted(() => {
  fetchPendingAttempts();
});
</script>

<style scoped>
/* Eventuali stili specifici per questa vista */
.grading-dashboard-view {
  max-width: 1200px;
  margin: 0 auto;
}
</style>