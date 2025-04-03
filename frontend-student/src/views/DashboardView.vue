<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'; // Aggiunto computed
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
import QuizList from '@/components/QuizList.vue';
import PathwayList from '@/components/PathwayList.vue';
import WalletCard from '@/components/WalletCard.vue';

const authStore = useAuthStore();
const dashboardStore = useDashboardStore();
const router = useRouter();

const isLoading = ref(true);
const dashboardError = computed(() => dashboardStore.error); // Computed per l'errore
onMounted(async () => {
  // Verifichiamo che l'utente sia autenticato quando la vista viene caricata
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
  <div class="dashboard bg-gray-100 p-4 md:p-8 min-h-screen">
    <header class="dashboard-header bg-white p-6 rounded-lg shadow-md mb-8 flex flex-col md:flex-row justify-between items-center">
      <div class="user-info mb-4 md:mb-0 text-center md:text-left">
        <h1 class="text-2xl font-bold text-purple-800 mb-1">Dashboard Studente</h1>
        <p class="text-gray-600">Benvenuto, <strong class="font-semibold">{{ authStore.userFullName }}</strong>!</p>
      </div>
      <div class="header-actions flex gap-4">
        <button @click="goToShop" class="shop-button bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-5 rounded-lg shadow flex items-center gap-2 transition-colors duration-200">
          <span class="text-xl">🛒</span> Shop Ricompense
        </button>
        <button @click="handleLogout" class="logout-button bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-5 rounded-lg shadow flex items-center gap-2 transition-colors duration-200">
          <span class="text-xl">🚪</span> Logout
        </button>
      </div>
    </header>

    <!-- Messaggio di errore generale -->
    <div v-if="dashboardError &amp;&amp; !isLoading" class="error-message dashboard-error">
      <p>{{ dashboardError }}</p>
      <button @click="dashboardStore.loadDashboard" class="retry-button">Riprova Caricamento</button>
    </div>
    
    <div v-if="isLoading" class="loading-container flex flex-col items-center justify-center p-12 text-center">
      <div class="loading-spinner"></div>
      <p class="mt-4 text-gray-600">Caricamento in corso...</p>
    </div>

    <div v-else class="dashboard-content grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Sezione wallet -->
      <div class="wallet-section lg:col-span-1">
        <WalletCard
          :wallet="dashboardStore.wallet"
          :loading="dashboardStore.loading.wallet"
        />
      </div>
      
      <!-- Sezione quiz e percorsi -->
      <div class="educational-content lg:col-span-2 flex flex-col gap-8">
        <!-- Quiz disponibili -->
        <QuizList
          :quizzes="dashboardStore.availableQuizzes"
          title="Quiz Disponibili"
          emptyMessage="Non ci sono quiz disponibili al momento."
          :loading="dashboardStore.loading.quizzes"
          :showStartButton="true"
        />

        <!-- Quiz in corso -->
        <QuizList
          :quizzes="dashboardStore.inProgressQuizzes"
          title="Quiz in Corso"
          emptyMessage="Non hai quiz in corso al momento."
          :loading="dashboardStore.loading.quizzes"
        />

        <!-- Percorsi in corso -->
        <PathwayList
          :pathways="dashboardStore.inProgressPathways"
          title="Percorsi in Corso"
          emptyMessage="Non hai percorsi in corso al momento."
          :loading="dashboardStore.loading.pathways"
        />

        <!-- Quiz completati -->
        <QuizList
          :quizzes="dashboardStore.completedQuizzes"
          title="Quiz Completati"
          emptyMessage="Non hai ancora completato nessun quiz."
          :loading="dashboardStore.loading.quizzes"
        />

        <!-- Percorsi completati -->
        <PathwayList
          :pathways="dashboardStore.completedPathways"
          title="Percorsi Completati"
          emptyMessage="Non hai ancora completato nessun percorso."
          :loading="dashboardStore.loading.pathways"
          :showResultLink="true"
        />
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
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: var(--vt-c-indigo);
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
  margin-bottom: 2rem;
  padding: 15px;
  border-radius: 5px;
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  text-align: center;
}

.retry-button {
    margin-top: 10px;
    padding: 5px 15px;
    font-size: 0.9em;
    cursor: pointer;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 3px;
}
.retry-button:hover {
    background-color: #5a6268;
}

</style>