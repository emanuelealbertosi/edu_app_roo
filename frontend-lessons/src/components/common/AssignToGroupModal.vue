<template>
  <TransitionRoot as="template" :show="open">
    <Dialog as="div" class="relative z-10" @close="$emit('close')">
      <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0" enter-to="opacity-100" leave="ease-in duration-200" leave-from="opacity-100" leave-to="opacity-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" enter-to="opacity-100 translate-y-0 sm:scale-100" leave="ease-in duration-200" leave-from="opacity-100 translate-y-0 sm:scale-100" leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95">
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
              <form @submit.prevent="handleSubmit">
                <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div class="sm:flex sm:items-start">
                    <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 sm:mx-0 sm:h-10 sm:w-10">
                      <FolderArrowDownIcon class="h-6 w-6 text-indigo-600" aria-hidden="true" />
                    </div>
                    <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                      <DialogTitle as="h3" class="text-lg font-medium leading-6 text-gray-900">Assegna a Gruppo</DialogTitle>
                      <div class="mt-4">
                        <p class="text-sm text-gray-600 mb-4">Seleziona un gruppo esistente o creane uno nuovo per assegnare i {{ itemCount }} elementi selezionati.</p>
                        
                        <!-- Sezione Gruppo Esistente -->
                        <div>
                          <label for="existingGroup" class="block text-sm font-medium text-gray-700">Gruppo Esistente</label>
                          <select
                            id="existingGroup"
                            v-model="selectedGroupId"
                            class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                            :disabled="isCreatingNew"
                          >
                            <option :value="null">-- Seleziona un gruppo --</option>
                            <option v-for="group in groups" :key="group.id" :value="group.id">{{ group.name }}</option>
                          </select>
                        </div>

                        <div class="relative my-4">
                          <div class="absolute inset-0 flex items-center">
                            <div class="w-full border-t border-gray-300" />
                          </div>
                          <div class="relative flex justify-center text-sm">
                            <span class="bg-white px-2 text-gray-500">Oppure</span>
                          </div>
                        </div>

                        <!-- Sezione Nuovo Gruppo -->
                        <div>
                          <label for="newGroupName" class="block text-sm font-medium text-gray-700">Crea Nuovo Gruppo</label>
                          <input
                            type="text"
                            id="newGroupName"
                            v-model="newGroupName"
                            @focus="isCreatingNew = true"
                            @blur="isCreatingNew = newGroupName !== ''"
                            placeholder="Nome del nuovo gruppo"
                            class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                  <button type="submit" class="inline-flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm" :disabled="!canSubmit">
                    Assegna
                  </button>
                  <button type="button" class="mt-3 inline-flex w-full justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm" @click="$emit('close')">
                    Annulla
                  </button>
                </div>
              </form>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue';
import { FolderArrowDownIcon } from '@heroicons/vue/24/outline';
import type { CourseGroup } from '@/types/uda'; // O UdaGroup, rendiamolo generico

type Group = Pick<CourseGroup, 'id' | 'name'>;

const props = defineProps<{
  open: boolean;
  groups: Group[];
  itemCount: number;
}>();

const emit = defineEmits(['close', 'assign']);

const selectedGroupId = ref<number | null>(null);
const newGroupName = ref('');
const isCreatingNew = ref(false);

const canSubmit = computed(() => {
  return selectedGroupId.value !== null || newGroupName.value.trim() !== '';
});

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    selectedGroupId.value = null;
    newGroupName.value = '';
    isCreatingNew.value = false;
  }
});

watch(newGroupName, (name) => {
    if (name.trim() !== '') {
        selectedGroupId.value = null;
        isCreatingNew.value = true;
    }
});

watch(selectedGroupId, (id) => {
    if (id !== null) {
        newGroupName.value = '';
        isCreatingNew.value = false;
    }
});

const handleSubmit = () => {
  if (!canSubmit.value) return;
  
  if (newGroupName.value.trim()) {
    emit('assign', { newGroupName: newGroupName.value.trim() });
  } else if (selectedGroupId.value !== null) {
    emit('assign', { groupId: selectedGroupId.value });
  }
};
</script>