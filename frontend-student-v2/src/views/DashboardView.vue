<template>
  <div>
    <h1 class="text-3xl font-bold mb-4">Dashboard Studente</h1>
    <p v-if="authStore.user">Benvenuto, {{ authStore.user.first_name }}!</p>
    <p v-else>Caricamento dati utente...</p>
    <div class="mt-6 p-4 bg-base-200 rounded-box">
      <h2 class="text-xl mb-2">Contenuto Dashboard (Placeholder)</h2>
      <p>Qui verranno visualizzati i quiz disponibili, i progressi, ecc.</p>
      <!-- Esempio di componente DaisyUI -->
      <button class="btn btn-accent mt-4">Azione Esempio</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();

// Potremmo voler chiamare fetchUser qui se non è già stato fatto all'avvio dello store
// import { onMounted } from 'vue';
// onMounted(() => {
//   if (!authStore.user && authStore.isAuthenticated) {
//     authStore.fetchUser();
//   }
// });
</script>

<style scoped>
/* Stili specifici per la dashboard */
</style>