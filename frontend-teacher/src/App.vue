<script setup lang="ts">
import { ref, computed, watch } from 'vue'; // Importa watch
import { useAuthStore } from '@/stores/auth'; // Store specifico Teacher (per logout)
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa store condiviso
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
// import NotificationContainer from '@/components/common/NotificationContainer.vue'; // Se esiste
import {
  HomeIcon, // Dashboard
  UsersIcon, // Studenti
  UserGroupIcon, // Gruppi Studenti (NUOVO)
  ClipboardDocumentListIcon, // Quiz Templates
  MapIcon, // Template Percorsi (Pathways)
  ClipboardDocumentCheckIcon, // Quiz Assegnati
  MapPinIcon, // Percorsi Assegnati
  GiftIcon, // Ricompense
  PaperAirplaneIcon, // Assegna
  PencilSquareIcon, // Valutazioni (Grading)
  InboxArrowDownIcon, // Consegne (Delivery)
  ChartBarIcon, // Progressi
  UserCircleIcon, // Profilo
  BookOpenIcon, // Lezioni (Link esterno)
  ArrowLeftOnRectangleIcon, // Logout
  BellIcon, // Notifiche
  Bars3Icon, // Icona Hamburger per menu mobile
  XMarkIcon, // Icona per chiudere menu mobile
  MagnifyingGlassIcon // Icona per Sfoglia Gruppi
} from '@heroicons/vue/24/outline';

const authStore = useAuthStore(); // Mantenuto per azione logout specifica
const sharedAuth = useSharedAuthStore(); // Usa store condiviso per stato auth
const route = useRoute();
const router = useRouter();
const isMobileMenuOpen = ref(false); // Stato per menu mobile

// URL per l'app Lezioni
const lessonsAppUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined) || '/lezioni/'); // Usa env var o fallback

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
};

const handleLogout = () => {
  authStore.logout();
};

const goToProfile = () => {
  router.push({ name: 'profile' });
};

// LOGGING per debug menu
watch(route, (to) => {
  console.log(`[App.vue Watch Route] Navigated to: ${to.path}, Route Name: ${String(to.name)}, IsAuthenticated: ${sharedAuth.isAuthenticated}`);
}, { immediate: true, deep: true }); // immediate per log iniziale, deep non strettamente necessario ma sicuro

</script>

