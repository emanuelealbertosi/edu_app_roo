<template>
  <div class="student-progress-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-4">Progressi Studenti</h1> <!-- Styled heading -->
    <p class="text-gray-600 mb-6">Sommario dei progressi degli studenti associati.</p> <!-- Styled paragraph -->

    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento progressi...</div> <!-- Styled loading -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento dei progressi: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="progressSummaries.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-gray-200 bg-white">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Studente</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Codice Studente</th> <!-- Modificato da Username -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quiz Completati</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Percorsi Completati</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Punti Totali</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="summary in progressSummaries" :key="summary.student_id" class="hover:bg-gray-50 transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ summary.full_name }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ summary.student_code }}</td> <!-- Modificato da username -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ summary.completed_quizzes_count ?? 0 }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ summary.completed_pathways_count ?? 0 }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ summary.total_points_earned ?? 0 }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <button @click="viewDetails(summary.student_id)" class="btn btn-link btn-sm">Dettagli</button> <!-- Added btn-sm -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-gray-500"> <!-- Styled no progress -->
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
  student_code: string; // Modificato da username
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
/* Stili specifici rimossi in favore di Tailwind */
</style>