<template>
  <div class="students-view p-4 md:p-6">
    <h1 class="text-2xl font-semibold mb-4">Gestione Studenti e Gruppi</h1>

    <!-- Sezione Gestione Gruppi -->
    <section class="mb-8 p-4 border rounded shadow-sm bg-white">
      <h2 class="text-xl font-semibold mb-3">Gestione Gruppi</h2>
      <button @click="openGroupForm()" class="btn btn-success btn-sm mb-3">Crea Nuovo Gruppo</button>

      <div v-if="isLoadingGroups" class="loading">Caricamento gruppi...</div>
      <div v-else-if="groupsError" class="error-message">Errore caricamento gruppi: {{ groupsError }}</div>
      <ul v-else-if="groups.length > 0" class="list-disc pl-5">
        <li v-for="group in groups" :key="group.id" class="mb-2 flex justify-between items-center">
          <span>{{ group.name }} ({{ group.member_count }} membri)</span>
          <div>
            <button @click="openGroupForm(group)" class="btn btn-warning btn-xs mr-2">Modifica</button>
            <button @click="handleDeleteGroup(group.id)" class="btn btn-danger btn-xs">Elimina</button>
          </div>
        </li>
      </ul>
      <p v-else class="text-gray-500 italic">Nessun gruppo creato.</p>

      <!-- Form Creazione/Modifica Gruppo (Modale o inline) -->
      <div v-if="showGroupForm" class="mt-4 p-3 border rounded bg-gray-100">
        <h3 class="text-lg font-medium mb-2">{{ editingGroup ? 'Modifica Gruppo' : 'Nuovo Gruppo' }}</h3>
         <div class="form-group">
           <label for="group-name">Nome Gruppo:</label>
           <input type="text" id="group-name" v-model="newGroupName" class="w-full p-2 border rounded" required>
         </div>
         <div v-if="groupFormError" class="error-message my-2">{{ groupFormError }}</div>
         <div class="form-actions mt-3">
           <button @click="handleSaveGroup" :disabled="isSavingGroup" class="btn btn-primary mr-2">
             {{ isSavingGroup ? 'Salvataggio...' : 'Salva Gruppo' }}
           </button>
           <button @click="closeGroupForm" class="btn btn-secondary">Annulla</button>
         </div>
      </div>
    </section>

    <!-- Sezione Gestione Studenti -->
    <section>
      <h2 class="text-xl font-semibold mb-3">Gestione Studenti</h2>
      <!-- Pulsante per aprire il form di creazione -->
      <div class="my-4">
        <button @click="openCreateForm" class="btn btn-primary">Crea Nuovo Studente</button>
      </div>

      <div v-if="isLoading" class="loading">Caricamento studenti...</div>
      <div v-else-if="error" class="error-message">
        Errore nel caricamento degli studenti: {{ error }}
      </div>
      <!-- <div v-if="unassignError" class="error-message">Errore disassegnazione: {{ unassignError }}</div> -->

    <!-- Form di creazione (mostrato condizionalmente) -->
    <div v-if="showCreateForm" class="create-form mt-6 p-4 border rounded shadow-md bg-gray-50">
      <h2>Nuovo Studente</h2>
      <div class="form-group">
        <label for="new-first-name">Nome:</label>
        <input type="text" id="new-first-name" v-model="newStudentFirstName" class="w-full p-2 border rounded" required>
      </div>
      <div class="form-group">
        <label for="new-last-name">Cognome:</label>
        <input type="text" id="new-last-name" v-model="newStudentLastName" class="w-full p-2 border rounded" required>
      </div>
      <div class="form-group">
         <label for="new-student-group">Gruppo (opzionale):</label>
         <select id="new-student-group" v-model="newStudentGroupId" class="w-full p-2 border rounded">
           <option :value="null">Nessun Gruppo</option>
           <option v-for="group in groups" :key="group.id" :value="group.id">
             {{ group.name }}
           </option>
         </select>
       </div>
      <div v-if="createStudentError" class="error-message mb-3">{{ createStudentError }}</div>
      <div class="form-actions">
        <button @click="handleCreateStudent" :disabled="isCreatingStudent" class="btn btn-success mr-2">
          {{ isCreatingStudent ? 'Creazione...' : 'Salva Studente' }}
        </button>
        <button @click="showCreateForm = false" class="btn btn-secondary">Annulla</button>
      </div>
    </div>

    <!-- Info Studente Creato (mostrato condizionalmente) -->
    <div v-if="createdStudentData" class="created-info mt-6 p-4 border rounded shadow-md bg-green-100 border-green-300">
      <h3 class="text-lg font-semibold text-green-800">Studente Creato con Successo!</h3>
      <p><strong>Nome:</strong> {{ createdStudentData.first_name }} {{ createdStudentData.last_name }}</p>
      <p><strong>Codice Studente:</strong> <code class="font-mono bg-green-200 px-1 rounded">{{ createdStudentData.student_code }}</code></p>
      <p><strong>PIN Iniziale:</strong> <code class="font-mono bg-green-200 px-1 rounded">{{ createdStudentData.pin }}</code></p>
      <p class="mt-2 text-red-700 font-bold"><strong>ATTENZIONE:</strong> Comunica immediatamente il Codice Studente e il PIN allo studente. Il PIN non sarà più visibile.</p>
      <button @click="closeCreatedStudentInfo" class="btn btn-secondary mt-3">Chiudi</button>
    </div>
    <div v-if="!isLoading && !error && students.length > 0" class="students-list overflow-x-auto">
      <table class="min-w-full">
        <thead>
          <tr>
            <th class="px-4 py-2 text-left">Nome</th>
            <th class="px-4 py-2 text-left">Cognome</th>
            <th class="px-4 py-2 text-left">Codice Studente</th>
            <th class="px-4 py-2 text-left">Gruppo</th> <!-- Nuova colonna Gruppo -->
            <th class="px-4 py-2 text-left">Azioni</th>
          </tr>
        </thead>
        <tbody>
          <!-- Corretto v-for singolo -->
          <tr v-for="student in students" :key="student.id" class="border-t">
            <td class="px-4 py-2">{{ student.first_name }}</td>
            <td class="px-4 py-2">{{ student.last_name }}</td>
            <td class="px-4 py-2">{{ student.student_code }}</td>
            <td class="px-4 py-2">
                <!-- Visualizzazione Gruppo -->
                <span v-if="!editingStudent || editingStudent.id !== student.id">
                    {{ student.group_name || 'N/A' }}
                </span>
                 <!-- Form Modifica Gruppo (inline) -->
                <div v-if="editingStudent && editingStudent.id === student.id" class="inline-edit-group">
                     <select v-model="editStudentGroupId" class="p-1 border rounded text-sm">
                         <option :value="null">Nessun Gruppo</option>
                         <option v-for="group in groups" :key="group.id" :value="group.id">
                             {{ group.name }}
                         </option>
                     </select>
                     <button @click="handleUpdateStudentGroup(student)" :disabled="isSavingStudentEdit" class="btn btn-success btn-xs ml-1">Salva</button>
                     <button @click="cancelEditStudentGroup" class="btn btn-secondary btn-xs ml-1">Annulla</button>
                     <div v-if="editStudentError" class="error-message text-xs">{{ editStudentError }}</div>
                </div>
            </td>
            <td class="px-4 py-2">
              <!-- Link alla pagina di dettaglio dello studente -->
              <router-link
                :to="{ name: 'student-detail', params: { id: student.id } }"
                class="btn btn-info btn-xs mr-1"
              >
                Dettagli
              </router-link>
              <!-- Pulsante Modifica Gruppo -->
               <button
                   v-if="!editingStudent || editingStudent.id !== student.id"
                   @click="openEditStudentGroupForm(student)"
                   class="btn btn-warning btn-xs"
               >
                   Modifica Gruppo
               </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!isLoading && !error && students.length === 0" class="no-students">
      Nessuno studente trovato.
    </div>
  </section> <!-- Aggiunto tag di chiusura mancante -->
  </div>
