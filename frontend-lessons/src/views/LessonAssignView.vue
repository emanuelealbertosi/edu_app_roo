<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-4">Assegna Lezione: {{ lesson?.title }}</h1>

    <div v-if="loadingLesson || loadingStudents" class="text-center">
      Caricamento dati...
    </div>
    <div v-else-if="errorLesson || errorStudents" class="text-red-500 text-center">
      Errore nel caricamento dei dati. Riprova più tardi.
    </div>

    <div v-else-if="lesson && students">
      <p class="mb-4">Seleziona gli studenti a cui vuoi assegnare questa lezione:</p>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div v-for="student in students" :key="student.id" class="border rounded p-3 flex items-center justify-between">
          <span>{{ student.first_name }} {{ student.last_name }} ({{ student.unique_identifier }})</span>
          <input
            type="checkbox"
            :value="student.id"
            v-model="selectedStudentIds"
            class="form-checkbox h-5 w-5 text-blue-600"
          />
        </div>
         <div v-if="students.length === 0" class="col-span-full text-center text-gray-500">
            Nessuno studente trovato per questo docente.
        </div>
      </div>

      <div class="flex justify-end space-x-4">
         <button
            @click="selectAllStudents"
            :disabled="students.length === 0"
            class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
          >
            Seleziona Tutti
          </button>
          <button
            @click="deselectAllStudents"
            :disabled="selectedStudentIds.length === 0"
            class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
          >
            Deseleziona Tutti
          </button>
        <button
          @click="assignLesson"
          :disabled="selectedStudentIds.length === 0 || assigning"
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="assigning">Assegnazione in corso...</span>
          <span v-else>Assegna Selezionati</span>
        </button>
      </div>

      <div v-if="assignmentSuccess" class="mt-4 p-3 bg-green-100 text-green-700 rounded">
        Lezione assegnata con successo agli studenti selezionati!
      </div>
      <div v-if="assignmentError" class="mt-4 p-3 bg-red-100 text-red-700 rounded">
        Errore durante l'assegnazione: {{ assignmentError }}
      </div>
       <div v-if="partialAssignmentInfo.length > 0" class="mt-4 p-3 bg-yellow-100 text-yellow-700 rounded">
        <p>Nota: Alcuni studenti potrebbero essere già stati assegnati a questa lezione:</p>
        <ul>
          <li v-for="info in partialAssignmentInfo" :key="info">{{ info }}</li>
        </ul>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLessonStore } from '@/stores/lessons'
import { useAuthStore } from '@/stores/auth' // Assumendo esista uno store per gli studenti o accessibile tramite auth/teacher
import type { Lesson, Student, AssignmentResult } from '@/types/lezioni' // Aggiunto AssignmentResult

const route = useRoute()
const router = useRouter()
const lessonStore = useLessonStore()
const authStore = useAuthStore() // O uno store dedicato ai dati del docente

const lesson = ref<Lesson | null>(null)
const students = ref<Student[]>([]) // Assumi che lo store auth o un altro store fornisca gli studenti del docente
const selectedStudentIds = ref<number[]>([])
const assigning = ref(false)
const assignmentSuccess = ref(false)
const assignmentError = ref<string | null>(null)
const partialAssignmentInfo = ref<string[]>([]) // Info su assegnazioni parziali o fallite

const loadingLesson = ref(true)
const loadingStudents = ref(true)
const errorLesson = ref<string | null>(null)
const errorStudents = ref<string | null>(null)

const lessonId = computed(() => Number(route.params.lessonId))

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
    console.warn("Manca implementazione fetchStudents - usare dati fittizi per ora");
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

const assignLesson = async () => {
  if (!lesson.value || selectedStudentIds.value.length === 0) return;

  assigning.value = true;
  assignmentSuccess.value = false;
  assignmentError.value = null;
  partialAssignmentInfo.value = [];

  try {
    const results = await lessonStore.assignLessonToStudents(lessonId.value, selectedStudentIds.value);

    // Gestione risultati parziali (alcuni successi, alcuni fallimenti/già assegnati)
    const successes = results.filter((r: AssignmentResult) => r.success);
    const failures = results.filter((r: AssignmentResult) => !r.success);

    if (successes.length === selectedStudentIds.value.length) {
      assignmentSuccess.value = true;
      selectedStudentIds.value = []; // Deseleziona dopo successo completo
       setTimeout(() => assignmentSuccess.value = false, 5000); // Nascondi messaggio dopo 5s
    } else {
       assignmentSuccess.value = successes.length > 0; // Successo parziale se almeno uno ok
       partialAssignmentInfo.value = failures.map((f: AssignmentResult) => {
           const student = students.value.find((s: Student) => s.id === f.studentId);
           const studentName = student ? `${student.first_name} ${student.last_name}` : `ID: ${f.studentId}`;
           return `${studentName}: ${f.error || 'Errore sconosciuto'}`;
       });
       // Mantieni selezionati gli studenti falliti per eventuale ri-tentativo? O deseleziona tutti?
       // Per ora deselezioniamo solo quelli andati a buon fine
       selectedStudentIds.value = failures.map((f: AssignmentResult) => f.studentId);
    }
     if (failures.length > 0 && successes.length === 0) {
        assignmentError.value = "Nessuna assegnazione riuscita. Controlla i dettagli sopra.";
     }


  } catch (err: any) {
    console.error("Errore durante l'assegnazione:", err);
    assignmentError.value = err.message || 'Si è verificato un errore imprevisto.';
     setTimeout(() => assignmentError.value = null, 7000); // Nascondi messaggio dopo 7s
  } finally {
    assigning.value = false;
  }
};

const selectAllStudents = () => {
  selectedStudentIds.value = students.value.map((s: Student) => s.id);
};

const deselectAllStudents = () => {
  selectedStudentIds.value = [];
};


onMounted(async () => {
  await fetchLesson();
  // Solo se la lezione è stata caricata correttamente, carica gli studenti
  if (lesson.value) {
      await fetchStudents();
  }
});
</script>

<style scoped>
/* Stili specifici se necessari */
</style>