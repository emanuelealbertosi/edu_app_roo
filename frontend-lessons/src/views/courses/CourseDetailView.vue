<template>
  <div class="course-detail-view p-4 md:p-8">
    <div v-if="pageLoading" class="text-center py-10">
      <p class="text-gray-600">Caricamento dettagli corso...</p>
    </div>

    <div v-else-if="pageError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ pageError }}</span>
      <div class="mt-4">
        <RouterLink :to="{ name: 'course-list' }" class="text-indigo-600 hover:text-indigo-800">
          Torna alla lista corsi
        </RouterLink>
      </div>
    </div>

    <div v-else-if="course" class="bg-white shadow-lg rounded-lg p-6">
      <div class="flex justify-between items-start mb-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-800 mb-2">{{ course.name }}</h1>
          <p class="text-sm text-gray-500">ID Corso: {{ course.id }}</p>
        </div>
        <RouterLink
          :to="{ name: 'course-edit', params: { id: course.id } }"
          class="bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-4 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
        >
          <PencilIcon class="h-5 w-5 mr-2" />
          Modifica Corso
        </RouterLink>
      </div>

      <div class="mb-6">
        <h2 class="text-xl font-semibold text-gray-700 mb-2">Descrizione</h2>
        <p class="text-gray-600 whitespace-pre-wrap">{{ course.description || 'Nessuna descrizione fornita.' }}</p>
      </div>

      <hr class="my-6">

      <div>
        <h2 class="text-2xl font-semibold text-gray-700 mb-4">Unità Didattiche di Apprendimento (UDA)</h2>
        <div v-if="udasLoading" class="text-center py-6">
          <p class="text-gray-500">Caricamento UDA...</p>
        </div>
        <div class="mb-4 flex space-x-2">
          <button
            @click="openAddUdaFromTemplateModal"
            class="bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
          >
            <PlusCircleIcon class="h-5 w-5 mr-2" />
            Aggiungi UDA da Template
          </button>
          <button
            @click="openCreateNewUdaModal"
            class="bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-4 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
          >
            <PlusCircleIcon class="h-5 w-5 mr-2" />
            Crea Nuova UDA
          </button>
        </div>
        <div v-if="udas.length === 0 && !udasLoading" class="text-center py-6 bg-gray-50 rounded-md">
          <p class="text-gray-600">Nessuna UDA associata a questo corso.</p>
        </div>
        <div v-else-if="!udasLoading">
          <!-- Lista e riordino delle UDA -->
          <div v-if="udas.length > 0" class="space-y-4">
            <div v-for="(uda, index) in udas" :key="uda.id" class="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-4">
              <div class="flex justify-between items-start">
                <div>
                  <h3 class="text-lg font-semibold text-indigo-700 hover:text-indigo-900">
                    <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }">
                      {{ uda.title }}
                    </RouterLink>
                  </h3>
                  <p class="text-sm text-gray-600 mt-1">{{ uda.description || 'Nessuna descrizione per questa UDA.' }}</p>
                  <p class="text-xs text-gray-500 mt-2">Stato: <span class="font-medium" :class="getStatusClass(uda.status)">{{ uda.status }}</span></p>
                  <p class="text-xs text-gray-500 mt-1">Ordine nel corso: {{ uda.order_in_course ?? 'Non specificato' }}</p>
                </div>
                <div class="flex space-x-2 flex-shrink-0 ml-4">
                  <RouterLink
                    :to="{ name: 'uda-edit', params: { id: uda.id } }"
                    class="text-sm bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-1 px-3 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
                    title="Modifica UDA"
                  >
                    <PencilIcon class="h-4 w-4" />
                  </RouterLink>
                  <button
                    @click="confirmDeleteUda(uda.id)"
                    class="text-sm bg-red-500 hover:bg-red-600 text-white font-medium py-1 px-3 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
                    title="Elimina UDA"
                  >
                    <TrashIcon class="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div class="mt-3 flex justify-end space-x-2">
                <button
                  @click="moveUdaUp(uda.id, index)"
                  :disabled="index === 0"
                  class="text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-1 px-2 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Sposta Su"
                >
                  <ArrowUpIcon class="h-4 w-4" />
                </button>
                <button
                  @click="moveUdaDown(uda.id, index)"
                  :disabled="index === udas.length - 1"
                  class="text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-1 px-2 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Sposta Giù"
                >
                  <ArrowDownIcon class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
          <p v-if="udas.length > 0" class="mt-4 text-sm text-gray-500">
            Per riordinare le UDA, utilizzare i bottoni Su/Giù. Il salvataggio dell'ordine avverrà con un apposito pulsante (da implementare) o automaticamente.
          </p>
          <!-- TODO: Implementare il drag-and-drop per il riordino o un pulsante "Salva Ordine" se necessario -->
        </div>
      </div>
       <div class="mt-8 text-right">
          <RouterLink :to="{ name: 'course-list' }" class="text-indigo-600 hover:text-indigo-800 font-medium">
            &larr; Torna alla lista corsi
          </RouterLink>
        </div>
    </div>
    <div v-else class="text-center py-10">
        <p class="text-xl text-gray-600">Corso non trovato.</p>
         <RouterLink :to="{ name: 'course-list' }" class="mt-4 inline-block text-indigo-600 hover:text-indigo-800">
          Torna alla lista corsi
        </RouterLink>
    </div>

    <AddUdaFromTemplateModal
      :open="showAddUdaFromTemplateModal"
      :course-id="courseId"
      @close="showAddUdaFromTemplateModal = false"
      @uda-created="handleUdaCreated"
    />

    <CreateNewUdaModal
      :open="showCreateNewUdaModal"
      :course-id="courseId"
      @close="showCreateNewUdaModal = false"
      @uda-created="handleUdaCreated"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { useCourseStore } from '@/stores/courseStore';
