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
import { computed } from 'vue';

const lessonsAppBaseUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined)?.replace(/\/$/, '') || '');
const pageUrl = computed(() => `${lessonsAppBaseUrl.value}/courses?embedded=true`);
</script>

<style scoped>
.embedded-view-container {
  width: 100%;
  height: calc(100vh - 64px); /* Adjust 64px based on your header height */
  display: flex;
}
.embedded-iframe {
  flex-grow: 1;
  border: none;
}
</style>