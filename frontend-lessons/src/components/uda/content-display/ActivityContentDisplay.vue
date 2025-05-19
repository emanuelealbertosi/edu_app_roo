<template>
  <div class="activity-content-display p-3 bg-white rounded-b-md space-y-3 text-sm">
    <!-- Il titolo è gestito da UdaContentItemRenderer -->
    
    <div v-if="props.content.estimated_hours" class="flex">
      <strong class="w-28 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
      <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
    </div>
    <div class="flex items-center">
      <strong class="w-28 flex-shrink-0 text-gray-700">Ore Effettive:</strong>
      <div v-if="!isEditingActualHours" class="flex items-center">
        <span class="text-gray-600 mr-2">{{ props.content.actual_hours !== null && typeof props.content.actual_hours !== 'undefined' ? props.content.actual_hours + 'h' : 'N/D' }}</span>
        <button @click="startEditingActualHours" class="text-xs text-blue-500 hover:text-blue-700">(modifica)</button>
      </div>
      <div v-else class="flex items-center space-x-2">
        <input
          type="number"
          step="0.1"
          min="0"
          v-model.number="editableActualHours"
          class="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
          placeholder="Ore"
        />
        <button @click="saveActualHours" class="px-2 py-1 text-xs bg-green-500 hover:bg-green-600 text-white rounded">Salva</button>
        <button @click="cancelEditingActualHours" class="px-2 py-1 text-xs bg-gray-300 hover:bg-gray-400 rounded">Annulla</button>
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
    
    <div v-if="content.activity_attachment_url" class="flex">
      <strong class="w-28 flex-shrink-0 text-gray-700">Allegato:</strong>
      <a :href="content.activity_attachment_url" target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:text-indigo-800 truncate">
        {{ content.activity_attachment_url.split('/').pop() || 'Vedi allegato' }}
      </a>
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
const isEditingActualHours = ref(false);
const editableActualHours = ref<number | undefined | null>(props.content.actual_hours);
const originalActualHours = ref<number | undefined | null>(props.content.actual_hours);


watch(() => props.content.activity_description, (newVal) => {
  if (!isEditingDescription.value) {
    editableDescription.value = newVal || '';
    originalDescription.value = newVal || '';
  }
});

watch(() => props.content.actual_hours, (newVal) => {
  if (!isEditingActualHours.value) {
    editableActualHours.value = newVal;
    originalActualHours.value = newVal;
  }
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
const startEditingActualHours = () => {
  originalActualHours.value = props.content.actual_hours;
  editableActualHours.value = props.content.actual_hours;
  isEditingActualHours.value = true;
};

const saveActualHours = async () => {
  console.log('[ActivityContentDisplay] saveActualHours called. editableActualHours:', editableActualHours.value);
  const valueToSave = (typeof editableActualHours.value === 'undefined' || editableActualHours.value === null)
                      ? null
                      : Number(editableActualHours.value);

  if (valueToSave !== originalActualHours.value) {
    if (typeof props.content.id === 'undefined' || typeof props.content.uda_id === 'undefined') {
      console.error('Cannot update actual hours: content ID or UDA ID is undefined.');
      // TODO: Mostrare un messaggio di errore all'utente
      return;
    }
    try {
      const updatedData: Partial<Pick<ActivityUDAContent, 'actual_hours'>> = {
        actual_hours: valueToSave,
      };
      await udaStore.updateContentInUda(props.content.uda_id, props.content.id, updatedData as UDAContent);
      originalActualHours.value = valueToSave;
      isEditingActualHours.value = false;
    } catch (error) {
      console.error('Failed to save actual hours:', error);
      // TODO: Gestire lo stato di errore per l'UI
    }
  } else {
    isEditingActualHours.value = false;
  }
};

const cancelEditingActualHours = () => {
  editableActualHours.value = originalActualHours.value;
  isEditingActualHours.value = false;
};

</script>

<style scoped>
.activity-content-display {
  font-size: 0.9rem;
}
/* Stili specifici per .activity-description :deep(p:last-child) rimossi per coerenza con NoteContentDisplay */
</style>