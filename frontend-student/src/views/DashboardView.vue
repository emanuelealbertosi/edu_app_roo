<script setup lang="ts">
import { onMounted, ref } from 'vue';
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
  <div class="dashboard">
    <header class="dashboard-header">
      <div class="user-info">
        <h1>Dashboard Studente</h1>
        <p>Benvenuto, <strong>{{ authStore.userFullName }}</strong>!</p>
      </div>
      <div class="header-actions">
        <button @click="goToShop" class="shop-button">
          <span class="button-icon">🛒</span> Shop Ricompense
        </button>
        <button @click="handleLogout" class="logout-button">
          <span class="button-icon">🚪</span> Logout
        </button>
      </div>
    </header>
    
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Caricamento in corso...</p>
    </div>
    
    <div v-else class="dashboard-content">
      <!-- Sezione wallet -->
      <div class="wallet-section">
        <WalletCard
          :wallet="dashboardStore.wallet"
          :loading="dashboardStore.loading.wallet"
        />
      </div>
      
      <!-- Sezione quiz e percorsi -->
      <div class="educational-content">
        <!-- Quiz disponibili -->
        <QuizList
          :quizzes="dashboardStore.availableQuizzes"
          title="Quiz Disponibili"
          emptyMessage="Non ci sono quiz disponibili al momento."
          :loading="dashboardStore.loading.quizzes"
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
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.user-info h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.user-info p {
  margin: 0;
  color: #666;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 2rem;
}

@media (max-width: 992px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }
}

.wallet-section {
  order: 1;
}

.educational-content {
  order: 2;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.dashboard-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.shop-button {
  background-color: #4caf50; /* Verde */
  padding: 0.75rem 1.5rem;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logout-button {
  background-color: #f44336; /* Rosso */
  padding: 0.75rem 1.5rem;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

button:hover {
  opacity: 0.9;
}

.button-icon {
  font-size: 1.2rem;
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
</style>