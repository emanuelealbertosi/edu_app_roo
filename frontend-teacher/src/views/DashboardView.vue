<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { getMyStudents } from '@/api/students'; // Importa solo la funzione API
import type { Student } from '@/types/users'; // Importa il tipo dalla sua fonte originale
import { fetchTeacherQuizTemplates, type QuizTemplate } from '@/api/quizzes'; // Import type from API file
import { fetchPathwayTemplates, type PathwayTemplate } from '@/api/pathways'; // Import type from API file
import { fetchRewards, type Reward } from '@/api/rewards'; // Import type from API file
import { RouterLink } from 'vue-router';
import {
  UsersIcon,
  ClipboardDocumentListIcon,
  MapIcon,
  GiftIcon,
  PaperAirplaneIcon,
  PencilSquareIcon,
  InboxArrowDownIcon,
  ChartBarIcon
} from '@heroicons/vue/24/outline'; // Importa Heroicons

const authStore = useAuthStore();

const students = ref<Student[]>([]); // Apply correct type
const quizTemplates = ref<QuizTemplate[]>([]); // Apply correct type
const pathwayTemplates = ref<PathwayTemplate[]>([]); // Apply correct type
const rewards = ref<Reward[]>([]); // Apply correct type
const isLoading = ref(true);
const error = ref<string | null>(null);

const teacherName = computed(() => authStore.user?.username || 'Teacher');

const loadDashboardData = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    // Fetch all data in parallel
    const [studentsRes, quizTemplatesRes, pathwayTemplatesRes, rewardsRes] = await Promise.all([
      getMyStudents(), // Usa il nome corretto della funzione
      fetchTeacherQuizTemplates(), // Correct function name
      fetchPathwayTemplates(),
      fetchRewards() // Removed argument
    ]);
    // Filter rewards locally if needed (e.g., for active ones)
    students.value = studentsRes.data; // Estrai l'array dalla proprietà 'data'
    quizTemplates.value = quizTemplatesRes;
    pathwayTemplates.value = pathwayTemplatesRes;
    // Example: Filter for active rewards if the API returns all
    // rewards.value = rewardsRes.filter(r => r.is_active);
    rewards.value = rewardsRes; // Assuming API returns relevant rewards or filtering is not needed for count
  } catch (err) {
    console.error('Error loading dashboard data:', err);
    error.value = 'Failed to load dashboard data. Please try again later.';
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadDashboardData();
});

// Aggiorna quickLinks con Heroicons
const quickLinks = [
  { name: 'Gestisci Studenti', path: '/students', icon: UsersIcon },
  { name: 'Template Quiz', path: '/quiz-templates', icon: ClipboardDocumentListIcon },
  // { name: 'Template Percorsi', path: '/pathway-templates', icon: MapIcon },
  { name: 'Gestisci Ricompense', path: '/rewards', icon: GiftIcon },
  { name: 'Assegna Contenuti', path: '/assign', icon: PaperAirplaneIcon },
  { name: 'Correggi Quiz', path: '/grading', icon: PencilSquareIcon },
  { name: 'Consegna Ricompense', path: '/delivery', icon: InboxArrowDownIcon },
  { name: 'Progressi Studenti', path: '/student-progress', icon: ChartBarIcon },
];
</script>

<template>
  <div class="dashboard-view p-6 bg-neutral-lightest min-h-screen"> <!-- Sfondo aggiornato -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h2 class="text-3xl font-bold mb-1">Dashboard Docente</h2> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="text-xl opacity-90">Benvenuto/a, {{ teacherName }}!</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>

    <div v-if="isLoading" class="text-center py-10">
      <p class="text-neutral-dark">Caricamento dati dashboard...</p>
      <!-- Optional: Add a spinner -->
       <svg class="animate-spin h-5 w-5 text-primary mx-auto mt-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"> <!-- Spinner primario -->
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>

    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert"> <!-- Stile errore aggiornato -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-if="!isLoading && !error" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
      <!-- Stat Cards -->
       <div class="bg-white p-6 rounded-lg shadow-md flex items-center space-x-4">
         <UsersIcon class="h-8 w-8 text-primary" />
         <div>
           <p class="text-neutral-dark text-sm">Studenti Attivi</p>
           <p class="text-2xl font-bold text-neutral-darkest">{{ Array.isArray(students) ? students.length : 0 }}</p>
         </div>
       </div>
       <!-- Qui andrebbero le altre Stat Cards -->
     </div>

    <div v-if="!isLoading && !error">
        <h3 class="text-2xl font-semibold mb-4 text-neutral-darker">Accesso Rapido</h3>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <RouterLink
                v-for="link in quickLinks"
                :key="link.path"
                :to="link.path"
                class="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 flex flex-col items-center justify-center text-center text-neutral-darker hover:text-primary"
            >
                <component :is="link.icon" class="h-10 w-10 mb-3" />
                <span class="font-medium text-sm">{{ link.name }}</span>
            </RouterLink>
        </div>
    </div>
    <!-- Rimuoviamo il div 'else' che nascondeva il contenuto per debug -->
    <!-- <div v-else>
        <p class="text-center text-gray-500 italic">Contenuto dashboard temporaneamente nascosto per debug.</p>
    </div> -->

  </div>
</template>

<style scoped>
/* Add any additional specific styles if needed */
.dashboard-view {
  /* Example: Add a subtle background pattern */
  /* background-image: url("data:image/svg+xml,%3Csvg width='6' height='6' viewBox='0 0 6 6' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%239C92AC' fill-opacity='0.1' fill-rule='evenodd'%3E%3Cpath d='M5 0h1L0 6V5zM6 5v1H5z'/%3E%3C/g%3E%3C/svg%3E"); */
}
</style>