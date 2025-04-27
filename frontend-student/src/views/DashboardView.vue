<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'; // Aggiunto computed
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
import QuizList from '@/components/QuizList.vue';
import PathwayList from '@/components/PathwayList.vue';
import WalletCard from '@/components/WalletCard.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import BaseTabs from '@/components/common/BaseTabs.vue';
import AnimatedBadge from '@/components/common/AnimatedBadge.vue'; // Importa AnimatedBadge

const authStore = useAuthStore();
const dashboardStore = useDashboardStore();
const router = useRouter();

const isLoading = ref(true);
const dashboardError = computed(() => dashboardStore.error);

// Definisci i tab (invariato)
const dashboardTabs = ref([
  { name: 'Da Fare', slotName: 'todo' },
  { name: 'Completati', slotName: 'completed' }
]);

// Accedi all'ultimo badge tramite getter
const latestBadge = computed(() => dashboardStore.latestEarnedBadge);

onMounted(async () => {
  const isAuthenticated = await authStore.checkAuth();
  if (!isAuthenticated) {
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

    <div v-else class="dashboard-content grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div class="wallet-section lg:col-span-1 flex flex-col gap-6">
         <div class="bg-white p-4 rounded-lg shadow-md text-center">
            <h3 class="text-lg font-semibold text-primary-dark mb-3">Ultimo Traguardo</h3>
            <div v-if="dashboardStore.loading.badges" class="text-sm text-neutral-dark italic">Caricamento...</div>
            <AnimatedBadge v-else-if="latestBadge" :badge="latestBadge" class="mx-auto"/>
            <p v-else class="text-sm text-neutral-dark italic">Nessun traguardo ancora raggiunto.</p>
            <router-link to="/badges" class="block text-sm text-primary hover:underline mt-3">Vedi tutti i traguardi</router-link>
         </div>
        <WalletCard
          :wallet="dashboardStore.wallet"
          :loading="dashboardStore.loading.wallet"
        />
      </div>

      <div class="educational-content lg:col-span-2 bg-white p-6 rounded-lg shadow-md">
        <BaseTabs :tabs="dashboardTabs">
          <template #todo>
            <div class="space-y-6">
              <QuizList
                :quizzes="dashboardStore.availableQuizzes"
                title="Quiz Disponibili"
                emptyMessage="Non ci sono quiz disponibili al momento."
                :loading="dashboardStore.loading.quizzes"
                :showStartButton="true"
              />
              <QuizList
                :quizzes="dashboardStore.inProgressOrFailedQuizzes"
                title="Quiz da Continuare o Ritentare"
                emptyMessage="Non hai quiz in corso o da ritentare."
                :loading="dashboardStore.loading.quizzes"
                :showStartButton="true"
              />
              <!-- PathwayList
                :pathways="dashboardStore.inProgressPathways"
                title="Percorsi in Corso"
                emptyMessage="Non hai percorsi in corso al momento."
                :loading="dashboardStore.loading.pathways"
              / -->
            </div>
          </template>

          <template #completed>
            <div class="space-y-6">
              <QuizList
                :quizzes="dashboardStore.completedQuizzes"
                title="Quiz Completati"
                emptyMessage="Non hai ancora completato nessun quiz."
                :loading="dashboardStore.loading.quizzes"
              />
              <!-- PathwayList
                :pathways="dashboardStore.completedPathways"
                title="Percorsi Completati"
                emptyMessage="Non hai ancora completato nessun percorso."
                :loading="dashboardStore.loading.pathways"
                :showResultLink="true"
              / -->
            </div>
          </template>
        </BaseTabs>
      </div>
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