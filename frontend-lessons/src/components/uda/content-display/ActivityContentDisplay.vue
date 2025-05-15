<template>
  <div class="activity-content-display p-3 bg-white rounded-b-md space-y-3 text-sm">
    <!-- Il titolo è gestito da UdaContentItemRenderer -->
    
    <div v-if="props.content.estimated_hours" class="flex">
        <strong class="w-28 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
    </div>

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

const isEditingDescription = ref(false);
const editableDescription = ref(props.content.activity_description || '');
const originalDescription = ref(props.content.activity_description || '');

watch(() => props.content.activity_description, (newVal) => {
  if (!isEditingDescription.value) {
    editableDescription.value = newVal || '';
    originalDescription.value = newVal || '';
  }
});

const startEditingDescription = () => {
  originalDescription.value = props.content.activity_description || '';
  editableDescription.value = props.content.activity_description || '';
  isEditingDescription.value = true;
};

const saveDescriptionChanges = async () => {
  console.log('[ActivityContentDisplay] saveDescriptionChanges called. editableDescription:', editableDescription.value, 'originalDescription:', originalDescription.value);

  if (editableDescription.value !== originalDescription.value) {
    console.log('Activity description changed, attempting to save...');
    if (typeof props.content.id === 'undefined') {
      console.error('Cannot update activity description: content ID is undefined.');
      // TODO: Mostrare un messaggio di errore all'utente
      return;
    }
    try {
      const updatedData: Partial<ActivityUDAContent> = {
        activity_description: editableDescription.value,
      };

      console.log(`[ActivityContentDisplay] About to update. uda_id: ${props.content.uda_id}, content_id: ${props.content.id}`);
      if (typeof props.content.uda_id === 'undefined') {
        console.error('[ActivityContentDisplay] CRITICAL: props.content.uda_id is undefined before calling store action!');
        // TODO: Mostrare un messaggio di errore all'utente
        return;
      }

      await udaStore.updateContentInUda(props.content.uda_id, props.content.id, updatedData as UDAContent);
      console.log('Activity description saved successfully. Waiting for prop update.');
      originalDescription.value = editableDescription.value; // Aggiorna originalDescription dopo il salvataggio
      isEditingDescription.value = false;
    } catch (error) {
      console.error('Failed to save activity description:', error);
      // TODO: Gestire lo stato di errore per l'UI
    }
  } else {
    console.log('Activity description not changed.');
    isEditingDescription.value = false;
  }
};

const cancelDescriptionEditing = () => {
  console.log('[ActivityContentDisplay] cancelDescriptionEditing called.');
  editableDescription.value = originalDescription.value; // Ripristina il contenuto originale
  isEditingDescription.value = false;
};

</script>

<style scoped>
.activity-content-display {
  font-size: 0.9rem;
}
/* Stili specifici per .activity-description :deep(p:last-child) rimossi per coerenza con NoteContentDisplay */
</style>