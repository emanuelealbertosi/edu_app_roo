<template>
  <div class="uda-content-editor">
    <!-- Il titolo è già presente nel componente genitore (UdaFormView/UdaTemplateFormView) -->
    <!-- <h3 class="text-xl font-semibold text-gray-700 mb-4">Contenuti</h3> -->
    <div class="content-list mb-6">
      <div v-if="!localContents || localContents.length === 0" class="empty-state p-6 text-center text-gray-500 border border-dashed border-gray-300 rounded-lg bg-gray-50">
        Nessun contenuto aggiunto. Clicca sui bottoni qui sotto per aggiungere contenuti.
      </div>
      <div v-else>
        <UdaContentItemRenderer
          v-for="(content, index) in localContents"
          :key="content.temp_id || content.id"
          :content="content"
          :is-first="index === 0"
          :is-last="index === localContents.length - 1"
          :uda-id="props.context === 'uda' ? props.udaId : undefined"
          :context="props.context"
          @edit="handleEditContent"
          @delete="handleDeleteContent"
          @move="handleMoveContent"
          @update:teacher-marked-completed="handleTeacherMarkedCompletedUpdate"
          @update:activity-completed="handleActivityCompletedUpdate"
          class="mb-3"
        />
      </div>
    </div>

    <div class="actions p-4 border-t border-gray-200 mt-6">
       <h4 class="text-md font-semibold text-gray-600 mb-3">Aggiungi Nuovo Elemento Didattico</h4>
       <div class="flex flex-wrap gap-2">
          <!-- TODO: Aggiungere icone Heroicons -->
          <button type="button"
                  class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md shadow-sm text-sm"
                  @click.stop="openAddExistingContentModal">
            Aggiungi Lezione/Quiz Esistente
          </button>
          <button type="button"
                  class="border border-gray-300 hover:bg-gray-100 text-gray-700 font-medium py-2 px-4 rounded-md shadow-sm text-sm"
                  @click.stop="openAddNoteModal">
            Aggiungi Nota
          </button>
          <button type="button"
                  class="border border-gray-300 hover:bg-gray-100 text-gray-700 font-medium py-2 px-4 rounded-md shadow-sm text-sm"
                  @click.stop="openAddActivityModal">
            Aggiungi Attività
          </button>
       </div>
    </div>

    <!-- Modale per selezionare Lezioni/Quiz esistenti -->
    <SelectExistingContentModal
      v-if="showSelectExistingContentModal"
      @close="closeSelectExistingContentModal"
      @select="handleExistingContentSelected"
    />

    <!-- Modale per aggiungere/modificare Note -->
    <EditNoteContentModal
      v-if="showEditNoteModal"
      :model-value="editingNoteContent"
      :context="props.context"
      @close="closeEditNoteModal"
      @save="handleSaveNote"
    />

    <!-- Modale per aggiungere/modificare Attività -->
    <EditActivityContentModal
      v-if="showEditActivityModal"
      :model-value="editingActivityContent"
      :context="props.context"
      @close="closeEditActivityModal"
      @save="handleSaveActivity"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType, nextTick } from 'vue'; // Assicurati che watch sia importato
import { useQuizStore } from '@/stores/quizStore'; // Importa quizStore
import { useUdaStore } from '@/stores/udaStore'; // Importa lo store UDA
import SelectExistingContentModal from './SelectExistingContentModal.vue';
import EditNoteContentModal from './EditNoteContentModal.vue';
import EditActivityContentModal from './EditActivityContentModal.vue'; // Importa la modale Attività
import UdaContentItemRenderer from './UdaContentItemRenderer.vue';
import {
  type UDAContent, type UDATemplateContent,
  UDAContentType, UDATemplateContentType,
  type LessonUDAContent, type NoteUDAContent, type ActivityUDAContent, // Rimosso QuizTemplateUDAContent, QuizUDAContent è già in UDAContent
  type NoteTemplateUDAContent, type ActivityTemplateUDAContent,
  type SelectedContentItem,
  type QuizUDAContent // Importato esplicitamente se serve per cast specifici, anche se già in UDAContent
} from '@/types/uda';
// import type { Lesson } from '@/types/lezioni'; // Già importato in SelectExistingContentModal se serve lì
// import type { Quiz } from '@/types/quiz'; // Già importato in SelectExistingContentModal se serve lì

