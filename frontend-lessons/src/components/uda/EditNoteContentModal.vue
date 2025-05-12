<template>
  <div class="fixed inset-0 bg-gray-800 bg-opacity-75 flex justify-center items-center z-50" @click.self="closeModal">
    <div class="bg-white rounded-lg shadow-xl p-6 mx-4 sm:mx-auto w-full max-w-lg flex flex-col max-h-[90vh]">
      <div class="flex justify-between items-center pb-4 border-b border-gray-200 mb-4">
        <h5 class="text-xl font-semibold text-gray-800">{{ isEditing ? 'Modifica Nota' : 'Aggiungi Nuova Nota' }}</h5>
        <button type="button" class="text-gray-400 hover:text-gray-600 text-2xl leading-none" @click="closeModal" aria-label="Close">&times;</button>
      </div>
      <div class="overflow-y-auto flex-grow pr-2 space-y-4">
        <form @submit.prevent="saveNote" class="space-y-4">
          <div>
            <label for="noteTitle" class="block text-sm font-medium text-gray-700 mb-1">Titolo Nota</label>
            <input type="text" id="noteTitle" v-model="editableContent.title" required
                   class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
          </div>
          <div>
            <label for="noteContent" class="block text-sm font-medium text-gray-700 mb-1">Contenuto Nota</label>
            <textarea id="noteContent" rows="5" v-model="editableContent.content"
                      class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2"></textarea>
          </div>
          <div>
            <label for="noteEstimatedHours" class="block text-sm font-medium text-gray-700 mb-1">Tempo Stimato (ore)</label>
            <input type="number" id="noteEstimatedHours" v-model.number="editableContent.estimated_hours" step="0.1" min="0"
                   placeholder="Es. 1.5"
                   class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
          </div>
        </form>
      </div>
      <div class="flex justify-end pt-4 border-t border-gray-200 mt-4 space-x-3">
        <button type="button"
                class="border border-gray-300 hover:bg-gray-100 text-gray-700 font-medium py-2 px-4 rounded-md shadow-sm text-sm"
                @click="closeModal">
          Annulla
        </button>
        <button type="button"
                class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md shadow-sm text-sm"
                @click="saveNote">
          Salva Nota
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType, computed } from 'vue';
import type { NoteUDAContent, NoteTemplateUDAContent, UDAContentType, UDATemplateContentType } from '@/types/uda';

type EditableNoteType = Partial<NoteUDAContent | NoteTemplateUDAContent> & {
  title?: string;
  content?: string;
  estimated_hours?: number | null; // Aggiunto
};

const props = defineProps({
  modelValue: {
    type: Object as PropType<NoteUDAContent | NoteTemplateUDAContent | null>,
    default: null
  },
  context: {
    type: String as PropType<'uda' | 'template'>,
    required: true
  }
});

const emit = defineEmits(['update:modelValue', 'save', 'close']);

const editableContent = ref<EditableNoteType>({ title: '', content: '', estimated_hours: null }); // Inizializzato

const isEditing = computed(() => !!(props.modelValue && (props.modelValue.id || props.modelValue.temp_id)));

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    if (props.context === 'template') {
      const templateNote = newValue as NoteTemplateUDAContent;
      editableContent.value = {
        ...templateNote,
        title: templateNote.note_template_title || '',
        content: templateNote.note_template_content || '',
        estimated_hours: templateNote.estimated_hours // Aggiunto
      };
    } else {
      const udaNote = newValue as NoteUDAContent;
      editableContent.value = {
        ...udaNote,
        title: udaNote.note_title || '',
        content: udaNote.note_content || '',
        estimated_hours: udaNote.estimated_hours // Aggiunto
      };
    }
  } else {
    editableContent.value = {
      title: '',
      content: '',
      estimated_hours: null // Aggiunto reset
    };
  }
}, { immediate: true, deep: true });

const closeModal = () => {
  emit('close');
};

const saveNote = () => {
  let finalContent: Partial<NoteUDAContent | NoteTemplateUDAContent>;

  if (props.context === 'template') {
    finalContent = {
      ...(props.modelValue || {}),
      note_template_title: editableContent.value.title,
      note_template_content: editableContent.value.content,
      estimated_hours: editableContent.value.estimated_hours || null, // Aggiunto
      content_type: 'NOTE_TEMPLATE' as UDATemplateContentType.NOTE_TEMPLATE,
    } as Partial<NoteTemplateUDAContent>;
  } else {
    finalContent = {
      ...(props.modelValue || {}),
      note_title: editableContent.value.title,
      note_content: editableContent.value.content,
      estimated_hours: editableContent.value.estimated_hours || null, // Aggiunto
      content_type: 'NOTE' as UDAContentType.NOTE,
    } as Partial<NoteUDAContent>;
  }
  
  if (!finalContent.id && !finalContent.temp_id) {
    // Gestito dal genitore
  }

  emit('save', finalContent);
  closeModal();
};

</script>

<style scoped>
/* Tutti gli stili sono ora gestiti da classi Tailwind nel template */
</style>