<template>
  <div class="student-progress-view">
    <h1>Progressi Studenti</h1>
    <p>Sommario dei progressi degli studenti associati.</p>

    <div v-if="isLoading" class="loading">Caricamento progressi...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento dei progressi: {{ error }}
    </div>
    <div v-else-if="progressSummaries.length > 0" class="progress-list">
      <table>
        <thead>
          <tr>
            <th>Studente</th>
            <th>Username</th>
            <th>Quiz Completati</th>
            <th>Percorsi Completati</th>
            <th>Punti Totali</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="summary in progressSummaries" :key="summary.student_id">
            <td>{{ summary.full_name }}</td>
            <td>{{ summary.username }}</td>
            <td>{{ summary.completed_quizzes_count ?? 0 }}</td>
            <td>{{ summary.completed_pathways_count ?? 0 }}</td>
            <td>{{ summary.total_points_earned ?? 0 }}</td>
            <td>
              <button @click="viewDetails(summary.student_id)" class="btn btn-link text-sm">Dettagli</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="no-progress">
      Nessun dato sui progressi trovato per i tuoi studenti.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '@/api/config'; // Usa apiClient per chiamate dirette
import type { AxiosResponse } from 'axios';

// Interfaccia basata su StudentProgressSummarySerializer
interface StudentProgressSummary {
  student_id: number;
  full_name: string;
  username: string;
  completed_quizzes_count: number | null; // Potrebbe essere null se non annotato
  completed_pathways_count: number | null;
  total_points_earned: number | null;
}

const router = useRouter();
const progressSummaries = ref<StudentProgressSummary[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);

const loadProgressSummaries = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    // L'URL completo è /api/teacher/student-progress-summary/
    // ma dato che le URL di users sono incluse sotto /api/, il percorso relativo è /teacher/student-progress-summary/
    const response: AxiosResponse<StudentProgressSummary[]> = await apiClient.get('/teacher/student-progress-summary/');
    progressSummaries.value = response.data;
  } catch (err: any) {
    console.error("Errore nel caricamento dei sommari progressi:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore caricamento sommario progressi.';
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadProgressSummaries);

const viewDetails = (studentId: number) => {
  console.log(`Visualizza dettagli per studente ${studentId} - da implementare`);
  // Navigare a una vista dettagliata, passando studentId
  // router.push({ name: 'student-progress-detail', params: { studentId: studentId.toString() } }); // Rotta da definire
};

</script>

<style scoped>
/* Stili simili alle altre viste tabella */
.student-progress-view {
  padding: 20px;
}
.loading, .error-message, .no-progress {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
.error-message {
  color: red;
  font-weight: bold;
}
.progress-list {
  margin-top: 20px;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
th {
  background-color: #f2f2f2;
}
td button {
  margin-right: 5px;
  padding: 3px 8px;
  cursor: pointer;
}
</style>