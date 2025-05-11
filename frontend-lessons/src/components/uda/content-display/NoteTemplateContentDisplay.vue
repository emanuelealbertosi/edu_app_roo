<template>
  <div class="note-template-content-display">
    <h6 v-if="content.note_template_title" class="mb-1">{{ content.note_template_title }}</h6>
    <div v-if="content.note_template_content" v-html="renderedMarkdown" class="note-body"></div>
    <p v-else class="text-muted">Nessun contenuto per questo template di nota.</p>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue';
import type { NoteTemplateUDAContent } from '@/types/uda';
import { marked } from 'marked'; // Per renderizzare Markdown
import DOMPurify from 'dompurify';

const props = defineProps({
  content: {
    type: Object as PropType<NoteTemplateUDAContent>,
    required: true
  }
});

const renderedMarkdown = computed(() => {
  if (props.content.note_template_content) {
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
    const rawHtml = marked(props.content.note_template_content, { renderer });
    return DOMPurify.sanitize(rawHtml as string);
  }
  return '';
});
</script>

<style scoped>
.note-template-content-display {
  font-size: 0.9rem;
  background-color: #f8f9fa; /* Leggero sfondo per distinguerlo da una nota normale */
  padding: 0.75rem;
  border-radius: .25rem;
}
.note-body :deep(p:last-child) {
  margin-bottom: 0;
}
.note-body :deep(ul), .note-body :deep(ol) {
  padding-left: 1.2rem;
}
</style>