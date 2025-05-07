<template>
  <div class="border border-gray-300 rounded-md p-2">
    <!-- Sostituiamo l'editor Tiptap con una semplice textarea -->
    <textarea
      :value="modelValue"
      @input="updateValue($event)"
      class="w-full h-64 p-2 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
      placeholder="Inserisci qui il codice HTML della lezione..."
    ></textarea>
  </div>
</template>

<script setup lang="ts">
// Rimuoviamo tutte le dipendenze e la logica di Tiptap
// Rimuoviamo anche 'props' perché 'modelValue' è usato direttamente nel template
/*
const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
})
*/
// Definiamo 'modelValue' direttamente come prop per usarlo nel template
defineProps({
  modelValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

// Funzione per emettere l'aggiornamento del valore quando l'input della textarea cambia
const updateValue = (event: Event) => {
  const target = event.target as HTMLTextAreaElement;
  if (target) {
    emit('update:modelValue', target.value)
  }
}

// Non è più necessario il watch o onBeforeUnmount per Tiptap
</script>

<style>
/* Rimuoviamo gli stili specifici di ProseMirror */
/* Possiamo aggiungere stili specifici per la textarea se necessario */
textarea {
  min-height: 200px; /* Manteniamo un'altezza minima */
  resize: vertical; /* Permettiamo il ridimensionamento verticale */
}
</style>