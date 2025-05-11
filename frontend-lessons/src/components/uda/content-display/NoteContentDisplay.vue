<template>
  <div class="note-content-display">
    <h6 v-if="content.note_title" class="mb-1">{{ content.note_title }}</h6>
    <div v-if="content.note_content" v-html="renderedMarkdown" class="note-body"></div>
    <p v-else class="text-muted">Nessun contenuto per questa nota.</p>
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