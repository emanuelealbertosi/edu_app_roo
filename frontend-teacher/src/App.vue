<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink, RouterView, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue'; // Importa l'indicatore

const authStore = useAuthStore();
const router = useRouter(); // Get router instance
const isMobileMenuOpen = ref(false); // State for mobile menu visibility

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
}

function closeMobileMenuAndNavigate(routeName: string) {
  isMobileMenuOpen.value = false;
  router.push({ name: routeName });
}

function closeMobileMenuAndLogout() {
  isMobileMenuOpen.value = false;
  authStore.logout();
}

</script>

<template>
  <GlobalLoadingIndicator /> <!-- Aggiungi l'indicatore qui -->
  <header class="fixed top-0 left-0 w-full bg-purple-800 text-white shadow-md z-20 p-4 flex justify-between items-center">
    <div class="wrapper flex justify-between items-center w-full">
      <h1 class="text-xl font-semibold">Teacher Portal</h1>

      <!-- Desktop Navigation -->
      <nav v-if="authStore.isAuthenticated" class="hidden md:flex items-center space-x-4 text-sm">
        <RouterLink :to="{ name: 'dashboard' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Dashboard</RouterLink>
        <RouterLink :to="{ name: 'students' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Studenti</RouterLink>
        <RouterLink :to="{ name: 'quiz-templates' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Quiz Templates</RouterLink>
        <RouterLink :to="{ name: 'pathway-templates' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Template Percorsi</RouterLink>
        <RouterLink :to="{ name: 'assigned-quizzes' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Quiz Assegnati</RouterLink>
        <RouterLink :to="{ name: 'assigned-pathways' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Percorsi Assegnati</RouterLink>
        <RouterLink :to="{ name: 'rewards' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Ricompense</RouterLink>
        <RouterLink :to="{ name: 'assign' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Assegna</RouterLink>
        <RouterLink :to="{ name: 'grading' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Valutazioni</RouterLink>
        <RouterLink :to="{ name: 'delivery' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Consegne</RouterLink>
        <RouterLink :to="{ name: 'student-progress' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Progressi</RouterLink>
        <button @click="authStore.logout" class="ml-4 btn btn-danger">Logout</button>
      </nav>

      <!-- Mobile Menu Button -->
      <div v-if="authStore.isAuthenticated" class="md:hidden">
        <button @click="toggleMobileMenu" class="text-white focus:outline-none">
          <svg v-if="!isMobileMenuOpen" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path></svg>
          <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
    </div>

    <!-- Mobile Navigation Menu -->
    <transition name="mobile-menu">
      <nav v-if="authStore.isAuthenticated && isMobileMenuOpen" class="md:hidden absolute top-full left-0 w-full bg-purple-700 shadow-lg py-2 z-10">
        <a @click="closeMobileMenuAndNavigate('dashboard')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Dashboard</a>
        <a @click="closeMobileMenuAndNavigate('students')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Studenti</a>
        <a @click="closeMobileMenuAndNavigate('quiz-templates')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Quiz Templates</a>
        <a @click="closeMobileMenuAndNavigate('pathway-templates')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Template Percorsi</a>
        <a @click="closeMobileMenuAndNavigate('assigned-quizzes')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Quiz Assegnati</a>
        <a @click="closeMobileMenuAndNavigate('assigned-pathways')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Percorsi Assegnati</a>
        <a @click="closeMobileMenuAndNavigate('rewards')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Ricompense</a>
        <a @click="closeMobileMenuAndNavigate('assign')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Assegna</a>
        <a @click="closeMobileMenuAndNavigate('grading')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Valutazioni</a>
        <a @click="closeMobileMenuAndNavigate('delivery')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Consegne</a>
        <a @click="closeMobileMenuAndNavigate('student-progress')" class="block px-4 py-2 text-white hover:bg-purple-600 cursor-pointer">Progressi</a>
        <button @click="closeMobileMenuAndLogout" class="w-full text-left btn btn-danger block px-4 py-2">Logout</button>
      </nav>
    </transition>
  </header>

  <main class="pt-20 px-4 md:px-8"> <!-- Ridotto padding top per header più sottile -->
    <RouterView :key="$route.fullPath" />
  </main>
</template>

<style scoped>
/* Stile per il link attivo */
.router-link-exact-active {
  @apply border-amber-300 text-amber-300; /* Stile studenti */
}

/* Mobile Menu Transition */
.mobile-menu-enter-active, .mobile-menu-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.mobile-menu-enter-from, .mobile-menu-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
.mobile-menu-enter-to, .mobile-menu-leave-from {
  opacity: 1;
  transform: translateY(0);
}

/* Eventuali altri stili specifici */
</style>