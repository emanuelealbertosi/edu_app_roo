<template>
  <div class="fixed inset-0 bg-gray-800 bg-opacity-75 flex justify-center items-center z-50" @click.self="closeModal">
    <div class="bg-white rounded-lg shadow-xl p-6 mx-4 sm:mx-auto w-[60vw] min-h-[50vh] flex flex-col">
      <div class="flex justify-between items-center pb-4 border-b border-gray-200 mb-4">
        <h5 class="text-xl font-semibold text-gray-800">{{ isEditing ? 'Modifica Attività' : 'Aggiungi Nuova Attività' }}</h5>
        <button type="button" class="text-gray-400 hover:text-gray-600 text-2xl leading-none" @click="closeModal" aria-label="Close">&times;</button>
      </div>
      <div class="overflow-y-auto flex-grow pr-2 space-y-4">
        <form @submit.prevent="saveActivity" class="space-y-4">
          <div>
            <label for="activityTitle" class="block text-sm font-medium text-gray-700 mb-1">Titolo Attività</label>
            <input type="text" id="activityTitle" v-model="editableContent.title" required
                   class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
          </div>
          <div>
            <label for="activityDescription" class="block text-sm font-medium text-gray-700 mb-1">Descrizione Attività</label>
            <WysiwygEditor
              id="activityDescription"
              v-model="editableContent.description"
              :editable="true"
              class="mt-1"
            />
          </div>
          <template v-if="props.context === 'uda'">
            <div>
              <label for="activityAttachment" class="block text-sm font-medium text-gray-700 mb-1">Allegato Attività</label>
              <FileUpload
                ref="fileUploadComponent"
                :current-file-url="editableContent.attachmentUrl"
                @file-selected="handleFileSelected"
                @file-removed="handleFileRemoved"
              />
              <!-- <small class="form-text text-muted">L'upload effettivo del file avverrà al salvataggio.</small> -->
            </div>
            <div>
              <label for="activityEstimatedHours" class="block text-sm font-medium text-gray-700 mb-1">Tempo Stimato (ore)</label>
              <input type="number" id="activityEstimatedHours" v-model.number="editableContent.estimated_hours" step="0.1" min="0"
                     placeholder="Es. 1.5"
                     class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
           </div>
           <div>
             <label for="activityActualHours" class="block text-sm font-medium text-gray-700 mb-1">Tempo Effettivo (ore)</label>
             <input type="number" id="activityActualHours" v-model.number="editableContent.actual_hours" step="0.1" min="0"
                    placeholder="Es. 1.0"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
           </div>
         </template>
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
                @click="saveActivity">
          Salva Attività
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType, computed } from 'vue';
import FileUpload from './FileUpload.vue';
import WysiwygEditor from '@/components/WysiwygEditor.vue'; // Import WysiwygEditor
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
  estimated_hours?: number | null;
  actual_hours?: number | null; // Aggiunto per ore effettive
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

const editableContent = ref<EditableActivityType>({ title: '', description: '', estimated_hours: null, actual_hours: null }); // Inizializzato
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
        description: templateActivity.activity_template_description || '',
        estimated_hours: templateActivity.estimated_hours,
        // actual_hours non è pertinente per i template
      };
    } else {
      const udaActivity = newValue as ActivityUDAContent;
      editableContent.value = {
        ...udaActivity,
        title: udaActivity.activity_title || '',
        description: udaActivity.activity_description || '',
        attachmentUrl: udaActivity.activity_attachment_url || '',
        estimated_hours: udaActivity.estimated_hours,
        actual_hours: udaActivity.actual_hours // Aggiunto
      };
    }
  } else {
    editableContent.value = {
      title: '',
      description: '',
      attachmentUrl: '',
      estimated_hours: null,
      actual_hours: null // Aggiunto reset
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
      estimated_hours: editableContent.value.estimated_hours || null,
      // actual_hours non pertinente per template
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
      teacher_marked_completed: currentActivityData?.teacher_marked_completed ?? false,
      estimated_hours: editableContent.value.estimated_hours || null,
      actual_hours: editableContent.value.actual_hours || null, // Aggiunto
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
/* Tutti gli stili sono ora gestiti da classi Tailwind nel template */
</style>