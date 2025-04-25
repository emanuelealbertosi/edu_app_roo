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
      <p class="text-gray-600 mb-4">Ruolo: <span class="font-medium text-indigo-600">{{ authStore.user.role }}</span></p>

      <div class="mt-6 border-t pt-6">
        <h2 class="text-xl font-semibold mb-4 text-gray-700">Azioni Rapide</h2>

        <div v-if="authStore.userRole === 'Docente'" class="space-y-3">
          <p class="text-gray-700">Gestisci le tue risorse didattiche:</p>
          <div class="flex flex-wrap gap-4">
             <router-link :to="{ name: 'teacher-lessons' }" class="action-link bg-blue-500 hover:bg-blue-600">Le Mie Lezioni</router-link>
             <router-link :to="{ name: 'topics' }" class="action-link bg-green-500 hover:bg-green-600">Gestisci Argomenti</router-link>
             <router-link :to="{ name: 'subjects' }" class="action-link bg-purple-500 hover:bg-purple-600">Gestisci Materie</router-link>
          </div>
        </div>

        <div v-else-if="authStore.userRole === 'Studente'" class="space-y-3">
          <p class="text-gray-700">Accedi alle tue lezioni:</p>
           <div class="flex flex-wrap gap-4">
            <router-link :to="{ name: 'assigned-lessons' }" class="action-link bg-cyan-500 hover:bg-cyan-600">Lezioni Assegnate</router-link>
          </div>
       </div>

        <div v-else-if="authStore.userRole === 'Admin'" class="space-y-3">
          <p class="text-gray-700">Gestisci le impostazioni globali:</p>
           <div class="flex flex-wrap gap-4">
             <router-link :to="{ name: 'subjects' }" class="action-link bg-purple-500 hover:bg-purple-600">Gestisci Materie</router-link>
             <router-link :to="{ name: 'topics' }" class="action-link bg-green-500 hover:bg-green-600">Gestisci Argomenti</router-link>
           </div>
        </div>
      </div>

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