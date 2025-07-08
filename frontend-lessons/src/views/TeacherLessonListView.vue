<template>
  <div class="lesson-list-container p-6">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex justify-between items-center">
      <h2 class="text-2xl font-semibold">Le Mie Lezioni</h2>
      <!-- Pulsante stile adattato per contrasto -->
      <button @click="openAddModalDirectly" class="flex items-center px-3 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-100 transition duration-150 ease-in-out font-medium">
        <PlusCircleIcon class="h-5 w-5 sm:mr-2" />
        <span class="hidden sm:inline">Crea Nuova Lezione</span>
      </button>
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca lezioni per titolo, argomento, materia, stato..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      />
    </div>

    <!-- Azioni di gruppo -->
    <div v-if="selectedLessons.size > 0" class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md flex items-center justify-between">
      <span class="text-sm font-medium text-blue-700">{{ selectedLessons.size }} {{ selectedLessons.size === 1 ? 'lezione selezionata' : 'lezioni selezionate' }}</span>
      <div class="flex items-center space-x-2">
        <button
          @click="confirmRemoveSelectedFromGroup"
          class="px-4 py-2 bg-red-100 border border-red-300 text-red-700 rounded-md shadow-sm hover:bg-red-200 transition duration-150 ease-in-out font-medium"
          :disabled="!atLeastOneSelectedLessonInGroup"
          title="Rimuovi le lezioni selezionate dai loro gruppi"
        >
          Rimuovi dal Gruppo
        </button>
        <button
          @click="openAssignToGroupModal"
          class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md shadow-sm hover:bg-gray-50 transition duration-150 ease-in-out font-medium"
          :disabled="lessonStore.lessonGroups.length === 0"
          title="Aggiungi le lezioni selezionate a un gruppo esistente"
        >
          Aggiungi a Gruppo...
        </button>
        <button @click="openCreateGroupModal" class="px-4 py-2 bg-blue-600 text-white rounded-md shadow-sm hover:bg-blue-700 transition duration-150 ease-in-out font-medium">
          Crea Nuovo Gruppo...
        </button>
      </div>
    </div>

    <div v-if="lessonStore.isLoading" class="text-center text-gray-500 py-10">
      Caricamento lezioni...
    </div>

    <div v-if="lessonStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore:</strong>
      <span class="block sm:inline"> {{ lessonStore.error }}</span>
    </div>

    <!-- Tabella Lezioni con Gruppi -->
    <div v-if="!lessonStore.isLoading && (groupedAndUngroupedLessons.groups.length > 0 || groupedAndUngroupedLessons.unscoped.length > 0)" class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="relative px-4 py-3">
              <input type="checkbox" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" @change="toggleSelectAll" :checked="areAllLessonsSelected" :disabled="allVisibleLessonIds.length === 0" />
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('title')">
              Titolo
              <span v-if="sortKey === 'title'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('description')">
             Descrizione
             <span v-if="sortKey === 'description'">
               <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
               <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
             </span>
           </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('topic')">
              Argomento
              <span v-if="sortKey === 'topic'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('subject')">
              Materia
              <span v-if="sortKey === 'subject'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('estimated_hours')">
              Ore Stimate
              <span v-if="sortKey === 'estimated_hours'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('is_published')">
              Stato
              <span v-if="sortKey === 'is_published'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('created_at')">
              Data Creazione
              <span v-if="sortKey === 'created_at'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <!-- Itera sui gruppi -->
          <!-- Itera sui gruppi -->
          <template v-for="group in groupedAndUngroupedLessons.groups" :key="group.id">
            <tr
              class="bg-blue-50 hover:bg-blue-100 cursor-pointer"
              @click="toggleGroup(group.id)"
              :class="{ 'group-header-expanded': expandedGroups.has(group.id) }"
            >
              <td colspan="9" class="px-6 py-3 text-sm font-semibold text-blue-800">
                <div class="flex items-center">
                  <FolderIcon class="h-5 w-5 mr-2" />
                  <span>{{ group.name }} ({{ group.lessons.length }})</span>
                  <div class="ml-auto flex items-center space-x-2">
                    <button @click.stop="confirmDeleteGroup(group)" class="text-red-500 hover:text-red-700" title="Elimina Gruppo">
                      <TrashIcon class="h-4 w-4" />
                    </button>
                    <ChevronDownIcon v-if="expandedGroups.has(group.id)" class="h-5 w-5" />
                    <ChevronRightIcon v-else class="h-5 w-5" />
                  </div>
                </div>
              </td>
            </tr>
            <!-- Itera sulle lezioni del gruppo se espanso -->
            <template v-if="expandedGroups.has(group.id)">
              <tr v-for="(lesson, index) in group.lessons" :key="lesson.id"
                class="hover:bg-gray-50"
                :class="{
                  'bg-blue-50': selectedLessons.has(lesson.id),
                  'lesson-in-expanded-group': true,
                  'last-lesson-in-group': index === group.lessons.length - 1
                }">
                <td class="px-4 py-4 whitespace-nowrap">
                  <input type="checkbox" :checked="selectedLessons.has(lesson.id)" @change="toggleLessonSelection(lesson.id)" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                </td>
                <td class="pl-12 pr-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600 hover:text-blue-800 cursor-pointer" @click="gotoContents(lesson.id)">
                  {{ lesson.title }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ lesson.description }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getTopicName(lesson.topic) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getSubjectNameFromTopic(lesson.topic) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ lesson.estimated_hours ? lesson.estimated_hours + 'h' : '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span :class="lesson.is_published ? 'text-green-600' : 'text-yellow-600'">
                    {{ lesson.is_published ? 'Pubblicata' : 'Bozza' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(lesson.created_at) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  <button @click="editLesson(lesson as Lesson)" class="text-yellow-600 hover:text-yellow-900 transition duration-150 ease-in-out" title="Modifica Lezione">
                    <PencilIcon class="h-5 w-5 inline-block" />
                  </button>
                  <button @click="gotoContents(lesson.id)" class="text-purple-600 hover:text-purple-900 transition duration-150 ease-in-out" title="Gestisci Contenuti">
                    <DocumentTextIcon class="h-5 w-5 inline-block" />
                  </button>
                  <button @click="gotoAssign(lesson.id)" class="text-cyan-600 hover:text-cyan-900 transition duration-150 ease-in-out" title="Assegna Lezione">
                    <UserPlusIcon class="h-5 w-5 inline-block" />
                  </button>
                  <button @click="confirmDelete(lesson as Lesson)" class="text-red-600 hover:text-red-900 transition duration-150 ease-in-out" title="Elimina Lezione">
                    <TrashIcon class="h-5 w-5 inline-block" />
                  </button>
                  <button @click.stop="confirmRemoveFromGroup(lesson)" class="text-gray-500 hover:text-gray-700" title="Rimuovi dal gruppo">
                    <XCircleIcon class="h-5 w-5" />
                  </button>
                </td>
              </tr>
            </template>
          </template>
          <!-- Itera sulle lezioni non raggruppate -->
          <tr v-for="lesson in groupedAndUngroupedLessons.unscoped" :key="lesson.id" class="hover:bg-gray-50" :class="{'bg-blue-50': selectedLessons.has(lesson.id)}">
            <td class="px-4 py-4 whitespace-nowrap">
              <input type="checkbox" :checked="selectedLessons.has(lesson.id)" @change="toggleLessonSelection(lesson.id)" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500">
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600 hover:text-blue-800 cursor-pointer" @click="gotoContents(lesson.id)">
              {{ lesson.title }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ lesson.description }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getTopicName(lesson.topic) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getSubjectNameFromTopic(lesson.topic) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ lesson.estimated_hours ? lesson.estimated_hours + 'h' : '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <span :class="lesson.is_published ? 'text-green-600' : 'text-yellow-600'">
                {{ lesson.is_published ? 'Pubblicata' : 'Bozza' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(lesson.created_at) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <button @click="editLesson(lesson as Lesson)" class="text-yellow-600 hover:text-yellow-900 transition duration-150 ease-in-out" title="Modifica Lezione">
                <PencilIcon class="h-5 w-5 inline-block" />
              </button>
              <button @click="gotoContents(lesson.id)" class="text-purple-600 hover:text-purple-900 transition duration-150 ease-in-out" title="Gestisci Contenuti">
                <DocumentTextIcon class="h-5 w-5 inline-block" />
              </button>
              <button @click="gotoAssign(lesson.id)" class="text-cyan-600 hover:text-cyan-900 transition duration-150 ease-in-out" title="Assegna Lezione">
                <UserPlusIcon class="h-5 w-5 inline-block" />
              </button>
              <button @click="confirmDelete(lesson as Lesson)" class="text-red-600 hover:text-red-900 transition duration-150 ease-in-out" title="Elimina Lezione">
                <TrashIcon class="h-5 w-5 inline-block" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Messaggio Nessuna Lezione Trovata -->
    <div v-if="!lessonStore.isLoading && groupedAndUngroupedLessons.groups.length === 0 && groupedAndUngroupedLessons.unscoped.length === 0 && !lessonStore.error" class="text-center text-gray-500 py-10">
      <span v-if="searchQuery">Nessuna lezione trovata per "{{ searchQuery }}".</span>
      <span v-else>Non hai ancora creato nessuna lezione o gruppo di lezioni.</span>
    </div>

     <LessonEditModal
      v-if="showAddModal || lessonToEdit"
      :lesson="lessonToEdit"
      :topics="topicStore.topicsSummary"
      :is-saving="isSaving"
      @close="closeModal"
      @save="handleSave"
    />

    <LessonGroupModal
      :show="showGroupModal"
      @close="showGroupModal = false"
      @save="handleGroupSave"
    />

    <AssignLessonModal
      :show="isAssignModalOpen"
      :lesson-id="currentLessonIdToAssign"
      @close="closeAssignModal"
      @assignment-complete="handleAssignmentCompletion"
    />

    <AssignToGroupModal
      :show="showAssignToGroupModal"
      :groups="lessonStore.lessonGroups"
      @close="showAssignToGroupModal = false"
      @assign="handleAssignToGroup"
    />

    <IFrameModal
      v-if="showIframeModal"
      :src="iframeSrc"
      title="Gestisci Contenuti Lezione"
      @close="handleCloseIframeModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useLessonStore } from '@/stores/lessons';
import { useTopicStore } from '@/stores/topicStore';
import { useSubjectStore } from '@/stores/subjectStore';
import { useUiStore } from '@/stores/ui';
import emitter from '@/eventBus';
import LessonEditModal from '../components/features/lezioni/LessonEditModal.vue';
import AssignLessonModal from '../components/features/lezioni/AssignLessonModal.vue';
import LessonGroupModal from '../components/features/lezioni/LessonGroupModal.vue';
import AssignToGroupModal from '../components/features/lezioni/AssignToGroupModal.vue';
import IFrameModal from '@/components/common/IFrameModal.vue';
import type { Lesson, LessonGroup } from '@/types/lezioni';
import { PlusCircleIcon, PencilIcon, TrashIcon, DocumentTextIcon, UserPlusIcon, ChevronUpIcon, ChevronDownIcon, FolderIcon, ChevronRightIcon, XCircleIcon } from '@heroicons/vue/24/outline';

const searchQuery = ref('');
const lessonStore = useLessonStore();
const topicStore = useTopicStore();
const subjectStore = useSubjectStore();
const uiStore = useUiStore(); // Istanzia uiStore
const router = useRouter();

const lessons = computed(() => lessonStore.lessons);

const showAddModal = ref(false);
const lessonToEdit = ref<Lesson | null>(null);
const isAssignModalOpen = ref(false);
const currentLessonIdToAssign = ref<number | null>(null);
const isSaving = ref(false);
const showIframeModal = ref(false);
const iframeSrc = ref('');

// Stato per l'ordinamento
const sortKey = ref('created_at');
const sortOrder = ref('desc');
const expandedGroups = ref<Set<number>>(new Set());
const selectedLessons = ref(new Set<number>());
const showGroupModal = ref(false);
const showAssignToGroupModal = ref(false);

// Funzione chiamata dall'event bus per aprire il modale
const handleOpenAddModalEvent = () => {
  console.log("TeacherLessonListView: Received open-add-lesson-modal event.");
  lessonToEdit.value = null; // Assicura che non siamo in modalità modifica
  showAddModal.value = true;
};

// Funzione chiamata dal pulsante "Crea Nuova Lezione" locale
const openAddModalDirectly = () => {
    lessonToEdit.value = null;
    showAddModal.value = true;
}

onMounted(async () => {
  await subjectStore.fetchSubjects();
  await topicStore.fetchTopics();
  await lessonStore.fetchLessons();
  await lessonStore.fetchLessonGroups(); // Carica i gruppi di lezioni
  // Registra il listener per l'evento
  emitter.on('open-add-lesson-modal', handleOpenAddModalEvent);
});

onUnmounted(() => {
  // Rimuovi il listener quando il componente viene smontato
  emitter.off('open-add-lesson-modal', handleOpenAddModalEvent);
});

const getTopicName = (topicId: number): string => {
    const topic = topicStore.topics.find(t => t.id === topicId);
    return topic ? topic.name : 'N/D';
};
const getSubjectNameFromTopic = (topicId: number): string => {
    const topic = topicStore.topics.find(t => t.id === topicId);
    if (!topic) return 'N/D';
    const subject = subjectStore.subjects.find(s => s.id === topic.subject);
    return subject ? subject.name : 'N/D';
};

const formatDate = (dateString: string): string => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'short', day: 'numeric' });
};

const editLesson = (lesson: Lesson) => {
  lessonToEdit.value = { ...lesson };
  showAddModal.value = false; // Chiudi modale aggiunta se aperto
};

const confirmDelete = async (lesson: Lesson) => {
  if (confirm(`Sei sicuro di voler eliminare la lezione "${lesson.title}"?`)) {
    await lessonStore.deleteLesson(lesson.id);
    if (lessonStore.error) {
        alert(`Errore durante l'eliminazione: ${lessonStore.error}`);
        lessonStore.error = null;
    }
  }
};

const confirmDeleteGroup = async (group: LessonGroup) => {
  if (confirm(`Sei sicuro di voler eliminare il gruppo "${group.name}"? Le lezioni contenute non saranno eliminate, ma solo separate dal gruppo.`)) {
    await lessonStore.deleteLessonGroup(group.id);
    if (lessonStore.error) {
      uiStore.addNotification({ message: `Errore durante l'eliminazione del gruppo: ${lessonStore.error}`, type: 'error' });
      lessonStore.error = null;
    } else {
      uiStore.addNotification({ message: `Gruppo "${group.name}" eliminato con successo.`, type: 'success' });
    }
  }
};

const confirmRemoveFromGroup = async (lesson: Lesson) => {
  if (confirm(`Sei sicuro di voler rimuovere la lezione "${lesson.title}" dal suo gruppo?`)) {
    await lessonStore.removeLessonFromGroup(lesson.id);
     if (lessonStore.error) {
      uiStore.addNotification({ message: `Errore durante la rimozione della lezione dal gruppo: ${lessonStore.error}`, type: 'error' });
      lessonStore.error = null;
    } else {
      uiStore.addNotification({ message: `Lezione rimossa dal gruppo con successo.`, type: 'success' });
    }
  }
};

const closeModal = () => {
  showAddModal.value = false;
  lessonToEdit.value = null;
};

const handleSave = async (lessonData: { id?: number; title: string; topic: number; description?: string; is_published?: boolean; estimated_hours?: number | null }) => {
    isSaving.value = true;
    let success = false;

    if (lessonData.id) {
        const updatedLesson = await lessonStore.updateLesson(lessonData.id, lessonData);
        success = !!updatedLesson;
    } else {
        const newLesson = await lessonStore.addLesson(lessonData);
        success = !!newLesson;
    }

    isSaving.value = false;

    if (success) {
        closeModal();
    } else {
         alert(`Errore durante il salvataggio: ${lessonStore.error}`);
         lessonStore.error = null;
    }
};

const gotoAssign = (lessonId: number) => {
    // router.push({ name: 'lesson-assign', params: { lessonId: lessonId.toString() } });
    currentLessonIdToAssign.value = lessonId;
    isAssignModalOpen.value = true;
};

const closeAssignModal = () => {
  isAssignModalOpen.value = false;
  currentLessonIdToAssign.value = null;
};

const handleAssignmentCompletion = (result: any) => {
  // Qui puoi gestire il risultato dell'assegnazione, ad esempio mostrando una notifica
  console.log('Risultato assegnazione dalla modale:', result);
  if (result.error) {
    uiStore.addNotification({ message: `Errore assegnazione: ${result.error}`, type: 'error' });
  } else if (result.created > 0) {
    uiStore.addNotification({ message: `${result.created} assegnazioni create con successo. Saltati: ${result.skipped}, Falliti: ${result.failed}.`, type: 'success' });
  } else if (result.skipped > 0 || result.failed > 0) {
     uiStore.addNotification({ message: `Nessuna nuova assegnazione. Saltati: ${result.skipped}, Falliti: ${result.failed}.`, type: 'warning' });
  } else {
    uiStore.addNotification({ message: 'Operazione di assegnazione completata, nessuna modifica effettuata.', type: 'info' });
  }
  // Non chiudiamo la modale qui, lo fa l'utente o la modale stessa dopo un successo chiaro.
};

const gotoContents = (lessonId: number) => {
  const routeData = router.resolve({
    name: 'lesson-contents',
    params: { lessonId: lessonId.toString() },
    query: { embedded: 'true' } // Aggiungiamo un query param per indicare che è in un iframe
  });
  iframeSrc.value = routeData.href;
  showIframeModal.value = true;
};

const handleCloseIframeModal = () => {
  showIframeModal.value = false;
  iframeSrc.value = '';
};

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

const toggleGroup = (groupId: number) => {
  if (expandedGroups.value.has(groupId)) {
    expandedGroups.value.delete(groupId);
  } else {
    expandedGroups.value.add(groupId);
  }
};

const openCreateGroupModal = () => {
  showGroupModal.value = true;
};

const handleGroupSave = async (groupName: string) => {
  const { group, error } = await lessonStore.createLessonGroup(groupName);
  if (error) {
    uiStore.addNotification({ message: error, type: 'error' });
  } else if (group) {
    const lessonIds = Array.from(selectedLessons.value);
    await lessonStore.assignLessonsToGroup(group.id, lessonIds);
    uiStore.addNotification({ message: `Gruppo "${groupName}" creato e ${lessonIds.length} lezioni assegnate.`, type: 'success' });
    selectedLessons.value.clear();
  }
  showGroupModal.value = false;
};

const openAssignToGroupModal = () => {
  showAssignToGroupModal.value = true;
};

const handleAssignToGroup = async (groupId: number) => {
  const lessonIds = Array.from(selectedLessons.value);
  await lessonStore.assignLessonsToGroup(groupId, lessonIds);
  if (lessonStore.error) {
    uiStore.addNotification({ message: `Errore durante l'assegnazione: ${lessonStore.error}`, type: 'error' });
    lessonStore.error = null;
  } else {
    const group = lessonStore.lessonGroups.find(g => g.id === groupId);
    uiStore.addNotification({ message: `${lessonIds.length} lezioni assegnate al gruppo "${group?.name}".`, type: 'success' });
    selectedLessons.value.clear();
  }
  showAssignToGroupModal.value = false;
};

const atLeastOneSelectedLessonInGroup = computed(() => {
  const selectedIds = Array.from(selectedLessons.value);
  return lessons.value.some(lesson => selectedIds.includes(lesson.id) && lesson.group);
});

const confirmRemoveSelectedFromGroup = async () => {
  const selectedIds = Array.from(selectedLessons.value);
  const lessonsToRemove = lessons.value.filter(lesson => selectedIds.includes(lesson.id) && lesson.group);
  
  if (lessonsToRemove.length === 0) {
    uiStore.addNotification({ message: "Nessuna delle lezioni selezionate è in un gruppo.", type: 'info' });
    return;
  }

  if (confirm(`Sei sicuro di voler rimuovere ${lessonsToRemove.length} lezioni dai loro rispettivi gruppi?`)) {
    const idsToRemove = lessonsToRemove.map(l => l.id);
    const result = await lessonStore.removeLessonsFromGroup(idsToRemove);
    
    let message = `${result.success} lezioni rimosse dai gruppi con successo.`;
    if (result.deletedGroups > 0) {
      message += ` ${result.deletedGroups} ${result.deletedGroups === 1 ? 'gruppo è stato' : 'gruppi sono stati'} eliminati perché rimasti vuoti.`;
    }

    uiStore.addNotification({ message, type: 'success' });

    if (result.failed > 0) {
      uiStore.addNotification({ message: `Errore: ${result.failed} lezioni non sono state rimosse.`, type: 'error' });
    }
    
    selectedLessons.value.clear();
  }
};

const toggleLessonSelection = (lessonId: number) => {
  if (selectedLessons.value.has(lessonId)) {
    selectedLessons.value.delete(lessonId);
  } else {
    selectedLessons.value.add(lessonId);
  }
};

const allVisibleLessonIds = computed(() => {
  return groupedAndUngroupedLessons.value.groups.flatMap(g => g.lessons.map(l => l.id))
    .concat(groupedAndUngroupedLessons.value.unscoped.map(l => l.id));
});

const areAllLessonsSelected = computed(() => {
  const visibleIds = allVisibleLessonIds.value;
  if (visibleIds.length === 0) return false;
  return visibleIds.every(id => selectedLessons.value.has(id));
});

const toggleSelectAll = () => {
  const visibleIds = allVisibleLessonIds.value;
  if (areAllLessonsSelected.value) {
    visibleIds.forEach(id => selectedLessons.value.delete(id));
  } else {
    visibleIds.forEach(id => selectedLessons.value.add(id));
  }
};

// Sostituisce filteredLessons con una logica che raggruppa le lezioni
const groupedAndUngroupedLessons = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  // 1. Filtra le lezioni in base alla query
  const filtered = query
    ? lessons.value.filter(lesson => {
        const topicName = getTopicName(lesson.topic).toLowerCase();
        const subjectName = getSubjectNameFromTopic(lesson.topic).toLowerCase();
        const status = (lesson.is_published ? 'pubblicata' : 'bozza').toLowerCase();
        const title = lesson.title.toLowerCase();
        const description = lesson.description ? lesson.description.toLowerCase() : '';
        const estimatedHours = lesson.estimated_hours ? lesson.estimated_hours.toString() : '';

        return title.includes(query) ||
               description.includes(query) ||
               topicName.includes(query) ||
               subjectName.includes(query) ||
               status.includes(query) ||
               (query && estimatedHours.includes(query));
      })
    : lessons.value;

  // 2. Ordina le lezioni filtrate
  const sorted = filtered.slice().sort((a, b) => {
    let valA: any;
    let valB: any;
    switch (sortKey.value) {
      case 'topic': valA = getTopicName(a.topic); valB = getTopicName(b.topic); break;
      case 'subject': valA = getSubjectNameFromTopic(a.topic); valB = getSubjectNameFromTopic(b.topic); break;
      default: valA = a[sortKey.value as keyof Lesson]; valB = b[sortKey.value as keyof Lesson];
    }
    if (typeof valA === 'string' && typeof valB === 'string') {
      valA = valA.toLowerCase(); valB = valB.toLowerCase();
    }
    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });

  // 3. Raggruppa le lezioni
  const unscoped: Lesson[] = [];
  const groupsMap = new Map<number, Lesson[]>();

  sorted.forEach(lesson => {
    if (lesson.group) {
      if (!groupsMap.has(lesson.group.id)) {
        groupsMap.set(lesson.group.id, []);
      }
      groupsMap.get(lesson.group.id)!.push(lesson);
    } else {
      unscoped.push(lesson);
    }
  });

  const groups = lessonStore.lessonGroups
    .map(group => ({
      ...group,
      lessons: groupsMap.get(group.id) || []
    }))
    .filter(group => group.lessons.length > 0);

  return { groups, unscoped };
});

</script>

<style scoped>
.group-header-expanded td {
  border-top: 2px solid #BFDBFE; /* blue-200 */
  border-left: 2px solid #BFDBFE;
  border-right: 2px solid #BFDBFE;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.lesson-in-expanded-group td:first-child {
  border-left: 2px solid #BFDBFE;
}
.lesson-in-expanded-group td:last-child {
  border-right: 2px solid #BFDBFE;
}

.last-lesson-in-group td {
  border-bottom: 2px solid #BFDBFE;
}

.last-lesson-in-group td:first-child {
  border-bottom-left-radius: 8px;
}

.last-lesson-in-group td:last-child {
  border-bottom-right-radius: 8px;
}

.pl-12 {
  padding-left: 3rem;
}
</style>
