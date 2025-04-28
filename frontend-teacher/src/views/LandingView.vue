<template>
  <div class="landing-view min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
    <div class="bg-white p-8 rounded-lg shadow-xl w-full max-w-md text-center">
      <h1 class="text-3xl font-bold text-gray-800 mb-6">Benvenuto/a!</h1>

      <div v-if="user" class="mb-6">
        <p class="text-lg text-gray-700">Accesso effettuato come:</p>
        <p class="text-xl font-semibold text-primary">{{ user.first_name }} {{ user.last_name }} ({{ userRole }})</p>
      </div>

      <div v-if="!user && !loading" class="text-red-500 mb-4">
          Errore nel caricamento dei dati utente.
      </div>
       <div v-if="loading" class="text-gray-500 mb-4">
          Caricamento dati utente...
      </div>

      <!-- Sezione Card Portali -->
      <div v-if="user" class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">

        <!-- Card Studente -->
        <div v-if="userRole === 'STUDENT'" class="portal-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
          <a href="/studenti/" class="flex flex-col items-center text-center">
            <!-- Icona Utente Semplice -->
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-blue-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span class="font-semibold text-gray-700">Portale Studenti</span>
          </a>
        </div>

        <!-- Card Lezioni Studente -->
         <div v-if="userRole === 'STUDENT'" class="portal-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
           <a href="/lezioni/dashboard" class="flex flex-col items-center text-center"> <!-- Modificato href -->
             <!-- Icona Libro Semplice -->
             <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-blue-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
               <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
             </svg>
             <span class="font-semibold text-gray-700">Portale Lezioni</span>
           </a>
         </div>

        <!-- Card Docente -->
        <div v-if="userRole === 'TEACHER' || userRole === 'ADMIN'" class="portal-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
          <router-link :to="{ name: 'dashboard' }" class="flex flex-col items-center text-center">
             <!-- Icona Cappello Laurea Semplice -->
             <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-blue-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
               <path d="M12 14l9-5-9-5-9 5 9 5z" />
               <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
            </svg>
            <span class="font-semibold text-gray-700">Portale Docenti</span>
          </router-link>
        </div>

         <!-- Card Lezioni Docente -->
         <div v-if="userRole === 'TEACHER' || userRole === 'ADMIN'" class="portal-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
           <a href="/lezioni/dashboard" class="flex flex-col items-center text-center"> <!-- Modificato href -->
             <!-- Icona Libro Semplice (come studente) -->
              <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-blue-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
               <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
             </svg>
             <span class="font-semibold text-gray-700">Portale Lezioni</span>
           </a>
         </div>

      </div>
      <!-- Fine Sezione Card Portali -->

      <div class="mt-10"> <!-- Aumentato margine superiore per distanziare dal blocco card -->
        <button @click="handleLogout" class="w-full max-w-xs mx-auto btn btn-danger py-2"> <!-- Limitata larghezza e centrato -->
          Logout
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'; // Importa onMounted
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa lo store condiviso
import { useAuthStore as useAuthTeacherStore } from '@/stores/auth'; // Importa lo store specifico del teacher per l'azione logout

const sharedAuth = useSharedAuthStore();
const authTeacherStore = useAuthTeacherStore(); // Usato solo per l'azione logout specifica

const user = computed(() => sharedAuth.user);
const userRole = computed(() => sharedAuth.userRole);
const loading = computed(() => sharedAuth.loading);

const handleLogout = async () => {
  // Chiama l'azione logout dello store specifico del teacher,
  // che a sua volta pulirà lo store condiviso e gestirà il redirect.
  await authTeacherStore.logout();
};

// Potrebbe essere necessaria logica aggiuntiva qui se l'utente arriva
// a questa pagina senza essere autenticato (es. redirect al login)
// o se i dati utente non sono ancora caricati dallo store condiviso.
// Un Navigation Guard nel router è il posto migliore per gestire questo.

onMounted(() => {
  console.log('[LandingView Mounted] Shared Auth State:', {
    isAuthenticated: sharedAuth.isAuthenticated,
    user: JSON.parse(JSON.stringify(sharedAuth.user)), // Clona per evitare log reattivi
    role: sharedAuth.userRole,
    tokenExists: !!sharedAuth.accessToken // Verifica se il token è presente nello stato Pinia
  });
  // Logga anche il contenuto diretto di localStorage per confronto
  console.log('[LandingView Mounted] localStorage sharedAuth:', localStorage.getItem('sharedAuth'));
});

</script>

<style scoped>
/* Stili per le card dei portali */
.portal-card a {
  text-decoration: none;
  color: inherit; /* Eredita colore testo dal genitore */
}

.portal-card {
  /* Aggiungi altri stili se necessario, es. min-height */
  min-width: 180px; /* Larghezza minima per le card */
}

/* Stili per i pulsanti (mantenuti per il logout, potrebbero essere rimossi se non usati altrove) */
.btn-primary {
    background-color: #3b82f6; /* blue-500 */
    color: white;
    transition: background-color 0.2s;
}
.btn-primary:hover {
    background-color: #2563eb; /* blue-600 */
}
/* .btn-secondary non più usato per i link, rimosso se non serve altrove */
/* .btn-secondary {
    background-color: #fbbf24; /* amber-400 */
/*    color: #4b5563; /* gray-600 */
/*     transition: background-color 0.2s;
} */
/* .btn-secondary:hover {
     background-color: #f59e0b; /* amber-500 */
/* } */

.btn-danger {
    background-color: #ef4444; /* red-500 */
    color: white;
     transition: background-color 0.2s;
}
.btn-danger:hover {
     background-color: #dc2626; /* red-600 */
}

.btn {
    padding: 0.5rem 1rem;
    border-radius: 0.375rem; /* rounded-md */
    font-weight: 500; /* font-medium */
    text-align: center;
}
</style>