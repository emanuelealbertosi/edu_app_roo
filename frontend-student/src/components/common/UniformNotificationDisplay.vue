<template>
  <div class="fixed bottom-0 right-0 p-4 space-y-2 z-50 max-w-sm w-full">
    <transition-group name="list-transition">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="p-4 rounded-md shadow-lg text-white flex items-start space-x-3"
        :class="{
          'bg-green-500': notification.type === 'success',
          'bg-red-500': notification.type === 'error',
          'bg-blue-500': notification.type === 'info',
          'bg-yellow-500': notification.type === 'warning',
        }"
      >
        <!-- Icona -->
        <div class="flex-shrink-0 flex items-center justify-center pt-1">
          <span v-if="notification.type === 'success'" class="text-xl">✅</span>
          <span v-else-if="notification.type === 'error'" class="text-xl">❌</span>
          <span v-else-if="notification.type === 'info'" class="text-xl">ℹ️</span>
          <span v-else-if="notification.type === 'warning'" class="text-xl">⚠️</span>
        </div>

        <!-- Contenuto Testuale -->
        <div class="flex-grow">
          <p v-if="notification.title" class="font-bold">{{ notification.title }}</p>
          <p>{{ notification.message }}</p>
        </div>

        <!-- Pulsante Chiudi -->
        <button
            @click="removeNotification(notification.id)"
            class="ml-auto -mx-1.5 -my-1.5 bg-transparent rounded-lg focus:ring-2 p-1.5 inline-flex h-8 w-8 text-white hover:text-gray-200 focus:outline-none"
            aria-label="Chiudi notifica"
          >
            <span class="sr-only">Chiudi</span>
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
// Importa dallo store notification di frontend-student e usa i nuovi state/azioni per le notifiche uniformi
import { useNotificationStore, type UniformNotification } from '@/stores/notification';

const notificationStore = useNotificationStore();

// Usa il nuovo state uniformToastNotifications e la nuova action removeUniformToastNotification
const notifications = computed(() => notificationStore.uniformToastNotifications as UniformNotification[]);

const removeNotification = (id: string) => {
  notificationStore.removeUniformToastNotification(id);
};
</script>

<style scoped>
.list-transition-enter-active,
.list-transition-leave-active {
  transition: all 0.5s ease;
}
.list-transition-enter-from,
.list-transition-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* Assicurati che lo z-index sia abbastanza alto per apparire sopra altri elementi */
/* Potrebbe essere necessario un z-index più alto se NotificationContainer.vue per i badge ha uno z-index simile */
.z-50 {
  z-index: 50; /* Mantenuto da fe-lessons, valutare se aumentarlo a 51 o più per coesistere con l'altro container */
}
</style>