<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import RewardsService, { type Badge, type EarnedBadge } from '@/api/rewards'; // Assumiamo che le interfacce siano in rewards

// State
const allBadges = ref<Badge[]>([]);
const earnedBadges = ref<EarnedBadge[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

// Computed property per mappare gli ID dei badge guadagnati per un controllo rapido
const earnedBadgeIds = computed(() => new Set(earnedBadges.value.map(eb => eb.badge.id)));

// Funzioni
async function fetchData() {
  isLoading.value = true;
  error.value = null;
  try {
    // Esegui le chiamate in parallelo
    const [allBadgesResponse, earnedBadgesResponse] = await Promise.all([
      RewardsService.getAllBadges(), // Da implementare in RewardsService
      RewardsService.getEarnedBadges() // Da implementare in RewardsService
    ]);
    allBadges.value = allBadgesResponse;
    earnedBadges.value = earnedBadgesResponse;
  } catch (err: any) {
    console.error("Errore durante il recupero dei dati dei badge:", err);
    error.value = "Impossibile caricare i badge. Riprova più tardi.";
  } finally {
    isLoading.value = false;
  }
}

// Lifecycle Hooks
onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="badges-view container mx-auto px-4 py-8">
    <header class="badges-header mb-8">
      <h1 class="text-3xl font-bold text-gray-800 flex items-center">
        <span class="text-4xl mr-3">🏆</span> I Miei Traguardi
      </h1>
    </header>

    <div v-if="isLoading" class="loading text-center py-10 text-gray-500">
      <p>Caricamento badge...</p>
      {/* Spinner */}
      <svg class="animate-spin h-5 w-5 text-gray-500 mx-auto mt-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>

    <div v-if="error" class="error-message bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded" role="alert">
      <p>{{ error }}</p>
    </div>

    <div v-if="!isLoading && !error" class="badges-grid grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
      <div 
        v-for="badge in allBadges" 
        :key="badge.id" 
        class="badge-card border rounded-lg p-4 text-center transition-all duration-300 ease-in-out"
        :class="{
          'bg-white shadow-md transform hover:scale-105': earnedBadgeIds.has(badge.id),
          'bg-gray-100 opacity-60 filter grayscale': !earnedBadgeIds.has(badge.id)
        }"
      >
        <img 
          :src="badge.image || '/placeholder-badge.svg'"
          :alt="badge.name" 
          class="w-20 h-20 mx-auto mb-3 object-contain"
          :class="{ 'opacity-50': !earnedBadgeIds.has(badge.id) }"
        />
        <h3 
          class="font-semibold text-sm mb-1"
          :class="{ 'text-gray-800': earnedBadgeIds.has(badge.id), 'text-gray-500': !earnedBadgeIds.has(badge.id) }"
        >
          {{ badge.name }}
        </h3>
        <p 
          class="text-xs"
          :class="{ 'text-gray-600': earnedBadgeIds.has(badge.id), 'text-gray-400': !earnedBadgeIds.has(badge.id) }"
          :title="badge.description"
        >
          {{ badge.description }}
        </p>
         <p v-if="earnedBadgeIds.has(badge.id)" class="text-xs text-green-600 mt-2 font-medium">
           Ottenuto!
         </p>
      </div>
    </div>
     <div v-if="!isLoading && !error && allBadges.length === 0" class="text-center py-10 text-gray-500">
        <p>Nessun badge definito al momento.</p>
     </div>
  </div>
</template>

<style scoped>
/* Stili aggiuntivi se necessari */
.badge-card img {
  /* Potrebbe servire per gestire meglio immagini non quadrate */
}
</style>