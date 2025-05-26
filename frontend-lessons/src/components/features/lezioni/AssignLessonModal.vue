<template>
  <div v-if="show" class="fixed inset-0 bg-gray-600 bg-opacity-75 overflow-y-auto h-full w-full z-40 flex items-center justify-center" @click.self="closeModal">
    <!-- Aumentato leggermente il padding e max-width per accomodare più contenuto -->
    <div class="relative mx-auto p-6 border w-full max-w-3xl shadow-lg rounded-md bg-white">
      <!-- Intestazione Modale con sfondo blu -->
      <div class="bg-blue-600 text-white p-4 rounded-t-md -m-6 mb-6"> <!-- -m-6 invece di -m-8 per adattarsi al padding p-6 del contenitore principale -->
        <h3 class="text-xl font-semibold text-center">Assegna Lezione: {{ lesson?.title || 'Caricamento...' }}</h3>
        <!-- Il pulsante di chiusura &times; viene rimosso per coerenza con LessonEditModal -->
      </div>

      <!-- Contenuto della modale (precedentemente LessonAssignView.vue) -->
      <div class="modal-body">
        <!-- Qui verrà incollato il contenuto di LessonAssignView.vue -->
        <!-- Per ora, un placeholder -->
        <p v-if="internalLoadingLesson || internalLoadingStudents || internalLoadingGroups" class="text-center">
          Caricamento dati per l'assegnazione...
        </p>
        <div v-else-if="internalErrorLesson || internalErrorStudents || internalErrorGroups" class="text-red-500 text-center">
          Errore nel caricamento dei dati necessari. {{ internalErrorLesson || internalErrorStudents || internalErrorGroups }}
        </div>
        <div v-else-if="lesson">
          <!-- Il contenuto effettivo di LessonAssignView andrà qui -->
          <p class="mb-4 text-gray-700">Seleziona gli studenti e/o i gruppi a cui vuoi assegnare questa lezione.</p>

          <!-- Sezione Studenti e Gruppi (da LessonAssignView) -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <!-- Colonna Selezione Studenti -->
            <div>
              <h3 class="text-lg font-medium mb-2 text-gray-800">Studenti</h3>
              <div v-if="internalLoadingStudents" class="text-gray-500 italic">Caricamento studenti...</div>
              <div v-else-if="internalErrorStudents" class="text-red-600">{{ internalErrorStudents }}</div>
              <div v-else-if="students.length > 0">
                <button
                  type="button"
                  @click="isStudentModalOpen = true"
                  class="mb-3 px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Seleziona Studenti
                </button>
                <div class="text-sm text-gray-600">
                  <span v-if="selectedStudentIds.length === 0">Nessuno studente selezionato.</span>
                  <span v-else-if="selectedStudentIds.length === 1">1 studente selezionato.</span>
                  <span v-else>{{ selectedStudentIds.length }} studenti selezionati.</span>
                </div>
              </div>
              <div v-else class="text-center py-4 text-gray-500">Nessuno studente disponibile.</div>
            </div>

            <!-- Colonna Selezione Gruppi -->
            <div>
              <h3 class="text-lg font-medium mb-2 text-gray-800">Gruppi</h3>
              <div v-if="internalLoadingGroups" class="text-gray-500 italic">Caricamento gruppi...</div>
              <div v-else-if="internalErrorGroups" class="text-red-600">{{ internalErrorGroups }}</div>
              <div v-else-if="groups.length > 0">
                <button
                  type="button"
                  @click="isGroupModalOpen = true"
                  class="mb-3 px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Seleziona Gruppi
                </button>
                <div class="text-sm text-gray-600">
                  <span v-if="selectedGroupIds.length === 0">Nessun gruppo selezionato.</span>
                  <span v-else-if="selectedGroupIds.length === 1">1 gruppo selezionato.</span>
                  <span v-else>{{ selectedGroupIds.length }} gruppi selezionati.</span>
                </div>
              </div>
              <div v-else class="text-center py-4 text-gray-500">Nessun gruppo disponibile.</div>
            </div>
          </div>
          <!-- Fine Griglia Selezione -->

          <!-- Riepilogo Selezione -->
          <div class="mb-6 text-center text-gray-700 font-medium">
            {{ selectionSummary }}
          </div>

          <!-- Pulsante Assegna -->
          <div class="flex justify-end space-x-4 mt-6 pt-4 border-t">
            <button @click="closeModal" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors">Annulla</button>
            <button
              @click="assignLessonToTargets"
              :disabled="(selectedStudentIds.length === 0 && selectedGroupIds.length === 0) || assigning"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Assegna la lezione ai target selezionati"
            >
              <span v-if="assigning">Assegnazione in corso...</span>
              <span v-else>Assegna Selezionati</span>
            </button>
          </div>

          <!-- Messaggi di Risultato Assegnazione -->
          <div v-if="assignmentAttempted" class="mt-6 p-4 border rounded-md"
              :class="{
                  'bg-green-50 border-green-300': assignmentSuccess && assignmentResultsSummary.failed === 0 && !assignmentError,
                  'bg-yellow-50 border-yellow-300': assignmentSuccess && (assignmentResultsSummary.skipped > 0 || assignmentResultsSummary.failed > 0) && !assignmentError,
                  'bg-orange-50 border-orange-300': !assignmentSuccess && assignmentResultsSummary.skipped > 0 && assignmentResultsSummary.failed === 0 && !assignmentError,
                  'bg-red-50 border-red-300': assignmentResultsSummary.failed > 0 || assignmentError
              }">

            <p class="font-semibold mb-2 text-lg"
                :class="{
                    'text-green-800': assignmentSuccess && assignmentResultsSummary.failed === 0 && !assignmentError,
                    'text-yellow-800': assignmentSuccess && (assignmentResultsSummary.skipped > 0 || assignmentResultsSummary.failed > 0) && !assignmentError,
                    'text-orange-800': !assignmentSuccess && assignmentResultsSummary.skipped > 0 && assignmentResultsSummary.failed === 0 && !assignmentError,
                    'text-red-800': assignmentResultsSummary.failed > 0 || assignmentError
                }">
                <span v-if="assignmentError">Errore API durante l'assegnazione</span>
                <span v-else-if="assignmentSuccess && assignmentResultsSummary.skipped === 0 && assignmentResultsSummary.failed === 0">Assegnazione completata con successo!</span>
                <span v-else-if="assignmentSuccess">Assegnazione completata con note</span>
                <span v-else-if="!assignmentSuccess && assignmentResultsSummary.skipped > 0 && assignmentResultsSummary.failed === 0">Nessuna nuova assegnazione effettuata</span>
                <span v-else>Assegnazione fallita per alcuni target</span>
            </p>

            <div class="text-sm space-y-1"
                  :class="{
                      'text-green-700': assignmentSuccess && assignmentResultsSummary.failed === 0 && !assignmentError,
                      'text-yellow-700': assignmentSuccess && (assignmentResultsSummary.skipped > 0 || assignmentResultsSummary.failed > 0) && !assignmentError,
                      'text-orange-700': !assignmentSuccess && assignmentResultsSummary.skipped > 0 && assignmentResultsSummary.failed === 0 && !assignmentError,
                      'text-red-700': assignmentResultsSummary.failed > 0 || assignmentError
                  }">
                <p v-if="assignmentResultsSummary.created > 0">
                    <span class="font-medium">{{ assignmentResultsSummary.created }}</span>
                    {{ assignmentResultsSummary.created === 1 ? 'nuova assegnazione' : 'nuove assegnazioni' }} effettuata{{ assignmentResultsSummary.created === 1 ? '' : 'e' }}.
                </p>
                <p v-if="assignmentResultsSummary.skipped > 0">
                    <span class="font-medium">{{ assignmentResultsSummary.skipped }}</span>
                    {{ assignmentResultsSummary.skipped === 1 ? 'target già assegnato' : 'target già assegnati' }} (saltato).
                </p>
                  <p v-if="assignmentResultsSummary.failed > 0">
                    <span class="font-medium">{{ assignmentResultsSummary.failed }}</span>
                    {{ assignmentResultsSummary.failed === 1 ? 'assegnazione fallita' : 'assegnazioni fallite' }} (ID non valido o errore).
                </p>
                <p v-if="assignmentError" class="mt-2 font-semibold">Dettaglio Errore API: {{ assignmentError }}</p>

                <ul v-if="assignmentResultsSummary.details.length > 0 && (assignmentResultsSummary.skipped > 0 || assignmentResultsSummary.failed > 0)" class="list-disc list-inside pl-4 mt-2 text-xs">
                    <li v-for="(detail, index) in assignmentResultsSummary.details" :key="index">{{ detail }}</li>
                </ul>
            </div>
          </div>
          <!-- Fine Messaggi Risultato -->
        </div>
      </div> <!-- Fine modal-body -->

      <!-- Modale Selezione Studenti (interna ad AssignLessonModal) -->
      <StudentSelectionModal
        :show="isStudentModalOpen"
        :students="students"
        :initial-selected-ids="selectedStudentIds"
        @close="isStudentModalOpen = false"
        @update:selectedIds="updateSelectedStudents"
      />

      <!-- Modale Selezione Gruppi (interna ad AssignLessonModal) -->
      <GroupSelectionModal
        :show="isGroupModalOpen"
        :groups="groups"
        :initial-selected-ids="selectedGroupIds"
        @close="isGroupModalOpen = false"
        @update:selectedIds="updateSelectedGroups"
      />

    </div> <!-- Fine div modale principale -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, type PropType } from 'vue';
