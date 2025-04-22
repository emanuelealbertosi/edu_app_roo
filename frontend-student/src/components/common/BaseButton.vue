<template>
  <button :class="buttonClasses" :disabled="disabled">
    <slot></slot> <!-- Permette di inserire testo o icone nel bottone -->
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning' | 'info' | 'ghost'; // Aggiunte varianti
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  disabled: false,
});

const buttonClasses = computed(() => {
  const base = 'inline-block font-bold rounded-lg text-sm px-5 py-2.5 text-center transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed shadow-md hover:shadow-lg active:shadow-sm'; // Stile base aggiornato

  // Mappatura varianti ai colori Kahoot
  const variants: Record<string, string> = {
    primary: 'bg-kahoot-purple text-white hover:bg-kahoot-purple-dark focus:ring-kahoot-purple',
    secondary: 'bg-brand-gray text-brand-gray-dark hover:bg-brand-gray-dark hover:text-white focus:ring-brand-gray', // Grigio
    danger: 'bg-kahoot-red text-white hover:bg-kahoot-red-light focus:ring-kahoot-red', // Rosso
    success: 'bg-kahoot-green text-white hover:bg-kahoot-green-light focus:ring-kahoot-green', // Verde
    warning: 'bg-kahoot-yellow text-white hover:bg-kahoot-yellow-light focus:ring-kahoot-yellow', // Giallo
    info: 'bg-kahoot-blue text-white hover:bg-kahoot-blue-light focus:ring-kahoot-blue', // Blu
    ghost: 'bg-transparent text-kahoot-purple hover:bg-kahoot-purple/10 focus:ring-kahoot-purple shadow-none', // Trasparente
  };

  return [base, variants[props.variant] || variants.primary];
});
</script>

<style scoped>
/* Eventuali stili specifici aggiuntivi per il bottone */
button:disabled {
  /* Stile specifico per il bottone disabilitato se necessario */
}
</style>