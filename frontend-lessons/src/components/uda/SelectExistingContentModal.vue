<template>
  <div class="fixed inset-0 bg-gray-800 bg-opacity-75 flex justify-center items-center z-50" @click.self="closeModal">
    <div class="bg-white rounded-lg shadow-xl p-6 mx-4 sm:mx-auto w-full max-w-5xl flex flex-col max-h-[90vh]">
      <div class="flex justify-between items-center pb-4 border-b border-gray-200 mb-4">
        <h5 class="text-xl font-semibold text-gray-800">Aggiungi Contenuto Esistente</h5>
        <button type="button" class="text-gray-400 hover:text-gray-600 text-2xl leading-none" @click="closeModal" aria-label="Close">&times;</button>
      </div>
      <div class="overflow-y-auto flex-grow pr-2"> <!-- Aggiunto pr-2 per scrollbar -->
        <div class="border-b border-gray-200 mb-4">
          <nav class="-mb-px flex space-x-6" aria-label="Tabs">
            <a href="#"
               @click.prevent="activeTab = 'lessons'"
               :class="[
                 activeTab === 'lessons'
                   ? 'border-indigo-500 text-indigo-600'
                   : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                 'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm'
               ]">
              Lezioni
            </a>
            <a href="#"
               @click.prevent="activeTab = 'quizzes'"
               :class="[
                 activeTab === 'quizzes'
                   ? 'border-indigo-500 text-indigo-600'
                   : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                 'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm'
               ]">
              Quiz Templates
            </a>
          </nav>
        </div>

        <div v-if="loading" class="text-center py-6">
          <svg class="animate-spin mx-auto h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-sm text-gray-500 mt-2">Caricamento...</p>
        </div>

        <div v-else-if="errorLoadingContent" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong class="font-bold">Errore!</strong>
          <span class="block sm:inline"> {{ errorLoadingContent }}</span>
        </div>
        <div v-else>
          <!-- Filtro di ricerca -->
         <div class="mb-4">
           <input
             type="text"
             v-model="searchQuery"
             :placeholder="`Cerca in ${activeTab}...`"
             class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
           />
         </div>
         <!-- Tab Lezioni -->
         <div v-show="activeTab === 'lessons'">
           <div class="flex justify-between items-center mb-2">
             <h6 class="text-md font-semibold text-gray-700">Seleziona Lezioni</h6>
              <button @click="showCreateLessonModal = true" type="button" class="flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-md shadow-sm hover:bg-blue-700 transition duration-150 ease-in-out text-xs font-medium">
                <PlusCircleIcon class="h-4 w-4 sm:mr-1" />
                <span class="hidden sm:inline">Crea Nuova Lezione</span>
              </button>
           </div>
           <div v-if="!filteredLessons.length" class="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded relative" role="alert">
             Nessuna lezione trovata.
           </div>
           <div v-else class="max-h-[40vh] overflow-y-auto border border-gray-300 rounded-md">
             <table class="min-w-full divide-y divide-gray-200">
               <thead class="bg-gray-50 sticky top-0">
                 <tr>
                   <th scope="col" class="w-12 px-6 py-3"></th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('title')">
                    Titolo <span v-if="sortKey === 'title'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('description')">
                    Descrizione <span v-if="sortKey === 'description'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('topic')">
                    Argomento <span v-if="sortKey === 'topic'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('subject')">
                    Materia <span v-if="sortKey === 'subject'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('group')">
                    Gruppo <span v-if="sortKey === 'group'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('estimated_hours')">
                    Ore Stimate <span v-if="sortKey === 'estimated_hours'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('is_published')">
                    Stato <span v-if="sortKey === 'is_published'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('created_at')">
                    Data Creazione <span v-if="sortKey === 'created_at'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                  </th>
                 </tr>
               </thead>
               <tbody class="bg-white divide-y divide-gray-200">
                 <tr v-for="lesson in filteredLessons" :key="lesson.id" class="hover:bg-gray-50">
                   <td class="px-6 py-4 whitespace-nowrap">
                     <input
                       type="checkbox"
                       :id="`lesson-${lesson.id}`"
                       :value="{ type: UDAContentType.LESSON, id: lesson.id, title: lesson.title, estimated_hours: lesson.estimated_hours }"
                       v-model="selectedItems"
                       class="h-5 w-5 text-indigo-600 border-gray-400 rounded focus:ring-indigo-500 focus:ring-2 focus:ring-offset-0 cursor-pointer"
                     />
                   </td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ lesson.title }}</td>
                   <td class="px-6 py-4 whitespace-normal text-sm text-gray-500 max-w-xs truncate">{{ lesson.description }}</td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getTopicName(lesson.topic) }}</td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getSubjectNameFromTopic(lesson.topic) }}</td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ lesson.group?.name || '-' }}</td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ lesson.estimated_hours ? `${lesson.estimated_hours}h` : '-' }}</td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm">
                     <span :class="lesson.is_published ? 'text-green-600' : 'text-yellow-600'">
                       {{ lesson.is_published ? 'Pubblicata' : 'Bozza' }}
                     </span>
                   </td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(lesson.created_at) }}</td>
                 </tr>
               </tbody>
             </table>
           </div>
         </div>

          <!-- Tab Quiz -->
          <div v-show="activeTab === 'quizzes'">
            <h6 class="text-md font-semibold text-gray-700 mb-2">Seleziona Template Quiz</h6>
            <div v-if="errorLoadingContent" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
              {{ errorLoadingContent }}
            </div>
            <div v-else-if="!filteredQuizTemplates.length" class="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded relative" role="alert">
              Nessun template di quiz trovato.
            </div>
            <div v-else class="max-h-[40vh] overflow-y-auto border border-gray-300 rounded-md">
               <table class="min-w-full divide-y divide-gray-200">
                 <thead class="bg-gray-50 sticky top-0">
                   <tr>
                     <th scope="col" class="w-12 px-6 py-3"></th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('title')">
                      Titolo <span v-if="sortKey === 'title'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                    </th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('description')">
                      Descrizione <span v-if="sortKey === 'description'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                    </th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('subject_name')">
                      Materia <span v-if="sortKey === 'subject_name'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                    </th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('topic_name')">
                      Argomento <span v-if="sortKey === 'topic_name'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                    </th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('created_at')">
                      Creato il <span v-if="sortKey === 'created_at'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="template in filteredQuizTemplates" :key="template.id" class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        :id="`quiz-${template.id}`"
                        :value="{ type: 'QUIZ_TEMPLATE', id: template.id, title: template.title }"
                        v-model="selectedItems"
                        class="h-5 w-5 text-indigo-600 border-gray-400 rounded focus:ring-indigo-500 focus:ring-2 focus:ring-offset-0 cursor-pointer"
                      />
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ template.title }}</td>
                    <td class="px-6 py-4 whitespace-normal text-sm text-gray-500 max-w-xs truncate">{{ template.description }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ template.subject_name || 'N/D' }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ template.topic_name || 'N/D' }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(template.created_at) }}</td>
                  </tr>
                </tbody>
               </table>
            </div>
          </div>
        </div>
      </div>
      <div class="flex justify-end pt-4 border-t border-gray-200 mt-4 space-x-3">
        <button type="button"
                class="border border-gray-300 hover:bg-gray-100 text-gray-700 font-medium py-2 px-4 rounded-md shadow-sm text-sm"
                @click="closeModal"
                :disabled="isConfirming">
          Annulla
        </button>
        <button
          type="button"
          class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md shadow-sm text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          @click="confirmSelection"
          :disabled="selectedItems.length === 0 || isConfirming"
        >
          <svg v-if="isConfirming" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isConfirming ? 'Aggiungendo...' : `Aggiungi Selezionati (${selectedItems.length})` }}
        </button>
      </div>
    </div>
  </div>

  <LessonEditModal
    v-if="showCreateLessonModal"
    :lesson="null"
    :topics="topicStore.topicsSummary"
    :is-saving="isSavingLesson"
    @close="showCreateLessonModal = false"
    @save="handleNewLessonSaved"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'; // Aggiunto computed
