<template>
  <div class="bg-white rounded-lg shadow-md border border-neutral-light">
    <div v-if="$slots.header || title" class="px-6 py-4 border-b border-neutral-light">
      <slot name="header">
        <h3 v-if="title" class="text-lg font-semibold text-neutral-darkest">{{ title }}</h3>
      </slot>
    </div>
    <div class="p-6">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string; // Titolo opzionale per la card
}
defineProps<Props>();
</script>

<style scoped>
/* Stili specifici per BaseCard, se necessari in futuro */
</style>