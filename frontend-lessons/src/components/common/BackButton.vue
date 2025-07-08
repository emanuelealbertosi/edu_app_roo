<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { ChevronLeftIcon } from '@heroicons/vue/24/solid';
import { canGoBack, goBack } from '@/utils/navigationHistory';

const router = useRouter();

// List of route names where the back button should not be displayed.
const hiddenOnRoutes = ['dashboard']; // Assuming 'dashboard' is the main route name

const isVisible = computed(() => {
  if (!canGoBack.value) {
    return false;
  }
  // We now use the router's current route to check the name, as our history only stores paths.
  const currentRouteName = router.currentRoute.value.name?.toString().toLowerCase() || '';
  return !hiddenOnRoutes.includes(currentRouteName);
});

const handleGoBack = () => {
  goBack(router);
};
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