import { useLessonStore } from '@/stores/lessons';
import type { Lesson, Student, AssignmentResult } from '@/types/lezioni';
import type { StudentGroup } from '@/types/groups';
import StudentSelectionModal from '@/components/common/StudentSelectionModal.vue';
import GroupSelectionModal from '@/components/common/GroupSelectionModal.vue';

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  lessonId: {
    type: Number as PropType<number | null>,
    required: false, // Diventa false perché potremmo non averlo subito se la modale si apre vuota
    default: null,
  }
});

const emit = defineEmits(['close', 'assignment-complete']);

const lessonStore = useLessonStore();

const lesson = ref<Lesson | null>(null);
const students = ref<Student[]>([]);
const groups = ref<StudentGroup[]>([]);
const selectedStudentIds = ref<number[]>([]);
const selectedGroupIds = ref<number[]>([]);
const assigning = ref(false);
const assignmentSuccess = ref(false);
const assignmentAttempted = ref(false);
const assignmentError = ref<string | null>(null);
const assignmentResultsSummary = ref<{ created: number; skipped: number; failed: number; details: string[] }>({ created: 0, skipped: 0, failed: 0, details: [] });
const isStudentModalOpen = ref(false);
const isGroupModalOpen = ref(false);

// Stati di caricamento ed errore interni alla modale
const internalLoadingLesson = ref(true);
const internalLoadingStudents = ref(true);
const internalLoadingGroups = ref(true);
const internalErrorLesson = ref<string | null>(null);
const internalErrorStudents = ref<string | null>(null);
const internalErrorGroups = ref<string | null>(null);


