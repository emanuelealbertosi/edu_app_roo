<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, RouterLink, type RouteLocationNormalizedLoaded } from 'vue-router';
import { ChevronRightIcon } from '@heroicons/vue/20/solid';

const route = useRoute();

interface BreadcrumbLink {
  text: string;
  to?: object;
  isHostLink?: boolean; // Aggiunta proprietà opzionale
}

const breadcrumbs = computed((): BreadcrumbLink[] => {
  if (route.meta && typeof route.meta.breadcrumb === 'function') {
    return (route.meta.breadcrumb as (route: RouteLocationNormalizedLoaded) => BreadcrumbLink[])(route);
  }
  return [];
});

// Funzione per gestire il click sul link che deve notificare l'host
const handleHostLinkClick = () => {
  // Invia un messaggio alla finestra genitore (l'host)
  window.parent.postMessage({ type: 'navigate-to-host-home' }, '*'); // Usa un target origin più specifico in produzione
};
</script>

<template>
  <nav v-if="breadcrumbs.length > 0" class="sticky top-0 z-10 bg-white py-2 shadow-md flex items-center space-x-2 text-sm font-medium text-gray-500 mb-4" aria-label="Breadcrumb">
    <template v-for="(crumb, index) in breadcrumbs" :key="index">
      <div class="flex items-center">
        <!-- Link speciale per notificare l'host -->
        <a
          v-if="crumb.isHostLink"
          href="#"
          @click.prevent="handleHostLinkClick"
          class="hover:text-gray-700 hover:underline"
        >
          {{ crumb.text }}
        </a>
        <!-- Link interno standard -->
        <RouterLink
          v-else-if="crumb.to"
          :to="crumb.to"
          class="hover:text-gray-700 hover:underline"
        >
          {{ crumb.text }}
        </RouterLink>
        <!-- Testo non cliccabile (ultimo elemento) -->
        <span v-else class="text-gray-700">
          {{ crumb.text }}
        </span>
        <ChevronRightIcon v-if="index < breadcrumbs.length - 1" class="h-5 w-5 ml-2 text-gray-400" aria-hidden="true" />
      </div>
    </template>
  </nav>
</template>

<style scoped>
/* Stili specifici se necessari */
</style>