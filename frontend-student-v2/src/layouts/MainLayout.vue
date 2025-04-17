<template>
  <div class="flex flex-col min-h-screen">
    <!-- Navbar -->
    <div class="navbar bg-base-100 shadow-md">
      <div class="flex-1">
        <router-link :to="{ name: 'home' }" class="btn btn-ghost text-xl">EduApp Studente v2</router-link>
      </div>
      <div class="flex-none">
        <!-- Menu Utente / Login -->
        <ul class="menu menu-horizontal px-1">
          <li v-if="!authStore.isAuthenticated">
            <router-link :to="{ name: 'login' }">Login</router-link>
          </li>
          <li v-if="authStore.isAuthenticated">
            <details>
              <summary>
                {{ authStore.user?.first_name || 'Studente' }}
              </summary>
              <ul class="p-2 bg-base-100 rounded-t-none z-10 shadow">
                <li><a>Profilo (TODO)</a></li>
                <li><a @click="handleLogout">Logout</a></li>
              </ul>
            </details>
          </li>
          <!-- Aggiungere altri link navbar qui se necessario -->
        </ul>
      </div>
    </div>

    <!-- Contenuto Principale -->
    <main class="flex-grow container mx-auto p-4">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="footer footer-center p-4 bg-base-300 text-base-content">
      <aside>
        <p>Copyright © 2025 - Tutti i diritti riservati</p>
      </aside>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const handleLogout = () => {
  authStore.logout();
  router.push({ name: 'login' }); // Reindirizza a login dopo logout
};
</script>

<style scoped>
/* Stili specifici per il layout se necessari */
</style>