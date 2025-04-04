<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import PathwayService from '@/api/pathway';
import type { PathwayAttemptDetails, NextQuizInfo } from '@/api/pathway';

const route = useRoute();
const router = useRouter();
const pathwayId = ref<number | null>(null);
const pathwayAttemptData = ref<PathwayAttemptDetails | null>(null);
const isLoading = ref(true);
const error = ref<string | null>(null);

const pathwayDetails = computed(() => pathwayAttemptData.value);
const currentQuiz = computed(() => pathwayAttemptData.value?.next_quiz);

const completionPercentage = computed(() => {
  if (!pathwayDetails.value || !pathwayDetails.value.progress || !pathwayDetails.value.quiz_details || pathwayDetails.value.quiz_details.length === 0) {
    return 0;
  }
  const completedOrders = Array.isArray(pathwayDetails.value.progress.completed_orders)
                          ? pathwayDetails.value.progress.completed_orders
                          : [];
  const completedCount = completedOrders.length;
  const totalCount = pathwayDetails.value.quiz_details.length;
  return Math.round((completedCount / totalCount) * 100);
});

const isQuizCompleted = (quizOrder: number): boolean => {
  const completedOrders = pathwayDetails.value?.progress?.completed_orders;
  return Array.isArray(completedOrders) ? completedOrders.includes(quizOrder) : false;
};

// --- Helper functions for classes ---
// Using 'any' for quizItem temporarily to avoid potential type issues if PathwayQuizDetail is not correctly defined/imported elsewhere
const getLiClass = (quizItem: any) => {
  const completed = isQuizCompleted(quizItem.order);
  // Corrected: use &&
  const isCurrent = currentQuiz.value && quizItem.quiz_id === currentQuiz.value.id && !completed;
  return {
    'bg-green-50 border border-green-200': completed,
    'bg-blue-50 border border-blue-200': isCurrent,
    // Corrected: use &&
    'bg-gray-50 border border-gray-200': !completed && !isCurrent
  };
};

const getSpanClass = (quizItem: any) => {
   const completed = isQuizCompleted(quizItem.order);
   // Corrected: use &&
   const isCurrent = currentQuiz.value && quizItem.quiz_id === currentQuiz.value.id && !completed;
   return {
     'text-green-800': completed,
     'text-blue-800': isCurrent,
     // Corrected: use &&
     'text-gray-600': !completed && !isCurrent
   };
};
// --- End Helper functions ---


onMounted(async () => {
  console.log('PathwayAttemptView onMounted hook started.'); // Added console log
  const id = Number(route.params.pathwayId);
  if (isNaN(id)) {
    error.value = 'ID Percorso non valido.';
    isLoading.value = false;
    return;
  }
  pathwayId.value = id;

  try {
    isLoading.value = true;
    error.value = null;
    console.log(`Caricamento dettagli tentativo per percorso ID: ${id}`);
    pathwayAttemptData.value = await PathwayService.getPathwayAttemptDetails(id);
    console.log('Dettagli tentativo percorso caricati:', pathwayAttemptData.value);
  } catch (err: any) {
    console.error('Errore durante il caricamento del tentativo del percorso:', err);
    // Corrected: use &&
    if (err.response && err.response.status === 403) {
         error.value = 'Non sei autorizzato a visualizzare questo percorso o non ti è stato assegnato.';
    // Corrected: use &&
    } else if (err.response && err.response.status === 404) {
         error.value = 'Percorso non trovato.';
    } else {
        error.value = 'Impossibile caricare i dettagli del percorso. Riprova più tardi.';
    }
  } finally {
    isLoading.value = false;
  }
});

const startSpecificQuiz = (quizId: number) => {
  if (quizId) {
    console.log(`Avvio quiz ID: ${quizId} per il percorso ID: ${pathwayId.value}`);
    router.push({ name: 'quiz-start-attempt', params: { quizId: quizId } });
  } else {
    console.error('ID Quiz non valido.');
    error.value = 'Impossibile avviare il quiz selezionato.';
  }
};

const goBackToDashboard = () => {
  router.push({ name: 'dashboard' });
};
</script>

<template>
  <div class="pathway-attempt-view p-4 md:p-8 bg-gray-100 min-h-screen">
    <button @click="goBackToDashboard" class="back-button mb-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
      </svg>
      Torna alla Dashboard
    </button>

    <div v-if="isLoading" class="loading-container text-center py-12">
      <div class="loading-spinner inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <p class="mt-4 text-gray-600">Caricamento percorso...</p>
    </div>

    <div v-else-if="error" class="error-message bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-else-if="pathwayDetails" class="pathway-content bg-white p-6 rounded-lg shadow-md">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">{{ pathwayDetails.title }}</h1>
      <p class="text-gray-600 mb-6">{{ pathwayDetails.description }}</p>

       <div v-if="pathwayDetails.progress" class="progress-info mb-6 border-b pb-4">
         <h2 class="text-lg font-semibold text-gray-700 mb-2">Il Tuo Progresso</h2>
         <div class="flex justify-between items-center mb-1">
            <p>Stato: <span class="font-medium">{{ pathwayDetails.progress.status_display }}</span></p>
            <p class="text-sm font-semibold text-indigo-600">{{ completionPercentage }}% Completato</p>
         </div>
         <div class="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
            <div class="bg-indigo-600 h-2.5 rounded-full transition-all duration-500 ease-out" :style="{ width: completionPercentage + '%' }"></div>
         </div>
       </div>

      <div class="pathway-quiz-list mt-8 border-t pt-6">
        <h3 class="text-lg font-semibold text-gray-700 mb-3">Quiz nel Percorso:</h3>
        <ul class="space-y-2">
          <li v-for="quizItem in pathwayDetails.quiz_details" :key="quizItem.quiz_id"
              class="p-3 rounded-md flex justify-between items-center"
              :class="getLiClass(quizItem)">
            <div class="flex-grow">
              <span class="font-medium" :class="getSpanClass(quizItem)">
                {{ quizItem.order + 1 }}. {{ quizItem.quiz_title }}
              </span>
              <span v-if="isQuizCompleted(quizItem.order)" class="ml-2 text-xs font-semibold text-green-600">(Completato)</span>
               <span v-if="currentQuiz && quizItem.quiz_id === currentQuiz.id && !isQuizCompleted(quizItem.order)" class="ml-2 text-xs font-semibold text-blue-600">(Prossimo)</span>
            </div>
            <button
              @click="startSpecificQuiz(quizItem.quiz_id)"
              class="ml-4 px-3 py-1 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              :class="{ 'opacity-50 cursor-not-allowed': isQuizCompleted(quizItem.order) }"
              :disabled="isQuizCompleted(quizItem.order)"
              >
              {{ isQuizCompleted(quizItem.order) ? 'Rivedi?' : 'Avvia' }}
            </button>
          </li>
        </ul>
      </div>

       <!-- Link ai risultati finali se il percorso è completato -->
       <!-- Corretto: usa && -->
       <div v-if="pathwayDetails.progress && pathwayDetails.progress.status === 'COMPLETED'" class="mt-8 text-center">
         <router-link :to="{ name: 'PathwayResult', params: { pathwayId: pathwayId } }" class="text-blue-600 hover:underline">
            Vedi Risultati Finali del Percorso
          </router-link>
       </div>

    </div>
  </div>
</template>

<style scoped>
/* Stili specifici se necessario, altrimenti usa Tailwind */
.loading-spinner {
  /* Tailwind 'animate-spin' applicato direttamente */
}
</style>