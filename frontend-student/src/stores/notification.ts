import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import type { Notification as ServerNotification, NotificationsState } from '@/types/notifications'; // Importa i nuovi tipi
import { getNotificationsAPI, markNotificationAsReadAPI, markAllNotificationsAsReadAPI } from '@/api/notifications'; // Importa le nuove API

// Interfaccia semplificata per il Badge (da allineare con l'API backend)
// Duplichiamo l'interfaccia qui o la importiamo da un file condiviso
interface BadgeInfo {
  id: number;
  name: string;
  description?: string | null;
  image?: string | null;
  animation_class?: string | null;
}

// Interfaccia per una singola notifica TOAST locale
export interface ToastNotification {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning' | 'badge';
  duration?: number;
  icon?: string; // Per tipi standard
  title?: string; // Per tipi standard
  badgeInfo?: BadgeInfo; // Nuovo: campo specifico per le notifiche badge
}

// ID univoco per le notifiche TOAST
let nextToastId = 0;

export const useNotificationStore = defineStore('notification', () => {
  // --- State per Notifiche TOAST Locali ---
  const toastNotifications = ref<ToastNotification[]>([]);
  const notifiedBadgeIds = ref(new Set<number>()); // Per tracciare badge già notificati via TOAST

  // --- State per Notifiche persistenti dal Server (Campanella) ---
  const serverNotifications = ref<ServerNotification[]>([]);
  const unreadServerNotificationCount = ref<number>(0);
  const isLoadingServerNotifications = ref<boolean>(false);
  const serverNotificationsError = ref<string | null>(null);

  // --- Azioni per Notifiche TOAST Locali ---
  function addToastNotification(notification: Omit<ToastNotification, 'id'>) {
    const id = nextToastId++;
    const duration = notification.duration || 5000; // Default 5 secondi

    toastNotifications.value.push({ ...notification, id });

    setTimeout(() => {
      removeToastNotification(id);
    }, duration);
  }

  function addBadgeToastNotification(badge: BadgeInfo) {
      if (notifiedBadgeIds.value.has(badge.id)) {
          console.log(`Badge ${badge.id} (${badge.name}) già notificato (toast), skip.`);
          return;
      }
      addToastNotification({
          message: `Hai ottenuto il badge: ${badge.name}!`,
          type: 'badge',
          badgeInfo: badge,
          duration: 7000
      });
      notifiedBadgeIds.value.add(badge.id);
  }

  function removeToastNotification(id: number) {
    toastNotifications.value = toastNotifications.value.filter(n => n.id !== id);
  }

  // --- Getters per Notifiche persistenti dal Server ---
  const unreadServerNotifications = computed(() => 
    serverNotifications.value.filter(n => !n.is_read)
  );

  const hasUnreadServerNotifications = computed(() => 
    unreadServerNotificationCount.value > 0
  );

  // --- Azioni per Notifiche persistenti dal Server ---
  async function fetchServerNotifications(onlyUnread: boolean = false) {
    isLoadingServerNotifications.value = true;
    serverNotificationsError.value = null;
    try {
      const data = await getNotificationsAPI(onlyUnread);
      // Se stiamo recuperando solo le non lette, potremmo voler solo aggiornare il conteggio
      // e non sovrascrivere l'intero array se già popolato.
      // Per semplicità iniziale, sovrascriviamo e ricalcoliamo.
      serverNotifications.value = data;
      unreadServerNotificationCount.value = data.filter(n => !n.is_read).length;
    } catch (error: any) {
      console.error('Failed to fetch server notifications:', error);
      serverNotificationsError.value = error.message || 'Errore nel recupero notifiche.';
      // Mantenere i dati vecchi o svuotare? Per ora manteniamo.
    } finally {
      isLoadingServerNotifications.value = false;
    }
  }

  async function markServerNotificationAsRead(notificationId: number) {
    try {
      await markNotificationAsReadAPI(notificationId);
      const notification = serverNotifications.value.find(n => n.id === notificationId);
      if (notification && !notification.is_read) {
        notification.is_read = true;
        unreadServerNotificationCount.value = Math.max(0, unreadServerNotificationCount.value - 1);
      }
    } catch (error: any) {
      console.error(`Failed to mark server notification ${notificationId} as read:`, error);
      // Gestire l'errore, magari mostrando un toast di errore
      addToastNotification({ type: 'error', message: 'Errore nel segnare la notifica come letta.' });
    }
  }

  async function markAllServerNotificationsAsRead() {
    try {
      await markAllNotificationsAsReadAPI();
      serverNotifications.value.forEach(n => n.is_read = true);
      unreadServerNotificationCount.value = 0;
    } catch (error: any) {
      console.error('Failed to mark all server notifications as read:', error);
      addToastNotification({ type: 'error', message: 'Errore nel segnare tutte le notifiche come lette.' });
    }
  }

  return { 
    // Toast notifications
    toastNotifications, 
    addToastNotification,
    removeToastNotification,
    addBadgeToastNotification,
    notifiedBadgeIds,

    // Server (bell) notifications
    serverNotifications,
    unreadServerNotificationCount,
    isLoadingServerNotifications,
    serverNotificationsError,
    fetchServerNotifications,
    markServerNotificationAsRead,
    markAllServerNotificationsAsRead,
    unreadServerNotifications, // getter
    hasUnreadServerNotifications // getter
  };
});