<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import RewardsService, { type Badge, type EarnedBadge } from '@/api/rewards'; // Assumiamo che le interfacce siano in rewards
import AnimatedBadge from '@/components/common/AnimatedBadge.vue'; // Importa il nuovo componente

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
      <h1 class="text-3xl font-bold text-primary-dark flex items-center"> <!-- Colore titolo aggiornato -->
        <span class="text-4xl mr-3">🏆</span> I Miei Traguardi
      </h1>
    </header>

    <div v-if="isLoading" class="loading text-center py-10 text-neutral-dark"> <!-- Colore testo aggiornato -->
      <p>Caricamento badge...</p>
      <svg class="animate-spin h-5 w-5 text-primary mx-auto mt-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"> <!-- Colore spinner aggiornato -->
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>

    <div v-if="error" class="error-message bg-error/10 border-l-4 border-error text-error p-4 mb-6 rounded" role="alert"> <!-- Colori errore aggiornati -->
      <p class="font-semibold">{{ error }}</p>
    </div>

    <div v-if="!isLoading && !error" class="badges-grid grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
      <!-- Usa AnimatedBadge -->
      <div
        v-for="badge in allBadges"
        :key="badge.id"
        class="badge-wrapper transition-opacity duration-300"
        :class="{
          'opacity-50 filter grayscale hover:opacity-100 hover:filter-none': !earnedBadgeIds.has(badge.id)
        }"
      >
        <AnimatedBadge :badge="badge" />
         <!-- Mostra data ottenimento se guadagnato -->
         <p v-if="earnedBadgeIds.has(badge.id)" class="text-xs text-success-dark mt-1 text-center"> <!-- Colore testo aggiornato -->
            <!-- TODO: Mostrare data effettiva da earnedBadges -->
            Ottenuto!
         </p>
      </div>
    </div>
     <div v-if="!isLoading && !error && allBadges.length === 0" class="text-center py-10 text-neutral-dark"> <!-- Colore testo aggiornato -->
        <p>Nessun badge definito al momento.</p>
     </div>
  </div>
</template>

<style scoped>
/* Rimuoviamo gli stili specifici per .badge-card img */
</style>