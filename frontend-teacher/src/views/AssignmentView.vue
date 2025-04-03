<template>
  <div class="assignment-view">
    <h1>Assegna Contenuti</h1>

    <div class="content-selection">
      <div class="form-group">
        <label for="content-type">Tipo Contenuto:</label>
        <select id="content-type" v-model="selectedContentType">
          <option value="quiz">Quiz</option>
          <option value="pathway">Percorso</option>
        </select>
      </div>

      <div class="form-group" v-if="selectedContentType === 'quiz'">
        <label for="quiz-select">Seleziona Quiz:</label>
        <select id="quiz-select" v-model="selectedContentId" :disabled="isLoadingQuizzes">
          <option disabled value="">{{ isLoadingQuizzes ? 'Caricamento...' : 'Seleziona un Quiz' }}</option>
          <option v-for="quiz in availableQuizzes" :key="quiz.id" :value="quiz.id">
            {{ quiz.title }}
          </option>
        </select>
        <div v-if="quizzesError" class="error-message small">{{ quizzesError }}</div>
      </div>

      <div class="form-group" v-if="selectedContentType === 'pathway'">
        <label for="pathway-select">Seleziona Percorso:</label>
        <select id="pathway-select" v-model="selectedContentId" :disabled="isLoadingPathways">
           <option disabled value="">{{ isLoadingPathways ? 'Caricamento...' : 'Seleziona un Percorso' }}</option>
           <option v-for="pathway in availablePathways" :key="pathway.id" :value="pathway.id">
            {{ pathway.title }}
          </option>
        </select>
         <div v-if="pathwaysError" class="error-message small">{{ pathwaysError }}</div>
      </div>
    </div>

    <div class="student-selection">
      <h2>Seleziona Studenti</h2>
      <div v-if="isLoadingStudents" class="loading">Caricamento studenti...</div>
      <div v-else-if="studentsError" class="error-message">{{ studentsError }}</div>
      <div v-else-if="availableStudents.length > 0">
         <div class="form-group">
             <label>
                 <input type="checkbox" @change="toggleSelectAllStudents" :checked="allStudentsSelected" />
                 Seleziona Tutti
             </label>
         </div>
         <ul class="student-list">
            <li v-for="student in availableStudents" :key="student.id">
              <label>
                <input type="checkbox" :value="student.id" v-model="selectedStudentIds" />
                {{ student.first_name }} {{ student.last_name }} ({{ student.username }})
              </label>
            </li>
         </ul>
      </div>
       <div v-else>Nessuno studente trovato.</div>
    </div>

    <div class="form-actions">
        <!-- Applicato stile Tailwind -->
        <button
            @click="assignContent"
            :disabled="!canAssign || isAssigning"
            class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
            {{ isAssigning ? 'Assegnazione...' : 'Assegna Selezionati' }}
        </button>
        <div v-if="assignmentError" class="error-message">{{ assignmentError }}</div>
        <div v-if="assignmentSuccess" class="success-message">{{ assignmentSuccess }}</div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { fetchStudents, type Student } from '@/api/students';
import { fetchQuizzes, type Quiz } from '@/api/quizzes';
import { fetchPathways, type Pathway } from '@/api/pathways';
import axios from 'axios'; // Per le chiamate API di assegnazione

// --- Stato Selezione Contenuto ---
const selectedContentType = ref<'quiz' | 'pathway'>('quiz');
const selectedContentId = ref<number | ''>('');

// --- Stato Caricamento Contenuti ---
const availableQuizzes = ref<Quiz[]>([]);
const isLoadingQuizzes = ref(false);
const quizzesError = ref<string | null>(null);
const availablePathways = ref<Pathway[]>([]);
const isLoadingPathways = ref(false);
const pathwaysError = ref<string | null>(null);

// --- Stato Caricamento Studenti ---
const availableStudents = ref<Student[]>([]);
const isLoadingStudents = ref(false);
const studentsError = ref<string | null>(null);
const selectedStudentIds = ref<number[]>([]);

// --- Stato Assegnazione ---
const isAssigning = ref(false);
const assignmentError = ref<string | null>(null);
const assignmentSuccess = ref<string | null>(null);

// --- Logica Caricamento Dati ---
const loadQuizzes = async () => {
  isLoadingQuizzes.value = true;
  quizzesError.value = null;
  try {
    availableQuizzes.value = await fetchQuizzes();
  } catch (err) {
    quizzesError.value = 'Errore caricamento quiz.';
    console.error(err);
  } finally {
    isLoadingQuizzes.value = false;
  }
};

const loadPathways = async () => {
  isLoadingPathways.value = true;
  pathwaysError.value = null;
  try {
    availablePathways.value = await fetchPathways();
  } catch (err) {
     pathwaysError.value = 'Errore caricamento percorsi.';
     console.error(err);
  } finally {
    isLoadingPathways.value = false;
  }
};