</template>

<script setup lang="ts">
// Test comment to force re-evaluation
import { ref, onMounted, computed } from 'vue'; // Aggiunto computed
import { fetchStudents, type Student, updateStudent, type StudentUpdatePayload } from '@/api/students'; // Importa la funzione API e il tipo, aggiunto updateStudent e StudentUpdatePayload
// Importa API per creazione studente
import {
  createStudentByTeacher, type TeacherCreateStudentPayload, type TeacherCreateStudentResponse
} from '@/api/students';
// Importa API Gruppi
import {
  fetchGroups, createGroup, updateGroup, deleteGroup, type StudentGroup
} from '@/api/groups';
// Rimosse importazioni non usate per assegnazioni/disassegnazioni inline
// import { fetchStudentAssignments, type StudentQuizAssignment, type StudentPathwayAssignment, type StudentAssignmentsResponse } from '@/api/students';
// import { unassignQuizFromStudent } from '@/api/quizzes';
// import { unassignPathwayFromStudent } from '@/api/pathways';

const students = ref<Student[]>([]); // Conterrà l'elenco degli studenti
const isLoading = ref(false); // Stato di caricamento
const error = ref<string | null>(null); // Messaggio di errore caricamento studenti
// const unassignError = ref<string | null>(null); // Rimosso errore disassegnazione

