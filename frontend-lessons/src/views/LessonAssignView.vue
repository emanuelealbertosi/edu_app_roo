<template>
  <div class="container mx-auto p-4">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6">
        <h1 class="text-2xl font-semibold">Assegna Lezione: {{ lesson?.title || '...' }}</h1>
    </div>

    <div v-if="loadingLesson || loadingStudents" class="text-center">
      Caricamento dati...
    </div>
    <div v-else-if="errorLesson || errorStudents" class="text-red-500 text-center">
      Errore nel caricamento dei dati. Riprova più tardi.
    </div>

    <div v-else-if="lesson && students">
      <p class="mb-4">Seleziona gli studenti e/o i gruppi a cui vuoi assegnare questa lezione:</p>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <!-- Colonna Selezione Studenti -->
        <div>
          <h3 class="text-lg font-medium mb-2">Studenti</h3>
          <div v-if="loadingStudents" class="text-gray-500 italic">Caricamento studenti...</div>
          <div v-else-if="errorStudents" class="text-red-600">{{ errorStudents }}</div>
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
          <h3 class="text-lg font-medium mb-2">Gruppi</h3>
          <div v-if="loadingGroups" class="text-gray-500 italic">Caricamento gruppi...</div>
          <div v-else-if="errorGroups" class="text-red-600">{{ errorGroups }}</div>
          <div v-else-if="groups.length > 0">
            <div class="space-y-2 max-h-60 overflow-y-auto border p-3 rounded-md">
              <div v-for="group in groups" :key="group.id" class="flex items-center">
                <input
                  type="checkbox"
                  :id="'group-' + group.id"
                  :value="group.id"
                  v-model="selectedGroupIds"
                  class="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <label :for="'group-' + group.id" class="ml-2 block text-sm text-gray-900">
                  {{ group.name }}
                </label>
              </div>
            </div>
             <div class="text-sm text-gray-600 mt-2">
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

      <div class="flex justify-end space-x-4">
        <button
          @click="assignLessonToTargets"
          :disabled="(selectedStudentIds.length === 0 && selectedGroupIds.length === 0) || assigning"
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Assegna la lezione ai target selezionati"
        >
          <span v-if="assigning">Assegnazione in corso...</span>
          <span v-else>Assegna Selezionati</span>
        </button>
      </div>

      <!-- Messaggi di Risultato Assegnazione -->
      <div v-if="assignmentAttempted" class="mt-6 p-4 border rounded"
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

              <!-- Mostra dettagli specifici se ci sono skipped o failed -->
              <ul v-if="assignmentResultsSummary.details.length > 0 && (assignmentResultsSummary.skipped > 0 || assignmentResultsSummary.failed > 0)" class="list-disc list-inside pl-4 mt-2 text-xs">
                  <li v-for="(detail, index) in assignmentResultsSummary.details" :key="index">{{ detail }}</li>
              </ul>
          </div>
      </div>
      <!-- Fine Messaggi Risultato -->

    </div>

    <!-- Modale Selezione Studenti -->
    <StudentSelectionModal
      :show="isStudentModalOpen"
      :students="students"
      :initial-selected-ids="selectedStudentIds"
      @close="isStudentModalOpen = false"
      @update:selectedIds="updateSelectedStudents"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useLessonStore } from '@/stores/lessons';
// Rimosso import non necessario di sharedAuthStore qui
import type { Lesson, Student, AssignmentResult } from '@/types/lezioni';
import type { StudentGroup } from '@/types/groups';
import StudentSelectionModal from '@/components/common/StudentSelectionModal.vue';
// Potrebbe servire un GroupSelectionModal se la lista diventa lunga

const route = useRoute()
// const router = useRouter() // Rimosso - non utilizzato
const lessonStore = useLessonStore()
// Rimosso sharedAuthStore
// const authStore = useAuthStore() // Rimosso - non utilizzato

const lesson = ref<Lesson | null>(null)
const students = ref<Student[]>([]);
const groups = ref<StudentGroup[]>([]); // Stato per i gruppi
const selectedStudentIds = ref<number[]>([]);
const selectedGroupIds = ref<number[]>([]); // Stato per gli ID dei gruppi selezionati
const assigning = ref(false);
const assignmentSuccess = ref(false); // Indica se almeno un'assegnazione è andata a buon fine
const assignmentAttempted = ref(false); // Flag per mostrare i messaggi di risultato
const assignmentError = ref<string | null>(null); // Errore generico dell'operazione
const assignmentResultsSummary = ref<{ created: number; skipped: number; failed: number; details: string[] }>({ created: 0, skipped: 0, failed: 0, details: [] }); // Nuovo stato per riepilogo dettagliato
const isStudentModalOpen = ref(false); // Stato per la modale studenti
// Aggiungere isGroupModalOpen se si usa una modale per gruppi

const loadingLesson = ref(true);
const loadingStudents = ref(true);
const loadingGroups = ref(true); // Stato di caricamento per i gruppi
const errorLesson = ref<string | null>(null);
const errorStudents = ref<string | null>(null);
const errorGroups = ref<string | null>(null); // Stato di errore per i gruppi

const lessonId = computed(() => Number(route.params.lessonId))
// Rimosso currentUserId

