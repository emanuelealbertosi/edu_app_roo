<template>
  <div class="embedded-view-container">
    <iframe
      id="teacher-lessons-iframe-subjects"
      ref="lessonsIframeRef"
      :src="pageUrl"
      frameborder="0"
      width="100%"
      class="embedded-iframe"
      allowfullscreen
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';

const lessonsIframeRef = ref<HTMLIFrameElement | null>(null);
const router = useRouter();

const lessonsAppBaseUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined)?.replace(/\/$/, '') || '');
const lessonsAppOrigin = computed(() => {
  try {
    // Assicurati che VITE_LESSONS_APP_URL sia un URL completo per new URL()
    const appUrl = lessonsAppBaseUrl.value;
    if (appUrl.startsWith('http')) {
      return new URL(appUrl).origin;
    } else if (typeof window !== 'undefined') {
      // Se è un percorso relativo, costruisci l'URL completo basato sull'origine corrente
      return new URL(appUrl, window.location.origin).origin;
    }
    console.warn('[EmbeddedView] Impossibile determinare l\'origine di lessonsAppBaseUrl in un contesto non-browser o con URL relativo non valido:', appUrl);
    return ''; // Fallback a stringa vuota se non può essere determinato
  } catch (e) {
    console.error("[EmbeddedView] Errore nel parsare VITE_LESSONS_APP_URL per ottenere l'origine:", lessonsAppBaseUrl.value, e);
    return ''; // Fallback
  }
});

const pageUrl = computed(() => `${lessonsAppBaseUrl.value}/materie?embedded=true`);

const handleMessage = (event: MessageEvent) => {
  // Aggiungi un controllo di sicurezza sull'origine del messaggio
  if (event.origin !== lessonsAppOrigin.value) {
    console.warn(`Messaggio ricevuto da un'origine non attendibile: ${event.origin}`);
    return;
  }

  if (event.data && event.data.type === 'navigate-to-host-home') {
    console.log('Messaggio ricevuto dall\'iframe per navigare alla home dell\'host.');
    router.push({ name: 'dashboard' });
  }
};

onMounted(() => {
  const iframe = lessonsIframeRef.value;
  if (iframe) {
    iframe.onload = () => {
      console.log('[EmbeddedTeacherSubjectsView] Iframe caricato. Invio HOST_READY_FOR_IFRAME_SIGNAL.');
      if (iframe.contentWindow && lessonsAppOrigin.value) {
        iframe.contentWindow.postMessage({ type: 'HOST_READY_FOR_IFRAME_SIGNAL' }, lessonsAppOrigin.value);
      } else if (!lessonsAppOrigin.value) {
        console.error('[EmbeddedTeacherSubjectsView] Impossibile determinare lessonsAppOrigin. VITE_LESSONS_APP_URL è configurato correttamente?');
      } else {
        console.warn('[EmbeddedTeacherSubjectsView] Iframe contentWindow non disponibile al momento dell\'invio di HOST_READY.');
      }
    };
  } else {
    console.error('[EmbeddedTeacherSubjectsView] Riferimento Iframe non trovato in onMounted.');
  }

  window.addEventListener('message', handleMessage);
});

onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage);
});
</script>

<style scoped>
.embedded-view-container {
  width: 100%;
  height: 100%;
  display: flex;
}
.embedded-iframe {
  flex-grow: 1;
  border: none;
}
</style>