<template>
  <div v-if="show" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center" @click.self="closeModal">
    <div class="relative mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
      <div class="mt-3 text-center">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Seleziona Studenti</h3>
        <div class="mt-2 px-7 py-3">
          <!-- Barra di Filtro -->
          <div class="mb-4">
            <input
              type="text"
              v-model="filterText"
              placeholder="Filtra per nome, cognome o codice..."
              class="w-full p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary"
            />
          </div>

          <!-- Lista Studenti -->
          <div v-if="filteredStudents.length > 0" class="text-left max-h-80 overflow-y-auto border border-neutral-DEFAULT rounded-md p-3 space-y-2 bg-neutral-lightest mb-4">
             <!-- Seleziona Tutti -->
             <div class="mb-3 border-b pb-2">
                 <label class="inline-flex items-center cursor-pointer">
                     <input
                       type="checkbox"
                       @change="toggleSelectAllFiltered"
                       :checked="allFilteredSelected"
                       :disabled="filteredStudents.length === 0"
                       class="styled-checkbox"
                     />
                     <span class="ml-2 text-sm font-medium text-neutral-darker">Seleziona Tutti (filtrati)</span>
                 </label>
             </div>
             <!-- Lista -->
             <ul class="space-y-2">
                <li v-for="student in filteredStudents" :key="student.id">
                  <label class="inline-flex items-center cursor-pointer w-full p-2 hover:bg-primary-lightest rounded transition-colors duration-150">
                    <input
                      type="checkbox"
                      :value="student.id"
                      v-model="localSelectedIds"
                      class="styled-checkbox"
                    />
                    <span class="ml-3 text-sm text-neutral-darkest">
                      {{ student.first_name }} {{ student.last_name }} <span class="text-xs text-neutral-dark">({{ student.student_code }})</span>
                    </span>
                  </label>
                </li>
             </ul>
          </div>
          <div v-else class="text-center py-6 text-neutral-dark">
            Nessuno studente corrisponde al filtro.
          </div>

        </div>
        <!-- Pulsanti Azione -->
        <div class="items-center px-4 py-3 border-t border-gray-200">
          <div class="flex justify-end space-x-3">
             <BaseButton variant="secondary" @click="closeModal">Annulla</BaseButton>
             <BaseButton variant="primary" @click="confirmSelection">Conferma Selezione</BaseButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, type PropType } from 'vue';
import type { Student } from '@/api/students';
import BaseButton from '@/components/common/BaseButton.vue';

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  students: {
    type: Array as PropType<Student[]>,
    required: true,
  },
  initialSelectedIds: {
    type: Array as PropType<number[]>,
    default: () => [],
  },
});

const emit = defineEmits(['update:selectedIds', 'close']);

const filterText = ref('');
const localSelectedIds = ref<number[]>([...props.initialSelectedIds]);

// Filtra studenti in base al testo
const filteredStudents = computed(() => {
  if (!filterText.value) {
    return props.students;
  }
  const lowerFilter = filterText.value.toLowerCase();
  return props.students.filter(student =>
    student.first_name.toLowerCase().includes(lowerFilter) ||
    student.last_name.toLowerCase().includes(lowerFilter) ||
    (student.student_code && student.student_code.toLowerCase().includes(lowerFilter))
  );
});

// Logica "Seleziona Tutti" (solo filtrati)
const allFilteredSelected = computed(() => {
  const filteredIds = filteredStudents.value.map(s => s.id);
  return filteredIds.length > 0 && filteredIds.every(id => localSelectedIds.value.includes(id));
});

const toggleSelectAllFiltered = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const filteredIds = filteredStudents.value.map(s => s.id);

  if (target.checked) {
    // Aggiungi solo gli ID filtrati non già presenti
    filteredIds.forEach(id => {
      if (!localSelectedIds.value.includes(id)) {
        localSelectedIds.value.push(id);
      }
    });
  } else {
    // Rimuovi solo gli ID filtrati
    localSelectedIds.value = localSelectedIds.value.filter(id => !filteredIds.includes(id));
  }
};

// Sincronizza la selezione locale quando cambiano le props iniziali
watch(() => props.initialSelectedIds, (newVal) => {
  localSelectedIds.value = [...newVal];
});

// Sincronizza la prop show per resettare il filtro all'apertura
watch(() => props.show, (newVal) => {
  if (newVal) {
    filterText.value = ''; // Resetta filtro all'apertura
    localSelectedIds.value = [...props.initialSelectedIds]; // Ricarica selezione iniziale
  }
});


const closeModal = () => {
  emit('close');
};

const confirmSelection = () => {
  emit('update:selectedIds', [...localSelectedIds.value]); // Emetti una copia
  closeModal();
};

</script>

<style scoped>
/* Stile base per i checkbox, migliorabile ulteriormente */
.styled-checkbox {
  appearance: none;
  background-color: #fff;
  margin: 0;
  font: inherit;
  color: currentColor;
  width: 1.15em;
  height: 1.15em;
  border: 0.1em solid theme('colors.neutral.DEFAULT'); /* Usa colore tema */
  border-radius: 0.25rem; /* Arrotondato */
  transform: translateY(-0.075em);
  display: grid;
  place-content: center;
  cursor: pointer;
  transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
}

.styled-checkbox::before {
  content: "";
  width: 0.65em;
  height: 0.65em;
  transform: scale(0);
  transition: 120ms transform ease-in-out;
  box-shadow: inset 1em 1em theme('colors.primary.DEFAULT'); /* Usa colore tema */
  transform-origin: bottom left;
  clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%); /* Forma checkmark */
}

.styled-checkbox:checked {
   background-color: theme('colors.primary.DEFAULT'); /* Usa colore tema */
   border-color: theme('colors.primary.DEFAULT'); /* Usa colore tema */
}

.styled-checkbox:checked::before {
  transform: scale(1);
}

.styled-checkbox:focus {
  outline: max(2px, 0.15em) solid theme('colors.primary.light'); /* Usa colore tema */
  outline-offset: max(2px, 0.1em);
}

.styled-checkbox:disabled {
  border-color: theme('colors.neutral.light');
  background-color: theme('colors.neutral.lightest');
  cursor: not-allowed;
}
.styled-checkbox:disabled::before {
   box-shadow: inset 1em 1em theme('colors.neutral.DEFAULT');
}
.styled-checkbox:disabled:checked {
   background-color: theme('colors.neutral.light');
}

</style>