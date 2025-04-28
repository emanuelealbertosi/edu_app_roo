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
          <option value="pathway" v-if="false">Template Percorso</option> <!-- Nascosto temporaneamente -->
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


    <!-- Sezione Selezione Target (Studenti o Gruppi) -->
    <div class="target-selection mb-8">
        <h2 class="text-xl font-semibold mb-4 text-neutral-darkest">Seleziona Destinatari</h2>
        <div class="flex items-center space-x-4 mb-4">
             <label class="flex items-center">
                <input type="radio" v-model="assignmentTargetType" value="students" name="targetType" class="form-radio h-4 w-4 text-primary focus:ring-primary border-neutral-DEFAULT">
                <span class="ml-2 text-sm text-neutral-darker">Studenti Singoli</span>
            </label>
            <label class="flex items-center">
                <input type="radio" v-model="assignmentTargetType" value="groups" name="targetType" class="form-radio h-4 w-4 text-primary focus:ring-primary border-neutral-DEFAULT">
                <span class="ml-2 text-sm text-neutral-darker">Gruppi</span>
            </label>
        </div>

        <!-- Sezione Selezione Studenti (Condizionale) -->
        <div v-if="assignmentTargetType === 'students'" class="student-selection">
            <h3 class="text-lg font-medium mb-3 text-neutral-darkest">Seleziona Studenti</h3>
            <div v-if="isLoadingStudents" class="loading text-center py-6 text-neutral-dark">Caricamento studenti...</div>
            <div v-else-if="studentsError" class="error-message bg-error/10 border border-error text-error p-3 rounded">{{ studentsError }}</div>
            <div v-else-if="availableStudents.length > 0">
                <BaseButton variant="outline" @click="isStudentModalOpen = true" class="mb-3">
                Apri Selezione Studenti
                </BaseButton>
                <div class="text-sm text-neutral-dark">
                <span v-if="selectedStudentIds.length === 0">Nessuno studente selezionato.</span>
                <span v-else-if="selectedStudentIds.length === 1">1 studente selezionato.</span>
                <span v-else>{{ selectedStudentIds.length }} studenti selezionati.</span>
                </div>
            </div>
            <div v-else class="text-center py-6 text-neutral-dark">Nessuno studente trovato.</div>
        </div>

        <!-- Sezione Selezione Gruppi (Condizionale) -->
         <div v-if="assignmentTargetType === 'groups'" class="group-selection">
             <h3 class="text-lg font-medium mb-3 text-neutral-darkest">Seleziona Gruppi</h3>
             <div v-if="isLoadingGroups" class="loading text-center py-6 text-neutral-dark">Caricamento gruppi...</div>
             <div v-else-if="groupsError" class="error-message bg-error/10 border border-error text-error p-3 rounded">{{ groupsError }}</div>
             <div v-else-if="availableGroups.length > 0">
                 <label for="group-select" class="block text-sm font-medium text-neutral-darker mb-1">Gruppi disponibili:</label>
                 <!-- TODO: Sostituire con un componente multi-select migliore se disponibile -->
                 <select
                    id="group-select"
                    v-model="selectedGroupIds"
                    multiple
                    class="w-full p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary h-32"
                 >
                    <option v-for="group in availableGroups" :key="group.id" :value="group.id">
                        {{ group.name }} ({{ group.student_count ?? '?' }} membri)
                    </option>
                 </select>
                 <div class="text-sm text-neutral-dark mt-2">
                    <span v-if="selectedGroupIds.length === 0">Nessun gruppo selezionato.</span>
                    <span v-else-if="selectedGroupIds.length === 1">1 gruppo selezionato.</span>
                    <span v-else>{{ selectedGroupIds.length }} gruppi selezionati.</span>
                 </div>
             </div>
             <div v-else class="text-center py-6 text-neutral-dark">Nessun gruppo trovato. <router-link :to="{ name: 'GroupsList' }" class="text-primary hover:underline">Gestisci Gruppi</router-link></div>
         </div>
   </div> <!-- Fine target-selection -->

    <div class="form-actions mt-6">
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

  <!-- Modale Selezione Studenti -->
  <StudentSelectionModal
    :show="isStudentModalOpen"
    :students="availableStudents"
    :initial-selected-ids="selectedStudentIds"
    @close="isStudentModalOpen = false"
    @update:selectedIds="updateSelectedStudents"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { getMyStudents } from '@/api/students'; // Importa la funzione corretta
