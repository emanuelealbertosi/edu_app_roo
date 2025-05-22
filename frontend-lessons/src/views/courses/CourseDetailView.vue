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
            <!-- Pulsante Esporta con Dropdown -->
            <div class="relative inline-block text-left">
              <div>
                <button
                  @click="toggleExportMenu"
                  :disabled="exportingFile"
                  type="button"
                  class="px-4 py-2 bg-white text-purple-700 border border-purple-300 rounded-md shadow-sm hover:bg-purple-50 transition duration-150 ease-in-out font-medium flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                  id="export-menu-button"
                  aria-expanded="true"
                  aria-haspopup="true"
                >
                  <DocumentArrowDownIcon class="h-5 w-5 mr-2" />
                  <span v-if="exportingFile">Esportazione...</span>
                  <span v-else>Esporta</span>
                  <ChevronDownIcon class="h-5 w-5 ml-2 -mr-1" aria-hidden="true" />
                </button>
              </div>

              <div
                v-if="showExportMenu"
                @clickaway="closeExportMenu"
                class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                role="menu"
                aria-orientation="vertical"
                aria-labelledby="export-menu-button"
                tabindex="-1"
              >
                <div class="py-1" role="none">
                  <a
                    href="#"
                    @click.prevent="handleExportUdas('docx')"
                    class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100 hover:text-gray-900"
                    role="menuitem"
                    tabindex="-1"
                    id="export-menu-item-0"
                  >
                    Esporta come DOCX
                  </a>
                  <a
                    href="#"
                    @click.prevent="handleExportUdas('pdf')"
                    class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100 hover:text-gray-900"
                    role="menuitem"
                    tabindex="-1"
                    id="export-menu-item-1"
                  >
                    Esporta come PDF
                  </a>
                </div>
              </div>
            </div>
            <!-- Fine Pulsante Esporta con Dropdown -->
            
            <!-- Pulsanti stile adattato per contrasto -->
            <button
              @click="openAssignExistingUdaModal"
              class="px-4 py-2 bg-white text-teal-700 border border-teal-300 rounded-md shadow-sm hover:bg-teal-50 transition duration-150 ease-in-out font-medium flex items-center"
            >
              <LinkIcon class="h-5 w-5 mr-2" /> <!-- Icona da cambiare, es. LinkIcon -->
              Associa Esistente
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
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creato da (UDA)</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Argomenti</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Materie</th>
                <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Contenuti</th>
                <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">N. Lez.</th>
                <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Ore Lez.</th>
                <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Ore Stimate Tot.</th>
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
                  {{ uda.teacher_username || course.teacher_username || '-' }} <!-- Username del creatore dell'UDA, fallback a quello del corso -->
                </td>
                 <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ uda.topics_display?.join(', ') || '-' }}
                </td>
                 <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ uda.subjects_display?.join(', ') || '-' }}
                </td>
                 <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">
                  {{ uda.contents?.length || 0 }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-center">
                  {{ uda.lesson_count || 0 }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-center">
                  {{ uda.total_lesson_estimated_hours || '0.0' }}h
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-center">
                  {{ uda.total_estimated_hours || '0.0' }}h
                </td>
                 <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(uda.start_date) }} / {{ formatDate(uda.end_date) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  <!-- Pulsanti Sposta -->
                  <button
                    @click="moveUdaUp(index)"
                    :disabled="index === 0"
                    class="text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed p-1 rounded-md hover:bg-gray-100"
                    title="Sposta Su"
                  >
                    <ArrowUpIcon class="h-4 w-4" />
                  </button>
                  <button
                    @click="moveUdaDown(index)"
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
                    @click="handleCopyUda(uda.id, uda.title)"
                    class="text-green-600 hover:text-green-900 p-1 rounded-md hover:bg-green-50"
                    title="Copia UDA"
                  >
                    <DocumentDuplicateIcon class="h-4 w-4 inline-block" />
                  </button>
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

    <CreateNewUdaModal
      :open="showCreateNewUdaModal"
      :course-id="courseId"
      @close="showCreateNewUdaModal = false"
      @uda-created="handleUdaCreated"
    />

    <AssignExistingUdaModal
      :open="showAssignExistingUdaModal"
      :course-id="courseId"
      @close="showAssignExistingUdaModal = false"
      @uda-associated="handleUdaCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, RouterLink, useRouter } from 'vue-router'; // Aggiunto useRouter
import { useCourseStore } from '@/stores/courseStore';
import { PencilIcon, PlusCircleIcon, TrashIcon, ArrowUpIcon, ArrowDownIcon, DocumentDuplicateIcon, LinkIcon, DocumentArrowDownIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'; // Aggiunto ChevronDownIcon
// import { directive as onClickaway } from 'vue3-click-away'; // Rimosso perché l'alias onClickaway non è usato e @clickaway nel template potrebbe funzionare ugualmente
import { useUdaStore } from '@/stores/udaStore';
import { useUiStore } from '@/stores/ui'; // Importa uiStore per le notifiche/conferme
import { useTopicStore } from '@/stores/topicStore'; // Importa store argomenti
import { useSubjectStore } from '@/stores/subjectStore'; // Importa store materie
import CreateNewUdaModal from '@/components/courses/CreateNewUdaModal.vue';
import AssignExistingUdaModal from '@/components/courses/AssignExistingUdaModal.vue'; // Nuovo Import
// Importa altri tipi o store se necessario

const courseStore = useCourseStore();
const udaStore = useUdaStore();
const uiStore = useUiStore();
const topicStore = useTopicStore(); // Istanzia store argomenti
const subjectStore = useSubjectStore(); // Istanzia store materie
const route = useRoute();
const router = useRouter(); // Istanza del router

const courseId = computed(() => Number(route.params.id));

const pageLoading = ref(true); // Loading generale per la pagina (dettagli corso)
const pageError = ref<string | null>(null);
const udasLoading = ref(false); // Loading specifico per le UDA
const exportingFile = ref(false); // Stato generico per l'esportazione
const showExportMenu = ref(false); // Stato per la visibilità del menu di esportazione

const course = computed(() => courseStore.currentCourse);
const udas = computed(() => courseStore.udasForCurrentCourse); // Queste sono le UDA già filtrate per il corso dallo store

// Stati per le modali
const showCreateNewUdaModal = ref(false);
const showAssignExistingUdaModal = ref(false); // Nuovo stato per la modale

// TODO: Implementare queste funzioni
const openCreateNewUdaModal = () => {
  showCreateNewUdaModal.value = true;
  console.log("Apri modale per creare nuova UDA");
};

const openAssignExistingUdaModal = () => {
  showAssignExistingUdaModal.value = true;
  console.log("Apri modale per associare UDA esistente");
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

const moveUdaUp = async (currentIndex: number) => { // Rimosso udaId non utilizzato
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

const moveUdaDown = async (currentIndex: number) => { // Rimosso udaId non utilizzato
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

// getTopicNames e getSubjectNames non sono più strettamente necessari se topics_display e subjects_display sono usati direttamente.
// Li lascio commentati per riferimento futuro o se si volesse una logica di fallback più complessa.
/*
const getTopicNames = (topicIds?: number[]): string => {
  if (!topicIds || topicIds.length === 0) return '';
  return topicIds.map(id => topicStore.getTopicById(id)?.name || `ID:${id}`).join(', ');
};

const getSubjectNames = (subjectIds?: number[]): string => {
  if (!subjectIds || subjectIds.length === 0) return '';
  return subjectIds.map(id => subjectStore.getSubjectById(id)?.name || `ID:${id}`).join(', ');
};
*/

const handleCopyUda = async (udaIdToCopy: number, udaTitle: string) => {
  uiStore.addNotification({ message: `Copia dell'UDA "${udaTitle}" in corso...`, type: 'info' });
  try {
    const newUda = await udaStore.copyUda(udaIdToCopy);
    if (newUda && newUda.id) {
      uiStore.addNotification({ message: `UDA "${udaTitle}" copiata con successo come "${newUda.title}". Puoi modificarla e associarla a un corso.`, type: 'success', duration: 5000 });
      // Dopo la copia, la nuova UDA non è associata a questo corso.
      // Reindirizziamo l'utente al form di modifica della nuova UDA.
      router.push({ name: 'uda-edit', params: { id: newUda.id } });
      // Non è necessario ricaricare le UDA di questo corso, perché la nuova UDA non ne fa parte (ancora).
    } else {
      throw new Error('ID della nuova UDA non ricevuto dopo la copia.');
    }
  } catch (error) {
    console.error(`Errore durante la copia dell'UDA ID ${udaIdToCopy}:`, error);
    uiStore.addNotification({ message: `Errore durante la copia dell'UDA: ${(error as Error).message}`, type: 'error' });
  }
};

const toggleExportMenu = () => {
  showExportMenu.value = !showExportMenu.value;
};

const closeExportMenu = () => {
  showExportMenu.value = false;
};

const handleExportUdas = async (format: 'docx' | 'pdf') => {
  closeExportMenu(); // Chiudi il menu dopo la selezione
  if (!courseId.value) {
    uiStore.addNotification({ message: 'ID del corso non valido per l\'esportazione.', type: 'error' });
    return;
  }
  exportingFile.value = true;
  const formatUpper = format.toUpperCase();
  uiStore.addNotification({ message: `Esportazione UDA in formato ${formatUpper} in corso...`, type: 'info' });
  try {
    // Assumiamo che esista una funzione exportUdas nello store che accetta il formato
    await courseStore.exportUdas(courseId.value, format);
    // Potremmo non avere una notifica di successo qui se il download è gestito dal browser
  } catch (error) {
    console.error(`Errore durante l'esportazione delle UDA in ${formatUpper}:`, error);
    uiStore.addNotification({ message: `Errore durante l'esportazione in ${formatUpper}: ${(error as Error).message}`, type: 'error' });
  } finally {
    exportingFile.value = false;
  }
};

onMounted(async () => {
  pageLoading.value = true;
  pageError.value = null;
  udasLoading.value = true;

  if (courseId.value) {
    try {
      // Carica materie e argomenti in parallelo con il corso
      await Promise.all([
        courseStore.fetchCourse(courseId.value), // Questo dovrebbe popolare course.teacher_username
        subjectStore.fetchSubjects(),
        topicStore.fetchTopics()
      ]);

      // Se fetchCourse ha successo e currentCourse è settato, allora carica le UDA
      // Le UDA caricate da fetchUdasForCourse dovrebbero includere teacher_username se il serializer lo fornisce
      if (courseStore.currentCourse) {
         await courseStore.fetchUdasForCourse(courseId.value);
      } else {
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