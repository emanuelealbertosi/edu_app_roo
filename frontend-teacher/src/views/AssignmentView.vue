<template>
  <div class="assignment-view">
    <h1>Assegna Contenuti</h1>

    <div class="content-selection">
      <div class="form-group">
        <label for="content-type">Tipo Contenuto da Assegnare:</label>
        <select id="content-type" v-model="selectedContentType" class="w-full p-2 border rounded">
          <option value="quiz">Template Quiz</option>
          <option value="pathway">Template Percorso</option>
        </select>
      </div>

      <!-- Rimosso blocco v-if="assignmentMode === 'existing'" -->

      <!-- Selezione Template (ora sempre visibile in base a selectedContentType) -->
      <div>
         <div class="form-group" v-if="selectedContentType === 'quiz'">
          <label for="quiz-template-select">Seleziona Template Quiz:</label>
          <select id="quiz-template-select" v-model="selectedTemplateId" :disabled="isLoadingQuizTemplates" class="w-full p-2 border rounded">
            <option disabled value="">{{ isLoadingQuizTemplates ? 'Caricamento...' : 'Seleziona un Template Quiz' }}</option>
            <option v-for="template in availableQuizTemplates" :key="template.id" :value="template.id">
              {{ template.title }}
            </option>
          </select>
          <div v-if="quizTemplatesError" class="error-message small">{{ quizTemplatesError }}</div>
        </div>

        <div class="form-group" v-if="selectedContentType === 'pathway'">
          <label for="pathway-template-select">Seleziona Template Percorso:</label>
          <select id="pathway-template-select" v-model="selectedTemplateId" :disabled="isLoadingPathwayTemplates" class="w-full p-2 border rounded">
             <option disabled value="">{{ isLoadingPathwayTemplates ? 'Caricamento...' : 'Seleziona un Template Percorso' }}</option>
             <option v-for="template in availablePathwayTemplates" :key="template.id" :value="template.id">
              {{ template.title }}
            </option>
          </select>
           <div v-if="pathwayTemplatesError" class="error-message small">{{ pathwayTemplatesError }}</div>
        </div>
      </div>

      <!-- Aggiunta Data Scadenza (solo per Quiz) -->
       <div class="form-group mt-4" v-if="selectedContentType === 'quiz'">
           <label for="due-date">Data Scadenza (Opzionale):</label>
           <input type="datetime-local" id="due-date" v-model="dueDate" class="w-full p-2 border rounded" />
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
            class="btn btn-success"
        >
            {{ isAssigning ? 'Assegnazione...' : 'Assegna Selezionati' }}
        </button>
        <div v-if="assignmentError" class="error-message">{{ assignmentError }}</div>
        <div v-if="assignmentSuccess" class="success-message">{{ assignmentSuccess }}</div>
    </div>

  </div>
  <!-- Aggiunto tag di chiusura mancante -->
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { fetchStudents, type Student } from '@/api/students';
// Importa API per contenuti esistenti e template
import { fetchQuizzes, fetchTeacherQuizTemplates, assignQuizToStudent, type Quiz, type QuizTemplate, type AssignQuizPayload, type QuizAssignmentResponse } from '@/api/quizzes'; // Usa fetchTeacherQuizTemplates
import { fetchPathways, fetchPathwayTemplates, assignPathwayToStudent, type Pathway, type PathwayTemplate, type AssignPathwayPayload, type PathwayAssignmentResponse } from '@/api/pathways';
// Rimosso import axios non più necessario per assignApiCall

// --- Stato Selezione Contenuto ---
const selectedContentType = ref<'quiz' | 'pathway'>('quiz');
const selectedContentId = ref<number | ''>(''); // Non più usato per la selezione primaria
// const assignmentMode = ref<'existing' | 'template'>('existing'); // Rimosso
const selectedTemplateId = ref<number | ''>(''); // ID del template selezionato
const dueDate = ref<string | null>(null); // Data di scadenza per i quiz

// --- Stato Caricamento Contenuti ---
const availableQuizzes = ref<Quiz[]>([]);
const isLoadingQuizzes = ref(false);
const quizzesError = ref<string | null>(null);
const availablePathways = ref<Pathway[]>([]);
const isLoadingPathways = ref(false);
const pathwaysError = ref<string | null>(null);
const availableQuizTemplates = ref<QuizTemplate[]>([]);
const isLoadingQuizTemplates = ref(false);
const quizTemplatesError = ref<string | null>(null);
const availablePathwayTemplates = ref<PathwayTemplate[]>([]);
const isLoadingPathwayTemplates = ref(false);
const pathwayTemplatesError = ref<string | null>(null);

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
  loadQuizTemplates(); // Carica anche i template
  loadPathwayTemplates(); // Carica anche i template
});

