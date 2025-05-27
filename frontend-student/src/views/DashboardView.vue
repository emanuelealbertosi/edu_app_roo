<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
import WalletCard from '@/components/WalletCard.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import AnimatedBadge from '@/components/common/AnimatedBadge.vue';
import BadgeDetailModal from '@/components/common/BadgeDetailModal.vue'; // Importa la nuova modale
import type { Badge } from '@/api/rewards'; // Importa il tipo Badge

const authStore = useAuthStore();
const dashboardStore = useDashboardStore();
const router = useRouter();

const isLoading = ref(true);
const dashboardError = computed(() => dashboardStore.error);

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

// Funzione helper per mappare un singolo oggetto badge (potenzialmente da API con snake_case)
// a un oggetto Badge con camelCase, come atteso dal frontend.
// Copiata da BadgesView.vue
function mapApiBadgeToFrontendBadge(apiBadge: any): Badge {
  // Assicurati che isEarned sia sempre un booleano, specialmente per il preferred badge
  // che per definizione è "earned".
  let isEarned = typeof apiBadge.isEarned === 'boolean' ? apiBadge.isEarned : (typeof apiBadge.is_earned === 'boolean' ? apiBadge.is_earned : false);
  if (apiBadge && Object.keys(apiBadge).length > 0) { // Se l'oggetto apiBadge non è vuoto, consideralo guadagnato
      isEarned = true;
  }

  // Gestione di fileUrl esattamente come in BadgesView.vue
  const fileUrl = apiBadge.fileUrl || apiBadge.file_url || null;

  let mediaType = apiBadge.mediaType || apiBadge.media_type || 'IMAGE_STATIC';
  if (typeof mediaType === 'string') {
    const upperType = mediaType.toUpperCase();
    if (upperType === 'VIDEO_MP4') mediaType = 'VIDEO_MP4';
    else if (upperType === 'IMAGE_GIF') mediaType = 'IMAGE_GIF';
    else if (upperType === 'IMAGE_STATIC') mediaType = 'IMAGE_STATIC';
    // else lascia mediaType com'è se non corrisponde o normalizza a IMAGE_STATIC come fallback
  } else {
    mediaType = 'IMAGE_STATIC';
  }
  
  return {
    id: apiBadge.id,
    name: apiBadge.name,
    description: apiBadge.description,
    fileUrl: fileUrl,
    mediaType: mediaType,
    thumbnailUrl: apiBadge.thumbnailUrl || apiBadge.thumbnail_url || null,
    trigger_type: apiBadge.trigger_type,
    trigger_type_display: apiBadge.trigger_type_display,
    trigger_condition: apiBadge.trigger_condition,
    is_active: apiBadge.is_active,
    isEarned: isEarned, // Usa il valore di isEarned calcolato
    created_at: apiBadge.created_at,
  };
}

const preferredBadgeToDisplay = computed(() => dashboardStore.preferredBadge);

const mappedPreferredBadge = computed(() => {
  if (preferredBadgeToDisplay.value) {
    // Applica la mappatura. Assicurati che preferredBadgeToDisplay.value non sia null.
    // La funzione mapApiBadgeToFrontendBadge si aspetta un 'any', quindi va bene.
    // Importante: assicurarsi che 'isEarned' sia gestito correttamente.
    // Un badge preferito è per definizione "guadagnato".
    const mapped = mapApiBadgeToFrontendBadge(preferredBadgeToDisplay.value);
    // Sovrascrivi isEarned a true per sicurezza, dato che è il badge preferito.
    // La funzione mapApiBadgeToFrontendBadge ora gestisce questo internamente.
    // mapped.isEarned = true;
    console.log('[DashboardView] Mapped Preferred Badge:', JSON.parse(JSON.stringify(mapped)));
    return mapped;
  }
  return null;
});

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
          <h2 class="text-xl font-bold text-primary-dark mb-4 flex items-center justify-center"><span class="text-2xl mr-2">🌟</span> Badge in Evidenza</h2>
          <div v-if="dashboardStore.loading.preferredBadge || dashboardStore.loading.badges" class="text-sm text-neutral-dark italic py-4">Caricamento badge...</div>
          <AnimatedBadge
            v-else-if="mappedPreferredBadge"
            :key="mappedPreferredBadge.id"
            :badge="mappedPreferredBadge"
            @open-modal="openBadgeModal"
            class="mx-auto max-w-[theme(spacing.72)] mb-3"
          />
          <p v-else class="text-sm text-neutral-dark italic py-4">Nessun badge preferito selezionato. Scegline uno dalla sezione Traguardi!</p>
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

    <BadgeDetailModal
      v-if="selectedBadge"
      :show="showBadgeModal"
      :badge="selectedBadge"
      @close="closeBadgeModal"
    />
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