<template>
  <div class="activity-template-content-display">
    <h6 v-if="content.activity_template_title" class="mb-1">{{ content.activity_template_title }}</h6>
    <div v-if="content.activity_template_description" v-html="renderedDescription" class="activity-description"></div>
    <p v-else class="text-muted">Nessuna descrizione per questo template di attività.</p>
    <!-- I template di attività non hanno un URL allegato o uno stato di completamento -->
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue';
import type { ActivityTemplateUDAContent } from '@/types/uda';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const props = defineProps({
  content: {
    type: Object as PropType<ActivityTemplateUDAContent>,
    required: true
  }
});

const renderedDescription = computed(() => {
  if (props.content.activity_template_description) {
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
    const rawHtml = marked(props.content.activity_template_description, { renderer });
    return DOMPurify.sanitize(rawHtml as string);
  }
  return '';
});
</script>

<style scoped>
.activity-template-content-display {
  font-size: 0.9rem;
  background-color: #f8f9fa; /* Leggero sfondo per distinguerlo da un'attività normale */
  padding: 0.75rem;
  border-radius: .25rem;
}
.activity-description :deep(p:last-child) {
  margin-bottom: 0;
}
</style>