import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface Notification {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number; // in ms
title?: string; // Titolo opzionale per la notifica
}

export const useUiStore = defineStore('ui', () => {
  // State refs per richiedere l'apertura dei modali di aggiunta
  const requestOpenAddSubjectModal = ref(false);
  const requestOpenAddTopicModal = ref(false);
  const requestOpenAddLessonModal = ref(false);

  // State per le notifiche
  const notifications = ref<Notification[]>([]);

  // State per la visibilità globale dei modali
  const isModalOpen = ref(false);

  // Actions per richiedere l'apertura
  function requestAddSubject() {
    console.log("UI Store: Requesting Add Subject Modal");
    requestOpenAddSubjectModal.value = true;
  }
  function requestAddTopic() {
    console.log("UI Store: Requesting Add Topic Modal");
    requestOpenAddTopicModal.value = true;
  }
  function requestAddLesson() {
    console.log("UI Store: Requesting Add Lesson Modal");
    requestOpenAddLessonModal.value = true;
  } // Parentesi graffa mancante aggiunta

  // Actions per confermare che la richiesta è stata gestita (resetta lo stato)
  function clearAddSubjectRequest() {
    console.log("UI Store: Clearing Add Subject Request");
    requestOpenAddSubjectModal.value = false;
  }
  function clearAddTopicRequest() {
     console.log("UI Store: Clearing Add Topic Request");
    requestOpenAddTopicModal.value = false;
  }
  function clearAddLessonRequest() {
     console.log("UI Store: Clearing Add Lesson Request");
    requestOpenAddLessonModal.value = false;
  }

  // Actions per le notifiche
  function addNotification(notification: Omit<Notification, 'id'>) {
    const id = Math.random().toString(36).substring(2, 9);
    notifications.value.push({ ...notification, id });
    if (notification.duration) {
      setTimeout(() => {
        removeNotification(id);
      }, notification.duration);
    }
  }

  function removeNotification(id: string) {
    notifications.value = notifications.value.filter(n => n.id !== id);
  }

  // Actions per lo stato del modale
  function setModalOpen(isOpen: boolean) {
    isModalOpen.value = isOpen;
  }

  return {
    requestOpenAddSubjectModal,
    requestOpenAddTopicModal,
    requestOpenAddLessonModal,
    requestAddSubject,
    requestAddTopic,
    requestAddLesson,
    clearAddSubjectRequest,
    clearAddTopicRequest,
    clearAddLessonRequest,

    // Notifiche
    notifications,
    addNotification,
    removeNotification,

    // Visibilità modale
    isModalOpen,
    setModalOpen,
  };
});