<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content-iframe">
      <div class="modal-header">
        <h3 class="text-xl font-semibold">{{ title }}</h3>
        <button @click="close" class="close-button">&times;</button>
      </div>
      <div class="modal-body">
        <iframe :src="src" frameborder="0" width="100%" height="100%"></iframe>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  src: string;
  title: string;
}>();

const emit = defineEmits(['close']);

const close = () => {
  emit('close');
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-content-iframe {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  width: 90vw;
  height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #eee;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
}

.modal-body {
  flex-grow: 1;
  padding: 0;
  overflow: hidden;
}

iframe {
  display: block;
}
</style>