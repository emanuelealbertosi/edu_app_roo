<script setup lang="ts">
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { computed, nextTick } from 'vue'; // Importa nextTick
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

// Nasconde la navbar nella pagina di login
const showNavbar = computed(() => route.name !== 'login');

const handleLogout = () => { // Rimosso async e nextTick
  authStore.logout(); // Lo store ora gestisce il redirect
};
</script>

<template>
  <header v-if="showNavbar" class="fixed top-0 left-0 w-full bg-purple-800 text-white shadow-md z-10 p-4 flex justify-between items-center">
    <nav class="flex gap-6">
      <RouterLink to="/dashboard" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Dashboard</RouterLink>
      <RouterLink to="/shop" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Shop</RouterLink>
      <RouterLink to="/profile" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Profilo</RouterLink>
      <RouterLink to="/purchases" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Acquisti</RouterLink>
    </nav>
    <div class="flex items-center gap-4">
       <span class="text-sm text-purple-200 hidden md:inline">Ciao, {{ authStore.userFullName }}!</span>
       <button @click="handleLogout" class="bg-red-600 hover:bg-red-700 text-white text-sm font-medium py-2 px-4 rounded transition-colors duration-200">Logout</button>
    </div>
  </header>
  <main class="pt-24 px-4 md:px-8">
    <RouterView v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </RouterView>
  </main>
</template>

<style scoped>
/* Stili specifici del componente App.vue che non sono coperti da Tailwind o richiedono override */

/* Stile per il link attivo (Tailwind non ha una classe diretta per router-link-exact-active, quindi lo manteniamo qui o usiamo JS per aggiungere una classe) */
.router-link-exact-active {
  /* Rimuoviamo @apply per ora, potrebbe causare problemi in scoped style */
  /* Gli stili base sono già nel template, questo serviva per la classe automatica di Vue Router */
  /* Potremmo dover aggiungere logica JS per applicare classi dinamicamente se necessario */
}

/* Stili per la transizione fade (mantenuti come prima) */

/* Stili per la transizione fade */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 480px) {
    .main-navbar nav {
        gap: 0.8rem;
    }
    .nav-link {
        font-size: 0.9em;
    }
    .user-greeting {
        display: none; /* Nascondi saluto su schermi molto piccoli */
    }
     .user-actions {
       justify-content: flex-end; /* Allinea solo il logout a destra */
   }
}
</style>

