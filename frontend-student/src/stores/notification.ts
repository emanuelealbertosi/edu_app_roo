import { ref } from 'vue';
import { defineStore } from 'pinia';

// Interfaccia per una singola notifica
export interface Notification {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning' | 'badge'; // Tipi di notifica
  duration?: number; // Durata in ms (opzionale, default gestito nel componente)
  icon?: string; // URL icona o nome classe icona (es. per badge)
  title?: string; // Titolo opzionale (es. nome badge)
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

  // Azione per aggiungere una notifica specifica per un badge, solo se non già notificata
  function addBadgeNotification(badgeId: number, badgeName: string, badgeImageUrl: string | null) {
      if (notifiedBadgeIds.value.has(badgeId)) {
          console.log(`Badge ${badgeId} (${badgeName}) già notificato, skip.`);
          return; // Non mostrare di nuovo la notifica
      }

      addNotification({
          title: "Traguardo Sbloccato!",
          message: `Hai ottenuto il badge: ${badgeName}`,
          type: 'badge',
          icon: badgeImageUrl || '/placeholder-badge.svg', // Usa placeholder se manca immagine
          duration: 7000 // Durata leggermente più lunga per i badge
      });

      // Aggiungi l'ID al set dei notificati
      notifiedBadgeIds.value.add(badgeId);
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