const loadStudents = async () => {
  isLoadingStudents.value = true;
  studentsError.value = null;
  try {
    availableStudents.value = await fetchStudents();
  } catch (err) {
     studentsError.value = 'Errore caricamento studenti.';
     console.error(err);
  } finally {
    isLoadingStudents.value = false;
  }
};

onMounted(() => {
  loadQuizzes();
  loadPathways();
  loadStudents();
});

// --- Logica Selezione Studenti ---
const allStudentsSelected = computed(() =>
    availableStudents.value.length > 0 &&
    selectedStudentIds.value.length === availableStudents.value.length
);

const toggleSelectAllStudents = (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.checked) {
        selectedStudentIds.value = availableStudents.value.map(s => s.id);
    } else {
        selectedStudentIds.value = [];
    }
};

// --- Logica Assegnazione ---
const canAssign = computed(() =>
    selectedContentId.value !== '' && selectedStudentIds.value.length > 0
);

import apiClient from '@/api/config'; // Importa apiClient
// Funzione helper per chiamare l'API di assegnazione
const assignApiCall = async (url: string, studentId: number) => {
    // Usa direttamente apiClient importato da config.ts
    // Assicurati che apiClient sia importato correttamente
    // import apiClient from '@/api/config'; // Aggiungi questo import se manca
    try {
        await apiClient.post(url, { student_id: studentId });
        return { success: true, studentId };
    } catch (error: unknown) {
        let errorMessage = `Errore assegnazione a studente ${studentId}`;
        if (axios.isAxiosError(error)) {
            errorMessage += `: ${error.response?.data?.detail || error.response?.data?.status || error.message}`;
        } else if (error instanceof Error) {
            errorMessage += `: ${error.message}`;
        }
        console.error(errorMessage);
        return { success: false, studentId, error: errorMessage };
    }
};


const assignContent = async () => {
  if (!canAssign.value) return;

  isAssigning.value = true;
  assignmentError.value = null;
  assignmentSuccess.value = null;

  const contentId = selectedContentId.value;
  const studentsToAssign = [...selectedStudentIds.value]; // Copia l'array
  let baseUrl = '';

  if (selectedContentType.value === 'quiz') {
    baseUrl = `/education/quizzes/${contentId}/assign-student/`;
  } else if (selectedContentType.value === 'pathway') {
    baseUrl = `/education/pathways/${contentId}/assign-student/`;
  } else {
    assignmentError.value = "Tipo di contenuto non valido.";
    isAssigning.value = false;
    return;
  }

  const results = await Promise.all(
      studentsToAssign.map(studentId => assignApiCall(baseUrl, studentId))
  );

  const successfulAssignments = results.filter(r => r.success).length;
  const failedAssignments = results.filter(r => !r.success);

  if (failedAssignments.length > 0) {
      assignmentError.value = `Errore durante l'assegnazione a ${failedAssignments.length} studenti. Controlla la console per i dettagli.`;
      // Potresti voler mostrare gli ID specifici o i messaggi di errore
  }
  if (successfulAssignments > 0) {
      assignmentSuccess.value = `Contenuto assegnato con successo a ${successfulAssignments} studenti.`;
      // Resetta la selezione studenti dopo successo?
      // selectedStudentIds.value = [];
  }

  isAssigning.value = false;

  // Resetta i messaggi dopo qualche secondo
  setTimeout(() => {
      assignmentError.value = null;
      assignmentSuccess.value = null;
  }, 5000);
};

// Resetta l'ID contenuto quando cambia il tipo
watch(selectedContentType, () => {
    selectedContentId.value = '';
});

</script>

<style scoped>
.assignment-view {
  padding: 20px;
  max-width: 900px;
  margin: auto;
}

.content-selection, .student-selection {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

.student-list {
    list-style: none;
    padding: 0;
    max-height: 300px; /* Limita altezza e aggiunge scroll */
    overflow-y: auto;
    border: 1px solid #eee;
    padding: 10px;
    margin-top: 10px;
}

.student-list li {
    padding: 5px 0;
}
.student-list label {
    font-weight: normal;
    display: flex;
    align-items: center;
}
.student-list input[type="checkbox"] {
    margin-right: 10px;
}


.form-actions {
  margin-top: 20px;
}

/* Rimosso stile .form-actions button */
/* .form-actions button { ... } */
/* .form-actions button:disabled { ... } */

.error-message {
  color: red;
  margin-top: 10px;
  font-weight: bold;
}
.error-message.small {
    font-size: 0.9em;
    font-weight: normal;
    margin-top: 5px;
}
.success-message {
    color: green;
    margin-top: 10px;
    font-weight: bold;
}
.loading {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
</style>