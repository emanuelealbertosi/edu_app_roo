<template>
  <div v-if="show" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-[55] flex items-center justify-center" @click.self="closeModal">
    <div class="relative mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
      <div class="mt-3 text-center">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Seleziona Gruppi</h3>
        <div class="mt-2 px-7 py-3">
          <!-- Barra di Filtro -->
          <div class="mb-4">
            <input
              type="text"
              v-model="filterText"
              placeholder="Filtra per nome gruppo..."
              class="w-full p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary"
            />
          </div>

          <!-- Lista Gruppi -->
          <div v-if="filteredGroups.length > 0" class="text-left max-h-80 overflow-y-auto border border-neutral-DEFAULT rounded-md p-3 space-y-2 bg-neutral-lightest mb-4">
             <!-- Seleziona Tutti -->
             <div class="mb-3 border-b pb-2">
                 <label class="inline-flex items-center cursor-pointer">
                     <input
                       type="checkbox"
                       @change="toggleSelectAllFiltered"
                       :checked="allFilteredSelected"
                       :disabled="filteredGroups.length === 0"
                       class="styled-checkbox"
                     />
                     <span class="ml-2 text-sm font-medium text-neutral-darker">Seleziona Tutti (filtrati)</span>
                 </label>
             </div>
             <!-- Lista -->
             <ul class="space-y-2">
                <li v-for="group in filteredGroups" :key="group.id">
                  <label class="inline-flex items-center cursor-pointer w-full p-2 hover:bg-primary-lightest rounded transition-colors duration-150">
                    <input
                      type="checkbox"
                      :value="group.id"
                      v-model="localSelectedIds"
                      class="styled-checkbox"
                    />
                    <span class="ml-3 text-sm text-neutral-darkest">
                      {{ group.name }} <span class="text-xs text-neutral-dark">({{ group.student_count ?? 0 }} membri)</span>
                    </span>
                  </label>
                </li>
             </ul>
          </div>
          <div v-else class="text-center py-6 text-neutral-dark">
            Nessun gruppo corrisponde al filtro.
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
import type { StudentGroup } from '@/types/groups'; // Importa StudentGroup
import BaseButton from '@/components/common/BaseButton.vue';

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  groups: { // Rinominato da students a groups
    type: Array as PropType<StudentGroup[]>, // Usa StudentGroup
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

// Filtra gruppi in base al testo
const filteredGroups = computed(() => { // Rinominato
  if (!filterText.value) {
    return props.groups;
  }
  const lowerFilter = filterText.value.toLowerCase();
  return props.groups.filter(group => // Usa props.groups
    group.name.toLowerCase().includes(lowerFilter)
    // Aggiungere altri campi di filtro se necessario, es. group.description
  );
});

// Logica "Seleziona Tutti" (solo filtrati)
const allFilteredSelected = computed(() => {
  const filteredIds = filteredGroups.value.map(g => g.id); // Usa filteredGroups
  return filteredIds.length > 0 && filteredIds.every(id => localSelectedIds.value.includes(id));
});

const toggleSelectAllFiltered = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const filteredIds = filteredGroups.value.map(g => g.id); // Usa filteredGroups

  if (target.checked) {
    filteredIds.forEach(id => {
      if (!localSelectedIds.value.includes(id)) {
        localSelectedIds.value.push(id);
      }
    });
  } else {
    localSelectedIds.value = localSelectedIds.value.filter(id => !filteredIds.includes(id));
  }
};

watch(() => props.initialSelectedIds, (newVal) => {
  localSelectedIds.value = [...newVal];
});

watch(() => props.show, (newVal) => {
  if (newVal) {
    filterText.value = '';
    localSelectedIds.value = [...props.initialSelectedIds];
  }
});


const closeModal = () => {
  emit('close');
};

const confirmSelection = () => {
  emit('update:selectedIds', [...localSelectedIds.value]);
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