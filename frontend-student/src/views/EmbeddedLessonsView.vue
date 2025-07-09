<template>
  <div class="embedded-lessons-view">
    <iframe
      id="lessons-iframe"
      ref="lessonsIframeRef"
      :src="lessonsPageUrl"
      frameborder="0"
      width="100%"
      height="800px"
      allowfullscreen
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';

const lessonsIframeRef = ref<HTMLIFrameElement | null>(null);
const router = useRouter();

// Recupera l'URL base dell'app Lezioni dalle variabili d'ambiente o usa un fallback.
const lessonsAppBaseUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined)?.replace(/\/$/, '') || '/lezioni');
const lessonsAppOrigin = computed(() => {
  try {
    return new URL(lessonsAppBaseUrl.value.startsWith('http') ? lessonsAppBaseUrl.value : window.location.origin + lessonsAppBaseUrl.value).origin;
  } catch (e) {
    console.error("Errore nel parsare VITE_LESSONS_APP_URL per ottenere l'origine:", e);
    // Fallback a un'origine che probabilmente non funzionerà, per evitare errori, ma segnala il problema.
    // O gestisci diversamente, es. non inviare postMessage se l'origine non è valida.
    return import.meta.env.VITE_LESSONS_APP_URL_ORIGIN || ''; // Usa VITE_LESSONS_APP_URL_ORIGIN se VITE_LESSONS_APP_URL non è un URL completo
  }
});


const lessonsPageUrl = computed(() => {
  let url = '';
  if (lessonsAppBaseUrl.value.startsWith('http')) {
    url = `${lessonsAppBaseUrl.value}/lezioni-assegnate`;
  } else {
    url = `${lessonsAppBaseUrl.value}/lezioni-assegnate`;
  }
  return `${url}?embedded=true`;
});

const handleMessage = (event: MessageEvent) => {
  if (event.origin !== lessonsAppOrigin.value) {
    return;
  }
  if (event.data && typeof event.data.type === 'string') {
    switch (event.data.type) {
      case 'navigate-to-host-home':
        router.push({ name: 'dashboard' });
        break;
      case 'navigate-to-host-assigned-lessons':
        // Se siamo già sulla pagina che mostra le lezioni, un semplice push non
        // ricaricherebbe la vista o l'iframe. Forziamo un reload per resettare lo stato.
        if (router.currentRoute.value.name === 'EmbeddedLessons') {
          window.location.reload();
        } else {
          router.push({ name: 'EmbeddedLessons' });
        }
        break;
    }
  }
};

onMounted(() => {
  const iframe = lessonsIframeRef.value;
  if (iframe) {
    iframe.onload = () => {
      console.log('[EmbeddedLessonsView] Iframe caricato. Invio HOST_READY_FOR_IFRAME_SIGNAL.');
      if (iframe.contentWindow && lessonsAppOrigin.value) {
        iframe.contentWindow.postMessage({ type: 'HOST_READY_FOR_IFRAME_SIGNAL' }, lessonsAppOrigin.value);
      } else if (!lessonsAppOrigin.value) {
        console.error('[EmbeddedLessonsView] Impossibile determinare lessonsAppOrigin. VITE_LESSONS_APP_URL è configurato correttamente?');
      }
    };
  }
  window.addEventListener('message', handleMessage);
});

onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage);
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