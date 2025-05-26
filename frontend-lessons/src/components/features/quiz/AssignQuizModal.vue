<template>
  <div v-if="show" class="fixed inset-0 bg-gray-600 bg-opacity-75 overflow-y-auto h-full w-full z-40 flex items-center justify-center" @click.self="closeModal">
    <div class="relative mx-auto p-6 border w-full max-w-2xl md:max-w-3xl shadow-lg rounded-md bg-white">
      <!-- Intestazione Modale con sfondo blu -->
      <div class="bg-blue-600 text-white p-4 rounded-t-md -m-6 mb-6"> <!-- -m-6 invece di -m-8 per adattarsi al padding p-6 del contenitore principale -->
        <h3 class="text-xl font-semibold text-center">Assegna Quiz: {{ quizTemplateDetails?.title || 'Caricamento...' }}</h3>
        <!-- Il pulsante di chiusura &times; viene rimosso per coerenza con LessonEditModal -->
      </div>

      <!-- Contenuto della modale -->
      <div class="modal-body-quiz">
        <!-- Sezione Selezione Template (solo display) -->
        <div v-if="quizTemplateDetails" class="mb-6 p-4 border border-neutral-DEFAULT rounded-lg bg-neutral-lightest">
          <h3 class="text-lg font-semibold text-neutral-darkest mb-2">Template Selezionato</h3>
          <p class="text-neutral-dark">
            <strong>Titolo:</strong> {{ quizTemplateDetails.title }} <br>
            <span v-if="quizTemplateDetails.description"><strong>Descrizione:</strong> {{ quizTemplateDetails.description }}</span>
          </p>
        </div>
        <div v-else-if="isLoadingTemplateDetails" class="text-center py-4 text-neutral-dark">
          Caricamento dettagli template...
        </div>
        <div v-else class="text-center py-4 text-error">
          Dettagli template non disponibili.
        </div>

        <!-- Aggiunta Data Scadenza -->
        <div class="form-group mb-4">
          <label for="due-date-modal-quiz" class="block text-sm font-medium text-neutral-darker mb-1">Data Scadenza (Opzionale):</label>
          <input type="datetime-local" id="due-date-modal-quiz" v-model="dueDate" class="w-full p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary" />
        </div>

        <!-- Sezione Selezione Target (Studenti o Gruppi) -->
        <div class="target-selection mb-6">
          <h2 class="text-xl font-semibold mb-3 text-neutral-darkest">Seleziona Destinatari</h2>
          <div class="flex items-center space-x-4 mb-4">
            <label class="flex items-center cursor-pointer">
              <input type="radio" v-model="assignmentTargetType" value="students" name="targetTypeModalQuiz" class="form-radio h-4 w-4 text-primary focus:ring-primary border-neutral-DEFAULT">
              <span class="ml-2 text-sm text-neutral-darker">Studenti Singoli</span>
            </label>
            <label class="flex items-center cursor-pointer">
              <input type="radio" v-model="assignmentTargetType" value="groups" name="targetTypeModalQuiz" class="form-radio h-4 w-4 text-primary focus:ring-primary border-neutral-DEFAULT">
              <span class="ml-2 text-sm text-neutral-darker">Gruppi</span>
            </label>
          </div>

          <div v-if="assignmentTargetType === 'students'" class="student-selection">
            <h3 class="text-lg font-medium mb-2 text-neutral-darkest">Seleziona Studenti</h3>
            <div v-if="isLoadingStudents" class="loading text-center py-4 text-neutral-dark">Caricamento studenti...</div>
            <div v-else-if="studentsError" class="error-message bg-error/10 border border-error text-error p-3 rounded">{{ studentsError }}</div>
            <div v-else-if="availableStudents.length > 0">
              <button @click="isStudentModalOpen = true" class="mb-2 px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                Seleziona Studenti
              </button>
              <div class="text-xs text-neutral-dark">
                <span v-if="selectedStudentIds.length === 0">Nessuno studente selezionato.</span>
                <span v-else-if="selectedStudentIds.length === 1">1 studente selezionato.</span>
                <span v-else>{{ selectedStudentIds.length }} studenti selezionati.</span>
              </div>
            </div>
            <div v-else class="text-center py-4 text-neutral-dark">Nessuno studente trovato.</div>
          </div>

          <div v-if="assignmentTargetType === 'groups'" class="group-selection">
            <h3 class="text-lg font-medium mb-2 text-neutral-darkest">Seleziona Gruppi</h3>
            <div v-if="isLoadingGroups" class="loading text-center py-4 text-neutral-dark">Caricamento gruppi...</div>
            <div v-else-if="groupsError" class="error-message bg-error/10 border border-error text-error p-3 rounded">{{ groupsError }}</div>
            <div v-else-if="availableGroups.length > 0">
              <button @click="isGroupModalOpen = true" class="mb-2 px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                Seleziona Gruppi
              </button>
              <div class="text-xs text-neutral-dark">
                <span v-if="selectedGroupIds.length === 0">Nessun gruppo selezionato.</span>
                <span v-else-if="selectedGroupIds.length === 1">1 gruppo selezionato.</span>
                <span v-else>{{ selectedGroupIds.length }} gruppi selezionati.</span>
              </div>
            </div>
            <div v-else class="text-center py-4 text-neutral-dark">Nessun gruppo trovato. <!-- Potrebbe servire un link per creare gruppi --></div>
          </div>
        </div>

        <div v-if="assignmentError" class="error-message my-3 text-error text-sm p-3 bg-error/10 border border-error rounded">{{ assignmentError }}</div>
        <div v-if="assignmentSuccess" class="success-message my-3 text-success-dark text-sm p-3 bg-success/10 border border-success rounded">{{ assignmentSuccess }}</div>
      </div> <!-- Fine modal-body-quiz -->

      <!-- Footer per i pulsanti -->
      <div class="flex justify-end space-x-4 mt-6 pt-4 border-t">
        <button @click="closeModal" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors">Annulla</button>
        <button
            @click="handleAssignContent"
            :disabled="!canAssign || isAssigning"
            class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Assegna il quiz ai target selezionati"
        >
          <span v-if="isAssigning">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Assegnazione...
          </span>
          <span v-else>Assegna Selezionati</span>
        </button>
      </div>
    </div> <!-- Fine div modale principale -->
  </div>

  <!-- Modali di Selezione Studenti/Gruppi (da creare/adattare) -->
  <StudentSelectionModal
      v-if="availableStudents.length > 0"
      :show="isStudentModalOpen"
      :students="availableStudents"
      :initial-selected-ids="selectedStudentIds"
      @close="isStudentModalOpen = false"
      @update:selectedIds="updateSelectedStudents"
  />

  <GroupSelectionModal
      v-if="availableGroups.length > 0"
      :show="isGroupModalOpen"
      :groups="availableGroups"
      :initial-selected-ids="selectedGroupIds"
      @close="isGroupModalOpen = false"
      @update:selectedIds="updateSelectedGroups"
  />

