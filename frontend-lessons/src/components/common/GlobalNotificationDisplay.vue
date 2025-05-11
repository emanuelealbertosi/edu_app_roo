<template>
  <div class="fixed bottom-0 right-0 p-4 space-y-2 z-50 max-w-sm w-full">
    <transition-group name="list-transition">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="p-4 rounded-md shadow-lg text-white"
        :class="{
          'bg-green-500': notification.type === 'success',
          'bg-red-500': notification.type === 'error',
          'bg-blue-500': notification.type === 'info',
          'bg-yellow-500': notification.type === 'warning',
        }"
      >
        <div class="flex justify-between items-start">
          <p class="flex-grow">{{ notification.message }}</p>
          <button
            @click="removeNotification(notification.id)"
            class="ml-2 text-white hover:text-gray-200 focus:outline-none"
            aria-label="Chiudi notifica"
          >
            &times;
          </button>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useUiStore } from '@/stores/ui';

const uiStore = useUiStore();

const notifications = computed(() => uiStore.notifications);
const removeNotification = (id: string) => {
  uiStore.removeNotification(id);
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
.z-50 {
  z-index: 50;
}
</style>