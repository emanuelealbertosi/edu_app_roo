<template>
  <div class="student-detail-view p-6">
    <div v-if="isLoading" class="loading">Caricamento dettagli studente...</div>
    <div v-else-if="error" class="error-message">Errore: {{ error }}</div>
    <div v-else-if="studentData">
      <h2 class="text-2xl font-semibold mb-4">
        Dettagli Studente: {{ studentData.full_name }}
      </h2>

      <!-- Sezione Dati Anagrafici -->
      <div class="card mb-6">
        <h3 class="card-header">Informazioni Studente</h3>
        <div class="card-body grid grid-cols-1 md:grid-cols-2 gap-4">
          <p><strong>ID:</strong> {{ studentData.id }}</p>
          <p><strong>Username:</strong> {{ studentData.username }}</p>
          <p><strong>Nome:</strong> {{ studentData.first_name }}</p>
          <p><strong>Cognome:</strong> {{ studentData.last_name }}</p>
          <p><strong>Codice Studente:</strong> <code>{{ studentData.student_code }}</code></p>
          <p><strong>Stato:</strong> {{ studentData.is_active ? 'Attivo' : 'Non Attivo' }}</p>
          <p><strong>Docente:</strong> {{ studentData.teacher_username }}</p>
          <p v-if="studentData.created_at"><strong>Creato il:</strong> {{ new Date(studentData.created_at).toLocaleDateString() }}</p>
        </div>
      </div>

      <!-- Sezione Statistiche Progresso -->
      <div class="card mb-6">
        <h3 class="card-header">Statistiche Progresso</h3>
        <div v-if="isLoadingStats" class="loading small p-4">Caricamento statistiche...</div>
        <div v-else-if="statsError" class="error-message small p-4">Errore statistiche: {{ statsError }}</div>
        <div v-else-if="studentStats" class="card-body grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="stat-item">
                <span class="stat-label">Quiz Completati:</span>
                <span class="stat-value">{{ studentStats.completed_quizzes_count }}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Percorsi Completati:</span>
                <span class="stat-value">{{ studentStats.completed_pathways_count }}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Punti Guadagnati:</span>
                <span class="stat-value">{{ studentStats.total_points_earned }}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Punteggio Medio Quiz (%):</span>
                <span class="stat-value">{{ studentStats.average_quiz_score }}</span>
            </div>
        </div>
         <div v-else class="p-4 text-gray-500 italic">Nessuna statistica disponibile.</div>
      </div>

      <!-- Sezione Assegnazioni -->
      <div class="card">
        <h3 class="card-header">Assegnazioni</h3>
        <div v-if="isLoadingAssignments" class="loading small p-4">Caricamento assegnazioni...</div>
        <div v-else-if="assignmentsError" class="error-message small p-4">Errore assegnazioni: {{ assignmentsError }}</div>
        <div v-else-if="studentAssignments">
          <div class="p-4">
            <h4 class="text-lg font-semibold mb-2">Quiz Assegnati</h4>
            <ul v-if="studentAssignments.quiz_assignments.length > 0" class="list-disc ml-5 space-y-1">
              <li v-for="quizAssign in studentAssignments.quiz_assignments" :key="`q-${quizAssign.id}`">
                 {{ quizAssign.quiz_title }}
                 (Ass: {{ new Date(quizAssign.assigned_at).toLocaleDateString() }}
                 <span v-if="quizAssign.due_date">, Scad: {{ new Date(quizAssign.due_date).toLocaleDateString() }}</span>)
                 <!-- TODO: Aggiungere link a dettagli tentativo se disponibile -->
              </li>
            </ul>
            <p v-else class="text-gray-500 italic">Nessun quiz assegnato.</p>

            <h4 class="text-lg font-semibold mt-4 mb-2">Percorsi Assegnati</h4>
            <ul v-if="studentAssignments.pathway_assignments.length > 0" class="list-disc ml-5 space-y-1">
               <li v-for="pathwayAssign in studentAssignments.pathway_assignments" :key="`p-${pathwayAssign.id}`">
                 {{ pathwayAssign.pathway_title }}
                 (Ass: {{ new Date(pathwayAssign.assigned_at).toLocaleDateString() }})
                 <!-- TODO: Aggiungere link a dettagli progresso percorso se disponibile -->
               </li>
            </ul>
             <p v-else class="text-gray-500 italic">Nessun percorso assegnato.</p>
          </div>
        </div>
         <div v-else class="p-4 text-gray-500 italic">Nessuna assegnazione trovata.</div>
      </div>

      <div class="mt-6">
        <router-link :to="{ name: 'students' }" class="btn btn-secondary">Torna a Elenco Studenti</router-link>
      </div>

    </div>
    <div v-else class="error-message">Studente non trovato.</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router'; // Per accedere ai parametri della rotta
