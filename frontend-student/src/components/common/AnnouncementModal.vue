<template>
  <BaseModal 
    :show="announcementStore.isModalVisible" 
    :title="announcementStore.currentAnnouncement?.title"
    @close="handleClose"
  >
    <!-- Body -->
    <div 
      v-if="announcementStore.currentAnnouncement"
      class="p-6 prose max-w-none" 
      v-html="announcementStore.currentAnnouncement.content"
    ></div>

    <!-- Footer -->
    <template #footer>
        <div class="w-full flex justify-between items-center p-4">
            <button
                @click="handleDoNotShowAgain"
                class="text-sm text-neutral-dark hover:text-red-600 transition-colors"
            >
                Non mostrare più
            </button>
            <BaseButton
                @click="handleClose"
                variant="primary"
            >
                Chiudi
            </BaseButton>
        </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { useAnnouncementStore } from '@/stores/announcement';
import BaseModal from './BaseModal.vue';
import BaseButton from './BaseButton.vue';

const announcementStore = useAnnouncementStore();

const handleClose = () => {
  announcementStore.markAsReadAndShowNext();
};

const handleDoNotShowAgain = () => {
  announcementStore.markAsDoNotShowAgainAndHide();
};
</script>

<style scoped>
/* Stili per il contenuto HTML renderizzato da v-html */
.prose {
    /* Aggiungi qui eventuali stili di base se non già coperti da Tailwind Prose */
}
</style>