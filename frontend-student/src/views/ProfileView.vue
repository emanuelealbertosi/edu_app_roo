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
const studentCode = computed(() => authStore.studentCode);
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
  <div class="profile-view">
    <header class="profile-header">
      <h1>👤 Profilo Studente</h1>
      <button @click="router.push('/dashboard')" class="back-button">Torna alla Dashboard</button>
    </header>
    
    <!-- Messaggio di errore caricamento -->
     <div v-if="walletError" class="error-message">
      <p>{{ walletError }}</p>
    </div>

    <div class="profile-content">
      <div class="profile-card info-card">
        <h2>Informazioni Personali</h2>
        <div class="info-item">
          <span class="info-label">Nome:</span>
          <span class="info-value">{{ studentName }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Codice Studente:</span>
          <span class="info-value">{{ studentCode }}</span>
        </div>
      </div>

      <div class="profile-card stats-card">
        <h2>Statistiche</h2>
        <div class="info-item">
          <span class="info-label">Punti Attuali:</span>
          <span v-if="isLoadingWallet" class="loading-text">Caricamento...</span>
          <span v-else class="info-value points">{{ currentPoints }} ✨</span>
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
        <p class="stats-placeholder">(Altre statistiche saranno disponibili prossimamente)</p>
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
.profile-view {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  background-color: #f8f9fa;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.profile-header h1 {
  margin: 0;
  font-size: 1.8em;
  color: #333;
}

.back-button {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}
.back-button:hover {
  background-color: #5a6268;
}

.error-message {
  margin-bottom: 1.5rem;
  padding: 15px;
  border-radius: 5px;
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  text-align: center;
}

.loading-text {
    font-style: italic;
    color: #888;
}

.profile-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.profile-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.profile-card h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #0056b3; /* Blu scuro */
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 0.5rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed #eee;
}
.info-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
}

.info-label {
  font-weight: 500;
  color: #555;
}

.info-value {
  color: #333;
}

.info-value.points {
    font-weight: bold;
    color: #ff8f00; /* Arancione per i punti */
}

.stats-placeholder {
    color: #888;
    font-style: italic;
    text-align: center;
    margin-top: 1.5rem;
}

/* Stili per la card acquisti (se aggiunta) */
.purchases-card a {
    color: #007bff;
    text-decoration: none;
    font-weight: 500;
}
.purchases-card a:hover {
    text-decoration: underline;
}
</style>