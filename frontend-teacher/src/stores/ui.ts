import { ref, computed } from 'vue';
import { defineStore } from 'pinia';

export const useUiStore = defineStore('ui', () => {
  // State per contare le richieste API attive
  const activeApiRequests = ref(0);

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

  return { 
    isLoadingApi, 
    apiRequestStarted, 
    apiRequestEnded 
  };
});