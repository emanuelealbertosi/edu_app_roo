<template>
  <div class="grading-dashboard-view p-4">
    <!-- Stile titolo aggiornato -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Quiz da Correggere</h1>
      <p class="opacity-90">Elenco dei quiz che richiedono una valutazione manuale.</p>
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca per studente o nome quiz..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-neutral-DEFAULT rounded-md shadow-sm placeholder-neutral-dark focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
      />
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">
      <p>Caricamento tentativi in attesa di correzione...</p>
    </div>

    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
      <p>Errore nel caricamento dei tentativi: {{ error }}</p>
    </div>

    <div v-else-if="filteredAndSortedAttempts.length === 0" class="text-center py-10 text-neutral-dark">
      <p v-if="searchQuery">Nessun risultato per "{{ searchQuery }}".</p>
      <p v-else>Nessun quiz in attesa di correzione al momento.</p>
    </div>

    <div v-else class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full bg-white">
        <thead class="bg-neutral-lightest">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('student_name')">
              Studente
              <span v-if="sortKey === 'student_name'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('quiz_title')">
              Quiz
              <span v-if="sortKey === 'quiz_title'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('completed_at')">
              Inviato il
              <span v-if="sortKey === 'completed_at'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-neutral-DEFAULT">
          <tr v-for="attempt in filteredAndSortedAttempts" :key="attempt.id" class="hover:bg-neutral-lightest transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap">{{ attempt.student_name }}</td>
            <td class="px-6 py-4 whitespace-nowrap">{{ attempt.quiz_title }}</td>
            <td class="px-6 py-4 whitespace-nowrap">{{ formatDate(attempt.completed_at || attempt.started_at) }}</td>
            <td class="px-6 py-4 whitespace-nowrap">
              <BaseButton
                variant="primary"
                size="sm"
                @click="goToGrading(attempt.id)"
              >
                Correggi
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api/apiClient';
import type { QuizAttempt } from '@/types/education';
import BaseButton from '@/components/common/BaseButton.vue';
import { ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';

// Interfaccia specifica per i dati attesi dall'endpoint pending-attempts
interface PendingAttemptItem extends Pick<QuizAttempt, 'id' | 'status' | 'started_at' | 'completed_at'> {
  student_name: string;
  quiz_title: string;
}

const router = useRouter();
const pendingAttempts = ref<PendingAttemptItem[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);
const searchQuery = ref('');
const sortKey = ref('completed_at');
const sortOrder = ref('desc');

const filteredAndSortedAttempts = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  const filtered = query
    ? pendingAttempts.value.filter(attempt => {
        const studentName = attempt.student_name.toLowerCase();
        const quizTitle = attempt.quiz_title.toLowerCase();
        return studentName.includes(query) || quizTitle.includes(query);
      })
    : pendingAttempts.value;

  return filtered.slice().sort((a, b) => {
    let valA: any = a[sortKey.value as keyof PendingAttemptItem];
    let valB: any = b[sortKey.value as keyof PendingAttemptItem];

    // Gestione per date
    if (sortKey.value === 'completed_at') {
      valA = a.completed_at ? new Date(a.completed_at).getTime() : 0;
      valB = b.completed_at ? new Date(b.completed_at).getTime() : 0;
    } else if (typeof valA === 'string' && typeof valB === 'string') {
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
  router.push({ name: 'GradingAttemptView', params: { attemptId } });
};

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

onMounted(() => {
  fetchPendingAttempts();
});
</script>

<style scoped>
/* Eventuali stili specifici per questa vista */
.grading-dashboard-view {
  /* max-width: 1200px; */
  /* margin: 0 auto; */
}
</style>