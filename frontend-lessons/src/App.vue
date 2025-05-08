<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa lo store condiviso
import { useLessonStore } from '@/stores/lessons'; // Importa lo store delle lezioni
import { RouterLink, RouterView, useRouter } from 'vue-router'; // RouterView importata qui
import emitter from '@/eventBus';
// Rimosso import GlobalLoadingIndicator perché non esiste in questo FE
// import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import {
  HomeIcon,
  BookOpenIcon,
  AcademicCapIcon,
  CogIcon,
  ArrowLeftOnRectangleIcon,
  BellIcon,
  UserCircleIcon,
  ChevronDownIcon,
  PlusCircleIcon,
  QuestionMarkCircleIcon,
  Bars3Icon, // Hamburger
  XMarkIcon // Close
} from '@heroicons/vue/24/outline';

const sharedAuth = useSharedAuthStore(); // Usa lo store condiviso
const lessonStore = useLessonStore(); // Usa lo store delle lezioni
const router = useRouter();
const isMobileMenuOpen = ref(false); // Stato per menu mobile
const isCreateMenuOpen = ref(false); // Stato per il dropdown "Create"
const isNotificationsTooltipVisible = ref(false);
const notificationsButtonRef = ref<HTMLButtonElement | null>(null);
const notificationsDropdownRef = ref<HTMLDivElement | null>(null);

const toggleNotificationsDropdown = () => {
  isNotificationsTooltipVisible.value = !isNotificationsTooltipVisible.value;
};

const handleClickOutside = (event: MouseEvent) => {
  if (isNotificationsTooltipVisible.value &&
      notificationsButtonRef.value &&
      !notificationsButtonRef.value.contains(event.target as Node) &&
      notificationsDropdownRef.value &&
      !notificationsDropdownRef.value.contains(event.target as Node)) {
    isNotificationsTooltipVisible.value = false;
  }
};

// Recupera le lezioni assegnate se l'utente è uno studente
onMounted(() => {
  if (sharedAuth.userRole === 'STUDENT' && sharedAuth.isAuthenticated) {
    lessonStore.fetchAssignedLessons();
  }
  document.addEventListener('click', handleClickOutside);
});

watch(isNotificationsTooltipVisible, (newValue) => {
  if (newValue) {
    // Potremmo voler aggiungere il listener solo quando è visibile
    // e rimuoverlo quando non lo è, ma per ora lo lasciamo globale
    // document.addEventListener('click', handleClickOutside);
  } else {
    // document.removeEventListener('click', handleClickOutside);
  }
});

// Assicurati di rimuovere il listener quando il componente viene smontato
import { onBeforeUnmount } from 'vue';
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
});


// Watcher per ricaricare le lezioni assegnate se il ruolo utente cambia a STUDENTE o se lo stato di autenticazione cambia
watch(() => [sharedAuth.userRole, sharedAuth.isAuthenticated], ([newUserRole, newIsAuthenticated]) => {
  if (newUserRole === 'STUDENT' && newIsAuthenticated) {
    lessonStore.fetchAssignedLessons();
  }
});

const unreadLessons = computed(() => {
  if (sharedAuth.userRole === 'STUDENT') {
    return lessonStore.assignedLessons.filter(lesson => !lesson.viewed_at);
  }
  return [];
});

const unreadLessonsCount = computed(() => {
  return unreadLessons.value.length;
});

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
};

const toggleCreateMenu = () => { isCreateMenuOpen.value = !isCreateMenuOpen.value; };
const closeCreateMenu = () => { isCreateMenuOpen.value = false; };

// Funzioni per navigare e POI emettere evento
const goToSubjects = async () => {
  closeCreateMenu();
  toggleMobileMenu(); // Chiudi menu mobile se aperto
  await router.push({ name: 'subjects' });
  emitter.emit('open-add-subject-modal');
};
const goToTopics = async () => {
  closeCreateMenu();
  toggleMobileMenu(); // Chiudi menu mobile se aperto
  await router.push({ name: 'topics' });
  emitter.emit('open-add-topic-modal');
};
const goToTeacherLessons = async () => {
  closeCreateMenu();
  toggleMobileMenu(); // Chiudi menu mobile se aperto
  await router.push({ name: 'teacher-lessons' });
  emitter.emit('open-add-lesson-modal');
};

