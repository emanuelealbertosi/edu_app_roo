import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import type { Notification as ServerNotification } from '@/types/notifications'; // Rimosso NotificationsState se non usato direttamente qui
import { getNotificationsAPI, markNotificationAsReadAPI, markAllNotificationsAsReadAPI } from '@/api/notifications';

// --- Interfaccia per Notifiche Toast Uniformi (come da piano) ---
export interface UniformNotification {
  id: string; // ID stringa
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number; // in ms, default 5000ms
  title?: string; // Titolo opzionale
}

// --- Interfacce Esistenti per Notifiche Badge e Server (MANTENUTE INVARIATE) ---
interface BadgeInfo {
  id: number;
  name: string;
  description?: string | null;
  image?: string | null;
  animation_class?: string | null;
}

// Interfaccia per una singola notifica TOAST locale (USATA PER I BADGE)
export interface LegacyToastNotification { // Rinominata per chiarezza
  id: number; // ID numerico
  message: string;
  type: 'success' | 'error' | 'info' | 'warning' | 'badge';
  duration?: number;
  icon?: string; 
  title?: string; 
  badgeInfo?: BadgeInfo;
}

let nextLegacyToastId = 0; // Per LegacyToastNotification

export const useNotificationStore = defineStore('notification', () => {
  // --- State per Notifiche TOAST Uniformi (NUOVO) ---
  const uniformToastNotifications = ref<UniformNotification[]>([]);

  // --- State per Notifiche TOAST Locali Legacy (PER BADGE - MANTENUTO) ---
  const legacyToastNotifications = ref<LegacyToastNotification[]>([]); // Rinominato ref
  const notifiedBadgeIds = ref(new Set<number>()); 

  // --- State per Notifiche persistenti dal Server (Campanella - MANTENUTO INVARIATO) ---
  const serverNotifications = ref<ServerNotification[]>([]);
  const unreadServerNotificationCount = ref<number>(0);
  const isLoadingServerNotifications = ref<boolean>(false);
  const serverNotificationsError = ref<string | null>(null);

  // --- Azioni per Notifiche TOAST Uniformi (NUOVE) ---
  function addUniformToastNotification(notification: Omit<UniformNotification, 'id'>) {
    const id = Math.random().toString(36).substring(2, 9); // ID stringa
    const duration = notification.duration || 5000; // Default 5 secondi

    uniformToastNotifications.value.push({ ...notification, id, duration });
    
    setTimeout(() => {
      removeUniformToastNotification(id);
    }, duration);
  }

  function removeUniformToastNotification(id: string) {
    uniformToastNotifications.value = uniformToastNotifications.value.filter(n => n.id !== id);
  }

  // --- Azioni per Notifiche TOAST Locali Legacy (PER BADGE - MANTENUTE E ADATTATE AL NOME DEL REF) ---
  function addLegacyToastNotification(notification: Omit<LegacyToastNotification, 'id'>) { // Rinominata funzione per chiarezza
    const id = nextLegacyToastId++;
    const duration = notification.duration || 5000;

    legacyToastNotifications.value.push({ ...notification, id }); // Usa legacyToastNotifications

    setTimeout(() => {
      removeLegacyToastNotification(id); // Usa la rimozione corretta
    }, duration);
  }

  function addBadgeToastNotification(badge: BadgeInfo) { // MANTENUTA, usa addLegacyToastNotification
      if (notifiedBadgeIds.value.has(badge.id)) {
          console.log(`Badge ${badge.id} (${badge.name}) già notificato (toast), skip.`);
          return;
      }
      addLegacyToastNotification({ // Chiama la versione legacy
          message: `Hai ottenuto il badge: ${badge.name}!`,
          type: 'badge',
          badgeInfo: badge,
          duration: 7000
      });
      notifiedBadgeIds.value.add(badge.id);
  }

  function removeLegacyToastNotification(id: number) { // Rinominata funzione per chiarezza
    legacyToastNotifications.value = legacyToastNotifications.value.filter(n => n.id !== id); // Usa legacyToastNotifications
  }

  // --- Getters per Notifiche persistenti dal Server (MANTENUTI INVARIATI) ---
  const unreadServerNotifications = computed(() => 
    serverNotifications.value.filter(n => !n.is_read)
  );

  const hasUnreadServerNotifications = computed(() => 
    unreadServerNotificationCount.value > 0
  );

  // --- Azioni per Notifiche persistenti dal Server (MANTENUTE INVARIATE, MA LE CHIAMATE A addToastNotification PER ERRORI VANNO AGGIORNATE) ---
  async function fetchServerNotifications(onlyUnread: boolean = false) {
    isLoadingServerNotifications.value = true;
    serverNotificationsError.value = null;
    try {
      const data = await getNotificationsAPI(onlyUnread);
      serverNotifications.value = data;
      unreadServerNotificationCount.value = data.filter(n => !n.is_read).length;
    } catch (error: any) {
      console.error('Failed to fetch server notifications:', error);
      serverNotificationsError.value = error.message || 'Errore nel recupero notifiche.';
      // QUI: Usare il NUOVO sistema per notificare l'errore
      addUniformToastNotification({ type: 'error', message: serverNotificationsError.value || 'Errore sconosciuto nel recupero notifiche.' });
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
      // QUI: Usare il NUOVO sistema per notificare l'errore
      addUniformToastNotification({ type: 'error', message: (error as Error).message || 'Errore nel segnare la notifica come letta.' });
    }
  }

  async function markAllServerNotificationsAsRead() {
    try {
      await markAllNotificationsAsReadAPI();
      serverNotifications.value.forEach(n => n.is_read = true);
      unreadServerNotificationCount.value = 0;
    } catch (error: any) {
      console.error('Failed to mark all server notifications as read:', error);
      // QUI: Usare il NUOVO sistema per notificare l'errore
      addUniformToastNotification({ type: 'error', message: (error as Error).message || 'Errore nel segnare tutte le notifiche come lette.' });
    }
  }

  return { 
    // Notifiche Toast Uniformi (NUOVE)
    uniformToastNotifications,
    addUniformToastNotification,
    removeUniformToastNotification,

    // Notifiche Toast Legacy (PER BADGE - MANTENUTE)
    legacyToastNotifications, // Espone il ref rinominato
    addLegacyToastNotification, // Espone la funzione rinominata
    removeLegacyToastNotification, // Espone la funzione rinominata
    addBadgeToastNotification, // Questa rimane perché usa la logica legacy
    notifiedBadgeIds,

    // Notifiche Server (Campanella - MANTENUTE)
    serverNotifications,
    unreadServerNotificationCount,
    isLoadingServerNotifications,
    serverNotificationsError,
    fetchServerNotifications,
    markServerNotificationAsRead,
    markAllServerNotificationsAsRead,
    unreadServerNotifications, 
    hasUnreadServerNotifications 
  };
});