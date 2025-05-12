<template>
  <div class="activity-template-content-display p-3 bg-white rounded-b-md space-y-3 text-sm">
    <!-- Il titolo è gestito da UdaContentItemRenderer -->
     <div v-if="props.content.estimated_hours" class="flex">
        <strong class="w-28 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
    </div>
    <div v-if="content.activity_template_description">
      <strong class="block text-gray-700 mb-1">Descrizione:</strong>
      <div v-html="renderedDescription" class="prose prose-sm max-w-none text-gray-600"></div>
    </div>
    <p v-else class="text-gray-500">Nessuna descrizione per questo template di attività.</p>
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
/* Rimosse classi CSS custom, ora gestite da Tailwind e dal padding del div principale */
.activity-description :deep(p:last-child) {
  margin-bottom: 0;
}
</style>