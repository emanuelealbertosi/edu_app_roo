import { ref, computed } from 'vue';
import { defineStore } from 'pinia';

// Definizione dell'interfaccia per le notifiche, come da piano
export interface UniformNotification {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number; // in ms, default 5000ms
  title?: string; // Titolo opzionale
}

export const useUiStore = defineStore('ui', () => {
  // State per contare le richieste API attive
  const activeApiRequests = ref(0);

  // State per le notifiche
  const notifications = ref<UniformNotification[]>([]);

  // Getter per determinare se c'è almeno una richiesta attiva
  const isLoadingApi = computed(() => activeApiRequests.value > 0);

  // Azioni per incrementare/decrementare il contatore
  function apiRequestStarted() {
    activeApiRequests.value++;
  }

  function apiRequestEnded() {
    // Assicurati che il contatore non vada sotto zero
    if (activeApiRequests.value > 0) {
      activeApiRequests.value--;
    }
  }

  // Actions per le notifiche
  function addNotification(notification: Omit<UniformNotification, 'id'>) {
    const id = Math.random().toString(36).substring(2, 9);
    const duration = notification.duration || 5000; // Default 5 secondi se non specificato

    notifications.value.push({ ...notification, id, duration });
    
    setTimeout(() => {
      removeNotification(id);
    }, duration);
  }

  function removeNotification(id: string) {
    notifications.value = notifications.value.filter(n => n.id !== id);
  }

  return { 
    // API Loading
    isLoadingApi, 
    apiRequestStarted, 
    apiRequestEnded,

    // Notifiche
    notifications,
    addNotification,
    removeNotification,
  };
});