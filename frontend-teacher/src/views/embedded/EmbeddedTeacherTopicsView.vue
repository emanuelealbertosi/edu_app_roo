<template>
  <div class="embedded-view-container">
    <iframe
      :src="pageUrl"
      frameborder="0"
      width="100%"
      class="embedded-iframe"
      allowfullscreen
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const lessonsAppBaseUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined)?.replace(/\/$/, '') || '');
const lessonsAppOrigin = computed(() => {
  try {
    const appUrl = lessonsAppBaseUrl.value;
    if (appUrl.startsWith('http')) {
      return new URL(appUrl).origin;
    } else if (typeof window !== 'undefined') {
      return new URL(appUrl, window.location.origin).origin;
    }
    return '';
  } catch (e) {
    console.error("Errore nel parsare VITE_LESSONS_APP_URL:", e);
    return '';
  }
});

const pageUrl = computed(() => `${lessonsAppBaseUrl.value}/argomenti?embedded=true`);

const handleMessage = (event: MessageEvent) => {
  if (event.origin !== lessonsAppOrigin.value) {
    return;
  }
  if (event.data && event.data.type === 'navigate-to-host-home') {
    router.push({ name: 'dashboard' });
  }
};

onMounted(() => {
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