const fetchLessonDetails = async () => {
  if (!props.lessonId) {
    lesson.value = null;
    internalErrorLesson.value = "ID Lezione non fornito.";
    internalLoadingLesson.value = false;
    return;
  }
  internalLoadingLesson.value = true;
  internalErrorLesson.value = null;
  try {
    await lessonStore.fetchLesson(props.lessonId);
    lesson.value = lessonStore.getLessonById(props.lessonId) || null;
    if (!lesson.value) {
        throw new Error("Lezione non trovata.");
    }
  } catch (err: any) {
    console.error("Errore caricamento lezione nella modale:", err);
    internalErrorLesson.value = err.message || 'Errore sconosciuto';
    lesson.value = null;
  } finally {
    internalLoadingLesson.value = false;
  }
};

const fetchStudentsForModal = async () => {
  internalLoadingStudents.value = true;
  internalErrorStudents.value = null;
  try {
    students.value = await lessonStore.fetchStudentsForTeacher();
  } catch (err: any) {
    console.error("Errore caricamento studenti nella modale:", err);
    internalErrorStudents.value = err.message || 'Errore sconosciuto';
    students.value = [];
  } finally {
    internalLoadingStudents.value = false;
  }
};

const fetchGroupsForModal = async () => {
  internalLoadingGroups.value = true;
  internalErrorGroups.value = null;
  try {
    await lessonStore.fetchGroupsAction();
    groups.value = lessonStore.groups;
  } catch (err: any) {
    console.error("Errore caricamento gruppi nella modale:", err);
    internalErrorGroups.value = err.message || 'Errore sconosciuto';
    groups.value = [];
  } finally {
    internalLoadingGroups.value = false;
  }
};

const loadAllData = async () => {
  if (props.lessonId) {
    await Promise.all([
      fetchLessonDetails(),
      fetchStudentsForModal(),
      fetchGroupsForModal()
    ]);
  } else {
    // Se non c'è lessonId, carichiamo solo studenti e gruppi
    // o gestiamo come errore/stato vuoto
    internalLoadingLesson.value = false; // Non c'è lezione da caricare
    await Promise.all([
      fetchStudentsForModal(),
      fetchGroupsForModal()
    ]);
  }
};

watch(() => props.show, (newVal) => {
  if (newVal) {
    // Resetta stati quando la modale si apre
    selectedStudentIds.value = [];
    selectedGroupIds.value = [];
    assigning.value = false;
    assignmentSuccess.value = false;
    assignmentAttempted.value = false;
    assignmentError.value = null;
    assignmentResultsSummary.value = { created: 0, skipped: 0, failed: 0, details: [] };
    lesson.value = null; // Resetta la lezione
    
    // Carica i dati necessari
    loadAllData();
  }
});

