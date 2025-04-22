<script setup lang="ts">
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { computed, nextTick } from 'vue'; // Importa nextTick
import { useAuthStore } from '@/stores/auth';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import NotificationContainer from '@/components/common/NotificationContainer.vue'; // Importa contenitore notifiche

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

// Definisci i nomi delle rotte che NON devono mostrare il layout principale (header/navbar)
const publicRouteNames = ['login', 'StudentRegistration'];

// Calcola se mostrare la navbar (e quindi applicare il layout principale)
// Gestisce il caso in cui route.name sia null o undefined
const showLayout = computed(() => {
  const currentRouteName = route.name;
  return currentRouteName !== null && currentRouteName !== undefined && !publicRouteNames.includes(currentRouteName.toString());
});

const handleLogout = () => { // Rimosso async e nextTick
  authStore.logout(); // Lo store ora gestisce il redirect
};
</script>

<template>
  <GlobalLoadingIndicator />
  <NotificationContainer />
  <!-- Aggiungi il contenitore notifiche qui -->
  
  <header v-if="showLayout" class="fixed top-0 left-0 w-full bg-purple-800 text-white shadow-md z-10 p-4 flex justify-between items-center">
    <nav class="flex gap-6">
      <RouterLink to="/dashboard" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Dashboard</RouterLink>
      <RouterLink to="/shop" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Shop</RouterLink>
      <RouterLink to="/profile" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Profilo</RouterLink>
      <RouterLink to="/purchases" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Acquisti</RouterLink>
      <RouterLink to="/badges" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Traguardi</RouterLink> <!-- Aggiunto Link Badge -->
    </nav>
    <div class="flex items-center gap-4">
       <span class="text-sm text-purple-200 hidden md:inline">Ciao, {{ authStore.userFullName }}!</span>
       <button @click="handleLogout" class="bg-red-600 hover:bg-red-700 text-white text-sm font-medium py-2 px-4 rounded transition-colors duration-200">Logout</button>
    </div>
  </header>
  <!-- Applica il padding top solo se il layout (e quindi l'header) è mostrato -->
  <main :class="showLayout ? 'pt-24' : ''" class="px-4 md:px-8">
    <RouterView />
    
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

