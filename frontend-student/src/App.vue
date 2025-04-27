<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'; // Aggiunto useRouter
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import NotificationContainer from '@/components/common/NotificationContainer.vue';
import {
  HomeIcon, // Dashboard
  ShoppingCartIcon, // Shop
  UserCircleIcon, // Profilo
  CreditCardIcon, // Acquisti
  TrophyIcon, // Traguardi (Badges)
  BookOpenIcon, // Lezioni (Link esterno)
  ArrowLeftOnRectangleIcon, // Logout
  BellIcon, // Notifiche
  ChevronDownIcon, // Icona per Dropdown (anche se non usata qui, per coerenza)
  Bars3Icon, // Icona Hamburger per menu mobile
  XMarkIcon // Icona Chiusura per menu mobile
} from '@heroicons/vue/24/outline';

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter(); // Ottieni istanza router
const isMobileMenuOpen = ref(false); // Stato per sidebar mobile
// const isProfileMenuOpen = ref(false); // Rimosso stato dropdown (vecchio)

// URL per l'app Lezioni
const lessonsAppUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined) || '/lezioni/'); // Usa env var o fallback

const toggleMobileMenu = () => { isMobileMenuOpen.value = !isMobileMenuOpen.value; };
// const toggleProfileMenu = () => { isProfileMenuOpen.value = !isProfileMenuOpen.value; }; // Rimosso (vecchio)
// const closeProfileMenu = () => { isProfileMenuOpen.value = false; }; // Rimosso

// Definisci i nomi delle rotte che NON devono mostrare il layout principale (header/navbar)
// Aggiunto 'root' perché anche la root mostra il login e non deve avere il layout
const publicRouteNames = ['login', 'StudentRegistration', 'root'];

// Calcola se mostrare il layout principale
const showLayout = computed(() => {
  const currentRouteName = route.name;
  return currentRouteName !== null && currentRouteName !== undefined && !publicRouteNames.includes(currentRouteName.toString());
});

const handleLogout = () => {
  authStore.logout();
};

const goToProfile = () => {
  router.push({ name: 'Profile' });
  // closeProfileMenu(); // Rimosso
};

