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
                    <li><a @click="navigateTo(router, 'subjects')" class="text-blue-600 hover:underline cursor-pointer">Materie</a></li>
                    <li><a @click="navigateTo(router, 'topics')" class="text-blue-600 hover:underline cursor-pointer">Argomenti</a></li>
                    <li v-if="sharedAuthStore.userRole === 'TEACHER'"><a @click="navigateTo(router, 'teacher-lessons')" class="text-blue-600 hover:underline cursor-pointer">Gestione Lezioni</a></li>
                    <li><a @click="navigateTo(router, 'course-list')" class="text-blue-600 hover:underline cursor-pointer">Corsi</a></li>
                    <li><a @click="navigateTo(router, 'uda-list')" class="text-blue-600 hover:underline cursor-pointer">Unità Didattiche</a></li>
                    <li><a href="/dashboard" class="text-blue-600 hover:underline">Gestione Quiz (Altra App)</a></li>
                </template>

                <!-- Link per Studente -->
                <template v-if="sharedAuthStore.userRole === 'STUDENT'">
                    <li><a @click="navigateTo(router, 'assigned-lessons')" class="text-blue-600 hover:underline cursor-pointer">Lezioni Assegnate</a></li>
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
import { useRouter } from 'vue-router';
import { navigateTo } from '@/utils/navigation';

const sharedAuthStore = useSharedAuthStore(); // Usa lo store condiviso
const router = useRouter();

const studentAppUrl = computed(() => (import.meta.env.VITE_STUDENT_APP_URL as string | undefined) || '/studenti/');

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