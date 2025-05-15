 <template>
  <div class="note-content-display p-3 bg-white rounded-b-md"> <!-- Aggiunto padding e sfondo per coerenza -->
    <!-- Il titolo della nota è già gestito dal contentTitle in UdaContentItemRenderer -->
    <!-- <h6 v-if="content.note_title" class="mb-1">{{ content.note_title }}</h6> -->
    <div v-if="props.content.estimated_hours" class="flex text-sm mb-2">
        <strong class="w-24 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
    </div>
    <div v-if="!isEditing" @click="startEditing" class="note-body prose prose-sm max-w-none cursor-pointer min-h-[50px]">
      <div v-if="content.note_content" v-html="content.note_content"></div>
      <p v-else class="text-sm text-gray-500 italic">Clicca per aggiungere un contenuto alla nota.</p>
    </div>
    <div v-else>
      <WysiwygEditor
        v-model="editableContent"
        @blur="handleBlur"
        :editable="true"
      />
      <!-- Potremmo aggiungere un piccolo spinner/messaggio di salvataggio qui -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType } from 'vue';
import type { NoteUDAContent, UDAContent } from '@/types/uda'; // Assicurati che UDAContent sia importato se necessario per lo store
import WysiwygEditor from '@/components/common/WysiwygEditor.vue';
import { useUdaStore } from '@/stores/udaStore';

const props = defineProps({
  content: {
    type: Object as PropType<NoteUDAContent & { uda_id: number }>, // Aggiunto uda_id per l'update
    required: true
  },
  // Potrebbe essere necessario passare l'udaId se non è in content
  // udaId: {
  //   type: Number,
  //   required: true
  // }
});

const udaStore = useUdaStore();

const isEditing = ref(false);
const editableContent = ref(props.content.note_content || '');
const originalContent = ref(props.content.note_content || '');

watch(() => props.content.note_content, (newVal) => {
  if (!isEditing.value) {
    editableContent.value = newVal || '';
    originalContent.value = newVal || '';
  }
});

const startEditing = () => {
  originalContent.value = props.content.note_content || '';
  editableContent.value = props.content.note_content || ''; // Assicura che l'editor parta con il contenuto attuale
  isEditing.value = true;
  // Non è necessario focus programmatico qui perché WysiwygEditor dovrebbe gestirlo
};

const handleBlur = async () => {
  console.log('[NoteContentDisplay] handleBlur called. editableContent:', editableContent.value, 'originalContent:', originalContent.value);
  // Salva il valore di originalContent all'inizio del blur, che riflette lo stato prima dell'editing corrente.
  const initialOriginalContent = originalContent.value;

  if (editableContent.value !== initialOriginalContent) {
    console.log('Content changed, attempting to save...');
    if (typeof props.content.id === 'undefined') {
      console.error('Cannot update content: content ID is undefined.');
      editableContent.value = initialOriginalContent; // Revert all'originale prima dell'editing
      isEditing.value = false;
      // TODO: Mostrare un messaggio di errore all'utente
      return;
    }
    try {
      const updatedData: Partial<NoteUDAContent> = {
        note_content: editableContent.value,
      };

      console.log(`[NoteContentDisplay] About to update. uda_id: ${props.content.uda_id}, content_id: ${props.content.id}`);
      if (typeof props.content.uda_id === 'undefined') {
        console.error('[NoteContentDisplay] CRITICAL: props.content.uda_id is undefined before calling store action!');
        editableContent.value = initialOriginalContent; // Revert
        isEditing.value = false;
        return;
      }

      await udaStore.updateContentInUda(props.content.uda_id, props.content.id, updatedData as UDAContent);
      console.log('Content saved successfully. Waiting for prop update.');
      // Non modificare editableContent o originalContent qui.
      // Il watch su props.content.note_content dovrebbe sincronizzarli.
    } catch (error) {
      console.error('Failed to save note content:', error);
      editableContent.value = initialOriginalContent; // Revert all'originale prima dell'editing
      // Potrebbe essere utile notificare l'utente dell'errore
    } finally {
      isEditing.value = false;
    }
  } else {
    console.log('Content not changed.');
    isEditing.value = false;
  }
};

</script>

<style scoped>
.note-content-display {
  font-size: 0.9rem;
}
/* Rimuovi stili specifici di prose se WysiwygEditor li gestisce o se vuoi uno stile più pulito per v-html */
/* .note-body :deep(p:last-child) {
  margin-bottom: 0;
}
.note-body :deep(ul), .note-body :deep(ol) {
  padding-left: 1.2rem;
} */
</style>