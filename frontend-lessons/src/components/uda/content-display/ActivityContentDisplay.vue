<template>
  <div class="activity-content-display p-3 bg-white rounded-b-md space-y-3 text-sm">
    <!-- Il titolo è gestito da UdaContentItemRenderer -->
    
    <div v-if="props.content.estimated_hours" class="flex">
        <strong class="w-28 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
    </div>

    <div v-if="content.activity_description">
      <!-- Etichetta "Descrizione:" rimossa -->
      <div v-html="renderedDescription" class="prose prose-sm max-w-none text-gray-600"></div>
    </div>
    
    <div v-if="content.activity_attachment_url" class="flex">
      <strong class="w-28 flex-shrink-0 text-gray-700">Allegato:</strong>
      <a :href="content.activity_attachment_url" target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:text-indigo-800 truncate">
        {{ content.activity_attachment_url.split('/').pop() || 'Vedi allegato' }}
      </a>
    </div>

    <!-- Checkbox "Attività Completata" rimossa -->
    
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
  }
  // isLoadingActivityCompletion prop rimossa
});

// const emit = defineEmits(['update:activity-completed']); // Evento rimosso

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

// Funzione toggleActivityCompleted rimossa

</script>

<style scoped>
.activity-content-display {
  font-size: 0.9rem;
}
.activity-description :deep(p:last-child) {
  margin-bottom: 0;
}
</style>