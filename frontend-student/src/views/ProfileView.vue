<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';

// State
const router = useRouter();
const authStore = useAuthStore();
const dashboardStore = useDashboardStore();

// Computed properties per accedere facilmente ai dati
const studentName = computed(() => authStore.userFullName);
const studentCode = computed(() => authStore.user?.student_code ?? 'N/D'); // Accedi tramite user
const currentPoints = computed(() => dashboardStore.wallet?.current_points ?? 0);
const isLoadingWallet = computed(() => dashboardStore.loading.wallet); // Per mostrare caricamento wallet
const walletError = computed(() => dashboardStore.error); // Per mostrare errori caricamento

// TODO: Aggiungere statistiche quando disponibili (es. da API o calcolate)
// const quizzesCompleted = computed(() => dashboardStore.completedQuizzes.length);
// const pathwaysCompleted = computed(() => dashboardStore.completedPathways.length);
// const totalPointsEarned = computed(() => ...); // Potrebbe richiedere un nuovo endpoint API

// Lifecycle Hooks
onMounted(() => {
  // Assicurati che i dati necessari siano caricati
  if (!dashboardStore.wallet) {
    dashboardStore.fetchWallet(); // Corretto: usa fetchWallet
  }
  // Potremmo caricare altre statistiche qui se necessario
});

</script>

<template>
  <div class="profile-view container mx-auto px-4 py-8">
    <header class="profile-header bg-white p-4 md:p-6 rounded-lg shadow-md mb-8 flex justify-between items-center">
      <h1 class="text-2xl md:text-3xl font-bold text-gray-800 flex items-center"><span class="text-3xl md:text-4xl mr-3">👤</span> Profilo Studente</h1>
      <button @click="router.push('/dashboard')" class="back-button bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg shadow transition-colors duration-200">Torna alla Dashboard</button>
    </header>
    
    <!-- Messaggio di errore caricamento -->
     <div v-if="walletError" class="error-message bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded" role="alert">
      <p>{{ walletError }}</p>
    </div>

    <div class="profile-content grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="profile-card info-card bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-blue-700 mb-4 border-b pb-2">Informazioni Personali</h2>
        <div class="info-item flex justify-between items-center py-2 border-b border-dashed border-gray-200">
          <span class="info-label font-medium text-gray-600">Nome:</span>
          <span class="info-value text-gray-800">{{ studentName }}</span>
        </div>
        <div class="info-item flex justify-between items-center py-2">
          <span class="info-label font-medium text-gray-600">Codice Studente:</span>
          <span class="info-value text-gray-800 font-mono">{{ studentCode }}</span>
        </div>
      </div>

      <div class="profile-card stats-card bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-green-700 mb-4 border-b pb-2">Statistiche</h2>
        <div class="info-item flex justify-between items-center py-2 border-b border-dashed border-gray-200">
          <span class="info-label font-medium text-gray-600">Punti Attuali:</span>
          <span v-if="isLoadingWallet" class="loading-text text-sm italic text-gray-500">Caricamento...</span>
          <span v-else class="info-value points text-2xl font-bold text-yellow-600">{{ currentPoints }} ✨</span>
        </div>
        <!-- 
        <div class="info-item">
          <span class="info-label">Quiz Completati:</span>
          <span class="info-value">{{ quizzesCompleted }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Percorsi Completati:</span>
          <span class="info-value">{{ pathwaysCompleted }}</span>
        </div> 
        -->
        <p class="stats-placeholder text-sm text-gray-500 italic text-center mt-4">(Altre statistiche saranno disponibili prossimamente)</p>
      </div>

      <!-- Potremmo aggiungere qui la sezione per lo storico acquisti -->
      <!-- 
      <div class="profile-card purchases-card">
        <h2>Storico Acquisti</h2>
        <router-link to="/purchases">Vedi tutti gli acquisti</router-link>
        </div> 
      -->
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici rimasti o che richiedono override */
.loading-text {
  /* Stili Tailwind applicati direttamente nel template */
}
.stats-placeholder {
   /* Stili Tailwind applicati direttamente nel template */
}
/* Eventuali altri stili specifici */
</style>