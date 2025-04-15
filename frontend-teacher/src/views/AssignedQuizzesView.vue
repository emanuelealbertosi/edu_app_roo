<template>
  <div class="assigned-quizzes-view">
    <h1>Quiz Assegnati (Istanze)</h1>
    <p>Qui puoi visualizzare le istanze concrete dei quiz che hai assegnato.</p>
    <!-- Rimosso commento che poteva causare problemi con v-if -->

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
            <th>Azioni</th>
          </tr>
        </thead>
        <!-- Modificato tbody per usare template e gestire righe multiple per quiz -->
        <template v-for="quiz in assignedQuizzes" :key="quiz.id">
          <tbody>
          <tr>
            <td>{{ quiz.title }}</td>
            <td>{{ quiz.description || '-' }}</td>
            <td>{{ quiz.source_template ? `ID: ${quiz.source_template}` : 'Nessuno (Creato manualmente)' }}</td>
            <td>{{ new Date(quiz.created_at).toLocaleDateString() }}</td>
            <td>
              <button @click="toggleAssignments(quiz.id)" class="btn btn-secondary btn-sm">
                 {{ selectedQuizId === quiz.id ? 'Nascondi' : 'Visualizza' }} Assegnazioni
              </button>
              <!-- <button @click="deleteAssignedQuiz(quiz.id)" class="delete bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm">Elimina Istanza</button> -->
            </td>
          </tr>
          <!-- Riga aggiuntiva per visualizzare le assegnazioni, visibile solo se selezionato -->
          <tr v-if="selectedQuizId === quiz.id">
            <td :colspan="5">
              <div v-if="isLoadingAssignments" class="loading small">Caricamento assegnazioni...</div>
              <div v-else-if="assignmentsError" class="error-message small">Errore: {{ assignmentsError }}</div>
              <div v-else-if="selectedQuizAssignments && selectedQuizAssignments.length > 0">
                <h4 class="text-md font-semibold mt-2 mb-1">Studenti Assegnati:</h4>
                <ul class="assignment-list">
                  <li v-for="(assignment, index) in selectedQuizAssignments" :key="assignment.id">
                    <span>
                      <router-link
                        :to="{ name: 'student-detail', params: { id: assignment.student_id } }"
                        class="text-blue-600 hover:underline"
                      >
                        <strong>{{ assignment.student_full_name }}</strong>
                      </router-link>
                       ({{ assignment.student_username }})
                      - Ass: {{ new Date(assignment.assigned_at).toLocaleDateString() }}
                      <span v-if="assignment.due_date"> - Scad: {{ new Date(assignment.due_date).toLocaleDateString() }}</span>
                    </span>
                    <button
                      @click="handleUnassignQuiz(assignment.id, quiz.id)"
                      class="btn btn-danger btn-xs ml-2"
                      :disabled="isUnassigning === assignment.id"
                    >
                      {{ isUnassigning === assignment.id ? '...' : 'Disassegna' }}
                    </button>
                  </li>
                </ul>
                <div v-if="unassignError" class="error-message small mt-2">Errore disassegnazione: {{ unassignError }}</div>
              </div>
              <p v-else class="no-assignments">Nessuno studente assegnato a questo quiz.</p>
            </td>
          </tr>
          </tbody>
        </template> <!-- Fine template v-for -->
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
// Importa API per fetchare le istanze Quiz concrete e le assegnazioni
import {
  fetchQuizzes, deleteQuizApi, type Quiz,
  fetchQuizAssignments, type QuizAssignmentDetail, unassignQuizFromStudent
} from '@/api/quizzes';

const assignedQuizzes = ref<Quiz[]>([]); // Usa il tipo Quiz per le istanze
const isLoading = ref(false);
const router = useRouter();
const error = ref<string | null>(null); // Errore caricamento quiz
const unassignError = ref<string | null>(null); // Errore disassegnazione

// Stato per visualizzare le assegnazioni di un quiz specifico
const selectedQuizId = ref<number | null>(null);
const selectedQuizAssignments = ref<QuizAssignmentDetail[] | null>(null);
const isLoadingAssignments = ref(false);
const assignmentsError = ref<string | null>(null);
const isUnassigning = ref<number | null>(null); // ID dell'assegnazione in corso di disassegnazione

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