</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
// RIMOZIONE IMPORT BaseModal e BaseButton
// import BaseModal from '@/components/common/BaseModal.vue';
// import BaseButton from '@/components/common/BaseButton.vue';
import StudentSelectionModal from '@/components/common/StudentSelectionModal.vue';
import GroupSelectionModal from '@/components/common/GroupSelectionModal.vue';

import { useQuizStore } from '@/stores/quizStore';
import { useLessonStore } from '@/stores/lessons'; // Per fetchStudentsForTeacher e fetchGroupsAction
import type { QuizTemplate } from '@/types/quizTemplate';
import type { Student } from '@/types/lezioni'; // Usiamo il tipo Student da lezioni, come in AssignLessonModal
import type { StudentGroup } from '@/types/groups';

// Importa le funzioni di servizio reali
import { assignQuizToStudent, assignQuizTemplateToGroup } from '@/services/quizService';


const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  quizTemplateId: {
    type: Number as import('vue').PropType<number | null>,
    default: null,
  },
});

const emit = defineEmits(['close', 'assignment-complete']);

const quizStore = useQuizStore();
const lessonStore = useLessonStore();

const quizTemplateDetails = ref<QuizTemplate | null | undefined>(null);
const isLoadingTemplateDetails = ref(false);

const dueDate = ref<string | null>(null);
const assignmentTargetType = ref<'students' | 'groups'>('students');

const availableStudents = ref<Student[]>([]);
const isLoadingStudents = ref(false);
const studentsError = ref<string | null>(null);
const selectedStudentIds = ref<number[]>([]);
const isStudentModalOpen = ref(false);

const availableGroups = ref<StudentGroup[]>([]);
const isLoadingGroups = ref(false);
const groupsError = ref<string | null>(null);
const selectedGroupIds = ref<number[]>([]);
const isGroupModalOpen = ref(false);

const isAssigning = ref(false);
const assignmentError = ref<string | null>(null);
const assignmentSuccess = ref<string | null>(null);

