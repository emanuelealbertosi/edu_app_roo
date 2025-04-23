<script setup lang="ts">
import { ref, computed } from 'vue'; // Importa ref e computed
import { useAuthStore } from '@/stores/auth';
import { RouterLink, useRouter } from 'vue-router';
import emitter from '@/eventBus'; // Ri-aggiungi import emitter
import {
  HomeIcon,
  BookOpenIcon,
  AcademicCapIcon,
  UserGroupIcon, // Icona per Assegna Lezioni
  CogIcon,
  ArrowLeftOnRectangleIcon,
  BellIcon, // Icona Notifiche
  UserCircleIcon, // Icona Profilo
  ChevronDownIcon, // Icona per Dropdown
  PlusCircleIcon, // Icona per Create
  QuestionMarkCircleIcon // Icona per Quiz
} from '@heroicons/vue/24/outline'; // Esempio usando Heroicons

const authStore = useAuthStore();
// console.log('Auth Store User Role:', authStore.userRole); // DEBUG: Rimosso
const router = useRouter();
const isSidebarExpanded = ref(false);
const isCreateMenuOpen = ref(false); // Stato per il dropdown "Create"
const isProfileMenuOpen = ref(false); // Stato per dropdown profilo (opzionale)

const expandSidebar = () => { isSidebarExpanded.value = true; };
const collapseSidebar = () => { isSidebarExpanded.value = false; };
const toggleCreateMenu = () => { isCreateMenuOpen.value = !isCreateMenuOpen.value; };
const closeCreateMenu = () => { isCreateMenuOpen.value = false; };

// Funzioni per navigare e POI emettere evento
const goToSubjects = async () => {
  closeCreateMenu();
  await router.push({ name: 'subjects' }); // Attendi la navigazione
  console.log("App.vue: Navigated to subjects, emitting 'open-add-subject-modal'"); // Log
  emitter.emit('open-add-subject-modal');
};
const goToTopics = async () => {
  closeCreateMenu();
  await router.push({ name: 'topics' });
  console.log("App.vue: Navigated to topics, emitting 'open-add-topic-modal'"); // Log
  emitter.emit('open-add-topic-modal');
};
const goToTeacherLessons = async () => {
  closeCreateMenu();
  await router.push({ name: 'teacher-lessons' });
  console.log("App.vue: Navigated to teacher-lessons, emitting 'open-add-lesson-modal'"); // Log
  emitter.emit('open-add-lesson-modal');
};

// URL per le altre app frontend
const studentAppUrl = computed(() => (import.meta.env.VITE_STUDENT_APP_URL as string | undefined) || '/student-dashboard/'); // Usa env var o fallback
const teacherAppUrl = computed(() => (import.meta.env.VITE_TEACHER_APP_URL as string | undefined) || '/teacher-dashboard/'); // Usa env var o fallback

</script>

