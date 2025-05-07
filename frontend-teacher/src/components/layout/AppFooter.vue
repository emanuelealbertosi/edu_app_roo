<template>
  <footer class="text-center text-sm text-neutral-darkest py-4"> <!-- Changed text-xs to text-sm and text-neutral-dark to text-neutral-darkest -->
    <!-- Rimosse classi text-primary e hover:text-primary-dark -->
    <button @click="$emit('openPrivacy')" class="hover:underline mx-2" style="display: inline !important; color: #8B5CF6 !important;">Informativa Privacy</button> | <!-- Added inline style with !important -->
    <button @click="$emit('openCookie')" class="hover:underline mx-2" style="display: inline !important; color: #8B5CF6 !important;">Cookie Policy</button> <!-- Added inline style with !important -->
    <p class="mt-1">&copy; {{ new Date().getFullYear() }} eduapp.it</p>
  </footer>
</template>

<script setup lang="ts">
defineEmits(['openPrivacy', 'openCookie']);
</script>

<style scoped>
/* Stili specifici per i bottoni del footer, resi più specifici */
footer > button { /* Usato '>' per maggiore specificità */
  @apply text-primary hover:text-primary-dark; /* Colore definito qui */
  background: none; /* Rimuove sfondo di default */
  border: none; /* Rimuove bordo di default */
  padding: 0; /* Rimuove padding di default */
  cursor: pointer; /* Mostra cursore mano */
}
</style>