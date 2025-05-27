<template>
  <div v-if="editor" class="border border-gray-300 rounded-md">
    <div @mousedown.prevent @click.stop class="toolbar p-2 bg-gray-100 border-b border-gray-300 flex flex-wrap gap-2 items-center rounded-t-md">
      <button @click="editor.chain().focus().toggleBold().run()" :class="{ 'is-active': editor.isActive('bold') }"
        class="px-2 py-1 border rounded hover:bg-gray-200">
        B
      </button>
      <button @click="editor.chain().focus().toggleItalic().run()" :class="{ 'is-active': editor.isActive('italic') }"
        class="px-2 py-1 border rounded hover:bg-gray-200">
        I
      </button>
      <button @click="editor.chain().focus().toggleUnderline().run()"
        :class="{ 'is-active': editor.isActive('underline') }" class="px-2 py-1 border rounded hover:bg-gray-200">
        U
      </button>
      <button @click="setLink" :class="{ 'is-active': editor.isActive('link') }"
        class="px-2 py-1 border rounded hover:bg-gray-200">
        Link
      </button>
      <button @click="editor.chain().focus().toggleBulletList().run()"
        :class="{ 'is-active': editor.isActive('bulletList') }" class="px-2 py-1 border rounded hover:bg-gray-200">
        Lista Punt.
      </button>
      <button @click="editor.chain().focus().toggleOrderedList().run()"
        :class="{ 'is-active': editor.isActive('orderedList') }" class="px-2 py-1 border rounded hover:bg-gray-200">
        Lista Num.
      </button>

      <select @change="setColor($event.target.value)" class="px-2 py-1 border rounded hover:bg-gray-200 appearance-none">
        <option value="">Colore</option>
        <option v-for="color in colorPalette" :key="color.value" :value="color.value" :style="{ color: color.value }">
          {{ color.name }}
        </option>
        <option value="unset">Default</option>
      </select>

    </div>
    <editor-content :editor="editor" class="p-2 min-h-[100px]" />
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue';
import { useEditor, EditorContent } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link'; // Corretto import
import Underline from '@tiptap/extension-underline'; // Corretto import
import TextStyle from '@tiptap/extension-text-style'; // Corretto import
import { Color } from '@tiptap/extension-color';

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

const colorPalette = ref([
  { name: 'Nero', value: '#000000' },
  { name: 'Grigio Scuro', value: '#444444' },
  { name: 'Rosso', value: '#E00000' },
  { name: 'Blu', value: '#0000E0' },
  { name: 'Verde', value: '#008000' },
  { name: 'Arancione', value: '#FFA500' },
  { name: 'Viola', value: '#800080' },
]);

const editor = useEditor({
  content: props.modelValue,
  editable: props.editable,
  extensions: [
    StarterKit.configure({
      // Disabilita heading se non necessario per note/attività semplici
      heading: false,
      strike: false, // Esempio: disabilitare barrato se non richiesto
    }),
    Link.configure({
      openOnClick: false, // Apre i link in una nuova scheda al click sull'editor
      autolink: true,
      linkOnPaste: true,
    }),
    Underline,
    TextStyle,
    Color,
  ],
  onUpdate: () => {
    emit('update:modelValue', editor.value.getHTML());
  },
  onBlur: ({ event }) => { // Tiptap passa un oggetto { editor, event }
    // emit('blur', event); // Commentato per evitare errori stopPropagation durante unmount
  },
});

watch(() => props.modelValue, (newValue) => {
  if (editor.value && editor.value.getHTML() !== newValue) {
    editor.value.commands.setContent(newValue, false);
  }
});

watch(() => props.editable, (newEditableState) => {
  if (editor.value) {
    editor.value.setEditable(newEditableState);
  }
});

onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.destroy();
  }
});

const setLink = () => {
  if (!editor.value) return;
  const previousUrl = editor.value.getAttributes('link').href;
  const url = window.prompt('URL', previousUrl);

  // cancelled
  if (url === null) {
    return;
  }

  // empty
  if (url === '') {
    editor.value.chain().focus().extendMarkRange('link').unsetLink().run();
    return;
  }

  // update link
  editor.value.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
};

const setColor = (colorValue) => {
  if (!editor.value) return;
  if (colorValue === 'unset') {
    editor.value.chain().focus().unsetColor().run();
  } else if (colorValue) {
    editor.value.chain().focus().setColor(colorValue).run();
  }
};

</script>

<style>
.ProseMirror {
  outline: none;
}

.ProseMirror p {
  margin-bottom: 0.5rem;
}

.ProseMirror ul,
.ProseMirror ol {
  margin-left: 1.5rem;
  margin-bottom: 0.5rem;
}
.ProseMirror ul {
  list-style-type: disc;
}
.ProseMirror ol {
  list-style-type: decimal;
}

.toolbar button.is-active {
  background-color: #d1d5db; /* bg-gray-300 */
  font-weight: bold;
}
</style>