</script>
<template>
  <GlobalLoadingIndicator />
  <NotificationContainer />

  <div class="flex h-screen bg-neutral-lightest font-sans text-neutral-darkest">
    <!-- Sidebar Desktop (visibile da md in su) -->
    <aside
      v-if="authStore.isAuthenticated"
      class="bg-secondary text-neutral-lightest hidden md:flex flex-col w-20 group hover:w-64 transition-all duration-300 ease-in-out overflow-hidden"
      aria-label="Sidebar"
    >
      <!-- Logo/Titolo App -->
       <div class="h-16 flex items-center justify-center flex-shrink-0 px-4">
         <span class="text-xl font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Student Portal</span>
       </div>

      <!-- Navigazione Desktop -->
      <nav class="flex-grow p-4 overflow-y-auto overflow-x-hidden">
        <ul>
          <!-- Dashboard -->
          <li class="mb-3">
            <router-link :to="{ name: 'dashboard' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <HomeIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Dashboard</span>
            </router-link>
          </li>
          <!-- Shop -->
          <li class="mb-3">
            <router-link :to="{ name: 'shop' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <ShoppingCartIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Shop</span>
            </router-link>
          </li>
          <!-- Acquisti -->
          <li class="mb-3">
            <router-link :to="{ name: 'purchases' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <CreditCardIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Acquisti</span>
            </router-link>
          </li>
          <!-- Traguardi -->
          <li class="mb-3">
            <router-link :to="{ name: 'Badges' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <TrophyIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Traguardi</span>
            </router-link>
          </li>
          <!-- Lezioni (Link Esterno) -->
          <li class="mb-3">
            <a :href="lessonsAppUrl" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <BookOpenIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Lezioni</span>
            </a>
          </li>
        </ul>
      </nav>

      <!-- Logout Desktop -->
       <div class="p-4 mt-auto border-t border-purple-700 flex-shrink-0">
         <button @click="handleLogout" class="w-full flex items-center p-2 rounded text-neutral-lightest hover:bg-red-700">
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Logout</span>
         </button>
       </div>
    </aside>

    <!-- Sidebar Mobile (Overlay) -->
    <div v-if="isMobileMenuOpen && authStore.isAuthenticated" class="md:hidden" role="dialog" aria-modal="true">
      <!-- Overlay Sfondo -->
      <div class="fixed inset-0 bg-gray-600 bg-opacity-75 z-30" @click="toggleMobileMenu"></div>

      <!-- Contenuto Sidebar Mobile -->
      <aside class="fixed inset-y-0 left-0 z-40 w-64 bg-secondary text-neutral-lightest flex flex-col transition-transform duration-300 ease-in-out transform"
             :class="isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'">
        <!-- Logo/Titolo App e Bottone Chiusura -->
        <div class="h-16 flex items-center justify-between flex-shrink-0 px-4">
          <span class="text-xl font-semibold">Student Portal</span>
          <button @click="toggleMobileMenu" class="p-1 text-neutral-lightest hover:bg-purple-700 rounded">
            <span class="sr-only">Chiudi menu</span>
            <XMarkIcon class="h-6 w-6" />
          </button>
        </div>

        <!-- Navigazione Mobile -->
        <nav class="flex-grow p-4 overflow-y-auto">
          <ul>
            <!-- Dashboard -->
            <li class="mb-3">
              <router-link :to="{ name: 'dashboard' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <HomeIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Dashboard</span>
              </router-link>
            </li>
            <!-- Shop -->
            <li class="mb-3">
              <router-link :to="{ name: 'shop' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <ShoppingCartIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Shop</span>
              </router-link>
            </li>
            <!-- Acquisti -->
            <li class="mb-3">
              <router-link :to="{ name: 'purchases' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <CreditCardIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Acquisti</span>
              </router-link>
            </li>
            <!-- Traguardi -->
            <li class="mb-3">
              <router-link :to="{ name: 'Badges' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <TrophyIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Traguardi</span>
              </router-link>
            </li>
            <!-- Lezioni (Link Esterno) -->
            <li class="mb-3">
              <a :href="lessonsAppUrl" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <BookOpenIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Lezioni</span>
              </a>
            </li>
          </ul>
        </nav>

        <!-- Logout Mobile -->
        <div class="p-4 mt-auto border-t border-purple-700 flex-shrink-0">
          <button @click="handleLogout(); toggleMobileMenu();" class="w-full flex items-center p-2 rounded text-neutral-lightest hover:bg-red-700">
            <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
            <span class="ml-3">Logout</span>
          </button>
        </div>
      </aside>
    </div>

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow">
        <!-- Header -->
        <header v-if="authStore.isAuthenticated" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
             <!-- Pulsante Hamburger (visibile solo su mobile) -->
             <button @click="toggleMobileMenu" class="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500">
               <span class="sr-only">Apri menu principale</span>
               <Bars3Icon class="h-6 w-6" />
             </button>

             <!-- Placeholder per Titolo Pagina o Spazio (su desktop occupa spazio, su mobile no) -->
             <div class="flex-1 md:ml-4"></div>

             <!-- Pulsanti Header (Notifiche, Profilo) -->
             <div class="flex items-center space-x-4">
                 <!-- Pulsante Notifiche -->
                 <button class="p-2 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                     <span class="sr-only">View notifications</span>
                     <BellIcon class="h-6 w-6" />
                 </button>

                 <!-- Pulsante Profilo (Link diretto) -->
                 <button @click="goToProfile" class="p-1 rounded-full text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                     <span class="sr-only">Vai al profilo</span>
                     <UserCircleIcon class="h-7 w-7" />
                 </button>
             </div>
        </header>
        <!-- Se non autenticato, mostra solo il contenuto senza header -->
        <header v-else class="h-0"></header> <!-- Placeholder per mantenere struttura flex -->


        <!-- Area Contenuto -->
        <!-- Aggiunto padding-top se header è visibile -->
        <main class="flex-grow p-4 md:p-8 overflow-auto" :class="{ 'pt-20': authStore.isAuthenticated }">
          <RouterView />
        </main>
    </div>

  </div>
</template>

<style scoped>
/* Stili per link attivi e hover nella sidebar */
.router-link-exact-active {
  @apply bg-secondary-light; /* Usa il colore light della sidebar per l'attivo */
}
nav a:hover, nav button:hover {
  @apply bg-purple-700; /* Usa un viola più chiaro per hover per maggior contrasto */
}
/* Stile specifico per il bottone logout hover */
div > button.hover\:bg-red-700:hover { /* Selettore più specifico per override */
   @apply bg-error; /* Usa il colore error definito in tailwind.config */
}

/* Stili per i pulsanti dell'header */
header button {
  @apply text-neutral-dark hover:text-neutral-darker hover:bg-neutral-light focus:outline-none focus:bg-neutral-light focus:ring-2 focus:ring-offset-2 focus:ring-primary;
}
</style>
