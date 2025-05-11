<template>
  <TransitionRoot as="template" :show="open">
    <Dialog as="div" class="relative z-10" @close="emit('close')">
      <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0" enter-to="opacity-100" leave="ease-in duration-200" leave-from="opacity-100" leave-to="opacity-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" enter-to="opacity-100 translate-y-0 sm:scale-100" leave="ease-in duration-200" leave-from="opacity-100 translate-y-0 sm:scale-100" leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95">
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
              <div>
                <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                  <DialogTitle as="h3" class="text-lg font-semibold leading-6 text-gray-900">
                    Aggiungi UDA da Template al Corso
                  </DialogTitle>
                  <div class="mt-4">
                    <p class="text-sm text-gray-600 mb-2">
                      Seleziona un template UDA da cui creare una nuova Unità Didattica per questo corso.
                    </p>
                    
                    <div v-if="templateStore.loading" class="text-center">
                      <p>Caricamento template...</p>
                    </div>
                    <div v-else-if="templateStore.error" class="text-red-600">
                      Errore nel caricamento dei template: {{ templateStore.error }}
                    </div>
                    <div v-else-if="availableTemplates.length === 0" class="text-gray-500">
                      Nessun template UDA disponibile. Creane uno prima.
                    </div>
                    <div v-else class="space-y-2 max-h-60 overflow-y-auto">
                      <label 
                        v-for="template in availableTemplates" 
                        :key="template.id"
                        class="block p-3 border rounded-md hover:bg-gray-50 cursor-pointer"
                        :class="{ 'bg-indigo-100 border-indigo-500': selectedTemplateId === template.id }"
                      >
                        <input 
                          type="radio" 
                          name="udaTemplate" 
                          :value="template.id" 
                          v-model="selectedTemplateId"
                          class="sr-only"
                        />
                        <h4 class="font-medium text-gray-800">{{ template.name }}</h4>
                        <p class="text-xs text-gray-500">{{ template.description || 'Nessuna descrizione' }}</p>
                      </label>
                    </div>

                    <div class="mt-4">
                       <label for="newUdaTitle" class="block text-sm font-medium text-gray-700">Titolo per la nuova UDA (opzionale)</label>
                        <input
                          type="text"
                          v-model="newUdaTitle"
                          id="newUdaTitle"
                          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          placeholder="Lascia vuoto per usare il titolo del template"
                        />
                    </div>

                  </div>
                </div>
              </div>
              <div class="mt-5 sm:mt-6 sm:grid sm:grid-flow-row-dense sm:grid-cols-2 sm:gap-3">
                <button
                  type="button"
                  class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 sm:col-start-2"
                  @click="handleAddUdaFromTemplate"
                  :disabled="!selectedTemplateId || udaStore.loading"
                >
                  {{ udaStore.loading ? 'Creazione...' : 'Aggiungi UDA' }}
                </button>
                <button
                  type="button"
                  class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:col-start-1 sm:mt-0"
                  @click="emit('close')"
                  ref="cancelButtonRef"
                >
                  Annulla
                </button>
              </div>
               <div v-if="creationError" class="mt-3 text-sm text-red-600">
                Errore durante la creazione: {{ creationError }}
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue';
import { useUdaTemplateStore } from '@/stores/udaTemplateStore';
import { useUdaStore } from '@/stores/udaStore';
import { useCourseStore } from '@/stores/courseStore';
import type { UdaTemplate } from '@/types/uda';
import { useUiStore } from '@/stores/ui';


const props = defineProps<{
  open: boolean;
  courseId: number | null;
}>();

const emit = defineEmits(['close', 'uda-created']);

const templateStore = useUdaTemplateStore();
const udaStore = useUdaStore();
const courseStore = useCourseStore(); // Per ottenere il numero di UDA esistenti per l'ordine
const uiStore = useUiStore();


const selectedTemplateId = ref<number | null>(null);
const newUdaTitle = ref('');
const creationError = ref<string | null>(null);

const availableTemplates = computed(() => templateStore.udaTemplates);

watch(() => props.open, (newVal) => {
  if (newVal) {
    selectedTemplateId.value = null;
    newUdaTitle.value = '';
    creationError.value = null;
    if (templateStore.udaTemplates.length === 0 && !templateStore.loading) {
      templateStore.fetchUdaTemplates();
    }
  }
});

const handleAddUdaFromTemplate = async () => {
  if (!props.courseId || !selectedTemplateId.value) {
    creationError.value = "ID Corso o Template non selezionato.";
    return;
  }

  const template = templateStore.udaTemplates.find(t => t.id === selectedTemplateId.value);
  if (!template) {
    creationError.value = "Template selezionato non trovato.";
    return;
  }

  creationError.value = null;
  
  // Determina l'ordine della nuova UDA
  // Assicurati che le UDA per il corso siano caricate per calcolare l'ordine corretto
  if (courseStore.currentCourse?.id !== props.courseId || courseStore.udasForCurrentCourse.length === 0 && courseStore.currentCourse?.id === props.courseId) {
      // Potrebbe essere necessario ricaricare le UDA del corso se non sono aggiornate
      // o se stiamo operando su un corso diverso da quello attualmente caricato in dettaglio
      // Per semplicità, assumiamo che fetchUdasForCourse sia già stato chiamato o che
      // currentCourse.udas sia ragionevolmente aggiornato.
      // Una strategia più robusta potrebbe essere ricaricare qui se necessario.
      // await courseStore.fetchUdasForCourse(props.courseId); // Descommentare se si vuole forzare il refresh
  }
  const orderInCourse = courseStore.udasForCurrentCourse.length;


  // Prepara i dati per la nuova UDA
  const udaData = {
    title: newUdaTitle.value || template.name, // Usa il titolo del template se non specificato
    description: template.description,
    subject_id: template.subject?.id || null,
    topics: template.topics?.map(t => t.id) || [],
    source_template_id: template.id,
    course_id: props.courseId,
    order_in_course: orderInCourse,
    status: 'TODO' as 'TODO' | 'IN_PROGRESS' | 'COMPLETED', // Default status
    // I contenuti verranno copiati dal backend basandosi su source_template_id
  };

  try {
    const newUda = await udaStore.createUda(udaData);
    if (newUda) {
      uiStore.addNotification({ message: `UDA "${newUda.title}" creata con successo dal template!`, type: 'success', duration: 5000 });
      emit('uda-created');
      emit('close');
    } else {
      throw new Error("La creazione dell'UDA non ha restituito un risultato.");
    }
  } catch (err) {
    console.error("Errore durante la creazione dell'UDA da template:", err);
    creationError.value = (err as Error).message || "Errore sconosciuto durante la creazione dell'UDA.";
    uiStore.addNotification({ message: `Errore creazione UDA: ${creationError.value}`, type: 'error', duration: 5000 });
  }
};

</script>