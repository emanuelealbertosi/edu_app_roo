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
  ChevronDownIcon // Icona per Dropdown (anche se non usata qui, per coerenza)
} from '@heroicons/vue/24/outline';

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter(); // Ottieni istanza router
const isSidebarExpanded = ref(false);
// const isProfileMenuOpen = ref(false); // Rimosso stato dropdown

// URL per l'app Lezioni
const lessonsAppUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined) || '/lessons/'); // Usa env var o fallback

const expandSidebar = () => { isSidebarExpanded.value = true; };
const collapseSidebar = () => { isSidebarExpanded.value = false; };
// const toggleProfileMenu = () => { isProfileMenuOpen.value = !isProfileMenuOpen.value; }; // Rimosso
// const closeProfileMenu = () => { isProfileMenuOpen.value = false; }; // Rimosso

// Definisci i nomi delle rotte che NON devono mostrare il layout principale (header/navbar)
const publicRouteNames = ['login', 'StudentRegistration'];

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
    <!-- Sidebar -->
    <aside
      v-show="showLayout"
      class="bg-secondary text-neutral-lightest flex flex-col transition-all duration-300 ease-in-out"
      :class="isSidebarExpanded ? 'w-64' : 'w-20'"
      @mouseenter="expandSidebar"
      @mouseleave="collapseSidebar"
    >
      <!-- Logo/Titolo App -->
       <div class="h-16 flex items-center justify-center flex-shrink-0 px-4">
         <span v-if="isSidebarExpanded" class="text-xl font-semibold">Student Portal</span>
         <span v-else class="text-xl font-semibold">SP</span>
       </div>

      <!-- Navigazione -->
      <nav class="flex-grow p-4 overflow-y-auto">
        <ul>
          <!-- Dashboard -->
          <li class="mb-3">
            <router-link :to="{ name: 'dashboard' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Dashboard'">
              <HomeIcon class="h-6 w-6 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3">Dashboard</span>
            </router-link>
          </li>
          <!-- Shop -->
          <li class="mb-3">
            <router-link :to="{ name: 'shop' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Shop'">
              <ShoppingCartIcon class="h-6 w-6 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3">Shop</span>
            </router-link>
          </li>
          <!-- Profilo (spostato nell'header) -->
          <!-- Acquisti -->
          <li class="mb-3">
            <router-link :to="{ name: 'purchases' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Acquisti'">
              <CreditCardIcon class="h-6 w-6 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3">Acquisti</span>
            </router-link>
          </li>
          <!-- Traguardi -->
          <li class="mb-3">
            <router-link :to="{ name: 'Badges' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Traguardi'">
              <TrophyIcon class="h-6 w-6 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3">Traguardi</span>
            </router-link>
          </li>
          <!-- Lezioni (Link Esterno) -->
          <li class="mb-3">
            <a :href="lessonsAppUrl" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Lezioni'">
              <BookOpenIcon class="h-6 w-6 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3">Lezioni</span>
            </a>
          </li>
        </ul>
      </nav>

      <!-- Logout -->
       <div class="p-4 mt-auto border-t border-purple-700 flex-shrink-0">
         <button @click="handleLogout" class="w-full flex items-center p-2 rounded text-neutral-lightest hover:bg-red-700" :title="isSidebarExpanded ? '' : 'Logout'">
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span v-if="isSidebarExpanded" class="ml-3">Logout</span>
         </button>
       </div>
    </aside>

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow">
        <!-- Header -->
        <header v-show="showLayout" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
            <!-- Placeholder per spazio a sinistra o titolo pagina (potrebbe essere dinamico) -->
             <div class="flex-1"></div>

             <!-- Pulsanti Header -->
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

        <!-- Area Contenuto -->
        <!-- Applica padding top solo se il layout è mostrato -->
        <main class="flex-grow p-8 overflow-auto">
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