// Funzione per caricare gli studenti del docente (da adattare allo store effettivo)
const fetchStudents = async () => {
  loadingStudents.value = true;
  errorStudents.value = null;
  try {
    // Assumiamo che lo store auth o un altro store abbia un'azione per ottenere gli studenti del docente loggato
    // Questa parte dipende fortemente da come è strutturato lo store degli utenti/studenti
    // Esempio fittizio:
    // students.value = await teacherDataStore.fetchMyStudents();
    // Per ora, usiamo un placeholder o assumiamo che lo store lezioni possa farlo (meno ideale)
    // Se non hai uno store studenti, dovrai implementarlo o aggiungerlo allo store auth/lezioni
    // console.warn("Manca implementazione fetchStudents - usare dati fittizi per ora"); // Rimosso warning fuorviante
    // Dati fittizi per test UI:
    // students.value = [
    //   { id: 1, user_id: 1, first_name: 'Mario', last_name: 'Rossi', unique_identifier: 'S001', created_at: '', is_active: true },
    //   { id: 2, user_id: 1, first_name: 'Luigi', last_name: 'Verdi', unique_identifier: 'S002', created_at: '', is_active: true },
    // ];
    // TODO: Sostituire con la chiamata API reale tramite lo store appropriato
     students.value = await lessonStore.fetchStudentsForTeacher(); // Assumiamo esista questa azione
  } catch (err: any) {
    console.error("Errore caricamento studenti:", err);
    errorStudents.value = err.message || 'Errore sconosciuto';
    students.value = []; // Svuota in caso di errore
  } finally {
    loadingStudents.value = false;
  }
};

// Funzione per caricare i gruppi del docente
const fetchGroups = async () => {
  loadingGroups.value = true;
  errorGroups.value = null;
  try {
    await lessonStore.fetchGroupsAction(); // Chiama l'azione dello store
    groups.value = lessonStore.groups; // Prende i gruppi dallo stato dello store
  } catch (err: any) {
    console.error("Errore caricamento gruppi:", err);
    errorGroups.value = err.message || 'Errore sconosciuto durante caricamento gruppi';
    groups.value = [];
  } finally {
    loadingGroups.value = false;
  }
};


const fetchLesson = async () => {
  if (!lessonId.value) return;
  loadingLesson.value = true;
  errorLesson.value = null;
  try {
    await lessonStore.fetchLesson(lessonId.value);
    lesson.value = lessonStore.getLessonById(lessonId.value) || null;
    if (!lesson.value) {
        throw new Error("Lezione non trovata.");
    }
  } catch (err: any) {
    console.error("Errore caricamento lezione:", err);
    errorLesson.value = err.message || 'Errore sconosciuto';
    lesson.value = null;
  } finally {
    loadingLesson.value = false;
  }
};

// Rinominata e corretta per gestire studenti E gruppi
const assignLessonToTargets = async () => {
  // Modificato controllo: deve esserci almeno uno studente O un gruppo selezionato
  if (!lesson.value || (selectedStudentIds.value.length === 0 && selectedGroupIds.value.length === 0)) return;

  assigning.value = true;
  assignmentAttempted.value = false; // Resetta il flag tentativo
  assignmentSuccess.value = false; // Resetta successo
  assignmentError.value = null; // Resetta errore generico
  assignmentResultsSummary.value = { created: 0, skipped: 0, failed: 0, details: [] }; // Resetta riepilogo

  try {
    // Chiama la nuova azione dello store passando entrambi gli array di ID
    // Assumiamo che lo store restituisca la risposta diretta dal backend
    // L'azione dello store restituisce un array di AssignmentResult
    const results: AssignmentResult[] = await lessonStore.assignLessonToTargets(
        lessonId.value,
        selectedStudentIds.value,
        selectedGroupIds.value
    );

    // Processa l'array di AssignmentResult
    let createdCount = 0;
    let skippedCount = 0;
    let failedCount = 0;
    const details: string[] = [];

    results.forEach((result: AssignmentResult) => {
        let targetName = `ID ${result.targetId}`;
        try { // Aggiunto try-catch per sicurezza nell'accesso ai dati
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
            // Non aggiungiamo dettagli per i successi di default
        } else {
            // Controlla se l'errore indica "già assegnato" o un altro fallimento
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

    assignmentSuccess.value = createdCount > 0; // Successo se almeno uno creato

    assignmentResultsSummary.value = {
        created: createdCount,
        skipped: skippedCount,
        failed: failedCount,
        details: details // Popola con i messaggi raccolti
    };


    // Deseleziona TUTTI i target dopo il tentativo, indipendentemente dal risultato
    // L'utente può riselezionare se necessario vedendo i messaggi
    selectedStudentIds.value = [];
    selectedGroupIds.value = [];

    // Non impostare errore generico se ci sono solo skipped/failed gestiti sopra
    // assignmentError viene impostato solo per errori API generali nel blocco catch


  } catch (err: any) {
    // Errore generale API (es. network error, 500 server error)
    console.error("Errore durante l'assegnazione:", err);
    assignmentError.value = err.message || 'Si è verificato un errore imprevisto durante la richiesta.';
    // Non nascondere automaticamente l'errore generale
  } finally {
    assigning.value = false;
    assignmentAttempted.value = true; // Indica che il tentativo è stato fatto, per mostrare i messaggi
  }
};

// Funzione per aggiornare gli studenti selezionati dalla modale
const updateSelectedStudents = (newSelectedIds: number[]) => {
    selectedStudentIds.value = newSelectedIds;
};

// Rimosso computed isAssignmentPossible

// Proprietà calcolata per il riepilogo della selezione
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


// Rimosse funzioni selectAllStudents e deselectAllStudents

onMounted(async () => {
  await fetchLesson();
  // Solo se la lezione è stata caricata correttamente, carica studenti e gruppi
  if (lesson.value) {
      await Promise.all([ // Carica in parallelo
          fetchStudents(),
          fetchGroups()
      ]);
  }
});
</script>

<style scoped>
/* Stili specifici se necessari */
</style>