// --- Logica Caricamento Template ---
const loadQuizTemplates = async () => {
 isLoadingQuizTemplates.value = true;
 quizTemplatesError.value = null;
 try {
   availableQuizTemplates.value = await fetchTeacherQuizTemplates(); // Usa la funzione corretta
 } catch (err) {
   quizTemplatesError.value = 'Errore caricamento template quiz.';
   console.error(err);
 } finally {
   isLoadingQuizTemplates.value = false;
 }
};

const loadPathwayTemplates = async () => {
 isLoadingPathwayTemplates.value = true;
 pathwayTemplatesError.value = null;
 try {
   availablePathwayTemplates.value = await fetchPathwayTemplates();
 } catch (err) {
   pathwayTemplatesError.value = 'Errore caricamento template percorsi.';
   console.error(err);
 } finally {
   isLoadingPathwayTemplates.value = false;
 }
};


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
const canAssign = computed(() => {
    // Ora dipende solo da selectedTemplateId e selectedStudentIds
    return selectedTemplateId.value !== '' && selectedStudentIds.value.length > 0;
});

// Rimosso helper assignApiCall non più necessario


const assignContent = async () => {
 if (!canAssign.value) return;

 isAssigning.value = true;
 assignmentError.value = null;
 assignmentSuccess.value = null;

 const studentsToAssign = [...selectedStudentIds.value]; // Copia l'array
 let successfulAssignments = 0;
 const failedAssignmentsInfo: { studentId: number; error: string }[] = [];

 for (const studentId of studentsToAssign) {
   try {
     if (selectedContentType.value === 'quiz') {
       const payload: AssignQuizPayload = {
         student: studentId, // Usa 'student' come chiave, atteso dal serializer
         due_date: dueDate.value || null, // Includi data scadenza
         quiz_template_id: selectedTemplateId.value as number // Assegna sempre da template
       };
       await assignQuizToStudent(payload); // Chiamata API dentro if
       successfulAssignments++;
     } else if (selectedContentType.value === 'pathway') {
       const payload: AssignPathwayPayload = {
         student: studentId, // Usa 'student' come chiave, atteso dal serializer
         pathway_template_id: selectedTemplateId.value as number // Assegna sempre da template
       };
       await assignPathwayToStudent(payload); // Chiamata API dentro else if
       successfulAssignments++;
     }
   } catch (error: any) { // Catch è correttamente dentro il for loop ora
       let errorMessage = `Studente ${studentId}: ${error.response?.data?.detail || error.response?.data?.status || error.message || 'Errore sconosciuto'}`;
       console.error(`Errore assegnazione a studente ${studentId}:`, error);
       failedAssignmentsInfo.push({ studentId, error: errorMessage });
   }
 } // Fine ciclo for

 isAssigning.value = false;

 if (failedAssignmentsInfo.length > 0) {
     // Mostra un errore generale e dettagli in console o in un'area dedicata
     assignmentError.value = `Errore durante l'assegnazione a ${failedAssignmentsInfo.length} studenti. Dettagli: ${failedAssignmentsInfo.map((f: any) => f.error).join('; ')}`; // Aggiunto tipo any a f
 }
 if (successfulAssignments > 0) {
     assignmentSuccess.value = `Contenuto assegnato con successo a ${successfulAssignments} studenti.`;
     // Resetta selezione dopo successo
     selectedStudentIds.value = [];
     // selectedContentId.value = ''; // Non più necessario
     selectedTemplateId.value = ''; // Resetta solo il template
     dueDate.value = null; // Resetta data scadenza
 }

  // Resetta i messaggi dopo qualche secondo
  setTimeout(() => {
      assignmentError.value = null;
      assignmentSuccess.value = null;
  }, 5000);
};

// Resetta l'ID contenuto quando cambia il tipo
watch(selectedContentType, () => {
    // selectedContentId.value = ''; // Non più necessario
    selectedTemplateId.value = ''; // Resetta solo il template
    dueDate.value = null; // Resetta data scadenza
});

// Rimosso watch per assignmentMode

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