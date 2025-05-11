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
              <form @submit.prevent="handleCreateNewUda">
                <div>
                  <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <DialogTitle as="h3" class="text-lg font-semibold leading-6 text-gray-900">
                      Crea Nuova UDA per il Corso
                    </DialogTitle>
                    <div class="mt-4 space-y-4">
                      <div>
                        <label for="udaTitle" class="block text-sm font-medium text-gray-700">Titolo UDA <span class="text-red-500">*</span></label>
                        <input
                          type="text"
                          v-model="newUdaForm.title"
                          id="udaTitle"
                          required
                          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                      </div>
                      <div>
                        <label for="udaDescription" class="block text-sm font-medium text-gray-700">Descrizione</label>
                        <textarea
                          v-model="newUdaForm.description"
                          id="udaDescription"
                          rows="3"
                          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        ></textarea>
                      </div>
                      
                      <!-- Selezione Materia -->
                      <div>
                        <label for="udaSubject" class="block text-sm font-medium text-gray-700">Materia (Opzionale)</label>
                        <select
                          v-model="newUdaForm.subject_id"
                          id="udaSubject"
                          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          :disabled="subjectsLoading"
                        >
                          <option :value="null">Nessuna materia</option>
                          <option v-for="subject in availableSubjects" :key="subject.id" :value="subject.id">
                            {{ subject.name }}
                          </option>
                        </select>
                        <p v-if="subjectsLoading" class="mt-1 text-xs text-gray-500">Caricamento materie...</p>
                        <p v-if="subjectsError" class="mt-1 text-xs text-red-500">{{ subjectsError }}</p>
                      </div>

                      <!-- Selezione Argomenti (visibile solo se una materia è selezionata) -->
                      <div v-if="newUdaForm.subject_id">
                        <label class="block text-sm font-medium text-gray-700">Argomenti (Opzionale)</label>
                        <div v-if="topicsLoading" class="mt-1 text-xs text-gray-500">Caricamento argomenti...</div>
                        <div v-if="topicsError" class="mt-1 text-xs text-red-500">{{ topicsError }}</div>
                        <div v-if="!topicsLoading && !topicsError && availableTopics.length === 0 && newUdaForm.subject_id" class="mt-1 text-xs text-gray-500">
                          Nessun argomento disponibile per la materia selezionata.
                        </div>
                        <div v-if="!topicsLoading && !topicsError && availableTopics.length > 0" class="mt-2 space-y-2 max-h-40 overflow-y-auto border border-gray-300 rounded-md p-2">
                          <div v-for="topic in availableTopics" :key="topic.id" class="flex items-center">
                            <input
                              :id="'topic-' + topic.id"
                              type="checkbox"
                              :value="topic.id"
                              v-model="newUdaForm.topic_ids"
                              class="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                            />
                            <label :for="'topic-' + topic.id" class="ml-2 block text-sm text-gray-900">
                              {{ topic.name }}
                            </label>
                          </div>
                        </div>
                      </div>

                      <div>
                        <label for="udaStatus" class="block text-sm font-medium text-gray-700">Stato</label>
                        <select
                          v-model="newUdaForm.status"
                          id="udaStatus"
                          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        >
                          <option value="TODO">Da Fare</option>
                          <option value="IN_PROGRESS">In Corso</option>
                          <option value="COMPLETED">Completata</option>
                        </select>
                      </div>

                       <div>
                        <label for="udaStartDate" class="block text-sm font-medium text-gray-700">Data Inizio (Opzionale)</label>
                        <input type="date" v-model="newUdaForm.start_date" id="udaStartDate" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                      </div>
                      <div>
                        <label for="udaEndDate" class="block text-sm font-medium text-gray-700">Data Fine (Opzionale)</label>
                        <input type="date" v-model="newUdaForm.end_date" id="udaEndDate" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                      </div>

                    </div>
                  </div>
                </div>
                <div class="mt-5 sm:mt-6 sm:grid sm:grid-flow-row-dense sm:grid-cols-2 sm:gap-3">
                  <button
                    type="submit"
                    class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 sm:col-start-2"
                    :disabled="udaStore.loading"
                  >
                    {{ udaStore.loading ? 'Creazione...' : 'Crea UDA' }}
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
              </form>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { ref, watch, reactive, computed, onMounted } from 'vue';
import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue';
import { useUdaStore } from '@/stores/udaStore';
import { useCourseStore } from '@/stores/courseStore';
import { useUiStore } from '@/stores/ui';
import { useSubjectStore } from '@/stores/subjectStore'; // Assumendo esista
import { useTopicStore } from '@/stores/topicStore';   // Assumendo esista
import type { Uda } from '@/types/uda';
import type { Subject } from '@/types/subject'; // Assumendo esista
import type { Topic } from '@/types/topic';     // Assumendo esista

const props = defineProps<{
  open: boolean;
  courseId: number | null;
}>();

const emit = defineEmits(['close', 'uda-created']);

const udaStore = useUdaStore();
const courseStore = useCourseStore();
const uiStore = useUiStore();
const subjectStore = useSubjectStore(); // Assumendo esista
const topicStore = useTopicStore();   // Assumendo esista