import { fetchStudentById, fetchStudentAssignments, fetchStudentProgressSummary, type Student, type StudentAssignmentsResponse, type StudentProgressSummary } from '@/api/students'; // Assicurati che l'API abbia fetchStudentById e fetchStudentProgressSummary

// Props definite nella rotta
const props = defineProps<{
  studentId: number;
}>();

const route = useRoute(); // Non necessario se usiamo props, ma può essere utile

const studentData = ref<Student | null>(null);
const studentStats = ref<StudentProgressSummary | null>(null);
const studentAssignments = ref<StudentAssignmentsResponse | null>(null);

const isLoading = ref(false);
const isLoadingStats = ref(false);
const isLoadingAssignments = ref(false);

const error = ref<string | null>(null);
const statsError = ref<string | null>(null);
const assignmentsError = ref<string | null>(null);

const loadStudentData = async (id: number) => {
  isLoading.value = true;
  error.value = null;
  try {
    studentData.value = await fetchStudentById(id);
  } catch (err: any) {
    console.error(`Errore caricamento studente ${id}:`, err);
    error.value = err.response?.data?.detail || err.message || 'Errore sconosciuto.';
    studentData.value = null; // Resetta in caso di errore
  } finally {
    isLoading.value = false;
  }
};

const loadStudentStats = async (id: number) => {
  isLoadingStats.value = true;
  statsError.value = null;
  try {
    // fetchStudentProgressSummary deve restituire un array, prendiamo il primo elemento
    const statsArray = await fetchStudentProgressSummary(id);
    if (statsArray && statsArray.length > 0) {
        studentStats.value = statsArray[0];
    } else {
        studentStats.value = null; // Nessuna statistica trovata
    }
  } catch (err: any) {
    console.error(`Errore caricamento statistiche studente ${id}:`, err);
    statsError.value = err.response?.data?.detail || err.message || 'Errore sconosciuto.';
    studentStats.value = null;
  } finally {
    isLoadingStats.value = false;
  }
};

const loadStudentAssignments = async (id: number) => {
  isLoadingAssignments.value = true;
  assignmentsError.value = null;
  try {
    studentAssignments.value = await fetchStudentAssignments(id);
  } catch (err: any) {
    console.error(`Errore caricamento assegnazioni studente ${id}:`, err);
    assignmentsError.value = err.response?.data?.detail || err.message || 'Errore sconosciuto.';
    studentAssignments.value = null;
  } finally {
    isLoadingAssignments.value = false;
  }
};

// Carica i dati quando il componente viene montato o l'ID cambia
onMounted(() => {
  loadStudentData(props.studentId);
  loadStudentStats(props.studentId);
  loadStudentAssignments(props.studentId);
});

// Opzionale: ricarica se l'ID nella rotta cambia (utile se si naviga tra dettagli studenti)
watch(() => props.studentId, (newId) => {
  loadStudentData(newId);
  loadStudentStats(newId);
  loadStudentAssignments(newId);
});

</script>

<style scoped>
.card {
  border: 1px solid #e2e8f0; /* gray-300 */
  border-radius: 0.375rem; /* rounded-md */
  background-color: white;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}
.card-header {
  background-color: #f9fafb; /* gray-50 */
  padding: 0.75rem 1rem;
  font-weight: 600;
  border-bottom: 1px solid #e2e8f0; /* gray-300 */
  border-top-left-radius: 0.375rem;
  border-top-right-radius: 0.375rem;
}
.card-body {
  padding: 1rem;
}
.stat-item {
  background-color: #f3f4f6; /* gray-100 */
  padding: 0.75rem;
  border-radius: 0.25rem;
  border: 1px solid #e5e7eb; /* gray-200 */
}
.stat-label {
    display: block;
    font-size: 0.875rem; /* text-sm */
    color: #4b5563; /* gray-600 */
    margin-bottom: 0.25rem;
}
.stat-value {
    display: block;
    font-size: 1.5rem; /* text-2xl */
    font-weight: 700; /* font-bold */
    color: #1f2937; /* gray-800 */
}

code {
  background-color: #e5e7eb; /* gray-200 */
  padding: 0.1rem 0.3rem;
  border-radius: 0.25rem;
  font-family: monospace;
}

.loading, .error-message {
  margin-top: 1rem;
  font-style: italic;
  color: #666;
}
.error-message {
  color: red;
  font-weight: bold;
}
.loading.small, .error-message.small {
    font-size: 0.9em;
}
</style>