<template>
  <div class="dashboard-container p-6">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6">
        <h1 class="text-2xl font-semibold">Dashboard Lezioni</h1> <!-- Stile titolo adattato -->
    </div>
    <div v-if="sharedAuthStore.user" class="bg-white p-6 rounded-lg shadow-md"> <!-- Usa sharedAuthStore -->
      <p class="text-xl mb-2">
        Benvenuto/a, <span class="font-semibold">{{ sharedAuthStore.user.first_name || sharedAuthStore.user.username || 'Utente' }}</span>! <!-- Usa sharedAuthStore -->
      </p>
      <!-- Rimossa visualizzazione ruolo e sezione Azioni Rapide -->
    </div>
    <div v-else class="text-center text-gray-500 mt-10">
      <p>Caricamento dati utente...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa lo store condiviso
// import { useRouter } from 'vue-router'; // Rimosso - non utilizzato

const sharedAuthStore = useSharedAuthStore(); // Usa lo store condiviso

// La logica per fetchUser è gestita dalla guardia di navigazione ora
// if (!authStore.user && authStore.accessToken) {
//   authStore.fetchUser();
// }

// La logica di logout è gestita dal pulsante nella sidebar
// const router = useRouter();
// const handleLogout = () => {
//   authStore.logout();
//   router.push({ name: 'teacher-admin-login' }); // Usa il nome corretto
// };
</script>

<style scoped>
/* Stili specifici per i link rapidi */
.action-link {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  color: white;
  border-radius: 0.375rem; /* rounded-md */
  text-decoration: none;
  font-weight: 500; /* medium */
  transition: background-color 0.2s ease-in-out;
}
</style>