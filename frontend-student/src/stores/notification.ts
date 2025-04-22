import { ref } from 'vue';
import { defineStore } from 'pinia';

// Interfaccia semplificata per il Badge (da allineare con l'API backend)
// Duplichiamo l'interfaccia qui o la importiamo da un file condiviso
interface BadgeInfo {
  id: number;
  name: string;
  description?: string | null;
  image?: string | null;
  animation_class?: string | null;
}

// Interfaccia per una singola notifica
export interface Notification {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning' | 'badge';
  duration?: number;
  // Modificato: icon e title diventano specifici per tipi non-badge
  icon?: string; // Per tipi standard
  title?: string; // Per tipi standard
  // Nuovo: campo specifico per le notifiche badge
  badgeInfo?: BadgeInfo;
}

// ID univoco per le notifiche
let nextId = 0;

export const useNotificationStore = defineStore('notification', () => {
  // State: lista delle notifiche attive
  const notifications = ref<Notification[]>([]);
  // State: Set per tracciare gli ID dei badge già notificati in questa sessione
  const notifiedBadgeIds = ref(new Set<number>());

  // Azione per aggiungere una notifica
  function addNotification(notification: Omit<Notification, 'id'>) {
    const id = nextId++;
    const duration = notification.duration || 5000; // Default 5 secondi

    notifications.value.push({ ...notification, id });

    // Rimuovi la notifica dopo la durata specificata
    setTimeout(() => {
      removeNotification(id);
    }, duration);
  }

  // Modificato: Accetta l'intero oggetto BadgeInfo
  function addBadgeNotification(badge: BadgeInfo) {
      if (notifiedBadgeIds.value.has(badge.id)) {
          console.log(`Badge ${badge.id} (${badge.name}) già notificato, skip.`);
          return;
      }

      addNotification({
          // title: "Traguardo Sbloccato!", // Il titolo è ora nel badgeInfo
          message: `Hai ottenuto il badge: ${badge.name}`,
          type: 'badge',
          badgeInfo: badge, // Passa l'intero oggetto badge
          duration: 7000
      });

      notifiedBadgeIds.value.add(badge.id);
  }

  // Azione per rimuovere una notifica tramite ID
  function removeNotification(id: number) {
    notifications.value = notifications.value.filter(n => n.id !== id);
  }

  return { 
    notifications, 
    addNotification,
    removeNotification,
    addBadgeNotification, // Esporta la funzione specifica per badge
    notifiedBadgeIds // Esporta (opzionale, per debug o reset)
  };
});