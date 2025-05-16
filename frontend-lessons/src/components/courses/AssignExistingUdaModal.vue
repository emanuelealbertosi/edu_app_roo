<template>
  <TransitionRoot as="template" :show="open">
    <Dialog as="div" class="relative z-10" @close="closeModal">
      <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0" enter-to="opacity-100" leave="ease-in duration-200" leave-from="opacity-100" leave-to="opacity-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" enter-to="opacity-100 translate-y-0 sm:scale-100" leave="ease-in duration-200" leave-from="opacity-100 translate-y-0 sm:scale-100" leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95">
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
              <div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                <div class="sm:flex sm:items-start">
                  <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-sky-100 sm:mx-0 sm:h-10 sm:w-10">
                    <LinkIcon class="h-6 w-6 text-sky-600" aria-hidden="true" />
                  </div>
                  <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                    <DialogTitle as="h3" class="text-lg font-semibold leading-6 text-gray-900">Associa UDA Esistente</DialogTitle>
                    <div class="mt-2">
                      <p class="text-sm text-gray-500 mb-4">
                        Seleziona un'Unità Didattica di Apprendimento da associare a questo corso.
                        Se l'UDA selezionata è già associata a un altro corso, verrà creata una copia e associata a questo.
                      </p>
                      
                      <div v-if="loadingUdas" class="text-center">
                        <p class="text-sm text-gray-500">Caricamento UDA disponibili...</p>
                      </div>
                      <div v-else-if="fetchError" class="text-sm text-red-600">
                        Errore nel caricamento delle UDA: {{ fetchError }}
                      </div>
                      <div v-else>
                        <div class="mb-3">
                          <label for="udaSearchInModal" class="block text-sm font-medium text-gray-700">Cerca UDA per titolo o descrizione:</label>
                          <input type="text" id="udaSearchInModal" v-model="searchQuery" placeholder="Scrivi per filtrare..." class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2"/>
                        </div>
                        
                        <div v-if="!searchQuery && udasEligibleForAssociation.length === 0" class="text-sm text-gray-500 p-2">
                           Nessuna UDA disponibile per l'associazione (potrebbero essere tutte già associate a questo corso).
                        </div>
                        <div v-else>
                          <p class="block text-sm font-medium text-gray-700 mb-1">Seleziona UDA:</p>
                          <div class="max-h-60 overflow-y-auto border border-gray-300 rounded-md p-2 bg-white space-y-1">
                            <div v-if="filteredUdas.length === 0" class="text-sm text-gray-500 p-2">
                              Nessuna UDA corrisponde alla ricerca.
                            </div>
                            <div v-for="uda in filteredUdas" :key="uda.id"
                                 class="flex items-center p-2 rounded-md hover:bg-gray-100 cursor-pointer"
                                 :class="{ 'bg-sky-100': selectedUdaId === uda.id }"
                                 @click="selectedUdaId = uda.id">
                              <input
                                type="radio"
                                :id="'uda-option-' + uda.id"
                                :value="uda.id"
                                v-model="selectedUdaId"
                                class="h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500 cursor-pointer"
                              >
                              <label :for="'uda-option-' + uda.id" class="ml-2 text-sm text-gray-800 cursor-pointer">
                                {{ uda.title }}
                                <span class="text-xs text-gray-500" v-if="uda.course_name">(Corso: {{ uda.course_name }})</span>
                                <span class="text-xs text-gray-500" v-else>(Nessun corso associato)</span>
                              </label>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                <button
                  type="button"
                  class="inline-flex w-full justify-center rounded-md bg-sky-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-500 sm:ml-3 sm:w-auto disabled:opacity-50"
                  @click="handleAssociate"
                  :disabled="!selectedUdaId || isAssociating"
                >
                  <span v-if="isAssociating">Associazione...</span>
                  <span v-else>Associa Selezionata</span>
                </button>
                <button type="button" class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto" @click="closeModal" ref="cancelButtonRef">
                  Annulla
                </button>
              </div>
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
import { LinkIcon } from '@heroicons/vue/24/outline';
import { useUdaStore } from '@/stores/udaStore';
import { useUiStore } from '@/stores/ui';
import type { UDA } from '@/types/uda';

const props = defineProps<{
  open: boolean;
  courseId: number | null;
}>();

const emit = defineEmits(['close', 'uda-associated']);

const udaStore = useUdaStore();
const uiStore = useUiStore();

const selectedUdaId = ref<number | null>(null);
const teacherUdas = ref<UDA[]>([]);
const loadingUdas = ref(false);
const fetchError = ref<string | null>(null);
const isAssociating = ref(false);
const searchQuery = ref(''); // Nuovo stato per la ricerca