watch(() => props.lessonId, (newVal) => {
  if (props.show && newVal) {
    loadAllData(); // Ricarica i dati se lessonId cambia mentre la modale è aperta
  } else if (props.show && !newVal) {
    // Gestisci il caso in cui lessonId diventa null mentre la modale è aperta
    lesson.value = null;
    internalErrorLesson.value = "ID Lezione non più disponibile.";
    internalLoadingLesson.value = false;
  }
});


const assignLessonToTargets = async () => {
  if (!lesson.value || !props.lessonId || (selectedStudentIds.value.length === 0 && selectedGroupIds.value.length === 0)) return;

  assigning.value = true;
  assignmentAttempted.value = false;
  assignmentSuccess.value = false;
  assignmentError.value = null;
  assignmentResultsSummary.value = { created: 0, skipped: 0, failed: 0, details: [] };

  try {
    const results: AssignmentResult[] = await lessonStore.assignLessonToTargets(
        props.lessonId,
        selectedStudentIds.value,
        selectedGroupIds.value
    );

    let createdCount = 0;
    let skippedCount = 0;
    let failedCount = 0;
    const details: string[] = [];

    results.forEach((result: AssignmentResult) => {
        let targetName = `ID ${result.targetId}`;
        try {
            if (result.targetType === 'student') {
                const student = students.value.find(s => s.id === result.targetId);
                targetName = student ? `Studente: ${student.first_name} ${student.last_name}` : `Studente ID ${result.targetId}`;
            } else if (result.targetType === 'group') {
                const group = groups.value.find(g => g.id === result.targetId);
                targetName = group ? `Gruppo: ${group.name}` : `Gruppo ID ${result.targetId}`;
            }
        } catch (e) {
             console.error("Errore nel trovare nome target:", e);
        }

        if (result.success) {
            createdCount++;
        } else {
            const isAlreadyAssigned = result.error?.toLowerCase().includes('già assegnato');
            if (isAlreadyAssigned) {
                skippedCount++;
                details.push(`${targetName}: Già assegnato (saltato).`);
            } else {
                failedCount++;
                details.push(`${targetName}: Assegnazione fallita (${result.error || 'errore sconosciuto'}).`);
            }
        }
    });

    assignmentSuccess.value = createdCount > 0;
    assignmentResultsSummary.value = {
        created: createdCount,
        skipped: skippedCount,
        failed: failedCount,
        details: details
    };

    selectedStudentIds.value = [];
    selectedGroupIds.value = [];
    
    if (createdCount > 0 || skippedCount > 0 || failedCount > 0) { // Emetti solo se c'è stato un tentativo con risultati
        emit('assignment-complete', { ...assignmentResultsSummary.value, lessonId: props.lessonId });
    }
    // Non chiudere automaticamente la modale, l'utente può vedere i risultati e decidere.

  } catch (err: any) {
    console.error("Errore durante l'assegnazione:", err);
    assignmentError.value = err.message || 'Si è verificato un errore imprevisto durante la richiesta.';
    emit('assignment-complete', { error: assignmentError.value, lessonId: props.lessonId });
  } finally {
    assigning.value = false;
    assignmentAttempted.value = true;
  }
};

const updateSelectedStudents = (newSelectedIds: number[]) => {
    selectedStudentIds.value = newSelectedIds;
};

const updateSelectedGroups = (newSelectedIds: number[]) => {
    selectedGroupIds.value = newSelectedIds;
};

const selectionSummary = computed(() => {
  const studentCount = selectedStudentIds.value.length;
  const groupCount = selectedGroupIds.value.length;

  if (studentCount === 0 && groupCount === 0) {
    return 'Nessuno studente o gruppo selezionato.';
  }

  let parts: string[] = [];
  if (studentCount > 0) {
    parts.push(`${studentCount} ${studentCount === 1 ? 'studente' : 'studenti'}`);
  }
  if (groupCount > 0) {
    parts.push(`${groupCount} ${groupCount === 1 ? 'gruppo' : 'gruppi'}`);
  }

  return `Selezionati: ${parts.join(' e ')}.`;
});

const closeModal = () => {
  emit('close');
};

// Carica i dati quando il componente viene montato se la modale è già visibile e lessonId è fornito
// Questo è più per testing o scenari in cui la modale potrebbe essere resa visibile programmaticamente all'inizio
onMounted(() => {
  if (props.show && props.lessonId) {
    loadAllData();
  }
});

</script>

<style scoped>
/* Stili specifici per la modale di assegnazione, se necessari */
/* Assicurarsi che z-index sia inferiore a StudentSelectionModal e GroupSelectionModal se si sovrappongono */
/* StudentSelectionModal e GroupSelectionModal usano z-50, quindi questa può usare z-40 */
.modal-body {
  max-height: 70vh; /* o un valore che preferisci */
  overflow-y: auto;
}
</style>