import type { Student } from '@/types/users'; // Importa il tipo dal percorso corretto
// Importa API per template e assegnazione a studenti/gruppi
import {
    fetchTeacherQuizTemplates,
    assignQuizToStudent,
    assignQuizTemplateToGroup,
    type QuizTemplate,
    type AssignQuizPayload,
    type QuizAssignmentResponse, // Potrebbe non essere più usata direttamente se si gestisce solo successo/errore
    type AssignQuizTemplateToGroupPayload,
    type GroupAssignmentResponse
} from '@/api/quizzes';
import {
    fetchPathwayTemplates,
    assignPathwayToStudent,
    assignPathwayTemplateToGroup,
    type PathwayTemplate,
    type AssignPathwayPayload,
    type PathwayAssignmentResponse, // Potrebbe non essere più usata direttamente
    type AssignPathwayTemplateToGroupPayload
} from '@/api/pathways';
import { useGroupStore } from '@/stores/groups';
import type { StudentGroup } from '@/types/groups';
import { storeToRefs } from 'pinia';
import BaseButton from '@/components/common/BaseButton.vue';
import StudentSelectionModal from '@/components/features/assignment/StudentSelectionModal.vue';

// --- Stato Selezione Contenuto ---
const selectedContentType = ref<'quiz' | 'pathway'>('quiz');
const selectedContentId = ref<number | ''>(''); // Non più usato per la selezione primaria
// const assignmentMode = ref<'existing' | 'template'>('existing'); // Rimosso
const selectedTemplateId = ref<number | ''>(''); // ID del template selezionato
const dueDate = ref<string | null>(null); // Data di scadenza per i quiz

// --- Stato Caricamento Contenuti (Solo Template) ---
const availableQuizTemplates = ref<QuizTemplate[]>([]);
const isLoadingQuizTemplates = ref(false);
const quizTemplatesError = ref<string | null>(null);
const availablePathwayTemplates = ref<PathwayTemplate[]>([]);
const isLoadingPathwayTemplates = ref(false);
const pathwayTemplatesError = ref<string | null>(null);
// Rimosse variabili per quiz/pathway esistenti

// --- Stato Caricamento Gruppi --- NUOVO
const groupStore = useGroupStore();
const { groups: availableGroups, isLoadingList: isLoadingGroups, error: groupsError } = storeToRefs(groupStore); // Usa lo store per i gruppi
const selectedGroupIds = ref<number[]>([]); // NUOVO

// --- Stato Caricamento Studenti ---
const availableStudents = ref<Student[]>([]);
const isLoadingStudents = ref(false);
const studentsError = ref<string | null>(null);
const selectedStudentIds = ref<number[]>([]);

const assignmentTargetType = ref<'students' | 'groups'>('students'); // NUOVO: Target assegnazione

// --- Stato Assegnazione ---
const isAssigning = ref(false);
const assignmentError = ref<string | null>(null);
const assignmentSuccess = ref<string | null>(null);

const isStudentModalOpen = ref(false); // Stato per la modale

// --- Logica Caricamento Dati ---
const loadStudents = async () => {
  isLoadingStudents.value = true;
  studentsError.value = null;
  try {
    // Usa la funzione API corretta. Assumiamo che apiClient gestisca l'estrazione di .data
    const response = await getMyStudents();
    availableStudents.value = response.data; // Accedi al campo 'data'
  } catch (err) {
     studentsError.value = 'Errore caricamento studenti.';
     console.error(err);
  } finally {
    isLoadingStudents.value = false;
  }
};

