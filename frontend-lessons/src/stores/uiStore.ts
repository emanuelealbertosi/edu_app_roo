import { defineStore } from 'pinia';

export const useUiStore = defineStore('ui', {
  state: () => ({
    isModalOpen: false,
  }),
  actions: {
    setModalOpen(isOpen: boolean) {
      this.isModalOpen = isOpen;
    },
  },
});