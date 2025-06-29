<template>
  <div class="dashboard-container p-6">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6">
        <h1 class="text-2xl font-semibold">Dashboard Lezioni</h1> <!-- Stile titolo adattato -->
    </div>
    <div v-if="sharedAuthStore.user" class="bg-white p-6 rounded-lg shadow-md mb-6"> <!-- Usa sharedAuthStore, aggiunto mb-6 -->
      <p class="text-xl mb-2">
        Benvenuto/a, <span class="font-semibold">{{ sharedAuthStore.user.first_name || sharedAuthStore.user.username || 'Utente' }}</span>! <!-- Usa sharedAuthStore -->
      </p>
      <!-- Rimossa visualizzazione ruolo e sezione Azioni Rapide -->
    </div>

    <!-- Sezione Link di Navigazione -->
    <div v-if="sharedAuthStore.user" class="bg-white p-6 rounded-lg shadow-md">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold">Menu Principale</h2>
            <button
                @click="handleLogout"
                class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out">
                Logout
            </button>
        </div>
        <nav>
            <ul class="space-y-2">
                <!-- Link per Admin/Teacher -->
                <template v-if="sharedAuthStore.userRole === 'TEACHER' || sharedAuthStore.userRole === 'ADMIN'">
                    <li><router-link :to="{ name: 'subjects' }" @click="forceNavigate({ name: 'subjects' })" class="text-blue-600 hover:underline">Materie</router-link></li>
                    <li><router-link :to="{ name: 'topics' }" @click="forceNavigate({ name: 'topics' })" class="text-blue-600 hover:underline">Argomenti</router-link></li>
                    <li v-if="sharedAuthStore.userRole === 'TEACHER'"><router-link :to="{ name: 'teacher-lessons' }" @click="forceNavigate({ name: 'teacher-lessons' })" class="text-blue-600 hover:underline">Gestione Lezioni</router-link></li>
                    <li><router-link :to="{ name: 'course-list' }" @click="forceNavigate({ name: 'course-list' })" class="text-blue-600 hover:underline">Corsi</router-link></li>
                    <li><router-link :to="{ name: 'uda-list' }" @click="forceNavigate({ name: 'uda-list' })" class="text-blue-600 hover:underline">Unità Didattiche</router-link></li>
                    <li><a href="/dashboard" class="text-blue-600 hover:underline">Gestione Quiz (Altra App)</a></li>
                </template>

                <!-- Link per Studente -->
                <template v-if="sharedAuthStore.userRole === 'STUDENT'">
                    <li><router-link :to="{ name: 'assigned-lessons' }" @click="forceNavigate({ name: 'assigned-lessons' })" class="text-blue-600 hover:underline">Lezioni Assegnate</router-link></li>
                    <li><a :href="studentAppUrl" class="text-blue-600 hover:underline">I Miei Quiz (App Studenti)</a></li>
                </template>
            </ul>
        </nav>
    </div>

    <div v-else class="text-center text-gray-500 mt-10">
      <p>Caricamento dati utente...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'; // Aggiunto computed
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa lo store condiviso
import { useRouter, type RouteLocationRaw } from 'vue-router';

const sharedAuthStore = useSharedAuthStore(); // Usa lo store condiviso
const router = useRouter();

const studentAppUrl = computed(() => (import.meta.env.VITE_STUDENT_APP_URL as string | undefined) || '/studenti/');

const forceNavigate = (location: RouteLocationRaw) => {
  router.push(location);
};

const handleLogout = () => {
  sharedAuthStore.clearAuthData();
  // Reindirizza alla pagina di login o alla root del dominio.
  // Assumendo che esista una route di login o che la root gestisca il reindirizzamento al login.
  window.location.href = '/'; // O router.push({ name: 'loginRouteName' }); se preferito e configurato
};

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