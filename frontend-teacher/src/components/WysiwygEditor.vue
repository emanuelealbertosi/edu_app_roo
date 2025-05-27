<template>
  <div v-if="editor" class="border border-gray-300 rounded-md">
    <div class="toolbar p-2 bg-gray-100 border-b border-gray-300 flex flex-wrap gap-1">
      <button type="button" @click="editor.chain().focus().toggleBold().run()" :class="{ 'is-active': editor.isActive('bold') }" class="toolbar-button">
        B
      </button>
      <button type="button" @click="editor.chain().focus().toggleItalic().run()" :class="{ 'is-active': editor.isActive('italic') }" class="toolbar-button">
        I
      </button>
      <button type="button" @click="editor.chain().focus().toggleUnderline().run()" :class="{ 'is-active': editor.isActive('underline') }" class="toolbar-button">
        U
      </button>
      <button type="button" @click="editor.chain().focus().toggleBulletList().run()" :class="{ 'is-active': editor.isActive('bulletList') }" class="toolbar-button">
        Lista Punt.
      </button>
      <button type="button" @click="editor.chain().focus().toggleOrderedList().run()" :class="{ 'is-active': editor.isActive('orderedList') }" class="toolbar-button">
        Lista Num.
      </button>
      <button type="button" @click="setLink" :class="{ 'is-active': editor.isActive('link') }" class="toolbar-button">
        Link
      </button>
      <button type="button" @click="editor.chain().focus().unsetLink().run()" v-if="editor.isActive('link')" class="toolbar-button">
        Rimuovi Link
      </button>
      
      <!-- Palette Colori Predefinita -->
      <div class="flex gap-1 items-center">
        <span class="text-xs mr-1 text-gray-600">Colore:</span>
        <button
          type="button"
          v-for="colorValue in predefinedColors"
          :key="colorValue.name"
          @click="editor?.chain().focus().setColor(colorValue.hex).run()"
          :class="{ 'is-active-color': editor?.isActive('textStyle', { color: colorValue.hex }) }"
          class="color-swatch"
          :style="{ backgroundColor: colorValue.hex }"
          :title="colorValue.name"
        ></button>
        <button type="button" @click="editor?.chain().focus().unsetColor().run()" class="toolbar-button text-xs ml-1" title="Rimuovi colore">
          &#x2715; <!-- Simbolo X -->
        </button>
      </div>
    </div>
    <editor-content :editor="editor" class="p-3 min-h-[100px]" />
  </div>
</template>

<script setup lang="ts">
import { useEditor, EditorContent } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Underline from '@tiptap/extension-underline';
import TextStyle from '@tiptap/extension-text-style';
import { Color } from '@tiptap/extension-color';
import { ref, watch, onBeforeUnmount } from 'vue'; // Aggiunto ref

const predefinedColors = ref([
  { name: 'Nero', hex: '#000000' },
  { name: 'Rosso', hex: '#E00000' },
  { name: 'Blu', hex: '#0000E0' },
  { name: 'Verde', hex: '#008000' },
  { name: 'Giallo', hex: '#CCCC00' },
  { name: 'Viola', hex: '#800080' },
  { name: 'Arancione', hex: '#FFA500' },
  { name: 'Grigio', hex: '#808080' },
]);

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  editable: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(['update:modelValue', 'blur']);

const editor = useEditor({
  content: props.modelValue,
  editable: props.editable,
  extensions: [
    StarterKit.configure({
      // Configura StarterKit per escludere 'strike'
      strike: false,
      // heading: false, // Esempio per escludere altre funzionalità se necessario
      // blockquote: false,
    }),
    Link.configure({
      openOnClick: false,
      autolink: true,
      linkOnPaste: true,
      HTMLAttributes: {
        target: '_blank',
        rel: 'noopener noreferrer nofollow',
      },
    }),
    Underline,
    TextStyle,
    Color,
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML());
  },
  onBlur: () => {
    emit('blur');
  }
});

watch(() => props.modelValue, (newValue) => {
  if (editor.value && editor.value.getHTML() !== newValue) {
    editor.value.commands.setContent(newValue, false);
  }
});

watch(() => props.editable, (newEditableValue) => {
  if (editor.value) {
    editor.value.setEditable(newEditableValue);
  }
});

const setLink = () => {
  if (!editor.value) return;
  const previousUrl = editor.value.getAttributes('link').href;
  const url = window.prompt('URL', previousUrl);

  // Annullato
  if (url === null) {
    return;
  }

  // URL vuoto -> rimuovi link
  if (url === '') {
    editor.value.chain().focus().extendMarkRange('link').unsetLink().run();
    return;
  }

  // Applica URL
  editor.value.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
};

onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.destroy();
  }
});
</script>

<style scoped>
.toolbar-button {
  @apply px-2 py-1 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50;
}
.toolbar-button.is-active {
  @apply bg-blue-500 text-white;
}
/* Stili per i campioni di colore */
.color-swatch {
  @apply w-5 h-5 rounded-sm border border-gray-400 cursor-pointer hover:ring-2 hover:ring-offset-1 hover:ring-blue-500;
}
.color-swatch.is-active-color {
  @apply ring-2 ring-offset-1 ring-blue-700 border-blue-700;
}

/* Rimosso .toolbar-color-picker e i suoi stili specifici */

/* Stili per il contenuto dell'editor (se necessario per forzare Tailwind) */
:deep(.ProseMirror) {
  @apply max-w-none m-2 focus:outline-none;
  min-height: 100px; /* Assicura un'altezza minima */
}

/* Stili espliciti per le liste all'interno dell'editor */
:deep(.ProseMirror ul) {
  list-style-type: disc !important;
  padding-left: 2.5rem !important; /* Aumentato per visibilità */
  margin-left: 0 !important; /* Resetta eventuali margini di Tailwind */
}

:deep(.ProseMirror ol) {
  list-style-type: decimal !important;
  padding-left: 2.5rem !important; /* Aumentato per visibilità */
  margin-left: 0 !important; /* Resetta eventuali margini di Tailwind */
}

:deep(.ProseMirror li) {
  /* Potrebbe non essere necessario, ma per sicurezza */
  display: list-item !important;
}

:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: #adb5bd;
  pointer-events: none;
  height: 0;
}
</style>