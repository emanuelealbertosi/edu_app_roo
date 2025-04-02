<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router' // Import RouterLink
import { useAuthStore } from '@/stores/auth'; // Import auth store for logout/conditional rendering

const authStore = useAuthStore();
</script>

<template>
  <header>
    <div class="wrapper">
      <h1>Teacher Portal</h1>
      <nav v-if="authStore.isAuthenticated">
        <RouterLink :to="{ name: 'dashboard' }">Dashboard</RouterLink>
        <RouterLink :to="{ name: 'students' }">Studenti</RouterLink>
        <RouterLink :to="{ name: 'quizzes' }">Quiz</RouterLink>
        <RouterLink :to="{ name: 'pathways' }">Percorsi</RouterLink>
        <RouterLink :to="{ name: 'rewards' }">Ricompense</RouterLink>
        <RouterLink :to="{ name: 'assign' }">Assegna</RouterLink>
        <RouterLink :to="{ name: 'grading' }">Valutazioni</RouterLink>
        <RouterLink :to="{ name: 'student-progress' }">Progressi</RouterLink>
        <!-- Add other links here -->
        <button @click="authStore.logout">Logout</button>
      </nav>
    </div>
  </header>

  <main>
    <RouterView :key="$route.fullPath" /> <!-- Riaggiunta key per forzare ricreazione -->
  </main>
</template>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
  display: flex; /* Use flexbox for layout */
  justify-content: space-between; /* Space out title and nav */
  align-items: center; /* Align items vertically */
}

.wrapper {
  display: flex;
  align-items: center;
  width: 100%; /* Ensure wrapper takes full width */
}

nav {
  margin-left: auto; /* Push nav to the right */
  font-size: 1rem;
  text-align: right; /* Align nav items to the right */
}

nav a, nav button {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
  color: var(--color-text); /* Use theme color */
  text-decoration: none;
}

nav a:first-of-type {
  border: 0;
}

nav a.router-link-exact-active {
  color: var(--color-text); /* Or a different color for active link */
  font-weight: bold;
}

nav button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: inherit; /* Match link font size */
  color: var(--color-text); /* Match link color */
}

nav button:hover {
  background-color: hsla(160, 100%, 37%, 0.2); /* Subtle hover effect */
}


main {
  padding: 1rem;
}

h1 {
  font-weight: 500;
  font-size: 1.8rem;
  /* Removed position relative and top */
  margin: 0; /* Remove default margin */
}

/* Add more base styles if needed */
</style>