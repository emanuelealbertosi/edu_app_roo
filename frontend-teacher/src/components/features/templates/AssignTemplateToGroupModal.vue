<template>
  <div v-if="show" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-[55] flex items-center justify-center" @click.self="closeModal">
    <div class="relative mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
      <div class="mt-3 text-center">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Seleziona Gruppo di Destinazione</h3>
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
             <ul class="space-y-2">
                <li v-for="group in filteredGroups" :key="group.id">
                  <label class="inline-flex items-center cursor-pointer w-full p-2 hover:bg-primary-lightest rounded transition-colors duration-150">
                    <input
                      type="radio"
                      :value="group.id"
                      v-model="selectedGroupId"
                      name="group-selection"
                      class="styled-radio"
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
             <BaseButton variant="primary" @click="confirmSelection" :disabled="!selectedGroupId">Assegna al Gruppo</BaseButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, type PropType } from 'vue';
import type { StudentGroup } from '@/types/groups';
import BaseButton from '@/components/common/BaseButton.vue';

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  groups: {
    type: Array as PropType<StudentGroup[]>,
    required: true,
  },
});

const emit = defineEmits(['assign', 'close']);

const filterText = ref('');
const selectedGroupId = ref<number | null>(null);

const filteredGroups = computed(() => {
  if (!filterText.value) {
    return props.groups;
  }
  const lowerFilter = filterText.value.toLowerCase();
  return props.groups.filter(group =>
    group.name.toLowerCase().includes(lowerFilter)
  );
});

watch(() => props.show, (newVal) => {
  if (newVal) {
    filterText.value = '';
    selectedGroupId.value = null;
  }
});

const closeModal = () => {
  emit('close');
};

const confirmSelection = () => {
  if (selectedGroupId.value) {
    emit('assign', selectedGroupId.value);
    closeModal();
  }
};
</script>

<style scoped>
.styled-radio {
  appearance: none;
  background-color: #fff;
  margin: 0;
  font: inherit;
  color: currentColor;
  width: 1.15em;
  height: 1.15em;
  border: 0.1em solid theme('colors.neutral.DEFAULT');
  border-radius: 50%;
  transform: translateY(-0.075em);
  display: grid;
  place-content: center;
  cursor: pointer;
  transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
}

.styled-radio::before {
  content: "";
  width: 0.65em;
  height: 0.65em;
  border-radius: 50%;
  transform: scale(0);
  transition: 120ms transform ease-in-out;
  box-shadow: inset 1em 1em theme('colors.primary.DEFAULT');
}

.styled-radio:checked {
   background-color: theme('colors.primary.DEFAULT');
   border-color: theme('colors.primary.DEFAULT');
}

.styled-radio:checked::before {
  transform: scale(1);
}

.styled-radio:focus {
  outline: max(2px, 0.15em) solid theme('colors.primary.light');
  outline-offset: max(2px, 0.1em);
}
</style>