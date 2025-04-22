<template>
  <div class="animated-badge inline-block text-center" :title="badge.description || badge.name">
    <div
     class="badge-icon-wrapper relative w-16 h-16 mx-auto mb-1"
     
    >
      <img
        v-if="badge.image"
        :src="badge.image"
        :alt="badge.name"
        class="w-full h-full object-contain drop-shadow-md"
      />
      <!-- Placeholder se non c'è immagine -->
      <div v-else class="w-full h-full rounded-full bg-brand-gray-light flex items-center justify-center text-brand-gray text-3xl shadow-inner">
        🏆
      </div>
       <!-- Potremmo aggiungere elementi decorativi/animati qui con CSS -->
       <!-- <div class="sparkle absolute ..."></div> -->
    </div>
    <p class="badge-name text-xs font-semibold text-brand-gray-dark truncate w-full">
      {{ badge.name }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

// Interfaccia semplificata per il Badge (da allineare con l'API backend)
interface BadgeInfo {
  id: number;
  name: string;
  description?: string | null;
  image?: string | null; // URL dell'immagine (o SVG placeholder)
  // Assumiamo che il backend fornisca questa classe
  animation_class?: string | null;
}

const props = defineProps<{
  badge: BadgeInfo;
}>();

// // Calcola la classe di animazione da applicare (Rimosso)
// const animationClass = computed(() => {
//   // Aggiungiamo un prefisso o una classe base se necessario
//   // return props.badge.animation_class ? `animate-${props.badge.animation_class}` : '';
//   return props.badge.animation_class || ''; // Applica direttamente la classe fornita
// });

</script>

<style scoped>
/* Definiamo qui alcune animazioni CSS di esempio */
/* Queste classi dovrebbero corrispondere a quelle salvate nel backend */

.badge-pulse {
  animation: pulse-animation 1.5s infinite ease-in-out;
}

.badge-spin {
  animation: spin-animation 4s linear infinite;
}

.badge-bounce {
   animation: bounce-animation 1s infinite;
}

@keyframes pulse-animation {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

@keyframes spin-animation {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes bounce-animation {
  0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
	40% {transform: translateY(-10px);}
	60% {transform: translateY(-5px);}
}

/* Stili aggiuntivi per il wrapper o elementi decorativi */
.badge-icon-wrapper {
  /* Esempio: filtro drop-shadow */
  /* filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.2)); */
}
</style>