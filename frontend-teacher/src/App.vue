<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'; // Aggiunto useRouter
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
// import NotificationContainer from '@/components/common/NotificationContainer.vue'; // Se esiste
import {
  HomeIcon, // Dashboard
  UsersIcon, // Studenti
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
  PlusCircleIcon, // Crea
  ChevronDownIcon // Icona per Dropdown
} from '@heroicons/vue/24/outline';

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter(); // Aggiunta inizializzazione router
const isSidebarExpanded = ref(false);
const isCreateMenuOpen = ref(false); // Stato per il dropdown "Create" - Non usato ma lasciato per ora
// const isProfileMenuOpen = ref(false); // Rimosso stato dropdown

// URL per l'app Lezioni
const lessonsAppUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined) || '/lessons/'); // Usa env var o fallback

const expandSidebar = () => { isSidebarExpanded.value = true; };
const collapseSidebar = () => { isSidebarExpanded.value = false; };
// const toggleCreateMenu = () => { isCreateMenuOpen.value = !isCreateMenuOpen.value; }; // Rimosso
// const closeCreateMenu = () => { isCreateMenuOpen.value = false; }; // Rimosso
// const toggleProfileMenu = () => { isProfileMenuOpen.value = !isProfileMenuOpen.value; }; // Rimosso
// const closeProfileMenu = () => { isProfileMenuOpen.value = false; }; // Rimosso

// Rimosso showLayout e publicRouteNames, la visibilità dipende solo da isAuthenticated

const handleLogout = () => {
  authStore.logout();
};

// TODO: Implementare la logica per il dropdown "Crea" se necessario
// const goToCreateQuiz = () => { closeCreateMenu(); router.push({ name: 'create-quiz' }); };
// const goToCreatePathway = () => { closeCreateMenu(); router.push({ name: 'create-pathway' }); };

const goToProfile = () => {
  router.push({ name: 'profile' });
  // closeProfileMenu(); // Rimosso
};

</script>

