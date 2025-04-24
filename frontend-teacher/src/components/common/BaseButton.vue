<template>
  <!-- Permette di inserire testo o icone nel bottone -->
  <button :class="buttonClasses" :disabled="disabled">
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  variant?: 'primary' | 'secondary' | 'secondary-outline' | 'danger' | 'success' | 'warning' | 'info' | 'ghost'; // Aggiunta secondary-outline
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  disabled: false,
});

const buttonClasses = computed(() => {
  const base = 'inline-flex items-center justify-center font-semibold rounded-md text-sm px-4 py-2 text-center transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm hover:shadow active:shadow-inner'; // Stile base leggermente rivisto per coerenza

  // Mappatura varianti ai nuovi colori
  const variants: Record<string, string> = {
    primary: 'bg-primary text-white hover:bg-primary-dark focus:ring-primary',
    secondary: 'bg-neutral-DEFAULT text-neutral-darkest hover:bg-neutral-medium focus:ring-neutral-dark', // Grigio chiaro
    'secondary-outline': 'bg-transparent border border-neutral-lightest text-neutral-lightest hover:bg-neutral-lightest/10 focus:ring-neutral-lightest', // Per sfondi scuri
    danger: 'bg-error text-white hover:bg-error/90 focus:ring-error', // Rosso
    success: 'bg-success text-white hover:bg-success/90 focus:ring-success', // Verde
    warning: 'bg-warning text-neutral-darkest hover:bg-warning/90 focus:ring-warning', // Giallo/Arancio
    info: 'bg-sky-500 text-white hover:bg-sky-600 focus:ring-sky-500', // Blu cielo (esempio, non definito in config)
    ghost: 'bg-transparent text-primary hover:bg-primary/10 focus:ring-primary shadow-none', // Trasparente
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