<template>
  <div
    class="animated-badge inline-block text-center"
    :class="{ 'not-earned': !badge.isEarned }"
    :title="badge.description || badge.name"
  >
    <div
      class="badge-icon-wrapper relative w-72 h-72 mx-auto mb-1 overflow-hidden rounded-full shadow-xl border-2 border-purple-300 cursor-pointer"
      @click="handleBadgeClick"
    >
      <div v-if="!badge.isEarned" class="lock-overlay">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-8 h-8">
          <path fill-rule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v7a2 2 0 002 2h10a2 2 0 002-2v-7a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" clip-rule="evenodd" />
        </svg>
      </div>

      <img
        v-if="!badge.isEarned && (badge.mediaType === 'VIDEO_MP4' || badge.mediaType === 'IMAGE_GIF') && badge.thumbnailUrl"
        :src="badge.thumbnailUrl"
        :alt="badge.name + ' thumbnail'"
        class="badge-media static-preview"
      />

      <img
        v-else-if="!badge.isEarned && badge.fileUrl"
        :src="badge.fileUrl"
        :alt="badge.name"
        class="badge-media"
      />
      
      <video
        v-else-if="badge.isEarned && badge.mediaType === 'VIDEO_MP4' && badge.fileUrl"
        :src="badge.fileUrl"
        class="badge-media"
        autoplay
        loop
        muted
        playsinline
        :aria-label="badge.name"
      ></video>
      
      <img
        v-else-if="badge.isEarned && (badge.mediaType === 'IMAGE_STATIC' || badge.mediaType === 'IMAGE_GIF') && badge.fileUrl"
        :src="badge.fileUrl"
        :alt="badge.name"
        class="badge-media drop-shadow-md"
      />

      <div v-else class="w-full h-full rounded-full bg-neutral-light flex items-center justify-center text-neutral-dark text-3xl shadow-inner">
        ?
      </div>
    </div>
    <p class="badge-name text-lg font-semibold text-purple-600 truncate w-full">
      {{ badge.name }}
    </p>
  </div>
</template>

<script setup lang="ts">
import type { Badge } from '@/api/rewards'; // Importa il tipo Badge corretto

// Rimuoviamo l'interfaccia BadgeInfo locale e usiamo Badge importato
// interface BadgeInfo {
//   id: number;
//   name: string;
//   description?: string | null;
//   fileUrl?: string | null;
//   mediaType?: 'IMAGE_STATIC' | 'IMAGE_GIF' | 'VIDEO_MP4' | string;
//   thumbnailUrl?: string | null;
//   isEarned: boolean;
// }

const props = defineProps<{
  badge: Badge; // Usa il tipo Badge importato
}>();

const emit = defineEmits<{
  (e: 'open-modal', badgeInfo: Badge): void; // Emetti il tipo Badge importato
}>();

const handleBadgeClick = () => {
  if (props.badge.isEarned) {
    emit('open-modal', props.badge);
  }
};

</script>

<style scoped>
.animated-badge.not-earned .badge-icon-wrapper {
  filter: grayscale(100%);
  opacity: 0.6;
}

.lock-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  color: #FFD700; /* Colore dorato per il lucchetto */
  pointer-events: none;
}
.lock-overlay svg {
  filter: drop-shadow(0 1px 1px rgba(0,0,0,0.5));
}



.badge-icon-wrapper {
  /* filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.2)); */
}
.badge-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>