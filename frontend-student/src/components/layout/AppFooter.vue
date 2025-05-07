<template>
  <footer class="text-center text-xs text-neutral-dark py-4">
    <button @click="$emit('openPrivacy')" class="hover:underline mx-2 text-primary hover:text-primary-dark">Informativa Privacy</button> |
    <button @click="$emit('openCookie')" class="hover:underline mx-2 text-primary hover:text-primary-dark">Cookie Policy</button>
    <p class="mt-1">&copy; {{ new Date().getFullYear() }} eduapp.it</p>
  </footer>
</template>

<script setup lang="ts">
defineEmits(['openPrivacy', 'openCookie']);
</script>

<style scoped>
/* Stili specifici per i bottoni del footer */
footer button {
  @apply text-primary hover:text-primary-dark;
  background: none; /* Rimuove sfondo di default dei bottoni */
  border: none; /* Rimuove bordo di default */
  padding: 0; /* Rimuove padding di default */
  cursor: pointer; /* Mostra cursore mano */
}
</style>