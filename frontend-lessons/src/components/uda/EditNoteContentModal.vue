<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-content edit-note-modal-content">
      <div class="modal-header-custom">
        <h5 class="modal-title-custom">{{ isEditing ? 'Modifica Nota' : 'Aggiungi Nuova Nota' }}</h5>
        <button type="button" class="button-close-custom" @click="closeModal" aria-label="Close">&times;</button>
      </div>
      <div class="modal-body-custom">
        <form @submit.prevent="saveNote">
          <div class="form-group">
            <label for="noteTitle" class="form-label">Titolo Nota</label>
            <input type="text" class="form-control" id="noteTitle" v-model="editableContent.title" required>
          </div>
          <div class="form-group">
            <label for="noteContent" class="form-label">Contenuto Nota</label>
            <textarea class="form-control" id="noteContent" rows="5" v-model="editableContent.content"></textarea>
          </div>
        </form>
      </div>
      <div class="modal-footer-custom">
        <button type="button" class="button-cancel" @click="closeModal">Annulla</button>
        <button type="button" class="button-save" @click="saveNote">Salva Nota</button>
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

const editableContent = ref<EditableNoteType>({ title: '', content: '' });

const isEditing = computed(() => !!(props.modelValue && (props.modelValue.id || props.modelValue.temp_id)));

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    if (props.context === 'template') {
      const templateNote = newValue as NoteTemplateUDAContent;
      editableContent.value = {
        ...templateNote,
        title: templateNote.note_template_title || '',
        content: templateNote.note_template_content || ''
      };
    } else {
      const udaNote = newValue as NoteUDAContent;
      editableContent.value = {
        ...udaNote,
        title: udaNote.note_title || '',
        content: udaNote.note_content || ''
      };
    }
  } else {
    editableContent.value = {
      title: '',
      content: ''
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
      content_type: 'NOTE_TEMPLATE' as UDATemplateContentType.NOTE_TEMPLATE,
    } as Partial<NoteTemplateUDAContent>;
  } else {
    finalContent = {
      ...(props.modelValue || {}),
      note_title: editableContent.value.title,
      note_content: editableContent.value.content,
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
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.6); display: flex;
  justify-content: center; align-items: center; z-index: 1000;
}
.edit-note-modal-content { /* Classe specifica */
  background-color: white; padding: 1.5rem; border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  min-width: 400px; max-width: 600px;
  display: flex; flex-direction: column;
}

.modal-header-custom {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 1rem; border-bottom: 1px solid #eee; margin-bottom: 1rem;
}
.modal-title-custom {
  font-size: 1.25rem; font-weight: 600; margin: 0;
}
.button-close-custom {
  background: none; border: none; font-size: 1.5rem; cursor: pointer;
  padding: 0.5rem; line-height: 1;
}

.modal-body-custom {
  /* Non serve overflow-y: auto qui, il contenuto è limitato */
}

.form-group { margin-bottom: 1rem; }
.form-label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
.form-control {
  width: 100%; padding: 0.75rem; border: 1px solid #ccc;
  border-radius: 4px; box-sizing: border-box;
}
textarea.form-control { resize: vertical; }


.modal-footer-custom {
  display: flex; justify-content: flex-end;
  padding-top: 1rem; border-top: 1px solid #eee; margin-top: 1rem;
}
.modal-footer-custom button {
  padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer;
  font-size: 0.9rem; margin-left: 0.5rem; border: none;
}
.button-cancel { background-color: #6c757d; color: white; }
.button-cancel:hover { background-color: #5a6268; }
.button-save { background-color: #007bff; color: white; }
.button-save:hover:not(:disabled) { background-color: #0056b3; }
.button-save:disabled { background-color: #ccc; cursor: not-allowed; }
</style>