import { PencilIcon, PlusCircleIcon, TrashIcon, ArrowUpIcon, ArrowDownIcon } from '@heroicons/vue/24/outline';
import { useUdaStore } from '@/stores/udaStore';
import { useUdaTemplateStore } from '@/stores/udaTemplateStore';
import { useUiStore } from '@/stores/ui'; // Importa uiStore per le notifiche/conferme
import AddUdaFromTemplateModal from '@/components/courses/AddUdaFromTemplateModal.vue';
import CreateNewUdaModal from '@/components/courses/CreateNewUdaModal.vue';
// Importa altri tipi o store se necessario

const courseStore = useCourseStore();
const udaStore = useUdaStore();
const udaTemplateStore = useUdaTemplateStore();
const uiStore = useUiStore();
const route = useRoute();

const courseId = computed(() => Number(route.params.id));

const pageLoading = ref(true); // Loading generale per la pagina (dettagli corso)
const pageError = ref<string | null>(null);
const udasLoading = ref(false); // Loading specifico per le UDA

const course = computed(() => courseStore.currentCourse);
const udas = computed(() => courseStore.udasForCurrentCourse); // Queste sono le UDA già filtrate per il corso dallo store

// Stati per le modali
const showAddUdaFromTemplateModal = ref(false);
const showCreateNewUdaModal = ref(false);

// TODO: Implementare queste funzioni
const openAddUdaFromTemplateModal = () => {
  // Caricare i template UDA se non già presenti
  if (udaTemplateStore.udaTemplates.length === 0) {
    udaTemplateStore.fetchUdaTemplates();
  }
  showAddUdaFromTemplateModal.value = true;
  console.log("Apri modale per aggiungere UDA da template");
};

const openCreateNewUdaModal = () => {
  showCreateNewUdaModal.value = true;
  console.log("Apri modale per creare nuova UDA");
};

const handleUdaCreated = async () => {
  // Funzione chiamata dopo che un'UDA è stata creata (da template o nuova)
  // Ricarica le UDA per il corso corrente per aggiornare la lista
  if (courseId.value) {
    udasLoading.value = true;
    try {
      await courseStore.fetchUdasForCourse(courseId.value);
    } catch (error) {
      console.error("Errore nel ricaricare le UDA dopo la creazione:", error);
      // Potresti voler mostrare una notifica all'utente qui
    } finally {
      udasLoading.value = false;
    }
  }
};

const confirmDeleteUda = async (udaIdToDelete: number) => {
  // TODO: Sostituire window.confirm con una modale di conferma più carina usando uiStore.showConfirmationDialog
  //       quando uiStore.showConfirmationDialog sarà implementato.
  const confirmed = window.confirm(`Sei sicuro di voler eliminare questa UDA (ID: ${udaIdToDelete})? L'azione non è reversibile.`);

  if (confirmed) {
    uiStore.addNotification({ message: `Eliminazione UDA ID: ${udaIdToDelete} in corso...`, type: 'info' });
    try {
      await udaStore.deleteUda(udaIdToDelete);
      uiStore.addNotification({ message: 'UDA eliminata con successo.', type: 'success', duration: 3000 });
      // Ricarica le UDA per il corso corrente per aggiornare la lista
      if (courseId.value) {
        udasLoading.value = true;
        try {
          await courseStore.fetchUdasForCourse(courseId.value);
        } catch (fetchError) {
          console.error("Errore nel ricaricare le UDA dopo l'eliminazione:", fetchError);
          uiStore.addNotification({ message: `Errore nel ricaricare la lista UDA: ${(fetchError as Error).message}`, type: 'error' });
        } finally {
          udasLoading.value = false;
        }
      }
    } catch (error) {
      console.error(`Errore durante l'eliminazione dell'UDA ID ${udaIdToDelete}:`, error);
      uiStore.addNotification({ message: `Errore durante l'eliminazione dell'UDA: ${(error as Error).message}`, type: 'error' });
    }
  } else {
    uiStore.addNotification({ message: 'Eliminazione UDA annullata.', type: 'info', duration: 2000 });
  }
};

