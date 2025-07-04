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

    <div v-if="lessonStore.isLoading" class="text-center text-gray-500 py-10">
      Caricamento lezioni...
    </div>

    <div v-if="lessonStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore:</strong>
      <span class="block sm:inline"> {{ lessonStore.error }}</span>
    </div>

    <!-- Tabella Lezioni Filtrate -->
    <div v-if="!lessonStore.isLoading && filteredLessons.length > 0" class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
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
          <tr v-for="lesson in filteredLessons" :key="lesson.id" class="hover:bg-gray-50">
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
    <div v-if="!lessonStore.isLoading && filteredLessons.length === 0 && !lessonStore.error" class="text-center text-gray-500 py-10">
      <span v-if="searchQuery">Nessuna lezione trovata per "{{ searchQuery }}".</span>
      <span v-else>Non hai ancora creato nessuna lezione.</span>
    </div>

     <LessonEditModal
      v-if="showAddModal || lessonToEdit"
      :lesson="lessonToEdit"
      :topics="topicStore.topics"
      @close="closeModal"
      @save="handleSave"
    />

    <AssignLessonModal
      :show="isAssignModalOpen"
      :lesson-id="currentLessonIdToAssign"
      @close="closeAssignModal"
      @assignment-complete="handleAssignmentCompletion"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'; // Aggiunto onUnmounted
import { useRouter } from 'vue-router';
import { useLessonStore } from '@/stores/lessons';
import { useTopicStore } from '@/stores/topics';
import { useSubjectStore } from '@/stores/subjects';
import { useUiStore } from '@/stores/ui'; // Importa uiStore
const searchQuery = ref('');
import emitter from '@/eventBus'; // Importa l'event bus
import LessonEditModal from '../components/features/lezioni/LessonEditModal.vue';
import AssignLessonModal from '../components/features/lezioni/AssignLessonModal.vue'; // Importa la nuova modale
// La ricerca e l'ordinamento sono ora gestiti interamente lato client per coerenza.
const filteredLessons = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  // 1. Filtra le lezioni in base alla query di ricerca
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

  // 2. Ordina l'array filtrato (o completo)
  return filtered.slice().sort((a, b) => {
    let valA: any;
    let valB: any;

    // Assegna i valori da confrontare in base a sortKey
    switch (sortKey.value) {
      case 'topic':
        valA = getTopicName(a.topic);
        valB = getTopicName(b.topic);
        break;
      case 'subject':
        valA = getSubjectNameFromTopic(a.topic);
        valB = getSubjectNameFromTopic(b.topic);
        break;
      default:
        valA = a[sortKey.value as keyof Lesson];
        valB = b[sortKey.value as keyof Lesson];
    }

    // Gestione per diversi tipi di dato
    if (typeof valA === 'string' && typeof valB === 'string') {
      valA = valA.toLowerCase();
      valB = valB.toLowerCase();
    }
    
    if (valA < valB) {
      return sortOrder.value === 'asc' ? -1 : 1;
    }
    if (valA > valB) {
      return sortOrder.value === 'asc' ? 1 : -1;
    }
    return 0;
  });
});
import type { Lesson } from '@/types/lezioni';
import { PlusCircleIcon, PencilIcon, TrashIcon, DocumentTextIcon, UserPlusIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';


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

// Stato per l'ordinamento
const sortKey = ref('created_at');
const sortOrder = ref('desc');

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
  // Carica tutte le lezioni, l'ordinamento è gestito localmente
  await lessonStore.fetchLessons();
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

const closeModal = () => {
  showAddModal.value = false;
  lessonToEdit.value = null;
};

const handleSave = async (lessonData: { id?: number; title: string; topic: number; description?: string; is_published?: boolean; estimated_hours?: number | null }) => {
    let success = false;
    let savedLesson: Lesson | null = null;

    if (lessonData.id) {
        success = await lessonStore.updateLesson(lessonData.id, lessonData);
    } else {
        savedLesson = await lessonStore.addLesson(lessonData);
        success = !!savedLesson;
    }

    if (success) {
        closeModal();
        // Non è necessario chiamare fetchLessons() qui.
        // Le azioni addLesson/updateLesson nello store dovrebbero aver già aggiornato
        // l'array `lessons` in modo reattivo, e la `computed property` `lessons`
        // in questo componente dovrebbe riflettere tali cambiamenti.
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
     // Usa il nome della rotta definito nel router
    router.push({ name: 'lesson-contents', params: { lessonId: lessonId.toString() } });
};

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
  // L'ordinamento viene applicato reattivamente dalla computed property `filteredLessons`.
  // Non è più necessaria una chiamata API.
};

</script>
