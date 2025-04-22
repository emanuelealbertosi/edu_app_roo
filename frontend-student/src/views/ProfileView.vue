<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'; // Aggiunto ref
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton
// TODO: Importare la funzione API per aggiornare il PIN quando sarà disponibile
// import { updateUserPin } from '@/api/user';

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

// State per il form del PIN
const newPin = ref('');
const confirmPin = ref('');
const pinSuccessMessage = ref<string | null>(null);
const pinErrorMessage = ref<string | null>(null);
const isSettingPin = ref(false); // Per disabilitare il pulsante durante il salvataggio

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

// Funzione per gestire l'impostazione/modifica del PIN
const handleSetPin = async () => {
  pinSuccessMessage.value = null;
  pinErrorMessage.value = null;
  isSettingPin.value = true;

  // Validazione base
  if (newPin.value.length < 4) {
    pinErrorMessage.value = 'Il PIN deve contenere almeno 4 cifre.';
    isSettingPin.value = false;
    return;
  }
  if (newPin.value !== confirmPin.value) {
    pinErrorMessage.value = 'I PIN inseriti non coincidono.';
    isSettingPin.value = false;
    return;
  }
  if (!/^\d+$/.test(newPin.value)) {
    pinErrorMessage.value = 'Il PIN può contenere solo cifre numeriche.';
    isSettingPin.value = false;
    return;
  }

  try {
    // --- Chiamata API (da implementare) ---
    console.log('Tentativo di aggiornare il PIN con:', newPin.value);
    // await authStore.updateStudentPin(newPin.value); // Esempio di chiamata allo store
    // await updateUserPin(newPin.value); // Esempio di chiamata API diretta

    // Simula successo per ora
    await new Promise(resolve => setTimeout(resolve, 500)); 
    pinSuccessMessage.value = 'PIN aggiornato con successo!';
    newPin.value = ''; // Resetta i campi
    confirmPin.value = '';
    // --------------------------------------

  } catch (error: any) {
    console.error("Errore durante l'aggiornamento del PIN:", error);
    pinErrorMessage.value = error.message || "Si è verificato un errore durante l'aggiornamento del PIN.";
  } finally {
    isSettingPin.value = false;
  }
};

</script>

<template>
  <div class="profile-view container mx-auto px-4 py-8">
    <header class="profile-header bg-white p-4 md:p-6 rounded-lg shadow-md mb-8 flex flex-col md:flex-row justify-between items-center gap-4"> <!-- Aggiunto gap -->
      <h1 class="text-2xl md:text-3xl font-bold text-kahoot-purple flex items-center"><span class="text-3xl md:text-4xl mr-3">👤</span> Profilo Studente</h1> <!-- Colore titolo aggiornato -->
      <BaseButton variant="secondary" @click="router.push('/dashboard')">Torna alla Dashboard</BaseButton> <!-- Usa BaseButton -->
    </header>

    <!-- Messaggio di errore caricamento -->
     <div v-if="walletError" class="error-message bg-kahoot-red-light border-l-4 border-kahoot-red text-kahoot-red-dark p-4 mb-6 rounded" role="alert"> <!-- Colori errore aggiornati -->
      <p class="font-semibold">{{ walletError }}</p>
    </div>

    <div class="profile-content grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="profile-card info-card bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-kahoot-blue mb-4 border-b pb-2">Informazioni Personali</h2> <!-- Colore titolo aggiornato -->
        <div class="info-item flex justify-between items-center py-2 border-b border-dashed border-brand-gray-light"> <!-- Colore bordo aggiornato -->
          <span class="info-label font-medium text-brand-gray-dark">Nome:</span> <!-- Colore testo aggiornato -->
          <span class="info-value text-brand-gray-dark">{{ studentName }}</span> <!-- Colore testo aggiornato -->
        </div>
        <div class="info-item flex justify-between items-center py-2">
          <span class="info-label font-medium text-brand-gray-dark">Codice Studente:</span> <!-- Colore testo aggiornato -->
          <span class="info-value text-brand-gray-dark font-mono">{{ studentCode }}</span> <!-- Colore testo aggiornato -->
        </div>
      </div>

      <div class="profile-card stats-card bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-kahoot-green mb-4 border-b pb-2">Statistiche</h2> <!-- Colore titolo aggiornato -->
        <div class="info-item flex justify-between items-center py-2 border-b border-dashed border-brand-gray-light"> <!-- Colore bordo aggiornato -->
          <span class="info-label font-medium text-brand-gray-dark">Punti Attuali:</span> <!-- Colore testo aggiornato -->
          <span v-if="isLoadingWallet" class="loading-text text-sm italic text-brand-gray">Caricamento...</span> <!-- Colore testo aggiornato -->
          <span v-else class="info-value points text-2xl font-bold text-kahoot-yellow-dark">{{ currentPoints }} ✨</span> <!-- Colore punti aggiornato -->
        </div>
        
        <p class="stats-placeholder text-sm text-brand-gray italic text-center mt-4">(Altre statistiche saranno disponibili prossimamente)</p> <!-- Colore testo aggiornato -->
      </div>

      <!-- Nuova Card per Impostare/Modificare PIN -->
      <div class="profile-card pin-card bg-white rounded-lg shadow-md p-6 md:col-span-2">
        <h2 class="text-xl font-semibold text-kahoot-purple mb-4 border-b pb-2">Imposta / Modifica PIN</h2> <!-- Colore titolo aggiornato -->
        <form @submit.prevent="handleSetPin">
          <div class="mb-4">
            <label for="newPin" class="block text-brand-gray-dark text-sm font-bold mb-2">Nuovo PIN (min. 4 cifre):</label> <!-- Colore testo aggiornato -->
            <input
              type="password"
              id="newPin"
              v-model="newPin"
              required
              minlength="4"
              pattern="\d*"
              inputmode="numeric"
              autocomplete="new-password"
              class="shadow appearance-none border rounded w-full py-2 px-3 text-brand-gray-dark leading-tight focus:outline-none focus:ring-2 focus:ring-kahoot-purple focus:border-transparent"
            />
          </div>
          <div class="mb-6">
            <label for="confirmPin" class="block text-brand-gray-dark text-sm font-bold mb-2">Conferma Nuovo PIN:</label> <!-- Colore testo aggiornato -->
            <input
              type="password"
              id="confirmPin"
              v-model="confirmPin"
              required
              minlength="4"
              pattern="\d*"
              inputmode="numeric"
              autocomplete="new-password"
              class="shadow appearance-none border rounded w-full py-2 px-3 text-brand-gray-dark leading-tight focus:outline-none focus:ring-2 focus:ring-kahoot-purple focus:border-transparent"
            />
          </div>

          <!-- Messaggi di Errore/Successo -->
          <p v-if="pinErrorMessage" class="error-message text-kahoot-red text-sm mb-4 text-center">{{ pinErrorMessage }}</p> <!-- Colore errore aggiornato -->
          <p v-if="pinSuccessMessage" class="success-message text-kahoot-green-dark text-sm mb-4 text-center">{{ pinSuccessMessage }}</p> <!-- Colore successo aggiornato -->

          <BaseButton
            type="submit"
            variant="primary"
            :disabled="isSettingPin"
            class="w-full"
          >
            {{ isSettingPin ? 'Salvataggio...' : 'Salva PIN' }}
          </BaseButton>
        </form>
        <p class="text-xs text-brand-gray mt-4 italic">Ricorda: Il PIN viene utilizzato insieme al tuo codice studente per accedere.</p> <!-- Colore testo aggiornato -->
      </div>

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