onMounted(() => {
  loadStudents();
  loadQuizTemplates();
  loadPathwayTemplates();
  loadGroups();
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


// --- Logica Caricamento Gruppi --- NUOVO
const loadGroups = async () => {
    // Usa l'azione dello store, isLoadingGroups e groupsError sono già gestiti da storeToRefs
    await groupStore.fetchGroups();
};

// --- Logica Selezione Studenti (Modale) ---
const updateSelectedStudents = (newSelectedIds: number[]) => {
  selectedStudentIds.value = newSelectedIds;
};

// Rimosse logiche allStudentsSelected e toggleSelectAllStudents gestite dalla modale

// --- Logica Assegnazione ---
const canAssign = computed(() => {
    // Dipende da template selezionato E (studenti selezionati O gruppi selezionati)
    const isTemplateSelected = selectedTemplateId.value !== '';
    const isTargetSelected = (assignmentTargetType.value === 'students' && selectedStudentIds.value.length > 0) ||
                             (assignmentTargetType.value === 'groups' && selectedGroupIds.value.length > 0);
    return isTemplateSelected && isTargetSelected;
});

// Rimosso helper assignApiCall non più necessario


const assignContent = async () => {
 if (!canAssign.value) return;

 isAssigning.value = true;
 assignmentError.value = null;
 assignmentSuccess.value = null;

 let successfulAssignments = 0;
 const failedAssignmentsInfo: { targetId: number; targetType: 'student' | 'group'; error: string }[] = [];

 if (assignmentTargetType.value === 'students') {
     const studentsToAssign = [...selectedStudentIds.value];
     for (const studentId of studentsToAssign) {
         try {
             if (selectedContentType.value === 'quiz') {
                 // Payload ora contiene solo student e due_date
                 const payload: AssignQuizPayload = {
                     student: studentId,
                     due_date: dueDate.value || null
                     // quiz_template_id non è più nel payload, ma nell'URL
                 };
                 // Passa templateId come primo argomento
                 await assignQuizToStudent(selectedTemplateId.value as number, payload);
             } else if (selectedContentType.value === 'pathway') {
                 // La chiamata per i percorsi rimane invariata per ora
                 const payload: AssignPathwayPayload = {
                     student: studentId,
                     pathway_template_id: selectedTemplateId.value as number
                 };
                 await assignPathwayToStudent(payload);
             }
             successfulAssignments++;
         } catch (error: any) {
             let errorMessage = `Studente ${studentId}: ${error.response?.data?.detail || error.response?.data?.status || error.message || 'Errore sconosciuto'}`;
             console.error(`Errore assegnazione a studente ${studentId}:`, error);
             failedAssignmentsInfo.push({ targetId: studentId, targetType: 'student', error: errorMessage });
         }
     }
 } else if (assignmentTargetType.value === 'groups') {
     const groupsToAssign = [...selectedGroupIds.value];
     for (const groupId of groupsToAssign) {
          try {
             if (selectedContentType.value === 'quiz') {
                 const payload: AssignQuizTemplateToGroupPayload = {
                     group: groupId,
                     due_date: dueDate.value || null,
                 };
                 await assignQuizTemplateToGroup(selectedTemplateId.value as number, payload);
             } else if (selectedContentType.value === 'pathway') {
                  const payload: AssignPathwayTemplateToGroupPayload = {
                     group: groupId,
                 };
                 await assignPathwayTemplateToGroup(selectedTemplateId.value as number, payload);
             }
             successfulAssignments++;
         } catch (error: any) {
             let errorMessage = `Gruppo ${groupId}: ${error.response?.data?.detail || error.response?.data?.status || error.message || 'Errore sconosciuto'}`;
             console.error(`Errore assegnazione a gruppo ${groupId}:`, error);
             failedAssignmentsInfo.push({ targetId: groupId, targetType: 'group', error: errorMessage });
         }
     }
 }

 isAssigning.value = false;

 const targetTypeText = assignmentTargetType.value === 'students' ? 'studenti' : 'gruppi';

 if (failedAssignmentsInfo.length > 0) {
     assignmentError.value = `Errore durante l'assegnazione a ${failedAssignmentsInfo.length} ${targetTypeText}. Dettagli: ${failedAssignmentsInfo.map(f => f.error).join('; ')}`;
 }
 if (successfulAssignments > 0) {
     assignmentSuccess.value = `Contenuto assegnato con successo a ${successfulAssignments} ${targetTypeText}.`;
     // Resetta selezione dopo successo
     selectedStudentIds.value = [];
     selectedGroupIds.value = []; // Resetta anche i gruppi
     selectedTemplateId.value = '';
     dueDate.value = null;
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

// Resetta selezioni quando cambia il tipo di target
watch(assignmentTargetType, () => {
    selectedStudentIds.value = [];
    selectedGroupIds.value = [];
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