const moveUdaUp = async (udaId: number, currentIndex: number) => {
  if (currentIndex === 0 || !courseId.value) return;

  const currentUdas = [...udas.value];
  if (currentIndex < 0 || currentIndex >= currentUdas.length) return;

  const itemToMove = currentUdas.splice(currentIndex, 1)[0];
  currentUdas.splice(currentIndex - 1, 0, itemToMove);
  
  const newOrderIds = currentUdas.map(u => u.id);

  try {
    uiStore.addNotification({ message: 'Riordino UDA in corso...', type: 'info' });
    await courseStore.reorderUdasInCourse(courseId.value, newOrderIds);
    // Lo store fetchUdasForCourse viene già chiamato da reorderUdasInCourse,
    // quindi la lista 'udas' (che è una computed property) si aggiornerà automaticamente.
    uiStore.addNotification({ message: 'Ordine UDA aggiornato con successo.', type: 'success', duration: 3000 });
  } catch (error) {
    console.error("Errore durante il riordino dell'UDA (su):", error);
    uiStore.addNotification({ message: `Errore durante l'aggiornamento dell'ordine: ${(error as Error).message}`, type: 'error' });
    // Potrebbe essere utile ricaricare le UDA per tornare allo stato precedente in caso di errore
    await courseStore.fetchUdasForCourse(courseId.value);
  }
};

const moveUdaDown = async (udaId: number, currentIndex: number) => {
  if (currentIndex === udas.value.length - 1 || !courseId.value) return;

  const currentUdas = [...udas.value];
   if (currentIndex < 0 || currentIndex >= currentUdas.length -1) return;

  const itemToMove = currentUdas.splice(currentIndex, 1)[0];
  currentUdas.splice(currentIndex + 1, 0, itemToMove);

  const newOrderIds = currentUdas.map(u => u.id);

  try {
    uiStore.addNotification({ message: 'Riordino UDA in corso...', type: 'info' });
    await courseStore.reorderUdasInCourse(courseId.value, newOrderIds);
    uiStore.addNotification({ message: 'Ordine UDA aggiornato con successo.', type: 'success', duration: 3000 });
  } catch (error) {
    console.error("Errore durante il riordino dell'UDA (giù):", error);
    uiStore.addNotification({ message: `Errore durante l'aggiornamento dell'ordine: ${(error as Error).message}`, type: 'error' });
    await courseStore.fetchUdasForCourse(courseId.value);
  }
};

const getStatusClass = (status: string) => {
  if (status === 'COMPLETED' || status === 'Completata') return 'text-green-600 bg-green-100 px-2 py-0.5 rounded-full';
  if (status === 'IN_PROGRESS' || status === 'In Corso') return 'text-blue-600 bg-blue-100 px-2 py-0.5 rounded-full';
  if (status === 'TODO' || status === 'Da Fare') return 'text-yellow-600 bg-yellow-100 px-2 py-0.5 rounded-full';
  return 'text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full';
};

onMounted(async () => {
  pageLoading.value = true;
  pageError.value = null;
  udasLoading.value = true;

  if (courseId.value) {
    try {
      await courseStore.fetchCourse(courseId.value);
      // Se fetchCourse ha successo e currentCourse è settato, allora carica le UDA
      if (courseStore.currentCourse) {
         await courseStore.fetchUdasForCourse(courseId.value);
      } else {
        // Se currentCourse non è settato dopo fetchCourse, il corso non esiste
        pageError.value = 'Corso non trovato.';
      }
    } catch (err) {
      console.error("Errore durante il caricamento del corso o delle UDA:", err);
      pageError.value = (err as Error).message || 'Errore nel caricamento dei dati del corso.';
    } finally {
      pageLoading.value = false;
      udasLoading.value = false;
    }
  } else {
    pageError.value = 'ID del corso non valido.';
    pageLoading.value = false;
    udasLoading.value = false;
  }
});
</script>

<style scoped>
/* Stili aggiuntivi se necessari */
</style>