<template>
  <GlobalLoadingIndicator />
  <!-- <NotificationContainer /> --> <!-- Se esiste -->

  <div class="flex h-screen bg-neutral-lightest font-sans text-neutral-darkest"> <!-- Sfondo e testo base aggiornati -->
    <!-- Sidebar -->
    <!-- Colori sidebar aggiornati -->
    <aside
      v-if="authStore.isAuthenticated"
      class="bg-secondary text-neutral-lightest flex flex-col transition-all duration-300 ease-in-out"
      :class="isSidebarExpanded ? 'w-64' : 'w-20'"
      @mouseenter="expandSidebar"
      @mouseleave="collapseSidebar"
    >
      <!-- Logo/Titolo App -->
       <div class="h-16 flex items-center justify-center flex-shrink-0 px-4">
         <span v-if="isSidebarExpanded" class="text-xl font-semibold">Teacher Portal</span>
         <span v-else class="text-xl font-semibold">TP</span>
       </div>

      <!-- Navigazione -->
      <nav class="flex-grow p-4 overflow-y-auto">
        <ul>
          <!-- Dashboard -->
          <li class="mb-2">
            <router-link :to="{ name: 'dashboard' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Dashboard'"> <!-- Hover aggiornato -->
              <HomeIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Dashboard</span>
            </router-link>
          </li>
          <!-- Studenti -->
          <li class="mb-2">
            <router-link :to="{ name: 'students' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Studenti'"> <!-- Hover aggiornato -->
              <UsersIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Studenti</span>
            </router-link>
          </li>
           <!-- Quiz Templates -->
          <li class="mb-2">
            <router-link :to="{ name: 'quiz-templates' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Quiz Templates'"> <!-- Hover aggiornato -->
              <ClipboardDocumentListIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Quiz Templates</span>
            </router-link>
          </li>
          <!-- Template Percorsi -->
          <li class="mb-2">
            <router-link :to="{ name: 'pathway-templates' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Template Percorsi'"> <!-- Hover aggiornato -->
              <MapIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Template Percorsi</span>
            </router-link>
          </li>
          <!-- Quiz Assegnati -->
          <li class="mb-2">
            <router-link :to="{ name: 'assigned-quizzes' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Quiz Assegnati'"> <!-- Hover aggiornato -->
              <ClipboardDocumentCheckIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Quiz Assegnati</span>
            </router-link>
          </li>
          <!-- Percorsi Assegnati -->
          <li class="mb-2">
            <router-link :to="{ name: 'assigned-pathways' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Percorsi Assegnati'"> <!-- Hover aggiornato -->
              <MapPinIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Percorsi Assegnati</span>
            </router-link>
          </li>
          <!-- Ricompense -->
          <li class="mb-2">
            <router-link :to="{ name: 'rewards' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Ricompense'"> <!-- Hover aggiornato -->
              <GiftIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Ricompense</span>
            </router-link>
          </li>
          <!-- Assegna -->
          <li class="mb-2">
            <router-link :to="{ name: 'assign' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Assegna'"> <!-- Hover aggiornato -->
              <PaperAirplaneIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Assegna</span>
            </router-link>
          </li>
          <!-- Valutazioni -->
          <li class="mb-2">
            <router-link :to="{ name: 'grading' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Valutazioni'"> <!-- Hover aggiornato -->
              <PencilSquareIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Valutazioni</span>
            </router-link>
          </li>
          <!-- Consegne -->
          <li class="mb-2">
            <router-link :to="{ name: 'delivery' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Consegne'"> <!-- Hover aggiornato -->
              <InboxArrowDownIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Consegne</span>
            </router-link>
          </li>
          <!-- Progressi -->
          <li class="mb-2">
            <router-link :to="{ name: 'student-progress' }" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Progressi'"> <!-- Hover aggiornato -->
              <ChartBarIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Progressi</span>
            </router-link>
          </li>
          <!-- Profilo (spostato nell'header) -->
          <!-- Lezioni (Link Esterno) -->
          <li class="mb-2">
            <a :href="lessonsAppUrl" class="flex items-center p-2 rounded hover:bg-secondary-light" :title="isSidebarExpanded ? '' : 'Lezioni'"> <!-- Hover aggiornato -->
              <BookOpenIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Lezioni</span>
            </a>
          </li>
        </ul>
      </nav>

      <!-- Logout -->
       <div class="p-4 mt-auto border-t border-secondary-light flex-shrink-0"> <!-- Bordo aggiornato -->
         <button @click="handleLogout" class="w-full flex items-center p-2 rounded hover:bg-error" :title="isSidebarExpanded ? '' : 'Logout'"> <!-- Hover aggiornato -->
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span v-if="isSidebarExpanded" class="ml-3">Logout</span>
         </button>
       </div>
    </aside>

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow">
        <!-- Header -->
        <!-- Usa solo lo stato di autenticazione -->
        <header v-if="authStore.isAuthenticated" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
            <!-- Placeholder per spazio a sinistra o titolo pagina -->
             <div class="flex-1"></div>

             <!-- Pulsanti Header -->
             <div class="flex items-center space-x-4">
                  <!-- Pulsante Create RIMOSSO -->

                 <!-- Pulsante Notifiche -->
                 <button class="p-2 rounded-full text-neutral-dark hover:text-neutral-darker hover:bg-neutral-light focus:outline-none focus:bg-neutral-light focus:ring-2 focus:ring-offset-2 focus:ring-primary"> <!-- Stili aggiornati -->
                     <span class="sr-only">View notifications</span>
                     <BellIcon class="h-6 w-6" />
                 </button>

                 <!-- Pulsante Profilo (Link diretto) -->
                 <button @click="goToProfile" class="p-1 rounded-full text-neutral-dark hover:text-neutral-darker focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"> <!-- Stili aggiornati -->
                     <span class="sr-only">Vai al profilo</span>
                     <UserCircleIcon class="h-7 w-7" />
                 </button>
             </div>
        </header>

        <!-- Area Contenuto -->
        <!-- Applica padding top solo se il layout è mostrato -->
        <main class="flex-grow p-8 overflow-auto"> <!-- Rimosso class condizionale -->
          <RouterView /> <!-- Rimosso :key -->
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