// URL per le altre app frontend
const studentAppUrl = computed(() => (import.meta.env.VITE_STUDENT_APP_URL as string | undefined) || '/studenti/');
const handleLogout = () => {
  sharedAuth.clearAuthData(); // Pulisci lo store condiviso
  window.location.href = '/'; // Reindirizza manually alla root del dominio
};

</script>

<template>
  <!-- Rimosso <GlobalLoadingIndicator /> -->
  <!-- <NotificationContainer /> --> <!-- Se esiste -->

  <div class="flex h-screen bg-gray-100 font-sans">
    <!-- Sidebar Desktop (visibile da md in su) -->
    <aside
      v-if="sharedAuth.isAuthenticated"
      class="bg-indigo-900 text-white hidden md:flex flex-col w-20 group hover:w-64 transition-all duration-300 ease-in-out overflow-hidden"
      aria-label="Sidebar"
    >
      <!-- Logo/Titolo App -->
       <div class="h-16 flex items-center justify-center flex-shrink-0 px-4">
         <span class="text-xl font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Lezioni App</span>
       </div>

      <!-- Navigazione Desktop -->
      <nav class="flex-grow p-4 overflow-y-auto overflow-x-hidden">
        <ul>
          <!-- Dashboard -->
          <li class="mb-3">
            <router-link :to="{ name: 'dashboard' }" class="flex items-center p-2 rounded hover:bg-indigo-700">
              <HomeIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Dashboard</span>
            </router-link>
          </li>
          <!-- Materie (Admin/Teacher) -->
          <li v-if="sharedAuth.userRole === 'TEACHER' || sharedAuth.userRole === 'ADMIN'" class="mb-3">
            <router-link :to="{ name: 'subjects' }" class="flex items-center p-2 rounded hover:bg-indigo-700">
              <BookOpenIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Materie</span>
            </router-link>
          </li>
          <!-- Argomenti (Admin/Teacher) -->
          <li v-if="sharedAuth.userRole === 'TEACHER' || sharedAuth.userRole === 'ADMIN'" class="mb-3">
            <router-link :to="{ name: 'topics' }" class="flex items-center p-2 rounded hover:bg-indigo-700">
              <AcademicCapIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Argomenti</span>
            </router-link>
          </li>
          <!-- Gestione Lezioni (Teacher) -->
           <li v-if="sharedAuth.userRole === 'TEACHER'" class="mb-3">
             <router-link :to="{ name: 'teacher-lessons' }" class="flex items-center p-2 rounded hover:bg-indigo-700">
               <CogIcon class="h-6 w-6 flex-shrink-0" />
               <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Gestione Lezioni</span>
             </router-link>
           </li>
           <!-- Lezioni Assegnate (Studente) -->
           <li v-if="sharedAuth.userRole === 'STUDENT'" class="mb-3"> <!-- Corretto case 'STUDENT' -->
             <router-link :to="{ name: 'assigned-lessons' }" class="flex items-center p-2 rounded hover:bg-indigo-700">
               <CogIcon class="h-6 w-6 flex-shrink-0" />
               <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Lezioni Assegnate</span>
             </router-link>
           </li>
           <!-- Link Quiz Studente -->
            <li v-if="sharedAuth.userRole === 'STUDENT'" class="mb-3"> <!-- Corretto case 'STUDENT' -->
              <a :href="studentAppUrl" class="flex items-center p-2 rounded hover:bg-indigo-700">
                <QuestionMarkCircleIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Quiz</span>
              </a>
            </li>
             <!-- Link Gestione Quiz TEACHER/Admin -->
             <li v-if="sharedAuth.userRole === 'TEACHER' || sharedAuth.userRole === 'ADMIN'" class="mb-3">
               <a :href="'/dashboard'" class="flex items-center p-2 rounded hover:bg-indigo-700">
                 <QuestionMarkCircleIcon class="h-6 w-6 flex-shrink-0" />
                 <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Gestione Quiz</span>
               </a>
             </li>
        </ul>
      </nav>

      <!-- Logout Desktop -->
       <div class="p-4 mt-auto border-t border-indigo-700 flex-shrink-0">
         <button @click="handleLogout" class="w-full flex items-center p-2 rounded hover:bg-red-700">
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Logout</span>
         </button>
       </div>
    </aside>

    <!-- Sidebar Mobile (Overlay) -->
    <div v-if="isMobileMenuOpen && sharedAuth.isAuthenticated" class="md:hidden" role="dialog" aria-modal="true">
      <!-- Overlay Sfondo -->
      <div class="fixed inset-0 bg-gray-600 bg-opacity-75 z-30" @click="toggleMobileMenu"></div>

      <!-- Contenuto Sidebar Mobile -->
      <aside class="fixed inset-y-0 left-0 z-40 w-64 bg-indigo-900 text-white flex flex-col transition-transform duration-300 ease-in-out transform"
             :class="isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'">
        <!-- Logo/Titolo App e Bottone Chiusura -->
        <div class="h-16 flex items-center justify-between flex-shrink-0 px-4">
          <span class="text-xl font-semibold">Lezioni App</span>
          <button @click="toggleMobileMenu" class="p-1 text-white hover:bg-indigo-700 rounded">
            <span class="sr-only">Chiudi menu</span>
            <XMarkIcon class="h-6 w-6" />
          </button>
        </div>

        <!-- Navigazione Mobile -->
        <nav class="flex-grow p-4 overflow-y-auto">
          <ul>
            <!-- Dashboard -->
            <li class="mb-3">
              <router-link :to="{ name: 'dashboard' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-indigo-700">
                <HomeIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Dashboard</span>
              </router-link>
            </li>
            <!-- Materie (Admin/Teacher) -->
            <li v-if="sharedAuth.userRole === 'TEACHER' || sharedAuth.userRole === 'ADMIN'" class="mb-3">
              <router-link :to="{ name: 'subjects' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-indigo-700">
                <BookOpenIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Materie</span>
              </router-link>
            </li>
            <!-- Argomenti (Admin/Teacher) -->
            <li v-if="sharedAuth.userRole === 'TEACHER' || sharedAuth.userRole === 'ADMIN'" class="mb-3">
              <router-link :to="{ name: 'topics' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-indigo-700">
                <AcademicCapIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Argomenti</span>
              </router-link>
            </li>
            <!-- Gestione Lezioni (Teacher) -->
             <li v-if="sharedAuth.userRole === 'TEACHER'" class="mb-3">
               <router-link :to="{ name: 'teacher-lessons' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-indigo-700">
                 <CogIcon class="h-6 w-6 flex-shrink-0" />
                 <span class="ml-3">Gestione Lezioni</span>
               </router-link>
             </li>
             <!-- Lezioni Assegnate (Studente) -->
             <li v-if="sharedAuth.userRole === 'STUDENT'" class="mb-3"> <!-- Corretto case 'STUDENT' -->
               <router-link :to="{ name: 'assigned-lessons' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-indigo-700">
                 <CogIcon class="h-6 w-6 flex-shrink-0" />
                 <span class="ml-3">Lezioni Assegnate</span>
               </router-link>
             </li>
             <!-- Link Quiz Studente -->
              <li v-if="sharedAuth.userRole === 'STUDENT'" class="mb-3"> <!-- Corretto case 'STUDENT' -->
                <a :href="studentAppUrl" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-indigo-700">
                  <QuestionMarkCircleIcon class="h-6 w-6 flex-shrink-0" />
                  <span class="ml-3">Quiz</span>
                </a>
              </li>
               <!-- Link Gestione Quiz TEACHER/Admin -->
               <li v-if="sharedAuth.userRole === 'TEACHER' || sharedAuth.userRole === 'ADMIN'" class="mb-3">
                 <a :href="'/dashboard'" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-indigo-700">
                   <QuestionMarkCircleIcon class="h-6 w-6 flex-shrink-0" />
                   <span class="ml-3">Gestione Quiz</span>
                 </a>
               </li>
          </ul>
        </nav>

        <!-- Logout Mobile -->
        <div class="p-4 mt-auto border-t border-indigo-700 flex-shrink-0">
          <button @click="handleLogout(); toggleMobileMenu();" class="w-full flex items-center p-2 rounded hover:bg-red-700">
            <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
            <span class="ml-3">Logout</span>
          </button>
        </div>
      </aside>
    </div>

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow">
        <!-- Header -->
        <header v-if="sharedAuth.isAuthenticated" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
             <!-- Pulsante Hamburger (visibile solo su mobile) -->
             <button @click="toggleMobileMenu" class="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500">
               <span class="sr-only">Apri menu principale</span>
               <Bars3Icon class="h-6 w-6" />
             </button>

              <!-- Barra di ricerca rimossa -->
              <!-- Contenitore per allineare gli elementi a destra -->
              <div class="flex-grow"></div>


             <!-- Pulsanti Header -->
             <div class="flex items-center space-x-4">
                 <!-- Pulsante Create (Dropdown) - Visibile solo a Teacher/Admin -->
                 <div v-if="sharedAuth.userRole === 'TEACHER' || sharedAuth.userRole === 'ADMIN'" class="relative">
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

                 <!-- Pulsante Notifiche (solo per Studenti) con Badge e Dropdown -->
                 <div v-if="sharedAuth.userRole === 'STUDENT'" class="relative">
                     <button ref="notificationsButtonRef" @click="toggleNotificationsDropdown" class="p-2 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                         <span class="sr-only">View notifications</span>
                         <BellIcon class="h-6 w-6" />
                         <span v-if="unreadLessonsCount > 0" class="absolute top-0 right-0 block h-4 w-4 transform -translate-y-1/2 translate-x-1/2 rounded-full bg-red-500 text-white text-xs flex items-center justify-center">
                             {{ unreadLessonsCount }}
                         </span>
                     </button>
                     <!-- Dropdown Notifiche -->
                      <div ref="notificationsDropdownRef" v-if="isNotificationsTooltipVisible"
                           class="absolute right-0 mt-2 z-30">
                          <div v-if="unreadLessons.length > 0"
                               class="w-80 bg-white rounded-md shadow-lg py-1 border border-gray-200 max-h-96 overflow-y-auto">
                              <div class="px-4 py-2 text-sm font-semibold text-gray-700 border-b">Lezioni non visualizzate</div>
                              <ul>
                                  <li v-for="assignment in unreadLessons" :key="assignment.id" class="border-b last:border-b-0">
                                      <router-link :to="{ name: 'lesson-detail', params: { id: assignment.lesson.id }, query: { assignment_id: assignment.id } }"
                                                         @click="isNotificationsTooltipVisible = false"
                                                         class="block px-4 py-3 hover:bg-gray-100">
                                          <div class="font-semibold text-gray-800">{{ assignment.lesson.title || 'Titolo non disponibile' }}</div>
                                          <div class="text-xs text-gray-600">
                                              Materia: {{ assignment.lesson.subject_name || 'N/D' }}
                                          </div>
                                          <div class="text-xs text-gray-600">
                                              Argomento: {{ assignment.lesson.topic_name || 'N/D' }}
                                          </div>
                                          <div class="text-xs text-gray-500 italic">
                                              Assegnata da: {{ assignment.lesson.creator?.first_name || '' }} {{ assignment.lesson.creator?.last_name || 'Docente non specificato' }}
                                          </div>
                                      </router-link>
                                  </li>
                              </ul>
                          </div>
                          <div v-else
                               class="w-64 bg-white rounded-md shadow-lg py-3 px-4 border border-gray-200 text-sm text-gray-500">
                              Nessuna nuova lezione.
                          </div>
                      </div>
                 </div>
                 <!-- Pulsante/Dropdown Profilo Rimosso -->
                 <!-- Aggiungere dropdown profilo se necessario -->
             </div>
        </header>
         <!-- Se non autenticato, mostra solo il contenuto senza header -->
        <header v-else class="h-0"></header> <!-- Placeholder per mantenere struttura flex -->

        <!-- Area Contenuto -->
         <!-- Aggiunto padding-top se header è visibile -->
        <main class="flex-grow p-4 md:p-8 overflow-auto" :class="{ 'pt-20': sharedAuth.isAuthenticated }">
         <RouterView /> <!-- RouterView importata nello script -->
       </main>
    </div>

  </div>
</template>

<style scoped>
/* Stili aggiuntivi se necessari */
/* Assicurati che Tailwind sia configurato correttamente */
.router-link-exact-active {
  @apply bg-indigo-700; /* Stile link attivo aggiornato */
}
/* Potrebbe essere necessario installare @heroicons/vue: npm install @heroicons/vue */
/* Potrebbe essere necessario installare una libreria per il clickaway (es. vue-clickaway) o implementarlo manualmente */
</style>
