<template>
  <div class="embedded-lessons-view">
    <iframe
      :src="lessonsPageUrl"
      frameborder="0"
      width="100%"
      height="800px"
      allowfullscreen
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

// Recupera l'URL base dell'app Lezioni dalle variabili d'ambiente o usa un fallback.
// Assicurati che VITE_LESSONS_APP_URL sia configurata correttamente nel tuo file .env
// per puntare a http://localhost:5173 in sviluppo per frontend-lessons.
const lessonsAppBaseUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined)?.replace(/\/$/, '') || '/lezioni');

const lessonsPageUrl = computed(() => {
  let url = '';
  // Se lessonsAppBaseUrl è un URL completo (inizia con http), usalo direttamente.
  // Altrimenti, assumi che sia un percorso relativo al dominio corrente.
  if (lessonsAppBaseUrl.value.startsWith('http')) {
    url = `${lessonsAppBaseUrl.value}/lezioni-assegnate`;
  } else {
    // Per percorsi relativi, potrebbe essere necessario aggiustare a seconda di come è servita l'app.
    // Questo esempio assume che sia relativo alla root del dominio.
    url = `${lessonsAppBaseUrl.value}/lezioni-assegnate`;
  }
  return `${url}?embedded=true`;
});
</script>

<style scoped>
.embedded-lessons-view {
  width: 100%;
  height: calc(100vh - 120px); /* Esempio: altezza viewport meno header/footer, da aggiustare */
  display: flex;
}

iframe {
  flex-grow: 1;
  border: none; /* Rimuove il bordo predefinito dell'iframe */
}
</style>