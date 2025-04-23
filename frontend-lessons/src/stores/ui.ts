import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useUiStore = defineStore('ui', () => {
  // State refs per richiedere l'apertura dei modali di aggiunta
  const requestOpenAddSubjectModal = ref(false);
  const requestOpenAddTopicModal = ref(false);
  const requestOpenAddLessonModal = ref(false);

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
  };
});