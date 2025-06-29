 <template>
  <div class="note-content-display p-3 bg-white rounded-b-md"> <!-- Aggiunto padding e sfondo per coerenza -->
    <!-- Il titolo della nota è già gestito dal contentTitle in UdaContentItemRenderer -->
    <!-- <h6 v-if="content.note_title" class="mb-1">{{ content.note_title }}</h6> -->
    <div v-if="props.content.estimated_hours" class="flex text-sm mb-2">
      <strong class="w-24 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
      <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
    </div>
    <div class="flex text-sm mb-2 items-center">
      <strong class="w-24 flex-shrink-0 text-gray-700">Ore Effettive:</strong>
       <div class="flex items-center space-x-2">
         <input
           type="number"
           step="0.1"
           min="0"
           v-model.number="editableActualHours"
           @input="onActualHoursInput"
           class="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
           placeholder="Ore"
         />
         <span v-if="isSaving" class="text-xs text-gray-500">Salvataggio...</span>
       </div>
    </div>

    <!-- Modifica contenuto nota -->
    <div class="mt-2"> <!-- Aggiunto margin top per separare dalla sezione ore effettive -->
      <div v-if="!isEditingContent" @click="startEditingContent" class="note-body prose prose-sm max-w-none cursor-pointer min-h-[50px]">
        <div v-if="content.note_content" v-html="content.note_content"></div>
        <p v-else class="text-sm text-gray-500 italic">Clicca per aggiungere un contenuto alla nota.</p>
      </div>
      <div v-else>
        <WysiwygEditor
          v-model="editableContent"
          :editable="true"
        />
        <div class="mt-2 flex justify-start space-x-2">
          <button @click="cancelEditingContent" class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded">Annulla</button>
          <button @click="saveContentChanges" class="px-3 py-1 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded">Salva</button>
        </div>
        <!-- Potremmo aggiungere un piccolo spinner/messaggio di salvataggio qui durante il saveChanges -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType } from 'vue';
import type { NoteUDAContent, UDAContent } from '@/types/uda'; // Assicurati che UDAContent sia importato se necessario per lo store
import WysiwygEditor from '@/components/WysiwygEditor.vue';
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

// State per la modifica del contenuto della nota
const isEditingContent = ref(false);
const editableContent = ref(props.content.note_content || '');
const originalContent = ref(props.content.note_content || '');

// State per la modifica delle ore effettive
const editableActualHours = ref<number | undefined | null>(props.content.actual_hours);
const isSaving = ref(false);
let debounceTimer: number | undefined;


watch(() => props.content.note_content, (newVal) => {
  if (!isEditingContent.value) {
    editableContent.value = newVal || '';
    originalContent.value = newVal || '';
  }
});

watch(() => props.content.actual_hours, (newVal) => {
    editableActualHours.value = newVal;
});

// --- Metodi per la modifica del contenuto della nota ---
const startEditingContent = () => {
  originalContent.value = props.content.note_content || '';
  editableContent.value = props.content.note_content || '';
  isEditingContent.value = true;
};

const saveContentChanges = async () => {
  console.log('[NoteContentDisplay] saveContentChanges called. editableContent:', editableContent.value);

  if (editableContent.value !== originalContent.value) {
    if (typeof props.content.id === 'undefined' || typeof props.content.uda_id === 'undefined') {
      console.error('Cannot update note content: content ID or UDA ID is undefined.');
      // TODO: Mostrare un messaggio di errore all'utente
      return;
    }
    try {
      const updatedData: Partial<NoteUDAContent> = {
        note_content: editableContent.value,
      };
      await udaStore.updateContentInUda(props.content.uda_id, props.content.id, updatedData as UDAContent);
      originalContent.value = editableContent.value;
      isEditingContent.value = false;
    } catch (error) {
      console.error('Failed to save note content:', error);
      // TODO: Gestire lo stato di errore per l'UI
    }
  } else {
    isEditingContent.value = false;
  }
};

const cancelEditingContent = () => {
  editableContent.value = originalContent.value;
  isEditingContent.value = false;
};

// --- Metodi per la modifica delle ore effettive ---
const onActualHoursInput = () => {
  clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(() => {
    saveActualHours();
  }, 1500); // 1.5 secondi di debounce
};

const saveActualHours = async () => {
  isSaving.value = true;
  console.log('[NoteContentDisplay] saveActualHours called. editableActualHours:', editableActualHours.value);
  const valueToSave = (typeof editableActualHours.value === 'undefined' || editableActualHours.value === null)
                      ? null
                      : Number(editableActualHours.value);

  if (typeof props.content.id === 'undefined' || typeof props.content.uda_id === 'undefined') {
    console.error('Cannot update actual hours: content ID or UDA ID is undefined.');
    isSaving.value = false;
    // TODO: Mostrare un messaggio di errore all'utente
    return;
  }

  try {
    const updatedData: Partial<Pick<NoteUDAContent, 'actual_hours'>> = {
      actual_hours: valueToSave,
    };
    await udaStore.updateContentInUda(props.content.uda_id, props.content.id, updatedData as UDAContent);
  } catch (error) {
    console.error('Failed to save actual hours:', error);
    // TODO: Gestire lo stato di errore per l'UI
  } finally {
    isSaving.value = false;
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