<template>
  <div class="flex h-screen bg-gray-100 font-sans">
    <!-- Sidebar -->
    <aside
      v-if="authStore.isAuthenticated"
      class="bg-indigo-900 text-white flex flex-col transition-all duration-300 ease-in-out"
      :class="isSidebarExpanded ? 'w-64' : 'w-20'"
      @mouseenter="expandSidebar"
      @mouseleave="collapseSidebar"
    >
      <!-- Logo/Titolo App -->
       <div class="h-16 flex items-center justify-center flex-shrink-0 px-4">
         <span v-if="isSidebarExpanded" class="text-xl font-semibold">Lezioni App</span>
         <span v-else class="text-xl font-semibold">LA</span>
       </div>

      <!-- Navigazione -->
      <nav class="flex-grow p-4 overflow-y-auto">
        <ul>
          <!-- Dashboard -->
          <li class="mb-3">
            <router-link :to="{ name: 'dashboard' }" class="flex items-center p-2 rounded hover:bg-indigo-700" :title="isSidebarExpanded ? '' : 'Dashboard'">
              <HomeIcon class="h-6 w-6 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3">Dashboard</span>
            </router-link>
          </li>
          <!-- Materie (Admin/Docente) -->
          <li v-if="authStore.userRole === 'Docente' || authStore.userRole === 'Admin'" class="mb-3">
            <router-link :to="{ name: 'subjects' }" class="flex items-center p-2 rounded hover:bg-indigo-700" :title="isSidebarExpanded ? '' : 'Materie'">
              <BookOpenIcon class="h-6 w-6 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3">Materie</span>
            </router-link>
          </li>
          <!-- Argomenti (Admin/Docente) -->
          <li v-if="authStore.userRole === 'Docente' || authStore.userRole === 'Admin'" class="mb-3">
            <router-link :to="{ name: 'topics' }" class="flex items-center p-2 rounded hover:bg-indigo-700" :title="isSidebarExpanded ? '' : 'Argomenti'">
              <AcademicCapIcon class="h-6 w-6 flex-shrink-0" />
              <span v-if="isSidebarExpanded" class="ml-3">Argomenti</span>
            </router-link>
          </li>
          <!-- Le Mie Lezioni (Docente) -->
           <li v-if="authStore.userRole === 'Docente'" class="mb-3">
             <router-link :to="{ name: 'teacher-lessons' }" class="flex items-center p-2 rounded hover:bg-indigo-700" :title="isSidebarExpanded ? '' : 'Le Mie Lezioni'">
               <CogIcon class="h-6 w-6 flex-shrink-0" />
               <span v-if="isSidebarExpanded" class="ml-3">Le Mie Lezioni</span>
             </router-link>
           </li>
           <!-- Assegna Lezioni (Docente) - Link aggiunto -->
           <li v-if="authStore.userRole === 'Docente'" class="mb-3">
             <router-link :to="{ name: 'teacher-lessons' }" class="flex items-center p-2 rounded hover:bg-indigo-700" :title="isSidebarExpanded ? '' : 'Assegna Lezioni'">
               <UserGroupIcon class="h-6 w-6 flex-shrink-0" />
               <span v-if="isSidebarExpanded" class="ml-3">Assegna Lezioni</span>
             </router-link>
           </li>
           <!-- Lezioni Assegnate (Studente) -->
           <li v-if="authStore.userRole === 'Studente'" class="mb-3">
             <router-link :to="{ name: 'assigned-lessons' }" class="flex items-center p-2 rounded hover:bg-indigo-700" :title="isSidebarExpanded ? '' : 'Lezioni Assegnate'">
               <CogIcon class="h-6 w-6 flex-shrink-0" />
               <span v-if="isSidebarExpanded" class="ml-3">Lezioni Assegnate</span>
             </router-link>
           </li>
           <!-- Link Quiz Studente -->
            <li v-if="authStore.userRole === 'Studente'" class="mb-3">
              <a :href="studentAppUrl" class="flex items-center p-2 rounded hover:bg-indigo-700" :title="isSidebarExpanded ? '' : 'Vai ai Quiz'">
                <QuestionMarkCircleIcon class="h-6 w-6 flex-shrink-0" />
                <span v-if="isSidebarExpanded" class="ml-3">Quiz</span>
              </a>
            </li>
            <!-- Link Gestione Quiz Docente -->
             <!-- Link Gestione Quiz TEACHER/Admin -->
             <li v-if="authStore.userRole === 'TEACHER' || authStore.userRole === 'Admin'" class="mb-3">
               <a :href="teacherAppUrl" class="flex items-center p-2 rounded hover:bg-indigo-700" :title="isSidebarExpanded ? '' : 'Gestione Quiz'">
                 <QuestionMarkCircleIcon class="h-6 w-6 flex-shrink-0" />
                 <span v-if="isSidebarExpanded" class="ml-3">Gestione Quiz</span>
               </a>
             </li>
        </ul>
      </nav>

      <!-- Logout -->
       <div class="p-4 mt-auto border-t border-indigo-700 flex-shrink-0">
         <button @click="authStore.logout()" class="w-full flex items-center p-2 rounded hover:bg-red-700" :title="isSidebarExpanded ? '' : 'Logout'">
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span v-if="isSidebarExpanded" class="ml-3">Logout</span>
         </button>
       </div>
    </aside>

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow">
        <!-- Header -->
        <header v-if="authStore.isAuthenticated" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
            <!-- Barra di ricerca (Placeholder) -->
             <div class="relative">
                 <input type="text" placeholder="Cerca..." class="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
             </div>

             <!-- Pulsanti Header -->
             <div class="flex items-center space-x-4">
                 <!-- Pulsante Create (Dropdown) -->
                 <div v-if="authStore.userRole !== 'Studente'" class="relative">
                     <button @click="toggleCreateMenu" class="flex items-center px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-md shadow-sm transition duration-150 ease-in-out">
                         <PlusCircleIcon class="h-5 w-5 mr-1" />
                         Crea
                         <ChevronDownIcon class="h-4 w-4 ml-1" />
                     </button>
                     <!-- Dropdown Menu -->
                     <div v-if="isCreateMenuOpen" class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-20" @clickaway="closeCreateMenu">
                         <a @click="goToSubjects" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer">Materia</a>
                         <a @click="goToTopics" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer">Argomento</a>
                         <a @click="goToTeacherLessons" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer">Lezione</a>
                     </div>
                 </div>

                 <!-- Pulsante Notifiche -->
                 <button class="p-2 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                     <span class="sr-only">View notifications</span>
                     <BellIcon class="h-6 w-6" />
                 </button>

                 <!-- Pulsante/Dropdown Profilo -->
                 <button class="p-1 rounded-full text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                     <span class="sr-only">Open user menu</span>
                     <UserCircleIcon class="h-7 w-7" />
                 </button>
                 <!-- Aggiungere dropdown profilo se necessario -->
             </div>
        </header>

        <!-- Area Contenuto -->
        <main class="flex-grow p-8 overflow-auto">
          <router-view />
        </main>
    </div>

  </div>
</template>

<style scoped>
/* Stili aggiuntivi se necessari */
/* Assicurati che Tailwind sia configurato correttamente */
/* Potrebbe essere necessario installare @heroicons/vue: npm install @heroicons/vue */
/* Potrebbe essere necessario installare una libreria per il clickaway (es. vue-clickaway) o implementarlo manualmente */
</style>
