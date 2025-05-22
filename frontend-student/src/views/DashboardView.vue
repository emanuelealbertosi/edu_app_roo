<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
// import QuizList from '@/components/QuizList.vue'; // Rimosso QuizList
// import PathwayList from '@/components/PathwayList.vue'; // Rimosso PathwayList
import WalletCard from '@/components/WalletCard.vue';
import BaseButton from '@/components/common/BaseButton.vue';
// import BaseTabs from '@/components/common/BaseTabs.vue'; // Rimosso BaseTabs se non più usato per i quiz
import AnimatedBadge from '@/components/common/AnimatedBadge.vue'; // Importa AnimatedBadge

const authStore = useAuthStore();
const dashboardStore = useDashboardStore();
const router = useRouter();

const isLoading = ref(true);
const dashboardError = computed(() => dashboardStore.error);

const searchTerm = ref(''); // Sarà rimosso se la ricerca quiz è solo nella pagina quiz

// Definisci i tab (invariato) - Verrà rimosso se i tab erano solo per i quiz
// const dashboardTabs = ref([
//   { name: 'Da Fare', slotName: 'todo' },
//   { name: 'Completati', slotName: 'completed' }
// ]);

// Accedi all'ultimo badge tramite getter
const latestBadge = computed(() => dashboardStore.latestEarnedBadge);

// La logica di filtraggio dei quiz è spostata in QuizzesPageView.vue
// const filterQuizzes = (quizzes: any[]) => {
//   if (!searchTerm.value.trim()) {
//     return quizzes;
//   }
//   const lowerSearchTerm = searchTerm.value.toLowerCase();
//   return quizzes.filter(quiz => {
//     const subjectName = quiz.subject_name?.toLowerCase() || '';
//     const topicName = quiz.topic_name?.toLowerCase() || '';
//     const title = quiz.title?.toLowerCase() || '';
//     // const className = quiz.class_name?.toLowerCase() || ''; // Campo classe non presente direttamente
//     const teacherUsername = quiz.teacher_username?.toLowerCase() || '';
//     const teacherFirstName = quiz.teacher_first_name?.toLowerCase() || '';
//     const teacherLastName = quiz.teacher_last_name?.toLowerCase() || '';

//     return subjectName.includes(lowerSearchTerm) ||
//            topicName.includes(lowerSearchTerm) ||
//            title.includes(lowerSearchTerm) ||
//            // className.includes(lowerSearchTerm) ||
//            teacherUsername.includes(lowerSearchTerm) ||
//            teacherFirstName.includes(lowerSearchTerm) ||
//            teacherLastName.includes(lowerSearchTerm);
//   });
// };

// const filteredAvailableQuizzes = computed(() => filterQuizzes(dashboardStore.availableQuizzes));
// const filteredInProgressOrFailedQuizzes = computed(() => filterQuizzes(dashboardStore.inProgressOrFailedQuizzes));
// const filteredCompletedQuizzes = computed(() => filterQuizzes(dashboardStore.completedQuizzes));

onMounted(async () => {
  // Usa il getter isAuthenticated invece della funzione checkAuth rimossa
  if (!authStore.isAuthenticated) {
    console.warn('[DashboardView] User not authenticated, redirecting to login.'); // Aggiunto log
    router.push('/login');
    return;
  }

  try {
    // Carichiamo tutti i dati della dashboard
    await dashboardStore.loadDashboard();
  } catch (error) {
    console.error('Errore nel caricamento della dashboard:', error);
  } finally {
    isLoading.value = false;
  }
});

const handleLogout = async () => {
  await authStore.logout();
  router.push('/login');
};

// Funzione per navigare allo shop
const goToShop = () => {
  router.push('/shop');
};
</script>

<template>
  <div class="dashboard bg-neutral-lightest p-4 md:p-8">
    <header class="dashboard-header bg-accent text-neutral-lightest p-6 rounded-lg shadow-md mb-8 text-center md:text-left">
      <h1 class="text-3xl md:text-4xl font-bold mb-2">Dashboard Studente</h1>
      <p class="mb-4">Benvenuto, <strong class="font-semibold">{{ authStore.userFullName }}</strong>!</p>
      <div class="header-actions flex flex-col sm:flex-row justify-center md:justify-start gap-3 mt-2">
        <BaseButton variant="primary" size="sm" @click="goToShop">
          <span class="mr-2">🛒</span> Shop Ricompense
        </BaseButton>
        <BaseButton variant="secondary-outline" size="sm" @click="handleLogout">
          <span class="mr-2">🚪</span> Logout
        </BaseButton>
      </div>
    </header>

    <div v-if="dashboardError && !isLoading" class="error-message dashboard-error bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative text-center mb-6 shadow">
      <p class="font-semibold mb-2">{{ dashboardError }}</p>
      <BaseButton variant="secondary" size="sm" @click="dashboardStore.loadDashboard">Riprova</BaseButton>
    </div>

    <div v-if="isLoading" class="loading-container flex flex-col items-center justify-center p-12 text-center">
      <div class="loading-spinner"></div>
      <p class="mt-4 text-neutral-dark">Caricamento in corso...</p>
    </div>

    <div v-else class="dashboard-content">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <!-- Colonna Sinistra: Ultimo Traguardo -->
        <div class="bg-white p-6 rounded-lg shadow-md text-center">
          <h2 class="text-xl font-bold text-primary-dark mb-4 flex items-center justify-center"><span class="text-2xl mr-2">🏆</span> Ultimo Traguardo</h2>
          <div v-if="dashboardStore.loading.badges" class="text-sm text-neutral-dark italic py-4">Caricamento traguardi...</div>
          <AnimatedBadge v-else-if="latestBadge" :badge="latestBadge" class="mx-auto max-w-[theme(spacing.72)] mb-3"/>
          <p v-else class="text-sm text-neutral-dark italic py-4">Nessun traguardo ancora raggiunto.</p>
          <router-link to="/badges" class="block text-sm text-primary hover:underline mt-3">Vedi tutti i traguardi</router-link>
        </div>

        <!-- Colonna Destra: WalletCard -->
        <WalletCard
          :wallet="dashboardStore.wallet"
          :loading="dashboardStore.loading.wallet"
          :totalEarnedPoints="dashboardStore.wallet?.total_earned_points"
        />
      </div>
      
      <!-- RIMOZIONE COMPLETA DELLA SEZIONE "educational-content" -->
      <!--
      <div class="educational-content lg:col-span-2 bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-semibold text-primary-dark mb-6">Contenuti Educativi</h2>
        <p class="text-neutral-dark">Al momento non ci sono altri contenuti educativi da visualizzare qui. Puoi trovare i tuoi quiz nella sezione "I Miei Quiz" del menu.</p>
      </div>
      -->
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici rimasti (loading spinner, errore) */
.loading-container {
  /* Stili Tailwind applicati direttamente nel template */
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid theme('colors.primary.light / 30%'); /* Colore primario chiaro con opacità */
  border-left-color: theme('colors.primary.DEFAULT'); /* Colore primario */
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Stili per messaggio errore dashboard */
.error-message.dashboard-error {
  @apply bg-error/10 border border-error text-error; /* Usa colori 'error' con opacità per sfondo */
}
/* Rimossi stili .error-message.dashboard-error perché ora applicati con Tailwind nel template */

/* Rimosso stile .retry-button, ora gestito da BaseButton */

</style>