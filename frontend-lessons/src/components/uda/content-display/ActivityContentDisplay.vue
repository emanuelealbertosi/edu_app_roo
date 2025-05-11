<template>
  <div class="activity-content-display">
    <h6 v-if="content.activity_title" class="mb-1">{{ content.activity_title }}</h6>
    <div v-if="content.activity_description" v-html="renderedDescription" class="activity-description mb-2"></div>
    
    <div v-if="content.activity_attachment_url" class="mb-2">
      <strong>Allegato: </strong>
      <a :href="content.activity_attachment_url" target="_blank" rel="noopener noreferrer">
        {{ content.activity_attachment_url.split('/').pop() || 'Vedi allegato' }}
      </a>
    </div>
    <!-- Qui potrebbe andare il FileUpload.vue per caricare un nuovo allegato in fase di modifica -->
    <!-- Per ora, ci concentriamo sulla visualizzazione e sul completamento -->

    <div class="form-check mt-2">
      <input 
        class="form-check-input" 
        type="checkbox"
        :id="`activityCompleted-${content.id || content.temp_id}`"
        :checked="content.activity_completed || false"
        @change="toggleActivityCompleted"
        :disabled="isLoadingActivityCompletion"
      >
      <label class="form-check-label" :for="`activityCompleted-${content.id || content.temp_id}`">
        Attività Completata (dallo studente/formalmente)
      </label>
    </div>
    <small v-if="isLoadingActivityCompletion" class="text-muted">Aggiornamento stato attività...</small>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue';
import type { ActivityUDAContent } from '@/types/uda';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const props = defineProps({
  content: {
    type: Object as PropType<ActivityUDAContent>,
    required: true
  },
  isLoadingActivityCompletion: { // Passato dal genitore (UdaContentItemRenderer)
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:activity-completed']);

const renderedDescription = computed(() => {
  if (props.content.activity_description) {
    marked.setOptions({
      gfm: true,
      breaks: true,
    });
    const renderer = new marked.Renderer();
    renderer.link = (data: { href: string | null; title?: string | null; text: string; }) => {
      const { href, title, text } = data;
      const localHref = href || '#'; // Fallback per href nullo
      const localTitle = title || '';
      return `<a href="${localHref}" title="${localTitle}" target="_blank" rel="noopener noreferrer">${text}</a>`;
    };
    const rawHtml = marked(props.content.activity_description, { renderer });
    return DOMPurify.sanitize(rawHtml as string);
  }
  return '';
});

const toggleActivityCompleted = (event: Event) => {
  const target = event.target as HTMLInputElement;
  emit('update:activity-completed', target.checked);
};
</script>

<style scoped>
.activity-content-display {
  font-size: 0.9rem;
}
.activity-description :deep(p:last-child) {
  margin-bottom: 0;
}
</style>