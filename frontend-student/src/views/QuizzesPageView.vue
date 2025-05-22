<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useDashboardStore } from '@/stores/dashboard';
import QuizList from '@/components/QuizList.vue';
import BaseTabs from '@/components/common/BaseTabs.vue';
import type { QuizAttemptDashboardItem } from '@/api/dashboard'; // Assicurati che il percorso sia corretto

const dashboardStore = useDashboardStore();
const isLoading = ref(true);
const searchTerm = ref('');

const quizPageTabs = ref([
  { name: 'Da Fare', slotName: 'todoQuizzes' },
  { name: 'Completati', slotName: 'completedQuizzes' }
]);

onMounted(async () => {
  isLoading.value = true; // Imposta isLoading a true all'inizio
  try {
    // Controlla se i dati dei quiz sono già stati caricati o se c'è un errore pendente
    const quizzesAlreadyLoaded =
      dashboardStore.availableQuizzes.length > 0 ||
      dashboardStore.completedQuizzes.length > 0 ||
      dashboardStore.inProgressOrFailedQuizzes.length > 0;

    // Se i quiz non sono caricati e non c'è un errore che impedisca il caricamento
    if (!quizzesAlreadyLoaded && !dashboardStore.error) {
      // Chiamiamo loadDashboard. Lo store dovrebbe internamente gestire il non ricaricare se già in corso.
      await dashboardStore.loadDashboard();
    }
    // Se i dati erano già caricati, o dopo il tentativo di caricamento,
    // lo stato di errore e i dati saranno quelli aggiornati dallo store.
  } catch (error) {
    // Questo catch intercetterebbe errori non gestiti da loadDashboard() stesso,
    // ma loadDashboard dovrebbe impostare dashboardStore.error.
    console.error('Errore critico in onMounted di QuizzesPageView durante il tentativo di caricamento:', error);
    // Potremmo voler impostare un errore locale specifico per questa vista se necessario,
    // ma per ora ci affidiamo a dashboardStore.error per il template.
  } finally {
    // isLoading a false solo dopo che il tentativo di caricamento (se avvenuto) è concluso
    // o se i dati erano già presenti.
    isLoading.value = false;
  }
});

// Funzione di filtraggio (simile a quella della DashboardView)
const filterQuizzes = (quizzes: QuizAttemptDashboardItem[]) => {
  if (!searchTerm.value.trim()) {
    return quizzes;
  }
  const lowerSearchTerm = searchTerm.value.toLowerCase();
  return quizzes.filter(quiz => {
    const subjectName = quiz.subject_name?.toLowerCase() || '';
    const topicName = quiz.topic_name?.toLowerCase() || '';
    const title = quiz.title?.toLowerCase() || '';
    const teacherUsername = quiz.teacher_username?.toLowerCase() || '';
    const teacherFirstName = quiz.teacher_first_name?.toLowerCase() || '';
    const teacherLastName = quiz.teacher_last_name?.toLowerCase() || '';

    return subjectName.includes(lowerSearchTerm) ||
           topicName.includes(lowerSearchTerm) ||
           title.includes(lowerSearchTerm) ||
           teacherUsername.includes(lowerSearchTerm) ||
           teacherFirstName.includes(lowerSearchTerm) ||
           teacherLastName.includes(lowerSearchTerm);
  });
};

