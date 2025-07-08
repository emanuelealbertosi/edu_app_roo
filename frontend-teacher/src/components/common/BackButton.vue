<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ChevronLeftIcon } from '@heroicons/vue/24/solid';
import { canGoBack as canGoBackLocally, goBack } from '@/utils/navigationHistory';

const router = useRouter();
const route = useRoute();

// State to track if the iframe can go back
const iframeCanGoBack = ref(false);

// List of route names where the back button should not be displayed.
const hiddenOnRoutes = ['dashboard'];

// Combined logic to determine if the back button should be visible
const isVisible = computed(() => {
  const onHiddenRoute = hiddenOnRoutes.includes(route.name?.toString().toLowerCase() || '');
  if (onHiddenRoute) {
    return false;
  }
  // Visible if either the main app or the iframe can go back
  return canGoBackLocally.value || iframeCanGoBack.value;
});

const handleGoBack = () => {
  // Prioritize iframe navigation if it can go back
  if (iframeCanGoBack.value) {
    // Find the iframe and send a message to it
    const iframe = document.querySelector('iframe'); // Adjust selector if needed
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.postMessage({ type: 'goBack' }, '*'); // Use specific origin in prod
    }
  } else {
    // Otherwise, use the local goBack function
    goBack(router);
  }
};

// Message handler for updates from the iframe
const handleMessage = (event: MessageEvent) => {
  // Add origin check for security
  if (event.data && event.data.type === 'canGoBackUpdate') {
    iframeCanGoBack.value = event.data.value;
  }
};

// Register and unregister the event listener
onMounted(() => {
  window.addEventListener('message', handleMessage);
});

onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage);
});
</script>

<template>
  <div v-if="isVisible" class="mb-4">
    <button
      @click="handleGoBack"
      class="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-focus"
      aria-label="Torna alla pagina precedente"
    >
      <ChevronLeftIcon class="h-5 w-5 mr-2" />
      Indietro
    </button>
  </div>
</template>

<style scoped>
/* Add any specific styles if needed */
</style>