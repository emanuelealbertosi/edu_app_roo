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

// Definisci i nomi delle rotte che NON devono mostrare il layout principale (header/navbar)
const publicRouteNames = ['login', 'TeacherRegistration']; // Adattare se i nomi sono diversi

// Calcola se mostrare il layout principale
const showLayout = computed(() => {
  const currentRouteName = route.name;
  return currentRouteName !== null && currentRouteName !== undefined && !publicRouteNames.includes(currentRouteName.toString());
});

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

  <div class="flex h-screen bg-gray-100 font-sans">
    <!-- Sidebar -->
    <aside
      v-if="showLayout"
      class="bg-purple-800 text-white flex flex-col transition-all duration-300 ease-in-out"
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
            <router-link :to="{ name: 'dashboard' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Dashboard'">
              <HomeIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Dashboard</span>
            </router-link>
          </li>
          <!-- Studenti -->
          <li class="mb-2">
            <router-link :to="{ name: 'students' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Studenti'">
              <UsersIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Studenti</span>
            </router-link>
          </li>
           <!-- Quiz Templates -->
          <li class="mb-2">
            <router-link :to="{ name: 'quiz-templates' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Quiz Templates'">
              <ClipboardDocumentListIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Quiz Templates</span>
            </router-link>
          </li>
          <!-- Template Percorsi -->
          <li class="mb-2">
            <router-link :to="{ name: 'pathway-templates' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Template Percorsi'">
              <MapIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Template Percorsi</span>
            </router-link>
          </li>
          <!-- Quiz Assegnati -->
          <li class="mb-2">
            <router-link :to="{ name: 'assigned-quizzes' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Quiz Assegnati'">
              <ClipboardDocumentCheckIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Quiz Assegnati</span>
            </router-link>
          </li>
          <!-- Percorsi Assegnati -->
          <li class="mb-2">
            <router-link :to="{ name: 'assigned-pathways' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Percorsi Assegnati'">
              <MapPinIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Percorsi Assegnati</span>
            </router-link>
          </li>
          <!-- Ricompense -->
          <li class="mb-2">
            <router-link :to="{ name: 'rewards' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Ricompense'">
              <GiftIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Ricompense</span>
            </router-link>
          </li>
          <!-- Assegna -->
          <li class="mb-2">
            <router-link :to="{ name: 'assign' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Assegna'">
              <PaperAirplaneIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Assegna</span>
            </router-link>
          </li>
          <!-- Valutazioni -->
          <li class="mb-2">
            <router-link :to="{ name: 'grading' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Valutazioni'">
              <PencilSquareIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Valutazioni</span>
            </router-link>
          </li>
          <!-- Consegne -->
          <li class="mb-2">
            <router-link :to="{ name: 'delivery' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Consegne'">
              <InboxArrowDownIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Consegne</span>
            </router-link>
          </li>
          <!-- Progressi -->
          <li class="mb-2">
            <router-link :to="{ name: 'student-progress' }" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Progressi'">
              <ChartBarIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Progressi</span>
            </router-link>
          </li>
          <!-- Profilo (spostato nell'header) -->
          <!-- Lezioni (Link Esterno) -->
          <li class="mb-2">
            <a :href="lessonsAppUrl" class="flex items-center p-2 rounded hover:bg-purple-700" :title="isSidebarExpanded ? '' : 'Lezioni'">
              <BookOpenIcon class="h-5 w-5 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3 text-sm">Lezioni</span>
            </a>
          </li>
        </ul>
      </nav>

      <!-- Logout -->
       <div class="p-4 mt-auto border-t border-purple-700 flex-shrink-0">
         <button @click="handleLogout" class="w-full flex items-center p-2 rounded hover:bg-red-700" :title="isSidebarExpanded ? '' : 'Logout'">
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span v-if="isSidebarExpanded" class="ml-3">Logout</span>
         </button>
       </div>
    </aside>

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow">
        <!-- Header -->
        <header v-if="showLayout" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
            <!-- Placeholder per spazio a sinistra o titolo pagina -->
             <div class="flex-1"></div>

             <!-- Pulsanti Header -->
             <div class="flex items-center space-x-4">
                  <!-- Pulsante Create RIMOSSO -->

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
        <main class="flex-grow p-8 overflow-auto" :class="showLayout ? 'pt-16' : ''">
          <RouterView :key="$route.fullPath" />
        </main>
    </div>

  </div>
</template>

<style scoped>
/* Stili aggiuntivi se necessari */
.router-link-exact-active {
  @apply bg-purple-700; /* Stile per link attivo nella sidebar */
}
</style>