const fetchQuizTemplateDetails = async () => {
  if (!props.quizTemplateId) return;
  isLoadingTemplateDetails.value = true;
  try {
    const template = quizStore.getQuizTemplateById(props.quizTemplateId);
    if (template) {
        quizTemplateDetails.value = template;
    } else {
        await quizStore.fetchQuizTemplate(props.quizTemplateId);
        quizTemplateDetails.value = quizStore.getQuizTemplateById(props.quizTemplateId);
    }
    if (!quizTemplateDetails.value) {
        throw new Error('Template non trovato');
    }
  } catch (error) {
    console.error("Errore caricamento dettagli template quiz:", error);
    quizTemplateDetails.value = null;
  } finally {
    isLoadingTemplateDetails.value = false;
  }
};

const loadStudents = async () => {
  isLoadingStudents.value = true;
  studentsError.value = null;
  try {
    availableStudents.value = await lessonStore.fetchStudentsForTeacher();
  } catch (err) {
    studentsError.value = 'Errore caricamento studenti.';
    console.error(err);
  } finally {
    isLoadingStudents.value = false;
  }
};

const loadGroups = async () => {
  isLoadingGroups.value = true;
  groupsError.value = null;
  try {
    await lessonStore.fetchGroupsAction();
    availableGroups.value = lessonStore.groups;
  } catch (err) {
    groupsError.value = 'Errore caricamento gruppi.';
    console.error(err);
  } finally {
    isLoadingGroups.value = false;
  }
};

onMounted(() => {
  if (props.show) {
    fetchQuizTemplateDetails();
    loadStudents();
    loadGroups();
  }
});

watch(() => props.show, (newVal) => {
  if (newVal) {
    fetchQuizTemplateDetails();
    loadStudents();
    loadGroups();
    dueDate.value = null;
    assignmentTargetType.value = 'students';
    selectedStudentIds.value = [];
    selectedGroupIds.value = [];
    assignmentError.value = null;
    assignmentSuccess.value = null;
    isAssigning.value = false;
  }
});


const closeModal = () => {
  emit('close');
};

const updateSelectedStudents = (newSelectedIds: number[]) => {
  selectedStudentIds.value = newSelectedIds;
};

const updateSelectedGroups = (newSelectedIds: number[]) => {
  selectedGroupIds.value = newSelectedIds;
};

const canAssign = computed(() => {
  const isTemplateValid = !!props.quizTemplateId;
  const isTargetSelected = (assignmentTargetType.value === 'students' && selectedStudentIds.value.length > 0) ||
                           (assignmentTargetType.value === 'groups' && selectedGroupIds.value.length > 0);
  return isTemplateValid && isTargetSelected;
});

const handleAssignContent = async () => {
  if (!canAssign.value || !props.quizTemplateId) return;

  isAssigning.value = true;
  assignmentError.value = null;
  assignmentSuccess.value = null;
  let successfulAssignments = 0;
  const failedAssignmentsInfo: { targetId: number; targetType: 'student' | 'group'; error: string }[] = [];

  if (assignmentTargetType.value === 'students') {
    for (const studentId of selectedStudentIds.value) {
      try {
        await assignQuizToStudent(props.quizTemplateId, { student: studentId, due_date: dueDate.value });
        successfulAssignments++;
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Errore sconosciuto';
        failedAssignmentsInfo.push({ targetId: studentId, targetType: 'student', error: errorMessage });
        console.error(`Fallita assegnazione a studente ${studentId}:`, error);
      }
    }
  } else if (assignmentTargetType.value === 'groups') {
    for (const groupId of selectedGroupIds.value) {
      try {
        await assignQuizTemplateToGroup(props.quizTemplateId, { group: groupId, due_date: dueDate.value });
        successfulAssignments++;
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Errore sconosciuto';
        failedAssignmentsInfo.push({ targetId: groupId, targetType: 'group', error: errorMessage });
        console.error(`Fallita assegnazione a gruppo ${groupId}:`, error);
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
    setTimeout(() => {
      emit('assignment-complete');
      closeModal(); 
    }, 1500); 
  } else if (failedAssignmentsInfo.length === 0) {
    assignmentError.value = "Nessuna assegnazione effettuata. Selezionare destinatari.";
  }
};

</script>

<style scoped>
/* Eventuali stili specifici per questa modale */
.modal-body-quiz {
  max-height: 65vh; /* o un valore che preferisci, leggermente meno di AssignLessonModal per possibile minor contenuto verticale */
  overflow-y: auto;
}
</style>