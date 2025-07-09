<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, RouterLink, type RouteLocationNormalizedLoaded } from 'vue-router';
import { ChevronRightIcon } from '@heroicons/vue/20/solid';

const route = useRoute();

interface BreadcrumbLink {
  text: string;
  to?: object;
  isHostLink?: boolean;
  hostLinkType?: 'home' | 'assigned-lessons'; // Tipo di link per l'host
}

const breadcrumbs = computed((): BreadcrumbLink[] => {
  if (route.meta && typeof route.meta.breadcrumb === 'function') {
    return (route.meta.breadcrumb as (route: RouteLocationNormalizedLoaded) => BreadcrumbLink[])(route);
  }
  return [];
});

// Funzione generalizzata per gestire i click sui link che notificano l'host
const handleHostLinkClick = (type: 'home' | 'assigned-lessons' | undefined) => {
  if (!type) return;

  let messageType: string;
  switch (type) {
    case 'home':
      messageType = 'navigate-to-host-home';
      break;
    case 'assigned-lessons':
      messageType = 'navigate-to-host-assigned-lessons';
      break;
    default:
      console.warn('Tipo di link host non riconosciuto:', type);
      return;
  }
  // Invia un messaggio specifico alla finestra genitore (l'host)
  window.parent.postMessage({ type: messageType }, '*'); // Usa un target origin più specifico in produzione
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
          @click.prevent="handleHostLinkClick(crumb.hostLinkType)"
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