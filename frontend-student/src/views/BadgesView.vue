<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import RewardsService, { type Badge, type EarnedBadge } from '@/api/rewards'; // Assumiamo che le interfacce siano in rewards
import AnimatedBadge from '@/components/common/AnimatedBadge.vue'; // Importa il nuovo componente
import BadgeDetailModal from '@/components/common/BadgeDetailModal.vue'; // Importa la nuova modale
import { useDashboardStore } from '@/stores/dashboard'; // Importa lo store della dashboard

// State
const allBadges = ref<Badge[]>([]);
const earnedBadges = ref<EarnedBadge[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

const showBadgeModal = ref(false);
const selectedBadge = ref<Badge | null>(null);

const openBadgeModal = (badgeInfo: Badge) => {
  selectedBadge.value = badgeInfo;
  showBadgeModal.value = true;
};

const closeBadgeModal = () => {
  showBadgeModal.value = false;
  selectedBadge.value = null;
};

// Store Dashboard
const dashboardStore = useDashboardStore();
const preferredBadge = computed(() => dashboardStore.preferredBadge);
 
const earnedBadgeIds = computed(() =>
  new Set(earnedBadges.value.map(eb => eb.badge.id))
);

const processedBadges = computed(() => {
  if (!allBadges.value || !earnedBadges.value) return [];

  // Creiamo una mappa per un accesso efficiente ai dettagli dei badge guadagnati.
  // L'oggetto eb.badge è di tipo Badge, come definito in api/rewards.ts
  const earnedBadgesMap = new Map(
    earnedBadges.value.map(eb => [eb.badge.id, eb.badge])
  );

  return allBadges.value.map(badgeFromAll => {
    const isEarned = earnedBadgeIds.value.has(badgeFromAll.id);
    
    if (isEarned) {
      const earnedDetail = earnedBadgesMap.get(badgeFromAll.id);
      if (earnedDetail) {
        // Trovato il badge nei dettagli dei guadagnati.
        // Usiamo i dettagli da earnedDetail (che dovrebbero essere completi)
        // e ci assicuriamo che isEarned sia true.
        return {
          ...earnedDetail, // Questo include fileUrl, mediaType, thumbnailUrl da earnedDetail
          isEarned: true
        };
      } else {
        // Caso anomalo: l'ID è in earnedBadgeIds ma non ci sono dettagli in earnedBadgesMap.
        // Questo non dovrebbe succedere se i dati API sono consistenti.
        // Per sicurezza, usiamo i dati da badgeFromAll ma forziamo isEarned a true.
        // Potrebbe comunque mostrare '?' se badgeFromAll.fileUrl è null.
        return { ...badgeFromAll, isEarned: true };
      }
    } else {
      // Badge non guadagnato. Usiamo i dati da badgeFromAll.
      // Assicuriamoci che isEarned sia esplicitamente false.
      return { ...badgeFromAll, isEarned: false };
    }
  });
});

// Funzioni

// Funzione helper per mappare un singolo oggetto badge (potenzialmente da API con snake_case)
// a un oggetto Badge con camelCase, come atteso dal frontend.
function mapApiBadgeToFrontendBadge(apiBadge: any): Badge {
  return {
    id: apiBadge.id,
    name: apiBadge.name,
    description: apiBadge.description,
    fileUrl: apiBadge.fileUrl || apiBadge.file_url || null,
    mediaType: apiBadge.mediaType || apiBadge.media_type || 'IMAGE_STATIC',
    thumbnailUrl: apiBadge.thumbnailUrl || apiBadge.thumbnail_url || null,
    trigger_type: apiBadge.trigger_type,
    trigger_type_display: apiBadge.trigger_type_display,
    trigger_condition: apiBadge.trigger_condition,
    is_active: apiBadge.is_active,
    // isEarned qui è per la definizione generale del badge,
    // verrà sovrascritto in processedBadges se necessario.
    // L'API per /rewards/badges/ potrebbe non includere is_earned per lo studente specifico.
    isEarned: typeof apiBadge.isEarned === 'boolean' ? apiBadge.isEarned : (typeof apiBadge.is_earned === 'boolean' ? apiBadge.is_earned : false),
    created_at: apiBadge.created_at,
  };
}

async function fetchData() {
  isLoading.value = true;
  error.value = null;
  try {
    const [rawAllBadges, rawEarnedBadges] = await Promise.all([
      RewardsService.getAllBadges(),
      RewardsService.getEarnedBadges()
    ]);

    // Mappa allBadges
    allBadges.value = rawAllBadges.map(mapApiBadgeToFrontendBadge);

    // Mappa earnedBadges (che contengono un oggetto 'badge' annidato)
    earnedBadges.value = rawEarnedBadges.map((eb: any) => ({
      id: eb.id,
      student: eb.student,
      earned_at: eb.earned_at,
      badge: mapApiBadgeToFrontendBadge(eb.badge), // Mappa l'oggetto badge annidato
    }));

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
  // Assicurati che i dati della dashboard (incluso il preferredBadge) siano caricati.
  // Se non è già stato fatto altrove (es. App.vue), potrebbe essere necessario chiamare dashboardStore.loadDashboard()
  // Tuttavia, per ora presumiamo sia gestito a un livello superiore.
});

async function handleSetPreferredBadge(badgeId: number) {
  const currentPreferredId = preferredBadge.value?.id;
  let newPreferredId: number | null = badgeId;

  if (currentPreferredId === badgeId) {
    // Se si clicca sul badge già preferito, lo si deseleziona
    newPreferredId = null;
  }

  try {
    await dashboardStore.setPreferredBadge(newPreferredId);
    // Successo: lo store è aggiornato, il computed preferredBadge si aggiornerà
    // e l'UI rifletterà il cambiamento.
  } catch (err) {
    console.error("Errore nell'impostare il badge preferito:", err);
    // Mostra un messaggio di errore all'utente se necessario
    error.value = "Impossibile aggiornare il badge preferito. Riprova.";
    // Potresti voler resettare l'errore dopo un po'
    setTimeout(() => { error.value = null; }, 5000);
  }
}
</script>

<template>
  <div class="badges-view px-2 md:px-4 py-8"> <!-- Rimosso container mx-auto, aggiunto padding laterale -->
    <header class="badges-header bg-accent text-neutral-lightest p-4 rounded-lg shadow-md mb-6">
      <h1 class="text-2xl font-semibold flex items-center">
        <span class="text-3xl mr-3">🏆</span> I Miei Traguardi
      </h1>
    </header>

    <div class="w-full"> <!-- Contenuto principale avvolto in container -->
      <div v-if="isLoading" class="loading text-center py-10 text-neutral-dark">
      <p>Caricamento badge...</p>
      <svg class="animate-spin h-5 w-5 text-primary mx-auto mt-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>

    <div v-if="error" class="error-message bg-error/10 border-l-4 border-error text-error p-4 mb-6 rounded" role="alert">
      <p class="font-semibold">{{ error }}</p>
    </div>

    <div v-if="!isLoading && !error" class="badges-grid grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
      <div
        v-for="processedBadgeItem in processedBadges"
        :key="processedBadgeItem.id"
        class="badge-wrapper relative flex flex-col items-center"
      >
        <AnimatedBadge :badge="processedBadgeItem" @open-modal="openBadgeModal" />
        
        <!-- Pulsante Stella per selezionare/deselezionare il badge preferito -->
        <button
          v-if="processedBadgeItem.isEarned"
          @click="handleSetPreferredBadge(processedBadgeItem.id)"
          :title="processedBadgeItem.id === preferredBadge?.id ? 'Rimuovi dai preferiti' : 'Imposta come preferito'"
          class="absolute top-1 right-1 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          :class="{
            'text-yellow-400': processedBadgeItem.id === preferredBadge?.id,
            'text-gray-400 hover:text-yellow-400': processedBadgeItem.id !== preferredBadge?.id
          }"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-6 h-6">
            <path
              fill-rule="evenodd"
              d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.006 5.404.434c1.164.093 1.636 1.545.749 2.305l-4.116 3.588 1.28 5.281c.28 1.158-.98 2.035-1.99 1.451L12 18.654l-4.758 2.927c-1.01.584-2.27-.293-1.99-1.451l1.28-5.281-4.117-3.588c-.887-.76-.415-2.212.749-2.305l5.404-.434 2.082-5.005Z"
              clip-rule="evenodd"
            />
          </svg>
        </button>

        <p v-if="processedBadgeItem.isEarned" class="text-xs text-success-dark mt-1 text-center">
          Ottenuto!
        </p>
        <p v-else class="text-xs text-neutral-light mt-1 text-center">
          Non ottenuto
        </p>
      </div>
    </div>
     <div v-if="!isLoading && !error && processedBadges.length === 0" class="text-center py-10 text-neutral-dark">
        <p>Nessun badge definito al momento.</p>
     </div>
  </div> <!-- Chiusura del div container mx-auto -->

  <BadgeDetailModal
    v-if="selectedBadge"
    :show="showBadgeModal"
    :badge="selectedBadge"
    @close="closeBadgeModal"
  />
</div> <!-- Chiusura del div badges-view principale -->
</template>

<style scoped>
/* Rimuoviamo gli stili specifici per .badge-card img */
</style>