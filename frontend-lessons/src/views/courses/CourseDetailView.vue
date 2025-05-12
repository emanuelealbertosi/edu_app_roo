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
      <!-- Intestazione con sfondo blu -->
      <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-semibold">{{ course.name }}</h2>
          <p class="text-sm text-blue-100 mt-1">ID Corso: {{ course.id }}</p> <!-- Leggermente più chiaro per contrasto -->
        </div>
        <!-- Pulsante stile adattato per contrasto -->
        <RouterLink
          :to="{ name: 'course-edit', params: { id: course.id } }"
          class="px-4 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-50 transition duration-150 ease-in-out font-medium"
        >
          Modifica Corso
        </RouterLink>
      </div>

      <div class="mb-6">
        <h2 class="text-xl font-semibold text-gray-700 mb-2">Descrizione</h2>
        <p class="text-gray-600 whitespace-pre-wrap">{{ course.description || 'Nessuna descrizione fornita.' }}</p>
      </div>

      <hr class="my-6">

      <!-- Sezione UDA -->
      <div class="mt-8">
        <!-- Intestazione Sezione UDA con sfondo azzurro -->
        <div class="bg-sky-100 p-4 rounded-md mb-6 flex justify-between items-center border border-sky-200">
          <h2 class="text-xl font-semibold text-sky-800">Unità Didattiche di Apprendimento (UDA)</h2>
          <div class="flex space-x-2">
             <!-- Pulsanti stile adattato per contrasto -->
            <button
              @click="openAddUdaFromTemplateModal"
              class="px-4 py-2 bg-white text-sky-700 border border-sky-300 rounded-md shadow-sm hover:bg-sky-50 transition duration-150 ease-in-out font-medium flex items-center"
            >
              <PlusCircleIcon class="h-5 w-5 mr-2" />
              Aggiungi da Template
            </button>
            <button
              @click="openCreateNewUdaModal"
              class="px-4 py-2 bg-white text-sky-700 border border-sky-300 rounded-md shadow-sm hover:bg-sky-50 transition duration-150 ease-in-out font-medium flex items-center"
            >
              <PlusCircleIcon class="h-5 w-5 mr-2" />
              Crea Nuova
            </button>
          </div>
        </div>

        <div v-if="udasLoading" class="text-center py-6">
          <p class="text-gray-500">Caricamento UDA...</p>
        </div>
        <div v-else-if="udas.length === 0 && !udasLoading" class="text-center py-6 bg-gray-50 rounded-md">
          <p class="text-gray-600">Nessuna UDA associata a questo corso.</p>
        </div>
        <!-- Tabella UDA -->
        <div v-else class="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titolo</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stato</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Argomenti</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Materie</th>
                <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Contenuti</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date (Inizio/Fine)</th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(uda, index) in udas" :key="uda.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-indigo-700 hover:text-indigo-900">
                  <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }">
                    {{ uda.title }}
                  </RouterLink>
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                  <span :title="uda.description" v-if="uda.description && uda.description.length > 30">
                    {{ uda.description.substring(0, 30) + '...' }}
                  </span>
                  <span v-else>{{ uda.description || '-' }}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span class="font-medium px-2 py-0.5 rounded-full" :class="getStatusClass(uda.status)">{{ uda.status }}</span>
                </td>
                 <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ getTopicNames(uda.topics) || '-' }}
                </td>
                 <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ getSubjectNames(uda.subjects) || '-' }}
                </td>
                 <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">
                  {{ uda.contents?.length || 0 }}
                </td>
                 <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(uda.start_date) }} / {{ formatDate(uda.end_date) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  <!-- Pulsanti Sposta -->
                  <button
                    @click="moveUdaUp(uda.id, index)"
                    :disabled="index === 0"
                    class="text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed p-1 rounded-md hover:bg-gray-100"
                    title="Sposta Su"
                  >
                    <ArrowUpIcon class="h-4 w-4" />
                  </button>
                  <button
                    @click="moveUdaDown(uda.id, index)"
                    :disabled="index === udas.length - 1"
                    class="text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed p-1 rounded-md hover:bg-gray-100"
                    title="Sposta Giù"
                  >
                    <ArrowDownIcon class="h-4 w-4" />
                  </button>
                  <!-- Pulsanti Modifica/Elimina -->
                   <RouterLink
                    :to="{ name: 'uda-edit', params: { id: uda.id } }"
                    class="text-yellow-600 hover:text-yellow-900 p-1 rounded-md hover:bg-yellow-50"
                    title="Modifica UDA"
                  >
                    <PencilIcon class="h-4 w-4 inline-block" />
                  </RouterLink>
                  <button
                    @click="confirmDeleteUda(uda.id)"
                    class="text-red-600 hover:text-red-900 p-1 rounded-md hover:bg-red-50"
                    title="Elimina UDA"
                  >
                    <TrashIcon class="h-4 w-4 inline-block" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <!-- Nota sul salvataggio ordine rimossa, dato che i bottoni ora chiamano l'API -->
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
import { useTopicStore } from '@/stores/topicStore'; // Importa store argomenti
import { useSubjectStore } from '@/stores/subjectStore'; // Importa store materie
import AddUdaFromTemplateModal from '@/components/courses/AddUdaFromTemplateModal.vue';
import CreateNewUdaModal from '@/components/courses/CreateNewUdaModal.vue';
// Importa altri tipi o store se necessario

const courseStore = useCourseStore();
const udaStore = useUdaStore();
const udaTemplateStore = useUdaTemplateStore();
const uiStore = useUiStore();
const topicStore = useTopicStore(); // Istanzia store argomenti
const subjectStore = useSubjectStore(); // Istanzia store materie
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

const formatDate = (dateString?: string | null) => {
  if (!dateString) return 'N/D';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch (e) {
    return dateString; // Ritorna la stringa originale se non è una data valida
  }
};

const getTopicNames = (topicIds?: number[]): string => {
  if (!topicIds || topicIds.length === 0) return '';
  return topicIds.map(id => topicStore.getTopicById(id)?.name || `ID:${id}`).join(', ');
};

const getSubjectNames = (subjectIds?: number[]): string => {
  if (!subjectIds || subjectIds.length === 0) return '';
  // Assumendo che le UDA abbiano un array di ID materia
  return subjectIds.map(id => subjectStore.getSubjectById(id)?.name || `ID:${id}`).join(', ');
};


onMounted(async () => {
  pageLoading.value = true;
  pageError.value = null;
  udasLoading.value = true;

  if (courseId.value) {
    try {
      // Carica materie e argomenti in parallelo con il corso
      await Promise.all([
        courseStore.fetchCourse(courseId.value),
        subjectStore.fetchSubjects(), // Assicurati che siano caricate
        topicStore.fetchTopics()      // Assicurati che siano caricate
      ]);

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