import { useLessonStore } from '@/stores/lessons';
import { useQuizStore } from '@/stores/quizStore';
import { useTopicStore } from '@/stores/topicStore';
import { useSubjectStore } from '@/stores/subjectStore';
import { useUiStore } from '@/stores/ui';
// import type { Lesson } from '@/types/lezioni'; // Rimosso perché non utilizzato direttamente, il tipo per 'lessons' è inferito dallo store
// import type { Quiz } from '@/types/quiz'; // Non più usato direttamente per la lista
// import type { QuizTemplate } from '@/types/quizTemplate'; // Rimosso perché non utilizzato direttamente
import { UDAContentType } from '@/types/uda'; // Importa l'enum
import type { SelectedContentItem, RawSelectedContentItem } from '@/types/uda';
import type { Subject } from '@/types/subject';
import { ChevronUpIcon, ChevronDownIcon, PlusCircleIcon } from '@heroicons/vue/24/outline';
import type { Lesson } from '@/types/lezioni';
import LessonEditModal from '@/components/features/lezioni/LessonEditModal.vue';

const emit = defineEmits(['close', 'select']);

const activeTab = ref<'lessons' | 'quizzes'>('lessons');
const loading = ref(false);
// lessons è ora una computed property
// const quizTemplates = ref<QuizTemplate[]>([]); // Sostituito con computed
const selectedItems = ref<RawSelectedContentItem[]>([]);
const errorLoadingContent = ref<string | null>(null);
const isConfirming = ref(false);
const showCreateLessonModal = ref(false);
const isSavingLesson = ref(false);

