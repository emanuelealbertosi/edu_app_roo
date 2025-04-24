<template>
  <div class="assignment-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo -->
      <h1 class="text-2xl font-semibold">Assegna Contenuti</h1> <!-- Rimosso stile individuale -->
    </div>

    <div class="content-selection mb-8"> <!-- Margin bottom aumentato -->
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="content-type" class="block text-sm font-medium text-neutral-darker mb-1">Tipo Contenuto da Assegnare:</label> <!-- Stile label aggiornato -->
        <select id="content-type" v-model="selectedContentType" class="w-full p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary"> <!-- Stili select aggiornati -->
          <option value="quiz">Template Quiz</option>
          <option value="pathway">Template Percorso</option>
        </select>
      </div>

      <!-- Selezione Template -->
      <div>
         <div class="form-group mb-4" v-if="selectedContentType === 'quiz'"> <!-- Margin bottom -->
          <label for="quiz-template-select" class="block text-sm font-medium text-neutral-darker mb-1">Seleziona Template Quiz:</label> <!-- Stile label aggiornato -->
          <select id="quiz-template-select" v-model="selectedTemplateId" :disabled="isLoadingQuizTemplates" class="w-full p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary"> <!-- Stili select aggiornati -->
            <option disabled value="">{{ isLoadingQuizTemplates ? 'Caricamento...' : 'Seleziona un Template Quiz' }}</option>
            <option v-for="template in availableQuizTemplates" :key="template.id" :value="template.id">
              {{ template.title }}
            </option>
          </select>
          <div v-if="quizTemplatesError" class="text-error text-xs mt-1">{{ quizTemplatesError }}</div> <!-- Stile errore aggiornato -->
        </div>

        <div class="form-group mb-4" v-if="selectedContentType === 'pathway'"> <!-- Margin bottom -->
          <label for="pathway-template-select" class="block text-sm font-medium text-neutral-darker mb-1">Seleziona Template Percorso:</label> <!-- Stile label aggiornato -->
          <select id="pathway-template-select" v-model="selectedTemplateId" :disabled="isLoadingPathwayTemplates" class="w-full p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary"> <!-- Stili select aggiornati -->
             <option disabled value="">{{ isLoadingPathwayTemplates ? 'Caricamento...' : 'Seleziona un Template Percorso' }}</option>
             <option v-for="template in availablePathwayTemplates" :key="template.id" :value="template.id">
              {{ template.title }}
            </option>
          </select>
           <div v-if="pathwayTemplatesError" class="text-error text-xs mt-1">{{ pathwayTemplatesError }}</div> <!-- Stile errore aggiornato -->
        </div>
      </div>

      <!-- Aggiunta Data Scadenza (solo per Quiz) -->
       <div class="form-group mt-4" v-if="selectedContentType === 'quiz'">
           <label for="due-date" class="block text-sm font-medium text-neutral-darker mb-1">Data Scadenza (Opzionale):</label> <!-- Stile label aggiornato -->
           <input type="datetime-local" id="due-date" v-model="dueDate" class="w-full p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary" /> <!-- Stili input aggiornati -->
       </div>
    </div> <!-- Fine content-selection -->


    <div class="student-selection mb-8"> <!-- Margin bottom aumentato -->
      <h2 class="text-xl font-semibold mb-4 text-neutral-darkest">Seleziona Studenti</h2> <!-- Stile titolo aggiornato -->
      <div v-if="isLoadingStudents" class="loading text-center py-6 text-neutral-dark">Caricamento studenti...</div> <!-- Stile loading aggiornato -->
      <div v-else-if="studentsError" class="error-message bg-error/10 border border-error text-error p-3 rounded">{{ studentsError }}</div> <!-- Stile errore aggiornato -->
      <div v-else-if="availableStudents.length > 0">
         <div class="form-group mb-3"> <!-- Margin bottom -->
             <label class="inline-flex items-center cursor-pointer">
                 <input type="checkbox" @change="toggleSelectAllStudents" :checked="allStudentsSelected" class="rounded border-neutral-DEFAULT text-primary shadow-sm focus:border-primary focus:ring focus:ring-primary/20 focus:ring-offset-0" /> <!-- Stile checkbox aggiornato -->
                 <span class="ml-2 text-sm text-neutral-darker">Seleziona Tutti</span> <!-- Stile label aggiornato -->
             </label>
         </div>
         <ul class="student-list max-h-60 overflow-y-auto border border-neutral-DEFAULT rounded-md p-3 space-y-2 bg-neutral-lightest"> <!-- Stili lista aggiornati -->
            <li v-for="student in availableStudents" :key="student.id">
              <label class="inline-flex items-center cursor-pointer">
                <input type="checkbox" :value="student.id" v-model="selectedStudentIds" class="rounded border-neutral-DEFAULT text-primary shadow-sm focus:border-primary focus:ring focus:ring-primary/20 focus:ring-offset-0" /> <!-- Stile checkbox aggiornato -->
                <span class="ml-2 text-sm text-neutral-darkest">{{ student.first_name }} {{ student.last_name }} ({{ student.student_code }})</span> <!-- Mostra student_code, stile label aggiornato -->
              </label>
            </li>
         </ul>
      </div>
       <div v-else class="text-center py-6 text-neutral-dark">Nessuno studente trovato.</div> <!-- Stile messaggio vuoto aggiornato -->
    </div> <!-- Fine student-selection -->

    <div class="form-actions mt-6"> <!-- Margin top -->
        <BaseButton
            variant="success"
            @click="assignContent"
            :disabled="!canAssign || isAssigning"
        > <!-- Usa BaseButton -->
            <span v-if="isAssigning">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                 <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
               </svg>
              Assegnazione...
            </span>
            <span v-else>Assegna Selezionati</span>
        </BaseButton>
        <div v-if="assignmentError" class="error-message mt-3 text-error text-sm">{{ assignmentError }}</div> <!-- Stile errore aggiornato -->
        <div v-if="assignmentSuccess" class="success-message mt-3 text-success-dark text-sm">{{ assignmentSuccess }}</div> <!-- Stile successo aggiornato -->
    </div>

  </div> <!-- Fine assignment-view -->
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { fetchStudents, type Student } from '@/api/students';
// Importa API per contenuti esistenti e template
import { fetchQuizzes, fetchTeacherQuizTemplates, assignQuizToStudent, type Quiz, type QuizTemplate, type AssignQuizPayload, type QuizAssignmentResponse } from '@/api/quizzes'; // Usa fetchTeacherQuizTemplates
import { fetchPathways, fetchPathwayTemplates, assignPathwayToStudent, type Pathway, type PathwayTemplate, type AssignPathwayPayload, type PathwayAssignmentResponse } from '@/api/pathways';
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton
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
  // Rimosso caricamento quiz/pathway esistenti non più usati per assegnazione
  // loadQuizzes();
  // loadPathways();
  loadStudents();
  loadQuizTemplates(); // Carica i template quiz
  loadPathwayTemplates(); // Carica i template percorsi
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
/* Rimuovi stili specifici se non necessari, Tailwind dovrebbe gestire la maggior parte */
/* Esempio: rimuovi stili .form-group, .student-list, .form-actions se Tailwind è sufficiente */
/* .form-group { ... } */
/* .student-list { ... } */
/* .form-actions { ... } */
/* .error-message { ... } */
/* .success-message { ... } */
/* .loading { ... } */
</style>