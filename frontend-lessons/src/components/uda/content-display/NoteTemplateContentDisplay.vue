<template>
  <div class="note-template-content-display p-3 bg-white rounded-b-md"> <!-- Aggiunto padding e sfondo per coerenza -->
    <!-- Il titolo è gestito da UdaContentItemRenderer -->
    <div v-if="props.content.estimated_hours" class="flex text-sm mb-2">
        <strong class="w-24 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
    </div>
    <div v-if="!isEditing" @click="startEditing" class="note-body prose prose-sm max-w-none cursor-pointer min-h-[50px]">
      <div v-if="content.note_template_content" v-html="content.note_template_content"></div>
      <p v-else class="text-sm text-gray-500 italic">Clicca per aggiungere un contenuto al template della nota.</p>
    </div>
    <div v-else>
      <WysiwygEditor
        v-model="editableContent"
        :editable="true"
      />
      <div class="mt-2 flex justify-start space-x-2">
        <button @click="cancelEditing" class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded">Annulla</button>
        <button @click="saveChanges" class="px-3 py-1 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded">Salva</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType } from 'vue';
import type { NoteTemplateUDAContent, UDATemplateContent } from '@/types/uda';
import WysiwygEditor from '@/components/WysiwygEditor.vue';
import { useUdaTemplateStore } from '@/stores/udaTemplateStore';

const props = defineProps({
  content: {
    type: Object as PropType<NoteTemplateUDAContent & { uda_template_id: number }>, // Aggiunto uda_template_id
    required: true
  }
});

const udaTemplateStore = useUdaTemplateStore();

const isEditing = ref(false);
const editableContent = ref(props.content.note_template_content || '');
const originalContent = ref(props.content.note_template_content || '');

watch(() => props.content.note_template_content, (newVal) => {
  if (!isEditing.value) {
    editableContent.value = newVal || '';
    originalContent.value = newVal || '';
  }
});

const startEditing = () => {
  originalContent.value = props.content.note_template_content || '';
  editableContent.value = props.content.note_template_content || '';
  isEditing.value = true;
};

const saveChanges = async () => {
  if (editableContent.value !== originalContent.value) {
    if (typeof props.content.id === 'undefined' || typeof props.content.uda_template_id === 'undefined') {
      console.error('Cannot update template content: content ID or UDA Template ID is undefined.');
      // TODO: Mostrare un messaggio di errore all'utente
      return;
    }
    try {
      const updatedData: Partial<NoteTemplateUDAContent> = {
        note_template_content: editableContent.value,
      };
      await udaTemplateStore.updateContentInTemplate(props.content.uda_template_id, props.content.id, updatedData as UDATemplateContent);
      originalContent.value = editableContent.value;
      isEditing.value = false;
    } catch (error) {
      console.error('Failed to save note template content:', error);
      // TODO: Gestire lo stato di errore per l'UI
    }
  } else {
    isEditing.value = false;
  }
};

const cancelEditing = () => {
  editableContent.value = originalContent.value;
  isEditing.value = false;
};

</script>

<style scoped>
/* Rimosse classi CSS custom, ora gestite da Tailwind e dal padding del div principale */
.note-body :deep(p:last-child) {
  margin-bottom: 0;
}
.note-body :deep(ul), .note-body :deep(ol) {
  padding-left: 1.2rem;
}
</style>