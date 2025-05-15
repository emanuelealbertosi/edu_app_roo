<template>
  <div class="activity-template-content-display p-3 bg-white rounded-b-md space-y-3 text-sm">
    <!-- Il titolo è gestito da UdaContentItemRenderer -->
     <div v-if="props.content.estimated_hours" class="flex">
        <strong class="w-28 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
    </div>
    <div v-if="!isEditingDescription" @click="startEditingDescription" class="activity-description-display prose prose-sm max-w-none cursor-pointer min-h-[50px]">
      <strong class="block text-gray-700 mb-1">Descrizione:</strong>
      <div v-if="content.activity_template_description" v-html="content.activity_template_description" class="text-gray-600"></div>
      <p v-else class="text-sm text-gray-500 italic">Clicca per aggiungere una descrizione al template dell'attività.</p>
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
    <!-- I template di attività non hanno un URL allegato o uno stato di completamento -->
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType } from 'vue';
import type { ActivityTemplateUDAContent, UDATemplateContent } from '@/types/uda';
import WysiwygEditor from '@/components/WysiwygEditor.vue';
import { useUdaTemplateStore } from '@/stores/udaTemplateStore';

const props = defineProps({
  content: {
    type: Object as PropType<ActivityTemplateUDAContent & { uda_template_id: number }>, // Aggiunto uda_template_id
    required: true
  }
});

const udaTemplateStore = useUdaTemplateStore();

const isEditingDescription = ref(false);
const editableDescription = ref(props.content.activity_template_description || '');
const originalDescription = ref(props.content.activity_template_description || '');

watch(() => props.content.activity_template_description, (newVal) => {
  if (!isEditingDescription.value) {
    editableDescription.value = newVal || '';
    originalDescription.value = newVal || '';
  }
});

const startEditingDescription = () => {
  originalDescription.value = props.content.activity_template_description || '';
  editableDescription.value = props.content.activity_template_description || '';
  isEditingDescription.value = true;
};

const saveDescriptionChanges = async () => {
  if (editableDescription.value !== originalDescription.value) {
    if (typeof props.content.id === 'undefined' || typeof props.content.uda_template_id === 'undefined') {
      console.error('Cannot update template description: content ID or UDA Template ID is undefined.');
      // TODO: Mostrare un messaggio di errore all'utente
      return;
    }
    try {
      const updatedData: Partial<ActivityTemplateUDAContent> = {
        activity_template_description: editableDescription.value,
      };
      await udaTemplateStore.updateContentInTemplate(props.content.uda_template_id, props.content.id, updatedData as UDATemplateContent);
      originalDescription.value = editableDescription.value;
      isEditingDescription.value = false;
    } catch (error) {
      console.error('Failed to save activity template description:', error);
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

</script>

<style scoped>
/* Rimosse classi CSS custom, ora gestite da Tailwind e dal padding del div principale */
.activity-description-display :deep(p:last-child) {
  margin-bottom: 0;
}
</style>