<template>
  <GlobalLoadingIndicator />
  <!-- <NotificationContainer /> --> <!-- Se esiste -->

  <div class="flex h-screen bg-neutral-lightest font-sans text-neutral-darkest">
    <!-- Sidebar Desktop (visibile da md in su) -->
    <!-- Mostra sidebar solo se autenticato E non sulla landing page -->
    <aside
      v-if="sharedAuth.isAuthenticated && route.name !== 'landing'"
      class="bg-secondary text-neutral-lightest hidden md:flex flex-col w-20 group hover:w-64 transition-all duration-300 ease-in-out overflow-hidden"
      aria-label="Sidebar"
    >
      <!-- Logo/Titolo App -->
       <div class="h-16 flex items-center justify-center flex-shrink-0 px-4">
         <span class="text-xl font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Teacher Portal</span>
       </div>

      <!-- Navigazione Desktop -->
      <nav class="flex-grow p-4 overflow-y-auto overflow-x-hidden">
        <ul>
          <!-- Dashboard -->
          <li class="mb-2">
            <router-link :to="{ name: 'dashboard' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <HomeIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Dashboard</span>
            </router-link>
          </li>
          <!-- Studenti -->
          <li class="mb-2">
            <router-link :to="{ name: 'students' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <UsersIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Studenti</span>
            </router-link>
          </li>
          <!-- Gruppi Studenti (NUOVO) -->
          <li class="mb-2">
            <router-link :to="{ name: 'GroupsList' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <UserGroupIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Gruppi</span>
            </router-link>
          </li>
          <!-- Sfoglia Gruppi Pubblici -->
          <li class="mb-2">
            <router-link :to="{ name: 'BrowseGroups' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <MagnifyingGlassIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Sfoglia Gruppi</span>
            </router-link>
          </li>
           <!-- Quiz Templates -->
          <li class="mb-2">
            <router-link :to="{ name: 'quiz-templates' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <ClipboardDocumentListIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Quiz Templates</span>
            </router-link>
          </li>
          <!-- Template Percorsi - Temporarily Hidden -->
          <!--
          <li class="mb-2">
            <router-link :to="{ name: 'pathway-templates' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <MapIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Template Percorsi</span>
            </router-link>
          </li>
          -->
          <!-- Quiz Assegnati -->
          <li class="mb-2">
            <router-link :to="{ name: 'assigned-quizzes' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <ClipboardDocumentCheckIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Quiz Assegnati</span>
            </router-link>
          </li>
          <!-- Percorsi Assegnati - Temporarily Hidden -->
          <!--
          <li class="mb-2">
            <router-link :to="{ name: 'assigned-pathways' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <MapPinIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Percorsi Assegnati</span>
            </router-link>
          </li>
          -->
          <!-- Ricompense -->
          <li class="mb-2">
            <router-link :to="{ name: 'rewards' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <GiftIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Ricompense</span>
            </router-link>
          </li>
          <!-- Assegna -->
          <li class="mb-2">
            <router-link :to="{ name: 'assign' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <PaperAirplaneIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Assegna</span>
            </router-link>
          </li>
          <!-- Valutazioni -->
          <li class="mb-2">
            <router-link :to="{ name: 'grading' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <PencilSquareIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Valutazioni</span>
            </router-link>
          </li>
          <!-- Consegne -->
          <li class="mb-2">
            <router-link :to="{ name: 'delivery' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <InboxArrowDownIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Consegne</span>
            </router-link>
          </li>
          <!-- Progressi -->
          <li class="mb-2">
            <router-link :to="{ name: 'student-progress' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <ChartBarIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Progressi</span>
            </router-link>
          </li>
          <!-- Lezioni (Link Esterno) -->
          <li class="mb-2">
            <a :href="lessonsAppUrl" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <BookOpenIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Lezioni</span>
            </a>
          </li>
        </ul>
      </nav>

      <!-- Logout Desktop -->
       <div class="p-4 mt-auto border-t border-secondary-light flex-shrink-0">
         <button @click="handleLogout" class="w-full flex items-center p-2 rounded hover:bg-error">
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Logout</span>
         </button>
       </div>
    </aside>

    <!-- Sidebar Mobile (Overlay) - Mostra solo se autenticato E non sulla landing page -->
    <div v-if="isMobileMenuOpen && sharedAuth.isAuthenticated && route.name !== 'landing'" class="md:hidden" role="dialog" aria-modal="true">
      <!-- Overlay Sfondo -->
      <div class="fixed inset-0 bg-gray-600 bg-opacity-75 z-30" @click="toggleMobileMenu"></div>

      <!-- Contenuto Sidebar Mobile -->
      <aside class="fixed inset-y-0 left-0 z-40 w-64 bg-secondary text-neutral-lightest flex flex-col transition-transform duration-300 ease-in-out transform"
             :class="isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'">
        <!-- Logo/Titolo App e Bottone Chiusura -->
        <div class="h-16 flex items-center justify-between flex-shrink-0 px-4">
          <span class="text-xl font-semibold">Teacher Portal</span>
          <button @click="toggleMobileMenu" class="p-1 text-neutral-lightest hover:bg-secondary-light rounded">
            <span class="sr-only">Chiudi menu</span>
            <XMarkIcon class="h-6 w-6" />
          </button>
        </div>

        <!-- Navigazione Mobile -->
        <nav class="flex-grow p-4 overflow-y-auto">
          <ul>
            <!-- Dashboard -->
            <li class="mb-2">
              <router-link :to="{ name: 'dashboard' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <HomeIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Dashboard</span>
              </router-link>
            </li>
            <!-- Studenti -->
            <li class="mb-2">
              <router-link :to="{ name: 'students' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <UsersIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Studenti</span>
              </router-link>
            </li>
            <!-- Gruppi Studenti (NUOVO) -->
            <li class="mb-2">
              <router-link :to="{ name: 'GroupsList' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <UserGroupIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Gruppi</span>
              </router-link>
            </li>
            <!-- Sfoglia Gruppi Pubblici -->
            <li class="mb-2">
              <router-link :to="{ name: 'BrowseGroups' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <MagnifyingGlassIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Sfoglia Gruppi</span>
              </router-link>
            </li>
             <!-- Quiz Templates -->
            <li class="mb-2">
              <router-link :to="{ name: 'quiz-templates' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <ClipboardDocumentListIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Quiz Templates</span>
              </router-link>
            </li>
            <!-- Template Percorsi - Temporarily Hidden -->
            <!--
            <li class="mb-2">
              <router-link :to="{ name: 'pathway-templates' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <MapIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Template Percorsi</span>
              </router-link>
            </li>
            -->
            <!-- Quiz Assegnati -->
            <li class="mb-2">
              <router-link :to="{ name: 'assigned-quizzes' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <ClipboardDocumentCheckIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Quiz Assegnati</span>
              </router-link>
            </li>
            <!-- Percorsi Assegnati - Temporarily Hidden -->
            <!--
            <li class="mb-2">
              <router-link :to="{ name: 'assigned-pathways' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <MapPinIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Percorsi Assegnati</span>
              </router-link>
            </li>
            -->
            <!-- Ricompense -->
            <li class="mb-2">
              <router-link :to="{ name: 'rewards' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <GiftIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Ricompense</span>
              </router-link>
            </li>
            <!-- Assegna -->
            <li class="mb-2">
              <router-link :to="{ name: 'assign' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <PaperAirplaneIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Assegna</span>
              </router-link>
            </li>
            <!-- Valutazioni -->
            <li class="mb-2">
              <router-link :to="{ name: 'grading' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <PencilSquareIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Valutazioni</span>
              </router-link>
            </li>
            <!-- Consegne -->
            <li class="mb-2">
              <router-link :to="{ name: 'delivery' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <InboxArrowDownIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Consegne</span>
              </router-link>
            </li>
            <!-- Progressi -->
            <li class="mb-2">
              <router-link :to="{ name: 'student-progress' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <ChartBarIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Progressi</span>
              </router-link>
            </li>
            <!-- Lezioni (Link Esterno) -->
            <li class="mb-2">
              <a :href="lessonsAppUrl" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <BookOpenIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Lezioni</span>
              </a>
            </li>
          </ul>
        </nav>

        <!-- Logout Mobile -->
        <div class="p-4 mt-auto border-t border-secondary-light flex-shrink-0">
          <button @click="handleLogout(); toggleMobileMenu();" class="w-full flex items-center p-2 rounded hover:bg-error">
            <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
            <span class="ml-3">Logout</span>
          </button>
        </div>
      </aside>
    </div>

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow">
        <!-- Header - Mostra solo se autenticato E non sulla landing page -->
        <header v-if="sharedAuth.isAuthenticated && route.name !== 'landing'" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
             <!-- Pulsante Hamburger (visibile solo su mobile) -->
             <button @click="toggleMobileMenu" class="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500">
               <span class="sr-only">Apri menu principale</span>
               <Bars3Icon class="h-6 w-6" />
             </button>

             <!-- Placeholder per Titolo Pagina o Spazio -->
             <div class="flex-1 md:ml-4"></div>

             <!-- Pulsanti Header -->
             <div class="flex items-center space-x-4">
                 <!-- Pulsante Notifiche -->
                 <button class="p-2 rounded-full text-neutral-dark hover:text-neutral-darker hover:bg-neutral-light focus:outline-none focus:bg-neutral-light focus:ring-2 focus:ring-offset-2 focus:ring-primary">
                     <span class="sr-only">View notifications</span>
                     <BellIcon class="h-6 w-6" />
                 </button>

                 <!-- Pulsante Profilo (Link diretto) -->
                 <button @click="goToProfile" class="p-1 rounded-full text-neutral-dark hover:text-neutral-darker focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary">
                     <span class="sr-only">Vai al profilo</span>
                     <UserCircleIcon class="h-7 w-7" />
                 </button>
             </div>
        </header>
        <!-- Se non autenticato, mostra solo il contenuto senza header -->
        <header v-else class="h-0"></header> <!-- Placeholder per mantenere struttura flex -->

        <!-- Area Contenuto -->
        <!-- Aggiunto padding-top solo se header è visibile (autenticato e non su landing) -->
        <!-- Applica padding-top sempre se autenticato, per evitare che il contenuto vada sotto eventuali barre fisse -->
        <main class="flex-grow p-4 md:p-8 overflow-auto" :class="{ 'pt-20': sharedAuth.isAuthenticated }">
          <RouterView />
        </main>
    </div>

  </div>
</template>

<style scoped>
/* Stili aggiuntivi se necessari */
.router-link-exact-active {
  @apply bg-secondary-light; /* Stile per link attivo nella sidebar aggiornato */
}
/* Stile specifico per il bottone logout hover (già gestito inline) */
/* div > button.hover\:bg-red-700:hover {
   @apply bg-error;
} */
</style>