const lessonStore = useLessonStore();
const quizStore = useQuizStore();
const topicStore = useTopicStore();
const subjectStore = useSubjectStore();
const uiStore = useUiStore();

const searchQuery = ref('');
const sortKey = ref('created_at');
const sortOrder = ref('desc');

// lessons è ora una computed property che riflette direttamente lo store
const lessons = computed(() => lessonStore.lessons);
const quizTemplates = computed(() => quizStore.quizTemplates); // Aggiunta computed property per quizTemplates

const filteredLessons = computed(() => {
 const query = searchQuery.value.toLowerCase().trim();
 
 let filtered = lessons.value;

 if (query) {
   filtered = lessons.value.filter(lesson => {
     const title = lesson.title.toLowerCase();
     const description = lesson.description?.toLowerCase() || '';
     const topicName = getTopicName(lesson.topic).toLowerCase();
     const subjectName = getSubjectNameFromTopic(lesson.topic).toLowerCase();
     const groupName = lesson.group?.name.toLowerCase() || '';
     const status = (lesson.is_published ? 'pubblicata' : 'bozza').toLowerCase();
     return title.includes(query) || description.includes(query) || topicName.includes(query) || subjectName.includes(query) || groupName.includes(query) || status.includes(query);
   });
 }

 return filtered.slice().sort((a, b) => {
   let valA: any;
   let valB: any;

   switch (sortKey.value) {
     case 'topic':
       valA = getTopicName(a.topic);
       valB = getTopicName(b.topic);
       break;
     case 'subject':
       valA = getSubjectNameFromTopic(a.topic);
       valB = getSubjectNameFromTopic(b.topic);
       break;
     case 'group':
       valA = a.group?.name || '';
       valB = b.group?.name || '';
       break;
     default:
       valA = a[sortKey.value as keyof Lesson];
       valB = b[sortKey.value as keyof Lesson];
   }

   if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
   if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
   return 0;
 });
});

const filteredQuizTemplates = computed(() => {
 const query = searchQuery.value.toLowerCase().trim();
 let filtered = quizTemplates.value;

 if (query) {
   filtered = quizTemplates.value.filter(template => {
     const title = template.title.toLowerCase();
     const description = template.description?.toLowerCase() || '';
     const subjectName = template.subject_name?.toLowerCase() || '';
     const topicName = template.topic_name?.toLowerCase() || '';
     return title.includes(query) || description.includes(query) || subjectName.includes(query) || topicName.includes(query);
   });
 }
 
 return filtered.slice().sort((a, b) => {
   const valA = a[sortKey.value as keyof typeof a];
   const valB = b[sortKey.value as keyof typeof b];
   if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
   if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
   return 0;
 });
});

const loadInitialLessons = async () => {
  // Carica le lezioni solo se l'array nello store è vuoto all'inizio.
  // Successivamente, ci si affida alla reattività di `lessons` (computed).
  if (lessonStore.lessons.length === 0) {
    await lessonStore.fetchLessons();
  }
  // Non è più necessario assegnare a un ref locale `lessons.value` qui
};

const loadQuizTemplates = async () => {
  // Chiama fetchQuizTemplates solo se lo store è vuoto.
  // La computed property quizTemplates si aggiornerà automaticamente.
  if (quizStore.quizTemplates.length === 0) {
    await quizStore.fetchQuizTemplates();
  }
  // console.log('[SelectExistingContentModal] quizStore.quizTemplates (after potential fetch):', JSON.parse(JSON.stringify(quizStore.quizTemplates)));
};

onMounted(async () => {
  loading.value = true;
  errorLoadingContent.value = null;
  try {
    // Carica inizialmente le lezioni (o il tab attivo)
    // Carica tutti i dati necessari indipendentemente dal tab, così i nomi di argomenti/materie sono sempre disponibili
   await Promise.all([
     loadInitialLessons(),
     loadQuizTemplates(),
     topicStore.fetchTopics(),
     subjectStore.fetchSubjects(),
     lessonStore.fetchLessonGroups() // Aggiunto fetch dei gruppi
   ]);
  } catch (error) {
    const errorMessage = (error instanceof Error) ? error.message : "Errore sconosciuto nel caricamento dei contenuti.";
    console.error("Errore nel caricamento dei contenuti esistenti:", error);
    errorLoadingContent.value = `Impossibile caricare i contenuti: ${errorMessage}`;
    uiStore.addNotification({ message: errorLoadingContent.value, type: 'error' });
  } finally {
    loading.value = false;
  }
});

