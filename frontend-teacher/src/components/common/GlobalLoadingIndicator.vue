<script setup lang="ts">
import { useUiStore } from '@/stores/ui';

const uiStore = useUiStore();

// Non serve una variabile locale, usiamo direttamente uiStore.isLoadingApi nel template
</script>

<template>
  <transition name="loading-indicator-fade">
    <div 
      v-if="uiStore.isLoadingApi" 
      class="loading-indicator fixed top-0 left-0 w-full h-1 z-50"
      role="progressbar" 
      aria-busy="true" 
      aria-live="polite"
    >
      <div class="loading-bar h-full"></div> <!-- Rimosso bg-blue-500 -->
    </div>
  </transition>
</template>

<style scoped>
.loading-indicator {
  /* Posizionamento sopra tutto */
  z-index: 9999; 
}

.loading-bar {
  /* Animazione semplice della barra */
  animation: loading-progress 1.5s infinite linear;
  /* Usa i colori primari del tema da tailwind.config.js */
  background: linear-gradient(to right, #8B5CF6, #A78BFA, #8B5CF6); /* primary.DEFAULT, primary.light, primary.DEFAULT */
  background-size: 600px 100%; /* Larghezza gradiente per effetto movimento */
}

@keyframes loading-progress {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

/* Transizione fade per apparizione/scomparsa */
.loading-indicator-fade-enter-active,
.loading-indicator-fade-leave-active {
  transition: opacity 0.3s ease;
}

.loading-indicator-fade-enter-from,
.loading-indicator-fade-leave-to {
  opacity: 0;
}
</style>