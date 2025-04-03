<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router' // Import RouterLink
import { useAuthStore } from '@/stores/auth'; // Import auth store for logout/conditional rendering

const authStore = useAuthStore();
</script>

<template>
  <header class="fixed top-0 left-0 w-full bg-purple-800 text-white shadow-md z-10 p-4 flex justify-between items-center">
    <div class="wrapper flex justify-between items-center w-full">
      <h1 class="text-xl font-semibold">Teacher Portal</h1>
      <nav v-if="authStore.isAuthenticated" class="flex items-center space-x-4 text-sm">
        <RouterLink :to="{ name: 'dashboard' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Dashboard</RouterLink>
        <RouterLink :to="{ name: 'students' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Studenti</RouterLink>
        <RouterLink :to="{ name: 'quizzes' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Quiz</RouterLink>
        <RouterLink :to="{ name: 'pathways' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Percorsi</RouterLink>
        <RouterLink :to="{ name: 'rewards' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Ricompense</RouterLink>
        <RouterLink :to="{ name: 'assign' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Assegna</RouterLink>
        <RouterLink :to="{ name: 'grading' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Valutazioni</RouterLink>
        <RouterLink :to="{ name: 'delivery' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Consegne</RouterLink>
        <RouterLink :to="{ name: 'student-progress' }" class="py-1 hover:text-amber-300 border-b-2 border-transparent router-link-exact-active:border-amber-300 transition-colors duration-200">Progressi</RouterLink>
        <button @click="authStore.logout" class="ml-4 bg-red-600 hover:bg-red-700 text-white text-sm font-medium py-2 px-4 rounded transition-colors duration-200">Logout</button>
      </nav>
    </div>
  </header>

  <main class="pt-24 px-4 md:px-8">
    <RouterView :key="$route.fullPath" />
  </main>
</template>

<style scoped>
/* Stile per il link attivo */
.router-link-exact-active {
  @apply border-amber-300 text-amber-300; /* Stile studenti */
}

/* Eventuali altri stili specifici */
</style>