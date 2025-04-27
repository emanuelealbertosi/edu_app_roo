<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useStudentStore } from '@/stores/students';
import type { Student } from '@/types/users';

// Props
const props = defineProps<{
  modelValue: boolean; // Controlla la visibilità della modale (v-model)
  existingMemberIds: number[]; // Array degli ID degli studenti già membri
}>();

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void; // Per v-model
  (e: 'confirm-selection', selectedIds: number[]): void; // Evento con gli ID selezionati
}>();

// Store
const studentStore = useStudentStore();

// State locale
const selectedStudentIds = ref<number[]>([]);
const searchTerm = ref(''); // Per eventuale filtro di ricerca

// Computed: Studenti disponibili (non già membri e filtrati per ricerca)
const availableStudents = computed(() => {
  return studentStore.allStudents
    .filter(student => !props.existingMemberIds.includes(student.id))
    .filter(student =>
      student.full_name.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
      student.student_code.toLowerCase().includes(searchTerm.value.toLowerCase())
    );
});

// Funzioni
function closeModal() {
  emit('update:modelValue', false);
  selectedStudentIds.value = []; // Resetta la selezione alla chiusura
  searchTerm.value = '';
}

function confirmSelection() {
  emit('confirm-selection', selectedStudentIds.value);
  closeModal();
}

// Carica gli studenti quando la modale diventa visibile (se non già caricati)
watch(() => props.modelValue, (newValue) => {
  if (newValue && studentStore.students.length === 0) {
    studentStore.fetchStudents();
  }
});

// Carica gli studenti al montaggio se necessario (potrebbe essere già visibile inizialmente)
onMounted(() => {
    if (props.modelValue && studentStore.students.length === 0) {
        studentStore.fetchStudents();
    }
});

</script>

<template>
  <!-- Base per la modale (es. usando un componente UI esistente o HTML/CSS base) -->
  <div v-if="modelValue" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex justify-center items-center" @click.self="closeModal">
    <div class="relative mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
      <div class="mt-3 text-center">
        <h3 class="text-lg leading-6 font-medium text-gray-900">Seleziona Studenti da Aggiungere</h3>
        <div class="mt-4 px-7 py-3">
          <!-- Input di ricerca -->
          <input
            type="text"
            v-model="searchTerm"
            placeholder="Cerca per nome o codice..."
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 mb-4"
          />

          <!-- Elenco Studenti Selezionabili -->
          <div class="max-h-60 overflow-y-auto border rounded-md p-2 text-left">
            <div v-if="studentStore.isLoading" class="text-center text-gray-500">Caricamento...</div>
            <div v-else-if="studentStore.error" class="text-center text-red-500">{{ studentStore.error }}</div>
            <div v-else-if="availableStudents.length === 0" class="text-center text-gray-500">Nessun altro studente disponibile.</div>
            <div v-else v-for="student in availableStudents" :key="student.id" class="flex items-center space-x-3 p-2 hover:bg-gray-100 rounded">
              <input
                type="checkbox"
                :id="'student-' + student.id"
                :value="student.id"
                v-model="selectedStudentIds"
                class="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
              />
              <label :for="'student-' + student.id" class="flex-1 cursor-pointer">
                {{ student.full_name }} ({{ student.student_code }})
              </label>
            </div>
          </div>
        </div>
        <!-- Pulsanti Azione -->
        <div class="items-center px-4 py-3">
          <button
            @click="confirmSelection"
            :disabled="selectedStudentIds.length === 0"
            class="px-4 py-2 bg-indigo-600 text-white text-base font-medium rounded-md w-auto shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Aggiungi Selezionati ({{ selectedStudentIds.length }})
          </button>
          <button
            @click="closeModal"
            class="ml-3 px-4 py-2 bg-gray-200 text-gray-800 text-base font-medium rounded-md w-auto shadow-sm hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400"
          >
            Annulla
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici se necessario */
</style>