const creationError = ref<string | null>(null);
const subjectsLoading = ref(false);
const topicsLoading = ref(false);
const subjectsError = ref<string | null>(null);
const topicsError = ref<string | null>(null);

const initialFormState = {
  title: '',
  description: '',
  subject_id: null as number | null,
  topic_ids: [] as number[], // Sarà da implementare la selezione
  start_date: '' as string | null,
  end_date: '' as string | null,
  status: 'TODO' as Uda['status'],
};

const newUdaForm = reactive({ ...initialFormState });

watch(() => props.open, (newVal) => {
  if (newVal) {
    Object.assign(newUdaForm, initialFormState); // Reset form
    newUdaForm.topic_ids = []; // Assicura che topic_ids sia resettato
    creationError.value = null;
    subjectsError.value = null;
    topicsError.value = null;
    
    if (subjectStore.subjects.length === 0) {
      fetchSubjects();
    }
    // Resetta gli argomenti quando la modale si apre e subject_id è null
    if (!newUdaForm.subject_id) {
      topicStore.clearTopics(); // Assumendo esista un'azione per pulire gli argomenti
    }

  }
});

const availableSubjects = computed(() => subjectStore.subjects);
const availableTopics = computed(() => {
  if (newUdaForm.subject_id) {
    return topicStore.getTopicsForSubject(newUdaForm.subject_id); // Assumendo esista un getter
  }
  return [];
});

async function fetchSubjects() {
  subjectsLoading.value = true;
  subjectsError.value = null;
  try {
    await subjectStore.fetchSubjects();
  } catch (err) {
    console.error("Errore caricamento materie:", err);
    subjectsError.value = (err as Error).message || "Errore nel caricare le materie.";
    uiStore.addNotification({ message: subjectsError.value, type: 'error' });
  } finally {
    subjectsLoading.value = false;
  }
}

async function fetchTopicsForSelectedSubject() {
  if (!newUdaForm.subject_id) {
    topicStore.clearTopics(); // Assumendo esista
    newUdaForm.topic_ids = []; // Deseleziona argomenti se la materia viene deselezionata
    return;
  }
  topicsLoading.value = true;
  topicsError.value = null;
  try {
    await topicStore.fetchTopicsBySubject(newUdaForm.subject_id);
  } catch (err) {
    console.error(`Errore caricamento argomenti per materia ${newUdaForm.subject_id}:`, err);
    topicsError.value = (err as Error).message || "Errore nel caricare gli argomenti.";
    uiStore.addNotification({ message: topicsError.value, type: 'error' });
  } finally {
    topicsLoading.value = false;
  }
}

watch(() => newUdaForm.subject_id, (newSubjectId, oldSubjectId) => {
  if (newSubjectId !== oldSubjectId) {
    newUdaForm.topic_ids = []; // Resetta gli argomenti selezionati quando cambia la materia
    fetchTopicsForSelectedSubject();
  }
});

// Carica le materie al montaggio del componente se non già presenti
// Questo è utile se la modale è sempre nel DOM ma nascosta.
// Se la modale viene creata/distrutta, il watch su props.open è sufficiente.
onMounted(() => {
  if (props.open && subjectStore.subjects.length === 0) {
     fetchSubjects();
  }
});

const handleCreateNewUda = async () => {
  if (!props.courseId) {
    creationError.value = "ID Corso non fornito.";
    return;
  }
  if (!newUdaForm.title.trim()) {
    creationError.value = "Il titolo dell'UDA è obbligatorio.";
    return;
  }

  creationError.value = null;
  
  const orderInCourse = courseStore.udasForCurrentCourse.length;

  const udaDataPayload = {
    title: newUdaForm.title,
    description: newUdaForm.description || undefined, // Invia undefined se vuoto per non sovrascrivere con stringa vuota se il backend lo gestisce come null
    subject_id: newUdaForm.subject_id,
    topic_ids: newUdaForm.topic_ids.length > 0 ? newUdaForm.topic_ids : undefined,
    start_date: newUdaForm.start_date || null,
    end_date: newUdaForm.end_date || null,
    status: newUdaForm.status,
    course_id: props.courseId,
    order_in_course: orderInCourse,
    // source_template_id non è presente per UDA create da zero
  };

  try {
    // Rimuoviamo @ts-ignore se udaDataPayload è ora correttamente tipizzato
    // e se createUda accetta { topic_ids: number[] | undefined }
    const newUda = await udaStore.createUda(udaDataPayload as any); // Cast temporaneo se createUda non è aggiornato
    if (newUda) {
      uiStore.addNotification({ message: `UDA "${newUda.title}" creata con successo!`, type: 'success', duration: 5000 });
      emit('uda-created');
      emit('close');
    } else {
      throw new Error("La creazione dell'UDA non ha restituito un risultato.");
    }
  } catch (err) {
    console.error("Errore durante la creazione della nuova UDA:", err);
    creationError.value = (err as Error).message || "Errore sconosciuto durante la creazione dell'UDA.";
    uiStore.addNotification({ message: `Errore creazione UDA: ${creationError.value}`, type: 'error', duration: 5000 });
  }
};

</script>