// Rimossa logica per assegnazioni inline
// const selectedStudentId = ref<number | null>(null);
// const selectedStudentAssignments = ref<StudentAssignmentsResponse | null>(null);
// const isLoadingAssignments = ref(false);
// const assignmentsError = ref<string | null>(null);

// Stato per la gestione gruppi
const groups = ref<StudentGroup[]>([]);
const isLoadingGroups = ref(false);
const groupsError = ref<string | null>(null);
const showGroupForm = ref(false);
const editingGroup = ref<StudentGroup | null>(null); // Gruppo in modifica
const newGroupName = ref('');
const isSavingGroup = ref(false);
const groupFormError = ref<string | null>(null);

// Stato per la creazione studente
const showCreateForm = ref(false);
const newStudentFirstName = ref('');
const newStudentLastName = ref('');
const newStudentGroupId = ref<number | null>(null); // ID gruppo selezionato
const isCreatingStudent = ref(false);
const createdStudentData = ref<TeacherCreateStudentResponse | null>(null);
const createStudentError = ref<string | null>(null);
// Stato per modifica gruppo studente inline
const editingStudent = ref<Student | null>(null);
const editStudentGroupId = ref<number | null>(null);
const isSavingStudentEdit = ref(false);
const editStudentError = ref<string | null>(null);

// Caricamento iniziale studenti e gruppi
onMounted(async () => {
  loadStudents();
  loadGroups();
});

const loadStudents = async () => {
   isLoading.value = true;
   error.value = null;
   try {
     students.value = await fetchStudents();
   } catch (err: any) {
     console.error("Errore nel recupero degli studenti:", err);
     error.value = err.message || 'Si è verificato un errore sconosciuto.';
   } finally {
     isLoading.value = false;
   }
};

const loadGroups = async () => {
   isLoadingGroups.value = true;
   groupsError.value = null;
   try {
     groups.value = await fetchGroups();
   } catch (err: any) {
     console.error("Errore nel recupero dei gruppi:", err);
     groupsError.value = err.message || 'Si è verificato un errore sconosciuto.';
   } finally {
     isLoadingGroups.value = false;
   }
};

// Rimossa funzione showAssignments (ora gestita dalla vista dettaglio)
// Rimosse funzioni showAssignments e handleUnassign (logica spostata/non necessaria qui)
// Rimosso }; extra

// --- Logica Creazione Studente ---

const openCreateForm = () => {
  showCreateForm.value = true;
  newStudentFirstName.value = '';
  newStudentLastName.value = '';
  newStudentGroupId.value = null; // Resetta gruppo selezionato
  createStudentError.value = null;
  createdStudentData.value = null; // Nasconde info precedente
};

const handleCreateStudent = async () => {
  if (!newStudentFirstName.value || !newStudentLastName.value) {
    createStudentError.value = "Nome e Cognome sono obbligatori.";
    return;
  }

  isCreatingStudent.value = true;
  createStudentError.value = null;
  createdStudentData.value = null;

  const payload: TeacherCreateStudentPayload = {
    first_name: newStudentFirstName.value,
    last_name: newStudentLastName.value,
    group_id: newStudentGroupId.value // Aggiunge group_id (può essere null)
  };

  try {
    const newStudent = await createStudentByTeacher(payload);
    students.value.push(newStudent); // Aggiunge il nuovo studente alla lista visualizzata
    createdStudentData.value = newStudent; // Mostra i dati generati
    showCreateForm.value = false; // Chiude il form
  } catch (err: any) {
    console.error("Errore durante la creazione dello studente:", err);
    createStudentError.value = err.response?.data?.detail || err.message || "Errore sconosciuto durante la creazione.";
  } finally {
    isCreatingStudent.value = false;
  }
};

const closeCreatedStudentInfo = () => {
  createdStudentData.value = null;
};

// --- Logica Gestione Gruppi ---

const openGroupForm = (group: StudentGroup | null = null) => {
  if (group) {
    editingGroup.value = group;
    newGroupName.value = group.name;
  } else {
    editingGroup.value = null;
    newGroupName.value = '';
  }
  groupFormError.value = null;
  showGroupForm.value = true;
};

const closeGroupForm = () => {
  showGroupForm.value = false;
  editingGroup.value = null;
  newGroupName.value = '';
  groupFormError.value = null;
};

