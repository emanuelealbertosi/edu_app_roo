<template>
  <div class="activity-content-display p-3 bg-white rounded-b-md space-y-3 text-sm">
    <!-- Il titolo è gestito da UdaContentItemRenderer -->
    
   <div class="flex items-center">
     <strong class="w-28 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
     <div class="flex items-center space-x-2">
       <input
         type="number"
         step="0.1"
         min="0"
         v-model.number="editableEstimatedHours"
         @input="onEstimatedHoursInput"
         class="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
         placeholder="Ore"
       />
       <span v-if="isSavingEstimatedHours" class="text-xs text-gray-500">Salvataggio...</span>
     </div>
   </div>
   <div class="flex items-center">
     <strong class="w-28 flex-shrink-0 text-gray-700">Ore Effettive:</strong>
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
       <span v-if="isSavingActualHours" class="text-xs text-gray-500">Salvataggio...</span>
     </div>
   </div>

    <!-- Modifica descrizione attività -->
    <div class="mt-2"> <!-- Aggiunto margin top per separare -->
      <div v-if="!isEditingDescription" @click="startEditingDescription" class="activity-description prose prose-sm max-w-none cursor-pointer min-h-[50px]">
        <div v-if="content.activity_description" v-html="content.activity_description"></div>
        <p v-else class="text-sm text-gray-500 italic">Clicca per aggiungere una descrizione all'attività.</p>
      </div>
      <div v-else>
        <WysiwygEditor
          v-model="editableDescription"
          :editable="true"
        />
        <div class="mt-2 flex justify-start space-x-2">
          <button @click="cancelDescriptionEditing" class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded">Annulla</button>
          <button @click="saveDescriptionChanges" class="px-3 py-1 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded">Salva</button>
        </div>
      </div>
    </div>
    
    
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType } from 'vue';
import type { ActivityUDAContent, UDAContent } from '@/types/uda';
import WysiwygEditor from '@/components/WysiwygEditor.vue';
import { useUdaStore } from '@/stores/udaStore';

const props = defineProps({
  content: {
    type: Object as PropType<ActivityUDAContent & { uda_id: number }>, // Aggiunto uda_id per l'update
    required: true
  }
});

const udaStore = useUdaStore();

// State per la modifica della descrizione
const isEditingDescription = ref(false);
const editableDescription = ref(props.content.activity_description || '');
const originalDescription = ref(props.content.activity_description || '');

// State per la modifica delle ore effettive
const editableActualHours = ref<number | undefined | null>(props.content.actual_hours);
const isSavingActualHours = ref(false);
let debounceActualHoursTimer: number | undefined;

// State per la modifica delle ore stimate
const editableEstimatedHours = ref<number | undefined | null>(props.content.estimated_hours);
const isSavingEstimatedHours = ref(false);
let debounceEstimatedHoursTimer: number | undefined;


watch(() => props.content.activity_description, (newVal) => {
  if (!isEditingDescription.value) {
    editableDescription.value = newVal || '';
    originalDescription.value = newVal || '';
  }
});

watch(() => props.content.actual_hours, (newVal) => {
  editableActualHours.value = newVal;
});

watch(() => props.content.estimated_hours, (newVal) => {
  editableEstimatedHours.value = newVal;
});

// --- Metodi per la modifica della descrizione ---
const startEditingDescription = () => {
  originalDescription.value = props.content.activity_description || '';
  editableDescription.value = props.content.activity_description || '';
  isEditingDescription.value = true;
};

const saveDescriptionChanges = async () => {
  console.log('[ActivityContentDisplay] saveDescriptionChanges called. editableDescription:', editableDescription.value);

  if (editableDescription.value !== originalDescription.value) {
    if (typeof props.content.id === 'undefined' || typeof props.content.uda_id === 'undefined') {
      console.error('Cannot update activity description: content ID or UDA ID is undefined.');
      // TODO: Mostrare un messaggio di errore all'utente
      return;
    }
    try {
      const updatedData: Partial<ActivityUDAContent> = {
        activity_description: editableDescription.value,
      };
      await udaStore.updateContentInUda(props.content.uda_id, props.content.id, updatedData as UDAContent);
      originalDescription.value = editableDescription.value;
      isEditingDescription.value = false;
    } catch (error) {
      console.error('Failed to save activity description:', error);
      // TODO: Gestire lo stato di errore per l'UI
    }
  } else {
    isEditingDescription.value = false;
  }
};

const cancelDescriptionEditing = () => {
  editableDescription.value = originalDescription.value;
  isEditingDescription.value = false;
};

// --- Metodi per la modifica delle ore effettive ---
const onActualHoursInput = () => {
  clearTimeout(debounceActualHoursTimer);
  debounceActualHoursTimer = window.setTimeout(() => {
    saveActualHours();
  }, 1500);
};

const saveActualHours = async () => {
  isSavingActualHours.value = true;
  const valueToSave = (typeof editableActualHours.value === 'undefined' || editableActualHours.value === null)
                      ? null
                      : Number(editableActualHours.value);

  if (typeof props.content.id === 'undefined' || typeof props.content.uda_id === 'undefined') {
    console.error('Cannot update actual hours: content ID or UDA ID is undefined.');
    isSavingActualHours.value = false;
    return;
  }
  try {
    const updatedData: Partial<Pick<ActivityUDAContent, 'actual_hours'>> = {
      actual_hours: valueToSave,
    };
    await udaStore.updateContentInUda(props.content.uda_id, props.content.id, updatedData as UDAContent);
  } catch (error) {
    console.error('Failed to save actual hours:', error);
  } finally {
    isSavingActualHours.value = false;
  }
};

// --- Metodi per la modifica delle ore stimate ---
const onEstimatedHoursInput = () => {
  clearTimeout(debounceEstimatedHoursTimer);
  debounceEstimatedHoursTimer = window.setTimeout(() => {
    saveEstimatedHours();
  }, 1500);
};

const saveEstimatedHours = async () => {
  isSavingEstimatedHours.value = true;
  const valueToSave = (typeof editableEstimatedHours.value === 'undefined' || editableEstimatedHours.value === null)
                      ? null
                      : Number(editableEstimatedHours.value);

  if (typeof props.content.id === 'undefined' || typeof props.content.uda_id === 'undefined') {
    console.error('Cannot update estimated hours: content ID or UDA ID is undefined.');
    isSavingEstimatedHours.value = false;
    return;
  }
  try {
    const updatedData: Partial<Pick<ActivityUDAContent, 'estimated_hours'>> = {
      estimated_hours: valueToSave,
    };
    await udaStore.updateContentInUda(props.content.uda_id, props.content.id, updatedData as UDAContent);
  } catch (error) {
    console.error('Failed to save estimated hours:', error);
  } finally {
    isSavingEstimatedHours.value = false;
  }
};
</script>

<style scoped>
.activity-content-display {
  font-size: 0.9rem;
}
/* Stili specifici per .activity-description :deep(p:last-child) rimossi per coerenza con NoteContentDisplay */
</style>