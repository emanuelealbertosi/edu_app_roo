<template>
  <div class="student-progress-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-3xl font-bold mb-1">Progressi Studenti</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="text-xl opacity-90">Sommario dei progressi degli studenti associati.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca per nome o codice studente..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-neutral-DEFAULT rounded-md shadow-sm placeholder-neutral-dark focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
      />
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento progressi...</div>
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento dei progressi: {{ error }}</span>
    </div>
    
    <div v-else-if="filteredAndSortedSummaries.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white">
        <thead class="bg-neutral-lightest">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('full_name')">
              Studente
              <span v-if="sortKey === 'full_name'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('student_code')">
              Codice Studente
              <span v-if="sortKey === 'student_code'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('completed_quizzes_count')">
              Quiz Completati
              <span v-if="sortKey === 'completed_quizzes_count'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('completed_pathways_count')">
              Percorsi Completati
              <span v-if="sortKey === 'completed_pathways_count'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('total_points_earned')">
              Punti Totali
              <span v-if="sortKey === 'total_points_earned'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT">
          <tr v-for="summary in filteredAndSortedSummaries" :key="summary.student_id" class="hover:bg-neutral-lightest transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">
              <a href="#" @click.prevent="viewDetails(summary.student_id)" class="hover:underline cursor-pointer">
                {{ summary.full_name }}
              </a>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ summary.student_code }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ summary.completed_quizzes_count ?? 0 }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ summary.completed_pathways_count ?? 0 }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ summary.total_points_earned ?? 0 }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <BaseButton variant="info" size="sm" @click="viewDetails(summary.student_id)" class="p-2" title="Vedi Dettagli Progressi">
                <EyeIcon class="h-5 w-5" />
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark">
      <span v-if="searchQuery">Nessun risultato per "{{ searchQuery }}".</span>
      <span v-else>Nessun dato sui progressi trovato per i tuoi studenti.</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '@/api/config';
import type { AxiosResponse } from 'axios';
import BaseButton from '@/components/common/BaseButton.vue';
import { EyeIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';

// Interfaccia basata su StudentProgressSummarySerializer
interface StudentProgressSummary {
  student_id: number;
  full_name: string;
  student_code: string;
  completed_quizzes_count: number | null;
  completed_pathways_count: number | null;
  total_points_earned: number | null;
}

const router = useRouter();
const progressSummaries = ref<StudentProgressSummary[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const searchQuery = ref('');
const sortKey = ref('full_name');
const sortOrder = ref('asc');

const filteredAndSortedSummaries = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  const filtered = query
    ? progressSummaries.value.filter(summary => {
        const fullName = summary.full_name.toLowerCase();
        const studentCode = summary.student_code.toLowerCase();
        return fullName.includes(query) || studentCode.includes(query);
      })
    : progressSummaries.value;

  return filtered.slice().sort((a, b) => {
    let valA: any = a[sortKey.value as keyof StudentProgressSummary] ?? 0;
    let valB: any = b[sortKey.value as keyof StudentProgressSummary] ?? 0;

    if (typeof valA === 'string' && typeof valB === 'string') {
      valA = valA.toLowerCase();
      valB = valB.toLowerCase();
    }
    
    if (valA < valB) {
      return sortOrder.value === 'asc' ? -1 : 1;
    }
    if (valA > valB) {
      return sortOrder.value === 'asc' ? 1 : -1;
    }
    return 0;
  });
});

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
  router.push({ name: 'student-progress-detail', params: { studentId: studentId.toString() } });
};

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
</style>