// Prima filtra per non includere quelle già nel corso corrente
const udasEligibleForAssociation = computed(() => {
    return teacherUdas.value.filter(uda => uda.course !== props.courseId);
});

// Poi filtra in base alla searchQuery
const filteredUdas = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  if (!query) {
    return udasEligibleForAssociation.value;
  }
  return udasEligibleForAssociation.value.filter(uda => {
    const titleMatch = uda.title.toLowerCase().includes(query);
    const descriptionMatch = uda.description?.toLowerCase().includes(query) || false;
    return titleMatch || descriptionMatch;
  });
});


watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    selectedUdaId.value = null;
    searchQuery.value = ''; // Resetta anche la ricerca
    fetchError.value = null;
    // Carica sempre le UDA del docente quando la modale si apre,
    // per avere dati freschi, a meno che non ci sia già un caricamento in corso.
    if (!loadingUdas.value) {
      loadingUdas.value = true;
      try {
        await udaStore.fetchUdas({});
        // Filtra qui per non includere quelle già associate al corso corrente
        // teacherUdas.value = udaStore.udas.filter(u => u.course !== props.courseId);
        // La computed property `udasEligibleForAssociation` ora fa questo lavoro.
        teacherUdas.value = [...udaStore.udas];
      } catch (error) {
        console.error("Errore caricamento UDA per associazione:", error);
        fetchError.value = (error as Error).message || 'Errore sconosciuto.';
        teacherUdas.value = []; // Resetta in caso di errore
      } finally {
        loadingUdas.value = false;
      }
    }
  }
});

const closeModal = () => {
  if (isAssociating.value) return;
  emit('close');
};

const handleAssociate = async () => {
  if (!selectedUdaId.value || !props.courseId) return;

  isAssociating.value = true;
  uiStore.addNotification({ message: 'Associazione UDA in corso...', type: 'info' });

  try {
    const udaToAssociate = udaStore.getUdaById(selectedUdaId.value); // Assicurati che getUdaById esista e funzioni
    
    if (!udaToAssociate) {
      throw new Error('UDA selezionata non trovata nello store.');
    }

    // Calcola il prossimo order_in_course
    // Questo è un esempio base, potrebbe servire una logica più robusta
    // per ottenere le UDA del corso corrente e trovare l'ordine massimo.
    // Per ora, lo impostiamo a un valore alto o null se il backend lo gestisce.
    // const currentCourseUdas = udaStore.udas.filter(u => u.course === props.courseId);
    // const nextOrder = currentCourseUdas.length > 0 ? Math.max(...currentCourseUdas.map(u => u.order_in_course || 0)) + 1 : 1;
    // Semplifichiamo: il backend potrebbe gestire l'ordine se non fornito, o lo aggiungiamo in fondo.
    // Per ora, non inviamo order_in_course, lasciando che il backend lo gestisca o lo impostiamo a null.

    if (udaToAssociate.course === null || udaToAssociate.course === undefined) {
      // UDA non associata a nessun corso: aggiornala direttamente
      await udaStore.updateUda(selectedUdaId.value, { course_id: props.courseId /*, order_in_course: nextOrder */ });
      uiStore.addNotification({ message: `UDA "${udaToAssociate.title}" associata con successo al corso.`, type: 'success' });
    } else if (udaToAssociate.course !== props.courseId) {
      // UDA associata a un ALTRO corso: copia e poi associa la copia
      const copiedUda = await udaStore.copyUda(selectedUdaId.value);
      if (copiedUda && copiedUda.id) {
        await udaStore.updateUda(copiedUda.id, { course_id: props.courseId /*, order_in_course: nextOrder */ });
        uiStore.addNotification({ message: `UDA "${udaToAssociate.title}" copiata e associata con successo al corso come "${copiedUda.title}".`, type: 'success' });
      } else {
        throw new Error('Errore durante la copia dell\'UDA.'); // Ho aggiunto un backslash per l'apostrofo, potrebbe essere questo il problema di parsing.
      }
    } else {
      // UDA già associata a QUESTO corso
      uiStore.addNotification({ message: `L'UDA "${udaToAssociate.title}" è già associata a questo corso.`, type: 'info' });
      isAssociating.value = false;
      closeModal();
      return;
    }

    emit('uda-associated');
    closeModal();
  } catch (error) {
    console.error("Errore durante l'associazione dell'UDA:", error);
    uiStore.addNotification({ message: `Errore associazione: ${(error as Error).message}`, type: 'error' });
  } finally {
    isAssociating.value = false;
  }
};

</script>