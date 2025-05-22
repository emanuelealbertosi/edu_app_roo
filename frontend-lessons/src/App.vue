<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'; // Rimossi ref, useRouter, onBeforeUnmount
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa lo store condiviso
import { useLessonStore } from '@/stores/lessons'; // Importa lo store delle lezioni
import { RouterView, useRoute } from 'vue-router'; // RouterView e useRoute importate qui. Rimossi RouterLink, useRouter
// import emitter from '@/eventBus'; // Rimosso se non usato per i modali da qui
// Rimosso import GlobalLoadingIndicator perché non esiste in questo FE
// import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import GlobalNotificationDisplay from '@/components/common/GlobalNotificationDisplay.vue';
// Icone rimosse perché non più usate per menu/header
// import {
//   HomeIcon,
//   BookOpenIcon,
//   AcademicCapIcon,
//   CogIcon,
//   ArrowLeftOnRectangleIcon,
//   BellIcon,
//   ChevronDownIcon,
//   PlusCircleIcon,
//   QuestionMarkCircleIcon,
//   Bars3Icon, // Hamburger
//   XMarkIcon, // Close
//   ClipboardDocumentListIcon, // Icona per UDA
//   FolderIcon // Icona per Corsi
// } from '@heroicons/vue/24/outline';

const sharedAuth = useSharedAuthStore(); // Usa lo store condiviso
const lessonStore = useLessonStore(); // Usa lo store delle lezioni
const route = useRoute(); // Istanza di useRoute

// Variabili e funzioni per menu, notifiche header, create dropdown, logout rimosse
// const isMobileMenuOpen = ref(false);
// const isCreateMenuOpen = ref(false);
// const isNotificationsTooltipVisible = ref(false);
// const notificationsButtonRef = ref<HTMLButtonElement | null>(null);
// const notificationsDropdownRef = ref<HTMLDivElement | null>(null);

// const toggleNotificationsDropdown = () => { ... };
// const handleClickOutside = (event: MouseEvent) => { ... };
// onBeforeUnmount(() => { document.removeEventListener('click', handleClickOutside); });


// Recupera le lezioni assegnate se l'utente è uno studente - MANTENUTO se GlobalNotificationDisplay ne ha bisogno indirettamente
onMounted(() => {
  if (sharedAuth.userRole === 'STUDENT' && sharedAuth.isAuthenticated) {
    lessonStore.fetchAssignedLessons();
  }
  // document.addEventListener('click', handleClickOutside); // Rimosso se handleClickOutside è rimosso
});

// Watcher per ricaricare le lezioni assegnate - MANTENUTO
watch(() => [sharedAuth.userRole, sharedAuth.isAuthenticated], ([newUserRole, newIsAuthenticated]) => {
  if (newUserRole === 'STUDENT' && newIsAuthenticated) {
    lessonStore.fetchAssignedLessons();
  }
});

// Calcoli per badge notifiche - MANTENUTI se GlobalNotificationDisplay ne ha bisogno
// const unreadLessons = computed(() => { ... });
// const unreadLessonsCount = computed(() => { ... });


// Funzioni per toggle menu e navigazione modale rimosse
// const toggleMobileMenu = () => { ... };
// const toggleCreateMenu = () => { ... };
// const closeCreateMenu = () => { ... };
// const goToSubjects = async () => { ... };
// const goToTopics = async () => { ... };
// const goToTeacherLessons = async () => { ... };


// const studentAppUrl = computed(() => ...); // Rimosso se non usato qui
// const handleLogout = () => { ... }; // Rimosso, sarà gestito dalla DashboardView

const isEmbeddedMode = computed(() => { // Mantenuto se serve ad altri componenti o logica residua
  return route.query.embedded === 'true';
});

</script>

<template>
  <!-- Rimosso <GlobalLoadingIndicator /> -->
  <GlobalNotificationDisplay />

  <div class="flex h-screen bg-gray-100 font-sans">
    <!-- Sidebar Desktop (visibile da md in su) - RIMOSSA -->
    <!-- Sidebar Mobile (Overlay) - RIMOSSA -->

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow min-w-0">
        <!-- Header - RIMOSSO -->
        
        <!-- Area Contenuto -->
        <!-- La classe pt-20 condizionale è rimossa perché l'header è rimosso -->
        <main class="flex-grow overflow-auto" :class="{ 'p-4 md:p-8': !isEmbeddedMode }">
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