watch(activeTab, async (newTab, oldTab) => {
  if (newTab === oldTab) return;
  loading.value = true;
  errorLoadingContent.value = null;
  searchQuery.value = ''; // Resetta la ricerca quando si cambia tab
  selectedItems.value = []; // Resetta la selezione quando si cambia tab
  sortKey.value = 'created_at'; // Reset sort key
  sortOrder.value = 'desc'; // Reset sort order
  try {
    // I dati sono già caricati in onMounted, non è necessario ricaricarli
    // a meno di logiche specifiche di refresh non richieste.
  } catch (error) {
    const errorMessage = (error instanceof Error) ? error.message : `Errore caricando ${newTab}.`;
    console.error(`Errore caricando ${newTab}:`, error);
    errorLoadingContent.value = `Impossibile caricare ${newTab}: ${errorMessage}`;
    uiStore.addNotification({ message: errorLoadingContent.value, type: 'error' });
  } finally {
    loading.value = false;
  }
});

const closeModal = () => {
  if (isConfirming.value) return;
  emit('close');
};

const confirmSelection = async () => {
  if (isConfirming.value || selectedItems.value.length === 0) return;

  console.log('[SelectExistingContentModal] Confirming selection. Selected items:', JSON.parse(JSON.stringify(selectedItems.value)));
  isConfirming.value = true;
  const finalSelectedItems: SelectedContentItem[] = [];
  let hasError = false;

  for (const item of selectedItems.value) {
    if (item.type === 'QUIZ_TEMPLATE') {
      try {
        // Non creiamo più il quiz qui. Passiamo il riferimento al template.
        // Sarà compito del componente ricevente (es. UdaContentEditor tramite udaStore)
        // gestire l'eventuale creazione dell'istanza Quiz se necessario prima del salvataggio dell'UDA.
        finalSelectedItems.push({
          type: UDAContentType.QUIZ, // Il tipo finale per UDAContent sarà QUIZ
          id: item.id, // id qui è l'ID del QuizTemplate sorgente
          title: item.title || `Quiz da template ${item.id}`,
        });
      } catch (error) { // Questo blocco catch potrebbe non essere più necessario se non ci sono operazioni asincrone rischiose qui
        hasError = true; // Manteniamo hasError nel caso in cui altre operazioni nel loop falliscano
        const errorMessage = (error instanceof Error) ? error.message : `Errore processando il template quiz ${item.title || item.id}.`;
        console.error(errorMessage, error);
        uiStore.addNotification({ message: `Errore: ${errorMessage}`, type: 'error' });
      }
    } else if (item.type === UDAContentType.LESSON) { // Usa l'enum anche qui per coerenza
      finalSelectedItems.push(item as SelectedContentItem);
    }
  }

  isConfirming.value = false;

  if (finalSelectedItems.length > 0) {
     emit('select', finalSelectedItems);
  }
  
  if (!hasError || finalSelectedItems.length > 0) { // Chiudi se non ci sono stati errori o se almeno un item è stato processato
    closeModal();
  }
};

const handleNewLessonSaved = async (lessonData: { id?: number; title: string; topic: number; description?: string; is_published?: boolean; estimated_hours?: number | null }) => {
  isSavingLesson.value = true;
  const newLesson = await lessonStore.addLesson(lessonData);
  isSavingLesson.value = false;

  if (newLesson) {
    showCreateLessonModal.value = false;
    const newItem: RawSelectedContentItem = {
      type: UDAContentType.LESSON,
      id: newLesson.id,
      title: newLesson.title,
      estimated_hours: newLesson.estimated_hours
    };
    selectedItems.value.push(newItem);
    uiStore.addNotification({ message: `Lezione "${newLesson.title}" creata e aggiunta alla selezione.`, type: 'success' });
  } else {
    alert(`Errore durante la creazione della lezione: ${lessonStore.error}`);
    uiStore.addNotification({ message: `Errore durante la creazione della lezione: ${lessonStore.error}`, type: 'error' });
  }
};

const getTopicName = (topicId: number): string => {
    const topic = topicStore.getTopicById(topicId);
    return topic ? topic.name : 'N/D';
};

const getSubjectNameFromTopic = (topicId: number): string => {
    const topic = topicStore.getTopicById(topicId);
    if (!topic) return 'N/D';
    const subject = subjectStore.subjects.find((s: Subject) => s.id === topic.subject);
    return subject ? subject.name : 'N/D';
};

const formatDate = (dateString: string | null): string => {
   if (!dateString) return 'N/A';
   const date = new Date(dateString);
   return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'short', day: 'numeric' });
};

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};
 </script>
 
 <style scoped>
 </style>