// Quiz da fare: disponibili + in corso/falliti, ordinati per data di assegnazione (più recente prima)
// Nota: Assumiamo che 'assigned_at' o 'created_at' (per il tentativo) possa essere usato per l'ordinamento.
// Se 'assigned_at' non è direttamente sul tentativo, potrebbe essere necessario accedere al quiz originale.
// Per ora, usiamo 'created_at' del tentativo come proxy se 'assigned_at' non c'è.
const sortedTodoQuizzes = computed(() => {
  const getDateForSort = (item: QuizAttemptDashboardItem): number => {
    if (item.available_from) return new Date(item.available_from).getTime();
    if (item.status === 'IN_PROGRESS' && item.started_at) return new Date(item.started_at).getTime();
    if (item.started_at) return new Date(item.started_at).getTime();
    return 0; // Per quelli senza data, verranno ordinati per ID dopo
  };

  const sortLogic = (a: QuizAttemptDashboardItem, b: QuizAttemptDashboardItem): number => {
    const dateA = getDateForSort(a);
    const dateB = getDateForSort(b);

    if (dateA === 0 && dateB !== 0) return 1; // 'a' senza data va dopo 'b' con data
    if (dateB === 0 && dateA !== 0) return -1; // 'b' senza data va dopo 'a' con data
    if (dateA === 0 && dateB === 0) {
      // Se entrambe le date mancano, ordina per ID tentativo (più basso prima)
      return a.attempt_id - b.attempt_id;
    }
    return dateB - dateA; // Decrescente per data (più recente prima)
  };

  // 1. Quiz "da iniziare" (PENDING dallo store availableQuizzes)
  // availableQuizzes dovrebbe contenere quelli con stato PENDING o comunque non ancora iniziati attivamente.
  // Filtriamo ulteriormente per assicurarci che siano effettivamente 'PENDING' o simili, se necessario,
  // ma per ora assumiamo che availableQuizzes contenga quelli da iniziare.
  const toStartQuizzes = dashboardStore.availableQuizzes
    .filter(quiz => quiz.status === 'PENDING' || !quiz.status) // Considera PENDING o senza stato come "da iniziare"
    .sort(sortLogic);

  // 2. Quiz "da continuare o ritentare"
  // inProgressOrFailedQuizzes contiene quelli con stato IN_PROGRESS o FAILED.
  const toContinueOrRetryQuizzes = dashboardStore.inProgressOrFailedQuizzes
    .sort(sortLogic);
  
  // Combina i due gruppi, con "da iniziare" prima
  const combinedTodo = [...toStartQuizzes, ...toContinueOrRetryQuizzes];
  
  // Applica il filtro di ricerca testuale all'elenco combinato e ordinato
  return filterQuizzes(combinedTodo);
});

const filteredCompletedQuizzes = computed(() => {
  return filterQuizzes(dashboardStore.completedQuizzes);
});

</script>

<template>
  <div class="quizzes-page p-4 md:p-8">
    <header class="page-header bg-accent text-neutral-lightest p-4 rounded-lg shadow-md mb-6"> <!-- Padding p-4, rimosso allineamento testo esplicito -->
      <h1 class="text-2xl font-semibold flex items-center"><span class="text-3xl mr-3">📝</span>I Miei Quiz</h1>
    </header>

    <!-- Barra di ricerca spostata qui sotto -->
    <div class="mb-6">
        <input
            type="text"
            v-model="searchTerm"
            placeholder="Cerca quiz per materia, argomento, titolo..."
            class="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-700"
        />
    </div>

    <div v-if="isLoading" class="loading-container flex flex-col items-center justify-center p-12 text-center">
      <div class="loading-spinner"></div>
      <p class="mt-4 text-neutral-dark">Caricamento quiz...</p>
    </div>

    <div v-else-if="dashboardStore.error" class="error-message bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative text-center mb-6 shadow">
      <p class="font-semibold mb-2">{{ dashboardStore.error }}</p>
    </div>

    <div v-else>
      <BaseTabs :tabs="quizPageTabs">
        <template #todoQuizzes>
          <QuizList
            :quizzes="sortedTodoQuizzes"
            title="Quiz da Svolgere"
            emptyMessage="Non ci sono quiz da fare al momento."
            :loading="dashboardStore.loading.quizzes"
            :showStartButton="true"
            displayMode="grid">
          </QuizList>
        </template>

        <template #completedQuizzes>
          <QuizList
            :quizzes="filteredCompletedQuizzes"
            title="Quiz Completati"
            emptyMessage="Non hai ancora completato nessun quiz."
            :loading="dashboardStore.loading.quizzes"
            displayMode="grid">
          </QuizList>
        </template>
      </BaseTabs>
    </div>
  </div>
</template>

<style scoped>
.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid theme('colors.primary.light / 30%');
  border-left-color: theme('colors.primary.DEFAULT');
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>