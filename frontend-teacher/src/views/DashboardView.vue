<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { fetchStudents, type Student } from '@/api/students'; // Import type from API file
import { fetchTeacherQuizTemplates, type QuizTemplate } from '@/api/quizzes'; // Import type from API file
import { fetchPathwayTemplates, type PathwayTemplate } from '@/api/pathways'; // Import type from API file
import { fetchRewards, type Reward } from '@/api/rewards'; // Import type from API file
import { RouterLink } from 'vue-router';

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
      fetchStudents(),
      fetchTeacherQuizTemplates(), // Correct function name
      fetchPathwayTemplates(),
      fetchRewards() // Removed argument
    ]);
    // Filter rewards locally if needed (e.g., for active ones)
    students.value = studentsRes;
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

const quickLinks = [
  { name: 'Gestisci Studenti', path: '/students', icon: 'fas fa-users' },
  { name: 'Template Quiz', path: '/quiz-templates', icon: 'fas fa-file-alt' },
  { name: 'Template Percorsi', path: '/pathway-templates', icon: 'fas fa-project-diagram' },
  { name: 'Gestisci Ricompense', path: '/rewards', icon: 'fas fa-gift' },
  { name: 'Assegna Contenuti', path: '/assign', icon: 'fas fa-paper-plane' },
  { name: 'Correggi Quiz', path: '/grading', icon: 'fas fa-check-circle' },
  { name: 'Consegna Ricompense', path: '/delivery', icon: 'fas fa-truck' },
  { name: 'Progressi Studenti', path: '/student-progress', icon: 'fas fa-chart-line' },
];
</script>

<template>
  <div class="dashboard-view p-6 bg-gray-100 min-h-screen">
    <h2 class="text-3xl font-bold mb-6 text-gray-800">Dashboard Docente</h2>
    <p class="text-xl mb-8 text-gray-600">Benvenuto/a, {{ teacherName }}!</p>

    <div v-if="isLoading" class="text-center py-10">
      <p class="text-gray-500">Caricamento dati dashboard...</p>
      <!-- Optional: Add a spinner -->
    </div>

    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
      <!-- Stat Cards -->
      <div class="bg-white p-6 rounded-lg shadow-md flex items-center space-x-4">
        <i class="fas fa-users text-3xl text-blue-500"></i>
        <div>
          <p class="text-gray-500 text-sm">Studenti Attivi</p>
          <p class="text-2xl font-bold text-gray-800">{{ students.length }}</p>
        </div>
      </div>
      <div class="bg-white p-6 rounded-lg shadow-md flex items-center space-x-4">
        <i class="fas fa-file-alt text-3xl text-green-500"></i>
        <div>
          <p class="text-gray-500 text-sm">Template Quiz</p>
          <p class="text-2xl font-bold text-gray-800">{{ quizTemplates.length }}</p>
        </div>
      </div>
      <div class="bg-white p-6 rounded-lg shadow-md flex items-center space-x-4">
        <i class="fas fa-project-diagram text-3xl text-purple-500"></i>
        <div>
          <p class="text-gray-500 text-sm">Template Percorsi</p>
          <p class="text-2xl font-bold text-gray-800">{{ pathwayTemplates.length }}</p>
        </div>
      </div>
      <div class="bg-white p-6 rounded-lg shadow-md flex items-center space-x-4">
        <i class="fas fa-gift text-3xl text-red-500"></i>
        <div>
          <p class="text-gray-500 text-sm">Ricompense Totali</p> <!-- Changed label as we fetch all -->
          <p class="text-2xl font-bold text-gray-800">{{ rewards.length }}</p>
        </div>
      </div>
    </div>

    <!-- Quick Links -->
    <div v-if="!isLoading && !error">
        <h3 class="text-2xl font-semibold mb-4 text-gray-700">Accesso Rapido</h3>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <RouterLink
                v-for="link in quickLinks"
                :key="link.path"
                :to="link.path"
                class="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 flex flex-col items-center justify-center text-center text-gray-700 hover:text-blue-600"
            >
                <i :class="[link.icon, 'text-4xl mb-3']"></i>
                <span class="font-medium">{{ link.name }}</span>
            </RouterLink>
        </div>
    </div>

  </div>
</template>

<style scoped>
/* Add any additional specific styles if needed */
.dashboard-view {
  /* Example: Add a subtle background pattern */
  /* background-image: url("data:image/svg+xml,%3Csvg width='6' height='6' viewBox='0 0 6 6' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%239C92AC' fill-opacity='0.1' fill-rule='evenodd'%3E%3Cpath d='M5 0h1L0 6V5zM6 5v1H5z'/%3E%3C/g%3E%3C/svg%3E"); */
}
</style>