// Tipo temporaneo per i contenuti. Sarà sostituito con tipi specifici.
// interface BaseContentItem {
//   id?: string | number; // Potrebbe essere generato dal frontend temporaneamente o assente prima del salvataggio
//   order: number;
//   content_type: UDAContentType; // 'LESSON', 'QUIZ', 'NOTE', 'ACTIVITY' (o _TEMPLATE per i template)
//   lesson?: number | null; // FK a Lesson
//   quiz?: number | null; // FK a Quiz
//   note_title?: string | null;
//   note_content?: string | null;
//   activity_title?: string | null;
//   activity_description?: string | null;
//   // Campi specifici per UDATemplateContent
//   note_template_title?: string | null;
//   note_template_content?: string | null;
//   activity_template_title?: string | null;
//   activity_template_description?: string | null;
// }
type ContentItem = UDAContent | UDATemplateContent;

const props = defineProps({
  modelValue: {
    type: Array as PropType<ContentItem[]>,
    default: () => []
  },
  // Flag per distinguere il contesto (UDA o Template UDA) per gestire i tipi di contenuto corretti
  context: {
    type: String as PropType<'uda' | 'template'>,
    required: true
  },
  udaId: { // ID dell'UDA, necessario se context è 'uda' per le operazioni di update sullo store
    type: Number,
    required: false
  }
});

const emit = defineEmits(['update:modelValue']);
const udaStore = useUdaStore(); // Istanza dello store
const quizStore = useQuizStore(); // Istanza di quizStore

const localContents = ref<ContentItem[]>([]);
const showSelectExistingContentModal = ref(false);
const showEditNoteModal = ref(false);
const editingNoteContent = ref<NoteUDAContent | NoteTemplateUDAContent | null>(null);
const showEditActivityModal = ref(false); // Per la modale di modifica/aggiunta attività
const editingActivityContent = ref<ActivityUDAContent | ActivityTemplateUDAContent | null>(null); // Contenuto attività in modifica/creazione
const editingLessonOrQuizContentId = ref<string | number | null>(null); // Per tracciare l'item Lezione/Quiz da sostituire

// AGGIUNGI QUESTO WATCHER
watch(showSelectExistingContentModal, (newValue, oldValue) => { // Modificato per tracciamento più dettagliato
  // console.log(`[UdaContentEditor] WATCHER: showSelectExistingContentModal cambiato da ${oldValue} a ${newValue}`);
  if (newValue === true && oldValue === false) {
    // console.log("[UdaContentEditor] WATCHER: Modale SelectExistingContent STA PER APRIRSI.");
    // console.trace("[UdaContentEditor] WATCHER: Stack trace APERTURA modale SelectExistingContent");
  }
  if (newValue === false && oldValue === true) {
    // console.log("[UdaContentEditor] WATCHER: Modale SelectExistingContent SI È APPENA CHIUSA.");
    // console.trace("[UdaContentEditor] WATCHER: Stack trace CHIUSURA modale SelectExistingContent");
  }
});

watch(() => props.modelValue, (newValue) => {
  // Creare una copia profonda per evitare modifiche dirette alla prop
  const newLocalValue = newValue ? JSON.parse(JSON.stringify(newValue)) : [];
  // Aggiorna localContents.value solo se c'è una differenza effettiva
  // per evitare cicli di update.
  if (JSON.stringify(newLocalValue) !== JSON.stringify(localContents.value)) {
    localContents.value = newLocalValue;
  }
}, { immediate: true, deep: true });

watch(localContents, (newValue) => {
  emit('update:modelValue', newValue);
}, { deep: true });

