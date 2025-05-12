<template>
  <div class="note-content-display p-3 bg-white rounded-b-md"> <!-- Aggiunto padding e sfondo per coerenza -->
    <!-- Il titolo della nota è già gestito dal contentTitle in UdaContentItemRenderer -->
    <!-- <h6 v-if="content.note_title" class="mb-1">{{ content.note_title }}</h6> -->
    <div v-if="props.content.estimated_hours" class="flex text-sm mb-2">
        <strong class="w-24 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
    </div>
    <div v-if="content.note_content" v-html="renderedMarkdown" class="note-body prose prose-sm max-w-none"></div>
    <p v-else class="text-sm text-gray-500">Nessun contenuto per questa nota.</p>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue';
import type { NoteUDAContent } from '@/types/uda';
import { marked } from 'marked'; // Per renderizzare Markdown
import DOMPurify from 'dompurify';

const props = defineProps({
  content: {
    type: Object as PropType<NoteUDAContent>,
    required: true
  }
});

const renderedMarkdown = computed(() => {
  if (props.content.note_content) {
    marked.setOptions({
      gfm: true,
      breaks: true,
    });
    
    const renderer = new marked.Renderer();
    // Ripristina la firma originale che accetta un oggetto
    renderer.link = (data: { href: string | null; title?: string | null; text: string; }) => {
      const { href, title, text } = data;
      const localHref = href || '#'; // Fornisce un fallback per href nullo
      const localTitle = title || '';
      return `<a href="${localHref}" title="${localTitle}" target="_blank" rel="noopener noreferrer">${text}</a>`;
    };
    
    const rawHtml = marked(props.content.note_content, { renderer });
    return DOMPurify.sanitize(rawHtml as string);
  }
  return '';
});
</script>

<style scoped>
.note-content-display {
  font-size: 0.9rem;
}
.note-body :deep(p:last-child) {
  margin-bottom: 0;
}
.note-body :deep(ul), .note-body :deep(ol) {
  padding-left: 1.2rem;
}
</style>