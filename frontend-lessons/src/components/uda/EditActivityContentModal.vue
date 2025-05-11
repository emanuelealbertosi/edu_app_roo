<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-content edit-activity-modal-content">
      <div class="modal-header-custom">
        <h5 class="modal-title-custom">{{ isEditing ? 'Modifica Attività' : 'Aggiungi Nuova Attività' }}</h5>
        <button type="button" class="button-close-custom" @click="closeModal" aria-label="Close">&times;</button>
      </div>
      <div class="modal-body-custom">
        <form @submit.prevent="saveActivity">
          <div class="form-group">
            <label for="activityTitle" class="form-label">Titolo Attività</label>
            <input type="text" class="form-control" id="activityTitle" v-model="editableContent.title" required>
          </div>
          <div class="form-group">
            <label for="activityDescription" class="form-label">Descrizione Attività</label>
            <textarea class="form-control" id="activityDescription" rows="5" v-model="editableContent.description"></textarea>
          </div>
          <template v-if="props.context === 'uda'">
            <div class="form-group">
              <label for="activityAttachment" class="form-label">Allegato Attività</label>
              <FileUpload
                ref="fileUploadComponent"
                :current-file-url="editableContent.attachmentUrl"
                @file-selected="handleFileSelected"
                @file-removed="handleFileRemoved"
              />
              <!-- <small class="form-text text-muted">L'upload effettivo del file avverrà al salvataggio.</small> -->
            </div>
            <div class="form-group form-check">
              <input type="checkbox" class="form-check-input" id="activityCompleted" v-model="editableContent.completedByStudent">
              <label class="form-check-label" for="activityCompleted">Attività Completata (dallo studente)</label>
            </div>
          </template>
        </form>
      </div>
      <div class="modal-footer-custom">
        <button type="button" class="button-cancel" @click="closeModal">Annulla</button>
        <button type="button" class="button-save" @click="saveActivity">Salva Attività</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType, computed } from 'vue';
import FileUpload from './FileUpload.vue';
import { useUdaStore } from '@/stores/udaStore';
import {
  type ActivityUDAContent,
  type ActivityTemplateUDAContent,
  UDAContentType,
  UDATemplateContentType,
  type UDAContent
} from '@/types/uda';

type EditableActivityType = Partial<ActivityUDAContent | ActivityTemplateUDAContent> & {
  title?: string;
  description?: string;
  attachmentUrl?: string;
  completedByStudent?: boolean;
};

const props = defineProps({
  modelValue: {
    type: Object as PropType<ActivityUDAContent | ActivityTemplateUDAContent | null>,
    default: null
  },
  context: {
    type: String as PropType<'uda' | 'template'>,
    required: true
  },
  udaId: {
    type: Number,
    required: false
  }
});

const emit = defineEmits(['update:modelValue', 'save', 'close']);
const udaStore = useUdaStore();

const editableContent = ref<EditableActivityType>({ title: '', description: '' });
const fileUploadComponent = ref<InstanceType<typeof FileUpload> | null>(null);
const selectedActivityFileObject = ref<File | null>(null);

const isEditing = computed(() => !!(props.modelValue && (props.modelValue.id || props.modelValue.temp_id)));

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    if (props.context === 'template') {
      const templateActivity = newValue as ActivityTemplateUDAContent;
      editableContent.value = {
        ...templateActivity,
        title: templateActivity.activity_template_title || '',
        description: templateActivity.activity_template_description || ''
      };
    } else {
      const udaActivity = newValue as ActivityUDAContent;
      editableContent.value = {
        ...udaActivity,
        title: udaActivity.activity_title || '',
        description: udaActivity.activity_description || '',
        attachmentUrl: udaActivity.activity_attachment_url || '',
        completedByStudent: udaActivity.activity_completed || false
      };
    }
  } else {
    editableContent.value = {
      title: '',
      description: '',
      attachmentUrl: '',
      completedByStudent: false,
    };
    selectedActivityFileObject.value = null;
    fileUploadComponent.value?.reset();
  }
}, { immediate: true, deep: true });

const handleFileSelected = (file: File) => {
  selectedActivityFileObject.value = file;
};

const handleFileRemoved = () => {
  selectedActivityFileObject.value = null;
  editableContent.value.attachmentUrl = ''; // Pulisce l'URL se il file viene rimosso
};

const closeModal = () => {
  emit('close');
};

const saveActivity = async () => {
  let dataToSave: Partial<ActivityUDAContent | ActivityTemplateUDAContent>;

  if (props.context === 'template') {
    dataToSave = {
      ...(props.modelValue || {}),
      activity_template_title: editableContent.value.title,
      activity_template_description: editableContent.value.description,
      content_type: UDATemplateContentType.ACTIVITY_TEMPLATE,
    } as Partial<ActivityTemplateUDAContent>;
    emit('save', { activityData: dataToSave, file: undefined });
  } else {
    const currentActivityData = props.modelValue as ActivityUDAContent | null;
    dataToSave = {
      ...(currentActivityData || {}),
      activity_title: editableContent.value.title,
      activity_description: editableContent.value.description,
      activity_attachment_url: editableContent.value.attachmentUrl,
      activity_completed: editableContent.value.completedByStudent,
      teacher_marked_completed: currentActivityData?.teacher_marked_completed ?? false,
      content_type: UDAContentType.ACTIVITY,
    } as Partial<ActivityUDAContent>;

    if (!isEditing.value && dataToSave.teacher_marked_completed === undefined) {
        (dataToSave as Partial<ActivityUDAContent>).teacher_marked_completed = false;
    }
    
    if (isEditing.value && currentActivityData?.id && props.udaId) {
      try {
        await udaStore.updateContentInUda(
          props.udaId,
          currentActivityData.id,
          dataToSave as Partial<Omit<UDAContent, 'id' | 'uda_id' | 'created_at' | 'updated_at'>>,
          selectedActivityFileObject.value || undefined
        );
      } catch (error) {
        console.error("Errore durante l'aggiornamento dell'attività UDA:", error);
      }
    } else {
      emit('save', { activityData: dataToSave, file: selectedActivityFileObject.value || undefined });
    }
  }
  closeModal();
};

</script>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.6); display: flex;
  justify-content: center; align-items: center; z-index: 1000;
}
.edit-activity-modal-content { /* Classe specifica */
  background-color: white; padding: 1.5rem; border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  min-width: 400px; max-width: 600px;
  display: flex; flex-direction: column;
  max-height: 90vh;
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
  overflow-y: auto; /* Abilita scroll per il corpo se necessario */
  padding-right: 0.5rem; /* Spazio per la scrollbar se appare */
  flex-grow: 1;
}

.form-group { margin-bottom: 1rem; }
.form-label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
.form-control {
  width: 100%; padding: 0.75rem; border: 1px solid #ccc;
  border-radius: 4px; box-sizing: border-box;
}
textarea.form-control { resize: vertical; }
.form-check { display: flex; align-items: center; }
.form-check-input { margin-right: 0.5rem; }
.form-check-label { margin-bottom: 0; }


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