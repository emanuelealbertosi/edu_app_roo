<template>
  <div class="dashboard-container p-6">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6">
        <h1 class="text-2xl font-semibold">Dashboard Lezioni</h1> <!-- Stile titolo adattato -->
    </div>
    <div v-if="authStore.user" class="bg-white p-6 rounded-lg shadow-md">
      <p class="text-xl mb-2">
        Benvenuto/a, <span class="font-semibold">{{ authStore.user.first_name || authStore.user.username || 'Utente' }}</span>!
      </p>
      <!-- Rimossa visualizzazione ruolo e sezione Azioni Rapide -->
    </div>
    <div v-else class="text-center text-gray-500 mt-10">
      <p>Caricamento dati utente...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
// import { useRouter } from 'vue-router'; // Rimosso - non utilizzato

const authStore = useAuthStore();

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