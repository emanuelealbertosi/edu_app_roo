<template>
  <div class="fixed inset-0 bg-gray-800 bg-opacity-75 flex justify-center items-center z-50" @click.self="closeModal">
    <div class="bg-white rounded-lg shadow-xl p-6 mx-4 sm:mx-auto w-full max-w-2xl flex flex-col max-h-[90vh]">
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
          <!-- Tab Lezioni -->
          <div v-show="activeTab === 'lessons'">
            <h6 class="text-md font-semibold text-gray-700 mb-2">Seleziona Lezioni</h6>
            <div v-if="!lessons.length" class="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded relative" role="alert">
              Nessuna lezione disponibile.
            </div>
            <ul v-else class="max-h-[40vh] overflow-y-auto border border-gray-300 rounded-md bg-white divide-y divide-gray-200">
              <li v-for="lesson in lessons" :key="lesson.id" class="px-4 py-3 hover:bg-gray-50 flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  :id="`lesson-${lesson.id}`"
                  :value="{ type: UDAContentType.LESSON, id: lesson.id, title: lesson.title, estimated_hours: lesson.estimated_hours }"
                  v-model="selectedItems"
                  class="h-5 w-5 text-indigo-600 border-gray-400 rounded focus:ring-indigo-500 focus:ring-2 focus:ring-offset-0 cursor-pointer mr-3"
                />
                <label :for="`lesson-${lesson.id}`" class="flex-grow cursor-pointer">
                  <span class="select-none text-sm text-gray-900">{{ lesson.title }}</span>
                  <small v-if="lesson.subject_name" class="text-gray-500 ml-2">({{ lesson.subject_name }})</small>
                  <small v-if="lesson.estimated_hours" class="text-gray-500 ml-2">[{{ lesson.estimated_hours }}h]</small>
                </label>
              </li>
            </ul>
          </div>

          <!-- Tab Quiz -->
          <div v-show="activeTab === 'quizzes'">
            <h6 class="text-md font-semibold text-gray-700 mb-2">Seleziona Template Quiz</h6>
            <div v-if="errorLoadingContent" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
              {{ errorLoadingContent }}
            </div>
            <div v-else-if="!quizTemplates.length" class="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded relative" role="alert">
              Nessun template di quiz disponibile.
            </div>
            <ul v-else class="max-h-[40vh] overflow-y-auto border border-gray-300 rounded-md bg-white divide-y divide-gray-200">
              <li v-for="template in quizTemplates" :key="template.id" class="px-4 py-3 hover:bg-gray-50 flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  :id="`quiz-${template.id}`"
                  :value="{ type: 'QUIZ_TEMPLATE', id: template.id, title: template.title }"
                  v-model="selectedItems"
                  class="h-5 w-5 text-indigo-600 border-gray-400 rounded focus:ring-indigo-500 focus:ring-2 focus:ring-offset-0 cursor-pointer mr-3"
                />
                <label :for="`quiz-${template.id}`" class="flex-grow cursor-pointer">
                  <span class="select-none text-sm text-gray-900">{{ template.title }}</span>
                  <small v-if="template.subject_name" class="text-gray-500 ml-2">({{ template.subject_name }})</small>
                  <small v-if="template.questions_count !== undefined" class="text-gray-500 ml-1">[{{ template.questions_count }}q]</small>
                </label>
          </li>
            </ul>
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
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'; // Aggiunto computed
import { useLessonStore } from '@/stores/lessons';
import { useQuizStore } from '@/stores/quizStore';
import { useUiStore } from '@/stores/ui';
// import type { Lesson } from '@/types/lezioni'; // Rimosso perché non utilizzato direttamente, il tipo per 'lessons' è inferito dallo store
// import type { Quiz } from '@/types/quiz'; // Non più usato direttamente per la lista
// import type { QuizTemplate } from '@/types/quizTemplate'; // Rimosso perché non utilizzato direttamente
import { UDAContentType } from '@/types/uda'; // Importa l'enum
import type { SelectedContentItem, RawSelectedContentItem } from '@/types/uda';

const emit = defineEmits(['close', 'select']);

const activeTab = ref<'lessons' | 'quizzes'>('lessons');
const loading = ref(false);
// lessons è ora una computed property
// const quizTemplates = ref<QuizTemplate[]>([]); // Sostituito con computed
const selectedItems = ref<RawSelectedContentItem[]>([]);
const errorLoadingContent = ref<string | null>(null);
const isConfirming = ref(false);

const lessonStore = useLessonStore();
const quizStore = useQuizStore();
const uiStore = useUiStore();

// lessons è ora una computed property che riflette direttamente lo store
const lessons = computed(() => lessonStore.lessons);
const quizTemplates = computed(() => quizStore.quizTemplates); // Aggiunta computed property per quizTemplates

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
    if (activeTab.value === 'lessons') {
      await loadInitialLessons();
    } else if (activeTab.value === 'quizzes') { // Essere espliciti
      await loadQuizTemplates();
    }
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
  selectedItems.value = []; // Resetta la selezione quando si cambia tab
  try {
    if (newTab === 'lessons') {
      // Se le lezioni non sono mai state caricate (store vuoto), caricale.
      // Altrimenti, la computed property `lessons` si aggiornerà automaticamente.
      if (lessonStore.lessons.length === 0) {
        await lessonStore.fetchLessons();
      }
    } else if (newTab === 'quizzes') {
      // loadQuizTemplates ora gestisce internamente il controllo se fetchare o meno
      await loadQuizTemplates();
    }
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

</script>

<style scoped>
</style>