// Funzione per mostrare/nascondere e caricare le assegnazioni di un quiz
const toggleAssignments = async (quizId: number) => {
  if (selectedQuizId.value === quizId) {
    // Se clicco sullo stesso quiz, nascondo i dettagli
    selectedQuizId.value = null;
    selectedQuizAssignments.value = null;
    assignmentsError.value = null;
    unassignError.value = null;
  } else {
    // Altrimenti, carico le assegnazioni per il nuovo quiz selezionato
    selectedQuizId.value = quizId;
    selectedQuizAssignments.value = null; // Resetta prima di caricare
    isLoadingAssignments.value = true;
    assignmentsError.value = null;
    unassignError.value = null;
    console.log(`Recupero assegnazioni per quiz ${quizId}...`);
    try {
      const response = await fetchQuizAssignments(quizId); // Recupera l'oggetto risposta
      console.log('Assegnazioni recuperate (oggetto completo):', response);
      // Estrai l'array 'assignments' dall'oggetto risposta
      selectedQuizAssignments.value = response.assignments;
      console.log('Assegnazioni recuperate:', selectedQuizAssignments.value);
    } catch (err: any) {
      console.error(`Errore nel recupero delle assegnazioni per quiz ${quizId}:`, err);
      assignmentsError.value = err.message || 'Errore sconosciuto nel recupero delle assegnazioni.';
    } finally {
      isLoadingAssignments.value = false;
    }
  }
};

// Funzione per gestire la disassegnazione di un quiz da uno studente
const handleUnassignQuiz = async (assignmentId: number, quizId: number) => {
  unassignError.value = null;
  isUnassigning.value = assignmentId; // Mostra stato caricamento sul bottone specifico
  const confirmationMessage = `Sei sicuro di voler disassegnare questo quiz (ID Assegnazione: ${assignmentId})?`;

  if (!confirm(confirmationMessage)) {
    isUnassigning.value = null;
    return;
  }

  try {
    await unassignQuizFromStudent(assignmentId);
    alert(`Quiz disassegnato con successo.`);
    // Rimuovi l'assegnazione dalla lista locale per aggiornare l'UI
    if (selectedQuizId.value === quizId && selectedQuizAssignments.value) {
      selectedQuizAssignments.value = selectedQuizAssignments.value.filter(a => a.id !== assignmentId);

      // Se la lista delle assegnazioni per questo quiz è ora vuota,
      // rimuovi il quiz dalla lista principale 'assignedQuizzes'.
      if (selectedQuizAssignments.value.length === 0) {
        assignedQuizzes.value = assignedQuizzes.value.filter(q => q.id !== quizId);
        // Nascondi anche la sezione delle assegnazioni (opzionale, ma pulito)
        selectedQuizId.value = null;
      }
    }
  } catch (err: any) {
    console.error(`Errore durante la disassegnazione del quiz (Assignment ID: ${assignmentId}):`, err);
    unassignError.value = err.response?.data?.detail || err.message || `Errore sconosciuto durante la disassegnazione.`;
  } finally {
    isUnassigning.value = null; // Resetta stato caricamento bottone
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
/* Stili simili a QuizTemplatesView e StudentsView */
.assigned-quizzes-view {
  padding: 20px;
}
.loading, .error-message, .no-quizzes, .no-assignments {
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
  vertical-align: top; /* Allinea in alto per la riga espansa */
}
th {
  background-color: #f2f2f2;
}
.assignment-list {
  list-style: disc;
  margin-left: 20px;
  margin-top: 5px;
}
.assignment-list li {
  margin-bottom: 5px;
  display: flex; /* Per allineare bottone */
  justify-content: space-between; /* Spazio tra testo e bottone */
  align-items: center;
}
.no-assignments {
    font-style: italic;
    color: #888;
    margin-top: 5px;
}
.loading.small, .error-message.small {
    font-size: 0.9em;
    margin-top: 5px;
    padding: 10px; /* Aggiunge padding dentro la cella */
}
.btn-xs {
    padding: 2px 6px;
    font-size: 0.8rem;
    line-height: 1.2;
    border-radius: 0.2rem;
}
.ml-2 {
    margin-left: 0.5rem; /* 8px */
}
</style>