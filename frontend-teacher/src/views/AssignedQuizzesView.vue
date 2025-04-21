<template>
  <div class="assigned-quizzes-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-4">Quiz Assegnati (Istanze)</h1> <!-- Styled heading -->
    <p class="text-gray-600 mb-6">Qui puoi visualizzare le istanze concrete dei quiz che hai assegnato.</p> <!-- Styled paragraph -->
    <!-- Non c'è un pulsante "Crea" qui, le istanze vengono create tramite assegnazione -->

    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento quiz assegnati...</div> <!-- Styled loading -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento dei quiz assegnati: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="assignedQuizzes.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-gray-200 bg-white">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titolo Istanza</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Template Sorgente</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th> <!-- Azioni limitate sulle istanze? -->
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="quiz in assignedQuizzes" :key="quiz.id" class="hover:bg-gray-50 transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ quiz.title }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ quiz.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ quiz.source_template ? `ID: ${quiz.source_template}` : 'N/D' }}</td> <!-- Simplified display -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ new Date(quiz.created_at).toLocaleDateString() }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Added space-x-2 -->
              <!-- Forse solo visualizzazione dettagli o statistiche? Modifica/Eliminazione potrebbe essere problematica -->
              <button @click="viewQuizDetails(quiz.id)" class="btn btn-info btn-sm">Dettagli</button> <!-- Changed style -->
              <!-- L'eliminazione di un'istanza assegnata potrebbe richiedere logica aggiuntiva (es. rimuovere assegnazioni) -->
              <!-- <button @click="deleteAssignedQuiz(quiz.id)" class="btn btn-danger btn-sm">Elimina Istanza</button> -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-gray-500"> <!-- Styled no quizzes -->
      Nessun quiz assegnato trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa API per fetchare le istanze Quiz concrete
import { fetchQuizzes, deleteQuizApi, type Quiz } from '@/api/quizzes';

const assignedQuizzes = ref<Quiz[]>([]); // Usa il tipo Quiz per le istanze
const isLoading = ref(false);
const router = useRouter();
const error = ref<string | null>(null);

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
  // TODO: Implementare una vista dettagli read-only per le istanze quiz o riutilizzare QuizFormView in modalità read-only?
  console.warn(`Visualizzazione dettagli per quiz istanza ${id} non implementata.`);
  // router.push({ name: 'assigned-quiz-details', params: { id: id.toString() } }); // Rotta ipotetica
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