const openAddExistingContentModal = () => {
  // console.log('[UdaContentEditor] FN openAddExistingContentModal: Inizio esecuzione.');
  // console.log('[UdaContentEditor] FN openAddExistingContentModal: Valore di showSelectExistingContentModal PRIMA: ', showSelectExistingContentModal.value);

  showSelectExistingContentModal.value = true;

  // console.log('[UdaContentEditor] FN openAddExistingContentModal: Valore di showSelectExistingContentModal DOPO: ', showSelectExistingContentModal.value);
  // console.trace('[UdaContentEditor] FN openAddExistingContentModal: Stack trace DOPO aver impostato showSelectExistingContentModal a true');
};

const closeSelectExistingContentModal = () => {
  // console.log('[UdaContentEditor] FN closeSelectExistingContentModal: Inizio esecuzione.');
  // console.log('[UdaContentEditor] FN closeSelectExistingContentModal: Valore di showSelectExistingContentModal PRIMA: ', showSelectExistingContentModal.value);
  showSelectExistingContentModal.value = false;
  editingLessonOrQuizContentId.value = null; // Resetta l'ID di modifica quando la modale si chiude
  // console.log('[UdaContentEditor] FN closeSelectExistingContentModal: Valore di showSelectExistingContentModal DOPO: ', showSelectExistingContentModal.value);
};