const handleSaveGroup = async () => {
  if (!newGroupName.value) {
    groupFormError.value = "Il nome del gruppo è obbligatorio.";
    return;
  }

  isSavingGroup.value = true;
  groupFormError.value = null;
  const payload = { name: newGroupName.value };

  try {
    if (editingGroup.value) {
      // Aggiorna gruppo esistente
      const updated = await updateGroup(editingGroup.value.id, payload);
      // Aggiorna la lista locale
      const index = groups.value.findIndex(g => g.id === updated.id);
      if (index !== -1) {
        groups.value[index] = updated;
      }
    } else {
      // Crea nuovo gruppo
      const created = await createGroup(payload);
      groups.value.push(created); // Aggiungi alla lista locale
    }
    closeGroupForm(); // Chiudi il form dopo successo
  } catch (err: any) {
    console.error("Errore salvataggio gruppo:", err);
    groupFormError.value = err.response?.data?.detail || err.message || "Errore sconosciuto durante il salvataggio.";
  } finally {
    isSavingGroup.value = false;
  }
};

const handleDeleteGroup = async (groupId: number) => {
   const groupToDelete = groups.value.find(g => g.id === groupId);
   if (!groupToDelete) return;

   const confirmationMessage = `Sei sicuro di voler eliminare il gruppo "${groupToDelete.name}"? Gli studenti in questo gruppo non verranno eliminati, ma perderanno l'associazione al gruppo.`;
   if (!confirm(confirmationMessage)) {
       return;
   }

   try {
       await deleteGroup(groupId);
       // Rimuovi dalla lista locale
       groups.value = groups.value.filter(g => g.id !== groupId);
       // Ricarica gli studenti per aggiornare i loro campi 'group_name'
       await loadStudents();
       alert(`Gruppo "${groupToDelete.name}" eliminato con successo.`);
   } catch (err: any) {
       console.error(`Errore eliminazione gruppo ${groupId}:`, err);
       alert(`Errore durante l'eliminazione del gruppo: ${err.response?.data?.detail || err.message}`);
   }
};

// --- Logica Modifica Gruppo Studente ---

const openEditStudentGroupForm = (student: Student) => {
   editingStudent.value = student;
   editStudentGroupId.value = student.group_id ?? null; // Pre-seleziona gruppo attuale usando group_id
   editStudentError.value = null; // Resetta errore
};

const cancelEditStudentGroup = () => {
   editingStudent.value = null;
   editStudentGroupId.value = null;
   editStudentError.value = null;
};

const handleUpdateStudentGroup = async (student: Student) => {
   if (!editingStudent.value || editingStudent.value.id !== student.id) return;

   isSavingStudentEdit.value = true;
   editStudentError.value = null;
   const payload: StudentUpdatePayload = { group_id: editStudentGroupId.value }; // Usa group_id come definito nel tipo

   try {
       const updatedStudentData = await updateStudent(student.id, payload);
       // Aggiorna lo studente nella lista locale
       const index = students.value.findIndex(s => s.id === student.id);
       if (index !== -1) {
           // Aggiorna solo i campi rilevanti (group_id e group_name)
           // L'API updateStudent restituisce l'oggetto Student aggiornato, che dovrebbe includere group_id e group_name
           students.value[index].group_id = updatedStudentData.group_id;
           students.value[index].group_name = updatedStudentData.group_name;
       }
       cancelEditStudentGroup(); // Chiudi form modifica
   } catch (err: any) {
       console.error(`Errore aggiornamento gruppo per studente ${student.id}:`, err);
       editStudentError.value = err.response?.data?.detail || err.message || "Errore durante l'aggiornamento.";
   } finally {
       isSavingStudentEdit.value = false;
   }
};

</script>

<style scoped>
/* ... (stili esistenti) ... */
/* Stili globali per la vista */
.students-view {
  /* padding: 20px; */ /* Rimosso padding globale, aggiunto a sezioni */
}

.loading,
.error-message,
.no-students {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}

.error-message {
  color: red;
  font-weight: bold;
}

.students-list {
  margin-top: 20px;
}

/* Stili tabella migliorati con Tailwind (assicurati che Tailwind sia configurato) */
table {
  /* width: 100%; */ /* Usare min-w-full */
  border-collapse: collapse;
}

th, td {
  /* border: 1px solid #ddd; */ /* Usare classi border di Tailwind */
  /* padding: 8px; */ /* Usare classi px, py di Tailwind */
  text-align: left;
}

th {
  background-color: #f3f4f6; /* gray-100 */
  font-weight: 600; /* font-semibold */
}

.assignment-list {
  list-style: disc;
  margin-left: 20px;
  margin-top: 5px;
}
.assignment-list li {
  margin-bottom: 5px;
}
.no-assignments {
    font-style: italic;
    color: #888;
}
.loading.small, .error-message.small {
    font-size: 0.9em;
    margin-top: 5px;
}
.btn-xs {
    padding: 2px 6px;
    font-size: 0.8rem;
    line-height: 1.2;
    border-radius: 0.2rem;
}
.ml-2 {
    margin-left: 0.5rem; /* 8px */
}
.mt-3 {
    margin-top: 0.75rem; /* 12px */
}
</style>