<template>
  <div class="assigned-quizzes-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Quiz Assegnati (Istanze)</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="opacity-90">Qui puoi visualizzare le istanze concrete dei quiz che hai assegnato.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>
    <!-- Non c'è un pulsante "Crea" qui, le istanze vengono create tramite assegnazione -->

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca quiz per titolo o descrizione..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-neutral-DEFAULT rounded-md shadow-sm placeholder-neutral-dark focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
      />
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento quiz assegnati...</div>
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento dei quiz assegnati: {{ error }}</span>
    </div>
    
    <div v-else-if="filteredAndSortedQuizzes.length > 0" class="shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white">
        <thead class="bg-neutral-lightest">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('title')">
              Titolo Istanza
              <span v-if="sortKey === 'title'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('description')">
              Descrizione
              <span v-if="sortKey === 'description'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('source_template')">
              Template Sorgente
              <span v-if="sortKey === 'source_template'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('created_at')">
              Creato il
              <span v-if="sortKey === 'created_at'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT">
          <tr v-for="quiz in filteredAndSortedQuizzes" :key="quiz.id" class="hover:bg-neutral-lightest transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ quiz.title }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ quiz.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ quiz.source_template ? `ID: ${quiz.source_template}` : 'N/D' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ new Date(quiz.created_at).toLocaleDateString() }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
              <BaseButton variant="info" size="sm" @click="viewQuizDetails(quiz.id)" class="p-2" title="Vedi Dettagli Quiz Assegnato">
                <EyeIcon class="h-5 w-5" />
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark">
      <span v-if="searchQuery">Nessun quiz trovato per "{{ searchQuery }}".</span>
      <span v-else>Nessun quiz assegnato trovato.</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
// Importa API per fetchare le istanze Quiz concrete
import { fetchQuizzes, deleteQuizApi, type Quiz } from '@/api/quizzes';
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton
import { EyeIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';

const assignedQuizzes = ref<Quiz[]>([]); // Usa il tipo Quiz per le istanze
const isLoading = ref(false);
const router = useRouter();
const error = ref<string | null>(null);
const searchQuery = ref('');
const sortKey = ref('created_at');
const sortOrder = ref('desc');

const filteredAndSortedQuizzes = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  const filtered = query
    ? assignedQuizzes.value.filter(quiz => {
        const title = quiz.title.toLowerCase();
        const description = quiz.description ? quiz.description.toLowerCase() : '';
        return title.includes(query) || description.includes(query);
      })
    : assignedQuizzes.value;

  return filtered.slice().sort((a, b) => {
    let valA: any = a[sortKey.value as keyof Quiz];
    let valB: any = b[sortKey.value as keyof Quiz];

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

onMounted(async () => {
  isLoading.value = true;
  error.value = null;
  try {
    // Usiamo fetchQuizzes che dovrebbe restituire le istanze create dal docente
    // Potrebbe essere necessario filtrare ulteriormente o usare un endpoint dedicato in futuro
    assignedQuizzes.value = await fetchQuizzes();
  } catch (err: any) {
    console.error("Errore nel recupero dei quiz assegnati:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
  } finally {
    isLoading.value = false;
  }
});

// Funzione per visualizzare dettagli (potrebbe puntare a una vista read-only)
const viewQuizDetails = (id: number) => {
  router.push({ name: 'assigned-quiz-details', params: { id: id.toString() } }); // Rotta ipotetica
};

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

// Funzione eliminazione (commentata - richiede cautela)
/*
const deleteAssignedQuiz = async (id: number) => {
  if (!confirm(`Sei sicuro di voler eliminare l'istanza quiz con ID ${id}? Questo potrebbe rimuovere le assegnazioni associate.`)) {
    return;
  }
  try {
    await deleteQuizApi(id); // API esistente per eliminare istanze Quiz
    assignedQuizzes.value = assignedQuizzes.value.filter(quiz => quiz.id !== id);
    console.log(`Istanza quiz ${id} eliminata.`);
  } catch (err: any) {
    console.error(`Errore eliminazione istanza quiz ${id}:`, err);
    error.value = `Errore eliminazione istanza quiz: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
  }
};
*/
</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
</style>