const generateTempId = () => `temp_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

const recalculateOrder = () => {
  localContents.value.forEach((content, index) => {
    content.order = index + 1;
  });
};

const handleExistingContentSelected = async (selectedItems: SelectedContentItem[]) => {
  if (editingLessonOrQuizContentId.value) {
    // Siamo in modalità MODIFICA
    if (selectedItems.length === 1) {
      const newItemData = selectedItems[0]; // newItemData.type può essere UDAContentType.LESSON o UDAContentType.QUIZ (da SelectedContentItem)
      const indexToReplace = localContents.value.findIndex(
        content => (content.temp_id === editingLessonOrQuizContentId.value) || (content.id === editingLessonOrQuizContentId.value)
      );

      if (indexToReplace > -1) {
        const originalContent = localContents.value[indexToReplace];
        
        const updatedContentBase: Partial<ContentItem> & { order: number; id?: number | string; temp_id?: string } = {
          id: originalContent.id,
          temp_id: originalContent.temp_id,
          order: originalContent.order,
          // newItemData.type è già corretto per UDAContent (LESSON o QUIZ)
                          // o per UDATemplateContent (LESSON o QUIZ_TEMPLATE) a seconda di come SelectExistingContentModal emette
                          // Ma SelectedContentItem emette UDAContentType.QUIZ per i quiz.
          content_type: newItemData.type,
        };
        
        if (newItemData.type === UDAContentType.LESSON) {
          (updatedContentBase as LessonUDAContent).lesson = newItemData.id;
          (updatedContentBase as LessonUDAContent).lesson_title = newItemData.title;
        } else if (newItemData.type === UDAContentType.QUIZ) { // item.type da SelectedContentItem è UDAContentType.QUIZ
          // newItemData.id è l'ID del QuizTemplate
          if (props.context === 'uda') {
            updatedContentBase.content_type = UDAContentType.QUIZ; // Conferma tipo per UDAContent
            (updatedContentBase as QuizUDAContent).quiz_template = newItemData.id;
            (updatedContentBase as QuizUDAContent).quiz_title = newItemData.title;
          } else { // template context
            // Se stiamo modificando un template UDA, il tipo deve essere QUIZ_TEMPLATE
            updatedContentBase.content_type = UDATemplateContentType.QUIZ_TEMPLATE;
            (updatedContentBase as QuizUDAContent).quiz_template = newItemData.id; // QuizUDAContent gestisce quiz_template
            (updatedContentBase as QuizUDAContent).quiz_title = newItemData.title;
          }
        }

        if (props.context === 'uda' && 'teacher_marked_completed' in originalContent) {
          (updatedContentBase as UDAContent).teacher_marked_completed = (originalContent as UDAContent).teacher_marked_completed;
          if (originalContent.content_type === UDAContentType.ACTIVITY && updatedContentBase.content_type === UDAContentType.ACTIVITY) {
            (updatedContentBase as ActivityUDAContent).activity_completed = (originalContent as ActivityUDAContent).activity_completed;
          }
        }
        localContents.value.splice(indexToReplace, 1, updatedContentBase as ContentItem);
      }
    } else if (selectedItems.length > 1) {
      console.warn("Selezionati più item durante la modifica di un contenuto Lezione/Quiz. Sostituzione non eseguita.");
    }
    // editingLessonOrQuizContentId.value è resettato in closeSelectExistingContentModal
  } else {
    // Siamo in modalità AGGIUNTA
    for (const item of selectedItems) {
      const baseNewContent: Partial<UDAContent | UDATemplateContent> & { order: number; temp_id: string } = {
        temp_id: generateTempId(),
        // item.type da SelectedContentItem è UDAContentType.LESSON o UDAContentType.QUIZ
        content_type: item.type,
        order: 0 // Verrà ricalcolato
      };

      if (item.type === UDAContentType.LESSON) {
        if (item.id === undefined) {
          console.error("Nessun ID lezione specificato per questo contenuto.", item);
          continue;
        }
        (baseNewContent as LessonUDAContent).lesson = item.id;
        (baseNewContent as LessonUDAContent).lesson_title = item.title;
      } else if (item.type === UDAContentType.QUIZ) { // item.type da SelectedContentItem è UDAContentType.QUIZ
        // item.id è l'ID del QuizTemplate
        if (props.context === 'uda') {
          baseNewContent.content_type = UDAContentType.QUIZ; // Conferma tipo per UDAContent
          (baseNewContent as QuizUDAContent).quiz_template = item.id;
          (baseNewContent as QuizUDAContent).quiz_title = item.title;
        } else { // template context
          // Se stiamo aggiungendo a un template UDA, il tipo deve essere QUIZ_TEMPLATE
          baseNewContent.content_type = UDATemplateContentType.QUIZ_TEMPLATE;
          (baseNewContent as QuizUDAContent).quiz_template = item.id; // QuizUDAContent gestisce quiz_template
          (baseNewContent as QuizUDAContent).quiz_title = item.title;
        }
      }
      
      if (props.context === 'uda') {
        (baseNewContent as UDAContent).teacher_marked_completed = false;
        if (baseNewContent.content_type === UDAContentType.ACTIVITY) {
          (baseNewContent as ActivityUDAContent).activity_completed = false;
          (baseNewContent as ActivityUDAContent).activity_attachment_url = ''; // Default per nuova attività
        }
      }
      localContents.value.push(baseNewContent as ContentItem);
    }
    recalculateOrder();
  }
  closeSelectExistingContentModal(); // Chiude la modale in ogni caso
};

const openAddNoteModal = () => {
  console.log('[UdaContentEditor] Chiamata openAddNoteModal.');
  console.log('[UdaContentEditor] PRIMA NOTE - udaStore.currentUda:', udaStore.currentUda ? udaStore.currentUda.id : 'null', 'Error:', udaStore.error);
  if (props.context === 'template') {
    editingNoteContent.value = {
      // temp_id: generateTempId(), // temp_id sarà aggiunto in handleSaveNote se è una nuova nota
      content_type: UDATemplateContentType.NOTE_TEMPLATE,
      note_template_title: 'Nuovo Template Nota',
      note_template_content: '',
      order: 0, // Sarà ricalcolato
    } as NoteTemplateUDAContent;
  } else {
    editingNoteContent.value = {
      // temp_id: generateTempId(), // temp_id sarà aggiunto in handleSaveNote se è una nuova nota
      content_type: UDAContentType.NOTE,
      note_title: 'Nuova Nota',
      note_content: '',
      order: 0, // Sarà ricalcolato
      teacher_marked_completed: false, // Default per nuove note UDA
    } as NoteUDAContent;
  }
  showEditNoteModal.value = true;
  console.log('[UdaContentEditor] DOPO NOTE - udaStore.currentUda:', udaStore.currentUda ? udaStore.currentUda.id : 'null', 'Error:', udaStore.error);
};

const closeEditNoteModal = () => {
  showEditNoteModal.value = false;
  editingNoteContent.value = null;
};

const handleSaveNote = (savedNoteData: NoteUDAContent | NoteTemplateUDAContent) => {
  const existingIndex = localContents.value.findIndex(content =>
    (content.temp_id && content.temp_id === savedNoteData.temp_id) ||
    (content.id && content.id === savedNoteData.id)
  );

  if (existingIndex > -1) {
    // Modifica di una nota esistente
    localContents.value.splice(existingIndex, 1, { ...savedNoteData } as ContentItem);
  } else {
    // Aggiunta di una nuova nota
    const newNoteWithId = { ...savedNoteData, temp_id: savedNoteData.temp_id || generateTempId() };
    localContents.value.push(newNoteWithId as ContentItem);
  }
  recalculateOrder();
  closeEditNoteModal();
};


const openAddActivityModal = () => {
  console.log('[UdaContentEditor] Chiamata openAddActivityModal.');
  console.log('[UdaContentEditor] PRIMA ACTIVITY - udaStore.currentUda:', udaStore.currentUda ? udaStore.currentUda.id : 'null', 'Error:', udaStore.error);
  if (props.context === 'template') {
    editingActivityContent.value = {
      content_type: UDATemplateContentType.ACTIVITY_TEMPLATE,
      activity_template_title: 'Nuovo Template Attività',
      activity_template_description: '',
      order: 0,
    } as ActivityTemplateUDAContent;
  } else {
    editingActivityContent.value = {
      content_type: UDAContentType.ACTIVITY,
      activity_title: 'Nuova Attività',
      activity_description: '',
      activity_attachment_url: '',
      activity_completed: false,
      teacher_marked_completed: false,
      order: 0,
    } as ActivityUDAContent;
  }
  showEditActivityModal.value = true;
  console.log('[UdaContentEditor] DOPO ACTIVITY - udaStore.currentUda:', udaStore.currentUda ? udaStore.currentUda.id : 'null', 'Error:', udaStore.error);
};

const closeEditActivityModal = () => {
  showEditActivityModal.value = false;
  editingActivityContent.value = null;
};

const handleSaveActivity = async (payload: { activityData: Partial<ActivityUDAContent | ActivityTemplateUDAContent>, file?: File }) => {
  const { activityData, file } = payload;

  if (props.context === 'template') {
    const existingIndex = localContents.value.findIndex(content =>
        (content.temp_id && content.temp_id === activityData.temp_id) ||
        (content.id && content.id === activityData.id)
    );
    if (existingIndex > -1) {
        localContents.value.splice(existingIndex, 1, { ...activityData } as ContentItem);
    } else {
        const newActivityWithId = { ...activityData, temp_id: activityData.temp_id || generateTempId(), order: 0 };
        localContents.value.push(newActivityWithId as ContentItem);
    }
    recalculateOrder();
  } else if (props.context === 'uda') {
    if (!activityData.id && !activityData.temp_id) { // È un nuovo contenuto UDA
      if (props.udaId === undefined) {
        console.error("Impossibile aggiungere contenuto attività UDA: udaId non è definito.");
        closeEditActivityModal();
        return;
      }
      // Assicurati che activityData sia del tipo corretto per la creazione
      const createPayload: Partial<Omit<ActivityUDAContent, 'id' | 'uda_id' | 'created_at' | 'updated_at'>> = {
        content_type: UDAContentType.ACTIVITY,
        activity_title: (activityData as Partial<ActivityUDAContent>).activity_title,
        activity_description: (activityData as Partial<ActivityUDAContent>).activity_description,
        activity_attachment_url: (activityData as Partial<ActivityUDAContent>).activity_attachment_url,
        activity_completed: (activityData as Partial<ActivityUDAContent>).activity_completed || false,
        teacher_marked_completed: (activityData as Partial<ActivityUDAContent>).teacher_marked_completed || false,
        order: localContents.value.length + 1,
      };
      try {
        await udaStore.addContentToUda(props.udaId, createPayload, file);
      } catch (error) {
        console.error("Errore durante l'aggiunta del contenuto attività UDA:", error);
        // TODO: Gestire l'errore
      }
    } else {
      // La modifica di attività UDA esistenti è gestita dalla modale EditActivityContentModal,
      // che chiama direttamente lo store. Questo blocco non dovrebbe essere raggiunto per modifiche UDA.
      console.warn("handleSaveActivity in UdaContentEditor ha ricevuto un'attività UDA esistente per la gestione. Flusso inaspettato.");
       const existingIndex = localContents.value.findIndex(content =>
            (content.temp_id && content.temp_id === activityData.temp_id) ||
            (content.id && content.id === activityData.id)
        );
        if (existingIndex > -1) {
            localContents.value.splice(existingIndex, 1, { ...activityData } as ContentItem);
             recalculateOrder(); // Ricalcola se modifichiamo localmente
        }
    }
  }
  closeEditActivityModal();
};

// La funzione handleEditContent è definita una sola volta più avanti.
// Rimuoviamo il blocco di codice malformato e duplicato che iniziava qui.

const handleEditContent = (contentToEdit: ContentItem) => {
  if (
    (props.context === 'uda' && contentToEdit.content_type === UDAContentType.NOTE) ||
    (props.context === 'template' && contentToEdit.content_type === UDATemplateContentType.NOTE_TEMPLATE)
  ) {
    editingNoteContent.value = JSON.parse(JSON.stringify(contentToEdit));
    showEditNoteModal.value = true;
  } else if (
    (props.context === 'uda' && contentToEdit.content_type === UDAContentType.ACTIVITY) ||
    (props.context === 'template' && contentToEdit.content_type === UDATemplateContentType.ACTIVITY_TEMPLATE)
  ) {
    editingActivityContent.value = JSON.parse(JSON.stringify(contentToEdit));
    showEditActivityModal.value = true;
  } else if (
    (props.context === 'uda' && (contentToEdit.content_type === UDAContentType.LESSON || contentToEdit.content_type === UDAContentType.QUIZ)) ||
    (props.context === 'template' && (contentToEdit.content_type === UDATemplateContentType.LESSON || contentToEdit.content_type === UDATemplateContentType.QUIZ_TEMPLATE))
  ) {
    const contentId = contentToEdit.temp_id || contentToEdit.id;
    if (contentId === undefined) {
        console.error("Impossibile modificare contenuto Lezione/Quiz: ID o temp_id mancante.", contentToEdit);
        return;
    }
    editingLessonOrQuizContentId.value = contentId;
    showSelectExistingContentModal.value = true; // Apre la modale di selezione per sostituire
  } else {
    console.warn('Tipo di contenuto non gestito per la modifica:', contentToEdit.content_type, contentToEdit);
  }
};

const handleDeleteContent = (contentIdentifier: number | string) => {
  localContents.value = localContents.value.filter(content =>
    (content.id && content.id === contentIdentifier) || (content.temp_id && content.temp_id === contentIdentifier) ? false : true
  );
  recalculateOrder();
};

const handleMoveContent = (contentToMove: ContentItem, direction: -1 | 1) => {
  const index = localContents.value.findIndex(c => (c.temp_id && c.temp_id === contentToMove.temp_id) || (c.id && c.id === contentToMove.id));
  if (index === -1) return;

  const newIndex = index + direction;
  if (newIndex < 0 || newIndex >= localContents.value.length) return;

  // Rimuovi l'elemento e inseriscilo nella nuova posizione
  const item = localContents.value.splice(index, 1)[0];
  localContents.value.splice(newIndex, 0, item);
  
  recalculateOrder();
};

const handleTeacherMarkedCompletedUpdate = (update: { contentId: number; completed: boolean }) => {
  const content = localContents.value.find(c => c.id === update.contentId) as UDAContent | undefined;
  if (content && 'teacher_marked_completed' in content) {
    content.teacher_marked_completed = update.completed;
  }
};

const handleActivityCompletedUpdate = (update: { contentId: number; completed: boolean }) => {
  const content = localContents.value.find(c => c.id === update.contentId) as ActivityUDAContent | undefined;
  if (content && content.content_type === UDAContentType.ACTIVITY) {
    content.activity_completed = update.completed;
  }
};

</script>

<style scoped>
/* Rimosse classi CSS dirette, ora si usa Tailwind */
/* .uda-content-editor { ... } */
/* .empty-state { ... } */
/* .content-item .card-title { ... } */
/* .content-item pre { ... } */

/* Stili aggiuntivi se necessari */
</style>