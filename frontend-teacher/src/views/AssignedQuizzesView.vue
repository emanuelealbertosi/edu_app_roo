<template>
  <div class="assigned-quizzes-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Quiz Assegnati (Istanze)</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="opacity-90">Qui puoi visualizzare le istanze concrete dei quiz che hai assegnato.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>
    <!-- Non c'è un pulsante "Crea" qui, le istanze vengono create tramite assegnazione -->

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento quiz assegnati...</div> <!-- Stile loading aggiornato -->
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert"> <!-- Stile errore aggiornato -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento dei quiz assegnati: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="assignedQuizzes.length > 0" class="shadow-md rounded-lg mt-6"> <!-- Rimosso overflow-x-auto -->
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white"> <!-- Stile tabella aggiornato -->
        <thead class="bg-neutral-lightest"> <!-- Stile thead aggiornato -->
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Titolo Istanza</th> <!-- Stile th aggiornato -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Template Sorgente</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th> <!-- Azioni limitate sulle istanze? -->
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT"> <!-- Stile tbody aggiornato -->
          <tr v-for="quiz in assignedQuizzes" :key="quiz.id" class="hover:bg-neutral-lightest transition-colors duration-150"> <!-- Stile tr aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ quiz.title }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ quiz.description || '-' }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ quiz.source_template ? `ID: ${quiz.source_template}` : 'N/D' }}</td> <!-- Simplified display, stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ new Date(quiz.created_at).toLocaleDateString() }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Spazio ok -->
              <!-- Forse solo visualizzazione dettagli o statistiche? Modifica/Eliminazione potrebbe essere problematica -->
              <BaseButton variant="info" size="sm" @click="viewQuizDetails(quiz.id)">Dettagli</BaseButton> <!-- Usa BaseButton -->
              <!-- L'eliminazione di un'istanza assegnata potrebbe richiedere logica aggiuntiva (es. rimuovere assegnazioni) -->
              <!-- <BaseButton variant="danger" size="sm" @click="deleteAssignedQuiz(quiz.id)">Elimina Istanza</BaseButton> -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark"> <!-- Stile no quizzes aggiornato -->
      Nessun quiz assegnato trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa API per fetchare le istanze Quiz concrete
import { fetchQuizzes, deleteQuizApi, type Quiz } from '@/api/quizzes';
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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