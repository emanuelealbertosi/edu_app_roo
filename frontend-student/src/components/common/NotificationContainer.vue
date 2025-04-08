<script setup lang="ts">
import { useNotificationStore, type Notification } from '@/stores/notification';

const notificationStore = useNotificationStore();

// Funzione per ottenere classi CSS in base al tipo di notifica
const getNotificationClasses = (notification: Notification) => {
  return {
    'bg-green-100 border-green-500 text-green-700': notification.type === 'success',
    'bg-red-100 border-red-500 text-red-700': notification.type === 'error',
    'bg-blue-100 border-blue-500 text-blue-700': notification.type === 'info',
    'bg-yellow-100 border-yellow-500 text-yellow-700': notification.type === 'warning',
    'bg-purple-100 border-purple-500 text-purple-700': notification.type === 'badge', // Stile per badge
  };
};
</script>

<template>
  <div class="notification-container fixed bottom-5 right-5 z-50 space-y-3 max-w-sm w-full">
    <transition-group name="notification-item">
      <div 
        v-for="notification in notificationStore.notifications" 
        :key="notification.id"
        class="notification-item border-l-4 p-4 rounded-md shadow-lg flex items-start space-x-3"
        :class="getNotificationClasses(notification)"
        role="alert"
      >
        <!-- Icona (opzionale o specifica per tipo) -->
        <div v-if="notification.icon || notification.type === 'badge'" class="flex-shrink-0">
           <img v-if="notification.type === 'badge'" :src="notification.icon" :alt="notification.title || 'Badge'" class="w-10 h-10 object-contain">
           <!-- Altre icone per altri tipi potrebbero andare qui -->
           <span v-else-if="notification.type === 'success'" class="text-xl">✅</span>
           <span v-else-if="notification.type === 'error'" class="text-xl">❌</span>
           <span v-else-if="notification.type === 'info'" class="text-xl">ℹ️</span>
           <span v-else-if="notification.type === 'warning'" class="text-xl">⚠️</span>
        </div>

        <!-- Contenuto Testuale -->
        <div class="flex-grow">
          <p v-if="notification.title" class="font-bold">{{ notification.title }}</p>
          <p class="text-sm">{{ notification.message }}</p>
        </div>

        <!-- Pulsante Chiudi (opzionale) -->
        <button 
          @click="notificationStore.removeNotification(notification.id)" 
          class="ml-auto -mx-1.5 -my-1.5 bg-transparent rounded-lg focus:ring-2 p-1.5 inline-flex h-8 w-8" 
          :class="[
             {'text-green-500 focus:ring-green-400 hover:bg-green-200': notification.type === 'success'},
             {'text-red-500 focus:ring-red-400 hover:bg-red-200': notification.type === 'error'},
             {'text-blue-500 focus:ring-blue-400 hover:bg-blue-200': notification.type === 'info'},
             {'text-yellow-500 focus:ring-yellow-400 hover:bg-yellow-200': notification.type === 'warning'},
             {'text-purple-500 focus:ring-purple-400 hover:bg-purple-200': notification.type === 'badge'},
          ]"
          aria-label="Chiudi"
        >
          <span class="sr-only">Chiudi</span>
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>
        </button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
/* Transizioni per entrata/uscita notifiche */
.notification-item-enter-active,
.notification-item-leave-active {
  transition: all 0.5s ease;
}
.notification-item-enter-from,
.notification-item-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
.notification-item-move { /* Per riordinamento fluido se una notifica viene rimossa */
  transition: transform 0.5s ease;
}
</style>