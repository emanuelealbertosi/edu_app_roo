<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
    fetchTeacherQuizTemplates,
    deleteTeacherQuizTemplate,
    uploadQuizTemplateFromFile,
    assignQuizToStudent,
    assignQuizTemplateToGroup,
    type QuizTemplate,
    type AssignQuizPayload,
    type AssignQuizTemplateToGroupPayload
} from '@/api/quizzes';
import {
    fetchPathwayTemplates, // Anche se non usato attivamente per assegnazione ora, lo teniamo per coerenza se la logica pathway viene riattivata
    assignPathwayToStudent,
    assignPathwayTemplateToGroup,
    type PathwayTemplate,
    type AssignPathwayPayload,
    type AssignPathwayTemplateToGroupPayload
} from '@/api/pathways';
import { getMyStudents } from '@/api/students';
import type { Student } from '@/types/users';
import { useGroupStore } from '@/stores/groups';
import type { StudentGroup } from '@/types/groups';
import { storeToRefs } from 'pinia';

import BaseButton from '@/components/common/BaseButton.vue';
import BaseModal from '@/components/common/BaseModal.vue';
import StudentSelectionModal from '@/components/features/assignment/StudentSelectionModal.vue';
import GroupSelectionModal from '@/components/features/assignment/GroupSelectionModal.vue'; // Importa la nuova modale
import QuizUploadForm from '@/components/QuizUploadForm.vue'; // Importa il componente per l'upload
import { PlusCircleIcon, ArrowUpTrayIcon, XMarkIcon, CheckCircleIcon, PencilIcon, TrashIcon, PaperAirplaneIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';

const templates = ref<QuizTemplate[]>([]);
const isLoading = ref(false);
const router = useRouter();
const error = ref<string | null>(null);
const showUploadForm = ref(false);
const searchQuery = ref('');
const sortKey = ref('created_at');
const sortOrder = ref('desc');

// --- Stato per la Modale di Assegnazione ---
const isAssignModalOpen = ref(false);
const selectedTemplateForAssignment = ref<QuizTemplate | null>(null);

// --- Stato dalla logica di AssignmentView ---
const selectedContentType = ref<'quiz' | 'pathway'>('quiz'); // Fisso su quiz per ora
const selectedTemplateId = ref<number | ''>(''); // ID del template selezionato nella modale
const dueDate = ref<string | null>(null);

const availableQuizTemplates = computed(() => templates.value); // Usa i template già caricati
const isLoadingQuizTemplates = computed(() => isLoading.value); // Usa isLoading della vista principale
const quizTemplatesError = computed(() => error.value); // Usa error della vista principale

// const availablePathwayTemplates = ref<PathwayTemplate[]>([]); // Non caricati attivamente
// const isLoadingPathwayTemplates = ref(false);
// const pathwayTemplatesError = ref<string | null>(null);

const groupStore = useGroupStore();
const { groups: availableGroups, isLoadingList: isLoadingGroups, error: groupsError } = storeToRefs(groupStore);
const selectedGroupIds = ref<number[]>([]);

const availableStudents = ref<Student[]>([]);
const isLoadingStudents = ref(false);
const studentsError = ref<string | null>(null);
const selectedStudentIds = ref<number[]>([]);

const assignmentTargetType = ref<'students' | 'groups'>('students');

const isAssigning = ref(false);
const assignmentError = ref<string | null>(null);
const assignmentSuccess = ref<string | null>(null);

const isStudentModalOpen = ref(false);
const isGroupModalOpen = ref(false); // Stato per la modale dei gruppi
// --- Fine Stato dalla logica di AssignmentView ---


const loadTemplates = async () => {
   isLoading.value = true;
   error.value = null;
   try {
       templates.value = await fetchTeacherQuizTemplates();
   } catch (err: any) {
       console.error("Errore nel recupero dei template quiz:", err);
       error.value = err.message || 'Si è verificato un errore sconosciuto.';
   } finally {
       isLoading.value = false;
   }
};

const loadStudents = async () => {
  isLoadingStudents.value = true;
  studentsError.value = null;
  try {
    const response = await getMyStudents();
    availableStudents.value = response.data;
  } catch (err) {
     studentsError.value = 'Errore caricamento studenti.';
     console.error(err);
  } finally {
    isLoadingStudents.value = false;
  }
};

const loadGroups = async () => {
    await groupStore.fetchGroups();
};

// const loadPathwayTemplatesForModal = async () => { // Funzione separata se si riattivano i percorsi
//  isLoadingPathwayTemplates.value = true;
//  pathwayTemplatesError.value = null;
//  try {
//    availablePathwayTemplates.value = await fetchPathwayTemplates();
//  } catch (err) {
//    pathwayTemplatesError.value = 'Errore caricamento template percorsi.';
//    console.error(err);
//  } finally {
//    isLoadingPathwayTemplates.value = false;
//  }
// };

onMounted(async () => {
  await loadTemplates();
  // Carica studenti e gruppi solo se necessario (es. al primo click su "Assegna" o all'apertura della modale)
  // Per ora li carichiamo onMounted per semplicità, ma potrebbe essere ottimizzato.
  await loadStudents();
  await loadGroups();
  // await loadPathwayTemplatesForModal(); // Se si riattivano i percorsi
});

const editQuizTemplate = (id: number) => {
  router.push({ name: 'quiz-template-edit', params: { id: id.toString() } });
};

const deleteQuizTemplate = async (id: number) => {
  if (!confirm(`Sei sicuro di voler eliminare il template quiz con ID ${id}?`)) {
    return;
  }
  try {
    await deleteTeacherQuizTemplate(id);
    templates.value = templates.value.filter(template => template.id !== id);
    console.log(`Template quiz ${id} eliminato con successo.`);
  } catch (err: any) {
    console.error(`Errore durante l'eliminazione del template quiz ${id}:`, err);
    error.value = `Errore durante l'eliminazione del template quiz: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
  }
};

const createNewQuizTemplate = () => {
  router.push({ name: 'quiz-template-new' });
};

const toggleUploadForm = () => {
  showUploadForm.value = !showUploadForm.value;
  // Non è più necessario resettare i valori del form qui,
  // QuizUploadForm gestirà il proprio stato.
};

// handleFileUpload e submitUploadForm sono stati rimossi
// perché la logica di upload è ora in QuizUploadForm.vue

const handleQuizUploadSuccess = async () => {
  await loadTemplates();
  toggleUploadForm(); // Chiude la sezione del form di upload
  // Potresti voler mostrare un messaggio di successo globale qui, se necessario
};

// --- Funzioni per la Modale di Assegnazione ---
const openAssignModal = (template: QuizTemplate) => {
  selectedTemplateForAssignment.value = template;
  selectedTemplateId.value = template.id; // Imposta l'ID del template selezionato
  selectedContentType.value = 'quiz'; // Assicura che sia quiz
  // Resetta le selezioni precedenti della modale
  selectedStudentIds.value = [];
  selectedGroupIds.value = [];
  dueDate.value = null;
  assignmentError.value = null;
  assignmentSuccess.value = null;
  assignmentTargetType.value = 'students'; // Default a studenti
  isAssignModalOpen.value = true;
};

const closeAssignModal = () => {
  isAssignModalOpen.value = false;
  selectedTemplateForAssignment.value = null;
};

const updateSelectedStudentsInModal = (newSelectedIds: number[]) => {
  selectedStudentIds.value = newSelectedIds;
};

const updateSelectedGroupsInModal = (newSelectedIds: number[]) => { // Funzione per aggiornare i gruppi selezionati
  selectedGroupIds.value = newSelectedIds;
};

const canAssignInModal = computed(() => {
    const isTemplateSelected = selectedTemplateId.value !== ''; // selectedTemplateId è ora usato per la modale
    const isTargetSelected = (assignmentTargetType.value === 'students' && selectedStudentIds.value.length > 0) ||
                             (assignmentTargetType.value === 'groups' && selectedGroupIds.value.length > 0);
    return isTemplateSelected && isTargetSelected;
});

const assignContentFromModal = async () => {
 if (!canAssignInModal.value) return;

 isAssigning.value = true;
 assignmentError.value = null;
 assignmentSuccess.value = null;

 let successfulAssignments = 0;
 const failedAssignmentsInfo: { targetId: number; targetType: 'student' | 'group'; error: string }[] = [];

 const currentTemplateIdToAssign = selectedTemplateId.value; // Usa l'ID del template dalla modale

 if (!currentTemplateIdToAssign) {
     assignmentError.value = "ID del template non valido per l'assegnazione.";
     isAssigning.value = false;
     return;
 }

 if (assignmentTargetType.value === 'students') {
     const studentsToAssign = [...selectedStudentIds.value];
     for (const studentId of studentsToAssign) {
         try {
             if (selectedContentType.value === 'quiz') {
                 const payload: AssignQuizPayload = {
                     student: studentId,
                     due_date: dueDate.value || null
                 };
                 await assignQuizToStudent(currentTemplateIdToAssign as number, payload);
             } else if (selectedContentType.value === 'pathway') {
                 // Logica Pathway (se riattivata)
                 // const payload: AssignPathwayPayload = { student: studentId, pathway_template_id: currentTemplateIdToAssign as number };
                 // await assignPathwayToStudent(payload);
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
                 await assignQuizTemplateToGroup(currentTemplateIdToAssign as number, payload);
             } else if (selectedContentType.value === 'pathway') {
                  // Logica Pathway (se riattivata)
                  // const payload: AssignPathwayTemplateToGroupPayload = { group: groupId };
                  // await assignPathwayTemplateToGroup(currentTemplateIdToAssign as number, payload);
             }
             successfulAssignments++;
         } catch (error: any)
{
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
     // Non resettare le selezioni qui, ma chiudi la modale o dai feedback
     // La chiusura della modale resetterà i suoi stati interni se necessario
     setTimeout(() => {
        closeAssignModal();
        assignmentError.value = null; // Resetta anche nella vista principale
        assignmentSuccess.value = null; // Resetta anche nella vista principale
     }, 2000); // Chiudi dopo 2 secondi per mostrare il messaggio
 } else {
    // Se nessun successo, resetta i messaggi dopo un po'
    setTimeout(() => {
        assignmentError.value = null;
        assignmentSuccess.value = null;
    }, 5000);
 }
};

watch(selectedContentType, () => {
    // selectedTemplateId.value = ''; // Non resettare qui, gestito all'apertura della modale
    dueDate.value = null;
});

watch(assignmentTargetType, () => {
    selectedStudentIds.value = [];
    selectedGroupIds.value = [];
});

const filteredAndSortedTemplates = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  const filtered = query
    ? templates.value.filter(t => {
        const title = t.title.toLowerCase();
        const description = t.description?.toLowerCase() || '';
        const subject = t.subject?.toLowerCase() || '';
        const topic = t.topic?.toLowerCase() || '';
        return title.includes(query) || description.includes(query) || subject.includes(query) || topic.includes(query);
      })
    : templates.value;

  return filtered.slice().sort((a, b) => {
    let valA: any = a[sortKey.value as keyof QuizTemplate] ?? '';
    let valB: any = b[sortKey.value as keyof QuizTemplate] ?? '';

    if (typeof valA === 'string' && typeof valB === 'string') {
      valA = valA.toLowerCase();
      valB = valB.toLowerCase();
    }
    
    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

</script>

<template>
  <div class="quiz-templates-view p-4 md:p-6">
    <div class="bg-primary text-white p-4 rounded-md mb-6">
      <h1 class="text-2xl font-semibold mb-1">Gestione Template Quiz</h1>
      <p class="opacity-90">Qui puoi visualizzare, creare e modificare i tuoi template di quiz.</p>
    </div>
    <div class="actions mb-6 flex space-x-2">
      <BaseButton variant="primary" @click="createNewQuizTemplate" class="flex items-center">
        <PlusCircleIcon class="h-5 w-5 mr-2" />
        Crea Nuovo Template
      </BaseButton>
      <BaseButton variant="success" @click="toggleUploadForm" class="flex items-center">
        <ArrowUpTrayIcon class="h-5 w-5 mr-2" />
        Carica Template da File
      </BaseButton>
    </div>

    <div v-if="showUploadForm" class="upload-section mt-4 p-4 border border-neutral-DEFAULT rounded-lg bg-neutral-lightest shadow-sm mb-6">
      <!-- Il titolo è ora gestito da QuizUploadForm -->
      <QuizUploadForm @upload-successful="handleQuizUploadSuccess" />
      <div class="mt-6 text-right">
           <BaseButton type="button" variant="secondary" @click="toggleUploadForm" class="flex items-center">
            <XMarkIcon class="h-5 w-5 mr-2" />
            Chiudi Sezione Upload
           </BaseButton>
      </div>
      <!-- Eventuali messaggi di errore globali per l'upload potrebbero essere gestiti qui se QuizUploadForm non li copre tutti -->
    </div>

    <!-- Filtro -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca per titolo, descrizione, materia o argomento..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-neutral-DEFAULT rounded-md shadow-sm placeholder-neutral-dark focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
      />
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento template quiz...</div>
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
       <strong class="font-bold">Errore!</strong>
       <span class="block sm:inline"> Errore nel caricamento dei template quiz: {{ error }}</span>
    </div>
    <div v-else-if="filteredAndSortedTemplates.length > 0" class="shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white">
        <thead class="bg-neutral-lightest">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('title')">
              Titolo
              <span v-if="sortKey === 'title'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('description')">
              Descrizione
              <span v-if="sortKey === 'description'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('subject')">
              Materia
              <span v-if="sortKey === 'subject'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('topic')">
              Argomento
              <span v-if="sortKey === 'topic'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('created_at')">
              Creato il
              <span v-if="sortKey === 'created_at'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni Modifica</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni Assegnazione</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT">
          <tr v-for="template in filteredAndSortedTemplates" :key="template.id" class="hover:bg-neutral-lightest transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">
              <a href="#" @click.prevent="editQuizTemplate(template.id)" class="hover:underline cursor-pointer">
                {{ template.title }}
              </a>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ template.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ template.subject || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ template.topic || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ new Date(template.created_at).toLocaleDateString() }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
              <BaseButton variant="warning" size="sm" @click="editQuizTemplate(template.id)" class="p-2" title="Modifica Template">
                <PencilIcon class="h-5 w-5" />
              </BaseButton>
              <BaseButton variant="danger" size="sm" @click="deleteQuizTemplate(template.id)" class="p-2" title="Elimina Template">
                <TrashIcon class="h-5 w-5" />
              </BaseButton>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <BaseButton variant="info" size="sm" @click="openAssignModal(template)" class="p-2 flex items-center" title="Assegna Template">
                <PaperAirplaneIcon class="h-5 w-5 mr-1" /> Assegna
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark">
      <span v-if="searchQuery">Nessun template trovato per "{{ searchQuery }}".</span>
      <span v-else>Nessun template di quiz trovato.</span>
    </div>

    <!-- Modale di Assegnazione -->
    <BaseModal :show="isAssignModalOpen" :title="`Assegna Quiz: ${selectedTemplateForAssignment?.title || ''}`" @close="closeAssignModal" max-width-class="max-w-2xl md:max-w-3xl">
        <div class="p-6">
            <!-- Sezione Selezione Template (solo display) -->
            <div class="mb-6 p-4 border border-neutral-DEFAULT rounded-lg bg-neutral-lightest">
                <h3 class="text-lg font-semibold text-neutral-darkest mb-2">Template Selezionato</h3>
                <p v-if="selectedTemplateForAssignment" class="text-neutral-dark">
                    <strong>Titolo:</strong> {{ selectedTemplateForAssignment.title }} <br>
                    <span v-if="selectedTemplateForAssignment.description"><strong>Descrizione:</strong> {{ selectedTemplateForAssignment.description }}</span>
                </p>
                 <input type="hidden" :value="selectedTemplateId"> <!-- Mantiene selectedTemplateId aggiornato -->
            </div>

            <!-- Aggiunta Data Scadenza -->
            <div class="form-group mb-4">
                <label for="due-date-modal" class="block text-sm font-medium text-neutral-darker mb-1">Data Scadenza (Opzionale):</label>
                <input type="datetime-local" id="due-date-modal" v-model="dueDate" class="w-full p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary" />
            </div>

            <!-- Sezione Selezione Target (Studenti o Gruppi) -->
            <div class="target-selection mb-6">
                <h2 class="text-xl font-semibold mb-3 text-neutral-darkest">Seleziona Destinatari</h2>
                <div class="flex items-center space-x-4 mb-4">
                    <label class="flex items-center cursor-pointer">
                        <input type="radio" v-model="assignmentTargetType" value="students" name="targetTypeModal" class="form-radio h-4 w-4 text-primary focus:ring-primary border-neutral-DEFAULT">
                        <span class="ml-2 text-sm text-neutral-darker">Studenti Singoli</span>
                    </label>
                    <label class="flex items-center cursor-pointer">
                        <input type="radio" v-model="assignmentTargetType" value="groups" name="targetTypeModal" class="form-radio h-4 w-4 text-primary focus:ring-primary border-neutral-DEFAULT">
                        <span class="ml-2 text-sm text-neutral-darker">Gruppi</span>
                    </label>
                </div>

                <div v-if="assignmentTargetType === 'students'" class="student-selection">
                    <h3 class="text-lg font-medium mb-2 text-neutral-darkest">Seleziona Studenti</h3>
                    <div v-if="isLoadingStudents" class="loading text-center py-4 text-neutral-dark">Caricamento studenti...</div>
                    <div v-else-if="studentsError" class="error-message bg-error/10 border border-error text-error p-3 rounded">{{ studentsError }}</div>
                    <div v-else-if="availableStudents.length > 0">
                        <BaseButton variant="primary" @click="isStudentModalOpen = true" class="mb-2">
                        Seleziona
                        </BaseButton>
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
                        <BaseButton variant="primary" @click="isGroupModalOpen = true" class="mb-2">
                        Seleziona
                        </BaseButton>
                        <div class="text-xs text-neutral-dark">
                            <span v-if="selectedGroupIds.length === 0">Nessun gruppo selezionato.</span>
                            <span v-else-if="selectedGroupIds.length === 1">1 gruppo selezionato.</span>
                            <span v-else>{{ selectedGroupIds.length }} gruppi selezionati.</span>
                        </div>
                    </div>
                    <div v-else class="text-center py-4 text-neutral-dark">Nessun gruppo trovato. <router-link :to="{ name: 'GroupsList' }" class="text-primary hover:underline">Gestisci Gruppi</router-link></div>
                </div>
            </div>

            <div v-if="assignmentError" class="error-message my-3 text-error text-sm p-3 bg-error/10 border border-error rounded">{{ assignmentError }}</div>
            <div v-if="assignmentSuccess" class="success-message my-3 text-success-dark text-sm p-3 bg-success/10 border border-success rounded">{{ assignmentSuccess }}</div>
        </div>

        <template #footer>
            <div class="w-full flex justify-between items-center p-4">
                <BaseButton variant="secondary" @click="closeAssignModal">Annulla</BaseButton>
                <BaseButton
                    variant="success"
                    @click="assignContentFromModal"
                    :disabled="!canAssignInModal || isAssigning"
                >
                    <span v-if="isAssigning">
                        <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Assegnazione...
                    </span>
                    <span v-else>Assegna Selezionati</span>
                </BaseButton>
            </div>
        </template>
    </BaseModal>

    <!-- Modale Selezione Studenti (usata dalla modale di assegnazione) -->
    <StudentSelectionModal
        :show="isStudentModalOpen"
        :students="availableStudents"
        :initial-selected-ids="selectedStudentIds"
        @close="isStudentModalOpen = false"
        @update:selectedIds="updateSelectedStudentsInModal"
    />

    <!-- Modale Selezione Gruppi -->
    <GroupSelectionModal
        :show="isGroupModalOpen"
        :groups="availableGroups"
        :initial-selected-ids="selectedGroupIds"
        @close="isGroupModalOpen = false"
        @update:selectedIds="updateSelectedGroupsInModal"
    />

  </div>
</template>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
</style>