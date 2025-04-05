<template>
  <div class="assigned-quizzes-view">
    <h1>Quiz Assegnati (Istanze)</h1>
    <p>Qui puoi visualizzare le istanze concrete dei quiz che hai assegnato.</p>
    <!-- Non c'è un pulsante "Crea" qui, le istanze vengono create tramite assegnazione -->

    <div v-if="isLoading" class="loading">Caricamento quiz assegnati...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento dei quiz assegnati: {{ error }}
    </div>
    <div v-else-if="assignedQuizzes.length > 0" class="quizzes-list">
      <table>
        <thead>
          <tr>
            <th>Titolo Istanza</th>
            <th>Descrizione</th>
            <th>Template Sorgente</th>
            <th>Creato il</th>
            <th>Azioni</th> <!-- Azioni limitate sulle istanze? -->
          </tr>
        </thead>
        <tbody>
          <tr v-for="quiz in assignedQuizzes" :key="quiz.id">
            <td>{{ quiz.title }}</td>
            <td>{{ quiz.description || '-' }}</td>
            <td>{{ quiz.source_template ? `ID: ${quiz.source_template}` : 'Nessuno (Creato manualmente)' }}</td>
            <td>{{ new Date(quiz.created_at).toLocaleDateString() }}</td>
            <td>
              <!-- Forse solo visualizzazione dettagli o statistiche? Modifica/Eliminazione potrebbe essere problematica -->
              <button @click="viewQuizDetails(quiz.id)" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded text-sm mr-2">Dettagli</button>
              <!-- L'eliminazione di un'istanza assegnata potrebbe richiedere logica aggiuntiva (es. rimuovere assegnazioni) -->
              <!-- <button @click="deleteAssignedQuiz(quiz.id)" class="delete bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm">Elimina Istanza</button> -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="no-quizzes">
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
/* Stili simili a QuizTemplatesView */
.assigned-quizzes-view {
  padding: 20px;
}
.loading, .error-message, .no-quizzes {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
.error-message {
  color: red;
  font-weight: bold;
}
.quizzes-list {
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
</style>