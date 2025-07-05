import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import type { Announcement } from '@/types/announcements';
import { 
  getAnnouncementsAPI, 
  markAnnouncementAsReadAPI, 
  markAnnouncementAsDoNotShowAgainAPI 
} from '@/api/announcements';

export const useAnnouncementStore = defineStore('announcement', () => {
  // --- State ---
  const announcements = ref<Announcement[]>([]);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  // --- Getters ---
  const hasAnnouncements = computed(() => announcements.value.length > 0);
  const currentAnnouncement = computed(() => hasAnnouncements.value ? announcements.value[0] : null);
  const isModalVisible = ref<boolean>(false);

  // --- Actions ---

  /**
   * Recupera gli avvisi dal backend e mostra il primo, se presente.
   */
  async function fetchAnnouncements() {
    if (isLoading.value) return;
    isLoading.value = true;
    error.value = null;
    try {
      const data = await getAnnouncementsAPI();
      announcements.value = data;
      if (hasAnnouncements.value) {
        isModalVisible.value = true;
      }
    } catch (e: any) {
      error.value = e.message || 'Errore nel recupero degli avvisi.';
      console.error(error.value);
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Passa all'avviso successivo o chiude la modale se non ce ne sono più.
   */
  function showNextAnnouncement() {
    if (announcements.value.length > 0) {
      announcements.value.shift(); // Rimuove il primo elemento
    }
    if (!hasAnnouncements.value) {
      isModalVisible.value = false;
    }
  }

  /**
   * Segna l'avviso corrente come letto e mostra il successivo.
   */
  async function markAsReadAndShowNext() {
    if (!currentAnnouncement.value) return;
    
    try {
      await markAnnouncementAsReadAPI(currentAnnouncement.value.id);
      showNextAnnouncement();
    } catch (e: any) {
      error.value = `Errore nel segnare l'avviso come letto: ${e.message}`;
      console.error(error.value);
      // Nonostante l'errore, proviamo a mostrare il successivo per non bloccare l'utente
      showNextAnnouncement();
    }
  }

  /**
   * Segna l'avviso corrente come "non mostrare più" e chiude la modale.
   */
  async function markAsDoNotShowAgainAndHide() {
    if (!currentAnnouncement.value) return;

    try {
      await markAnnouncementAsDoNotShowAgainAPI(currentAnnouncement.value.id);
      isModalVisible.value = false;
      // Svuotiamo la lista per sicurezza, anche se il backend non lo rimanderà
      announcements.value = []; 
    } catch (e: any) {
      error.value = `Errore nell'impostazione "non mostrare più": ${e.message}`;
      console.error(error.value);
      // Chiudiamo comunque la modale per non bloccare l'utente
      isModalVisible.value = false;
    }
  }

  /**
   * Chiude forzatamente la modale senza azioni sul backend.
   */
  function closeModal() {
    isModalVisible.value = false;
  }

  return {
    // State
    announcements,
    isLoading,
    error,
    isModalVisible,
    // Getters
    hasAnnouncements,
    currentAnnouncement,
    // Actions
    fetchAnnouncements,
    markAsReadAndShowNext,
    markAsDoNotShowAgainAndHide,
    closeModal,
  };
});