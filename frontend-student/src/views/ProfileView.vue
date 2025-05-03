<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'; // Aggiunto ref e watch
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton
// TODO: Importare la funzione API per aggiornare il PIN quando sarà disponibile
// import { updateUserPin } from '@/api/user';
import apiClient from '@/api/config'; // Importa l'istanza axios configurata

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
// State per GDPR Export
const exportedData = ref<any | null>(null);
const isLoadingData = ref(false);
const exportError = ref<string | null>(null);
// State per Modifica Profilo (Nome/Cognome)
const firstName = ref('');
const lastName = ref('');
const isUpdatingProfile = ref(false);
const profileUpdateSuccessMessage = ref<string | null>(null);
const profileUpdateErrorMessage = ref<string | null>(null);
// State per Richiesta Cancellazione Dati
const isRequestingDeletion = ref(false);
const deletionRequestSuccessMessage = ref<string | null>(null);
const deletionRequestErrorMessage = ref<string | null>(null);

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
  // Inizializza i campi del form con i dati correnti dell'utente
  firstName.value = authStore.user?.first_name ?? '';
  lastName.value = authStore.user?.last_name ?? '';
  // Potremmo caricare altre statistiche qui se necessario
});

// Watch per aggiornare i campi del form se i dati dell'utente cambiano nello store
watch(() => authStore.user, (newUser) => {
  if (newUser) {
    firstName.value = newUser.first_name ?? '';
    lastName.value = newUser.last_name ?? '';
  }
}, { deep: true });

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
// Funzione per richiedere l'esportazione dei dati GDPR
const handleExportData = async () => {
  isLoadingData.value = true;
  exportError.value = null;
  exportedData.value = null;
  try {
    // Chiama l'endpoint API corretto usando apiClient
    const response = await apiClient.get('/profile/my-data/');
    exportedData.value = response.data; // Salva i dati ricevuti
  } catch (error: any) {
    console.error("Errore durante l'esportazione dei dati GDPR:", error);
    exportError.value = error.response?.data?.detail || error.message || "Si è verificato un errore durante l'esportazione dei dati.";
  } finally {
    isLoadingData.value = false;
  }
};

// Funzione per scaricare i dati come file JSON
const downloadData = () => {
  if (!exportedData.value) return;

  const dataStr = JSON.stringify(exportedData.value, null, 2); // Formattato per leggibilità
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

  const exportFileDefaultName = 'my_gdpr_data.json';

  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();
  linkElement.remove(); // Pulisce l'elemento link
};

// Funzione per aggiornare nome e cognome
const handleUpdateProfile = async () => {
  isUpdatingProfile.value = true;
  profileUpdateSuccessMessage.value = null;
  profileUpdateErrorMessage.value = null;

  // Validazione semplice
  if (!firstName.value.trim() || !lastName.value.trim()) {
    profileUpdateErrorMessage.value = 'Nome e Cognome non possono essere vuoti.';
    isUpdatingProfile.value = false;
    return;
  }

  try {
    const payload = {
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
    };
    // Chiama l'endpoint API per aggiornare il profilo usando apiClient
    await apiClient.patch('/profile/me/', payload);

    // Aggiorna lo store locale (assumendo che l'API ritorni l'utente aggiornato o che lo store abbia un metodo per farlo)
    // Idealmente, ci sarebbe una action nello store: authStore.updateUserProfile(payload);
    // Soluzione temporanea: aggiorna direttamente i dati utente nello store se possibile
    if (authStore.user) {
       authStore.user.first_name = payload.first_name;
       authStore.user.last_name = payload.last_name;
       // Forza l'aggiornamento del computed property userFullName se necessario
       // (potrebbe non essere necessario con la reattività di Pinia)
    }
    // Potrebbe essere più robusto ricaricare i dati utente: await authStore.fetchUser();

    profileUpdateSuccessMessage.value = 'Profilo aggiornato con successo!';

  } catch (error: any) {
    console.error("Errore durante l'aggiornamento del profilo:", error);
    profileUpdateErrorMessage.value = error.response?.data?.detail || error.message || "Si è verificato un errore durante l'aggiornamento del profilo.";
  } finally {
    isUpdatingProfile.value = false;
  }
};

// Funzione per richiedere la cancellazione dei dati
const handleRequestDeletion = async () => {
  // Chiedi conferma all'utente prima di procedere
  if (!confirm("Sei sicuro di voler richiedere la cancellazione definitiva dei tuoi dati? Questa azione non può essere annullata.")) {
    return;
  }

  isRequestingDeletion.value = true;
  deletionRequestSuccessMessage.value = null;
  deletionRequestErrorMessage.value = null;

  try {
    // Chiama l'endpoint API per richiedere la cancellazione
    await apiClient.post('/profile/request-deletion/');

    deletionRequestSuccessMessage.value = 'Richiesta di cancellazione inviata con successo. Verrai disconnesso a breve e i tuoi dati saranno eliminati secondo le policy.';
    // Opzionale: Potresti disabilitare altre azioni o mostrare un overlay
    // Potresti anche forzare il logout dopo un breve ritardo
    // setTimeout(() => {
    //   authStore.logout(); // Assumendo che esista una funzione logout nello store
    //   router.push('/login');
    // }, 5000); // Logout dopo 5 secondi

  } catch (error: any) {
    console.error("Errore durante la richiesta di cancellazione dati:", error);
    deletionRequestErrorMessage.value = error.response?.data?.detail || error.message || "Si è verificato un errore durante la richiesta di cancellazione.";
  } finally {
    isRequestingDeletion.value = false;
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
        <!-- Nota: Questi campi sono ora modificabili nella card apposita -->
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

      <!-- Nuova Card per Modificare Nome/Cognome -->
      <div class="profile-card edit-profile-card bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-kahoot-orange mb-4 border-b pb-2">Modifica Profilo</h2>
        <form @submit.prevent="handleUpdateProfile">
          <div class="mb-4">
            <label for="firstName" class="block text-brand-gray-dark text-sm font-bold mb-2">Nome:</label>
            <input
              type="text"
              id="firstName"
              v-model="firstName"
              required
              class="shadow appearance-none border rounded w-full py-2 px-3 text-brand-gray-dark leading-tight focus:outline-none focus:ring-2 focus:ring-kahoot-orange focus:border-transparent"
            />
          </div>
          <div class="mb-6">
            <label for="lastName" class="block text-brand-gray-dark text-sm font-bold mb-2">Cognome:</label>
            <input
              type="text"
              id="lastName"
              v-model="lastName"
              required
              class="shadow appearance-none border rounded w-full py-2 px-3 text-brand-gray-dark leading-tight focus:outline-none focus:ring-2 focus:ring-kahoot-orange focus:border-transparent"
            />
          </div>

          <!-- Messaggi di Errore/Successo -->
          <p v-if="profileUpdateErrorMessage" class="error-message text-kahoot-red text-sm mb-4 text-center">{{ profileUpdateErrorMessage }}</p>
          <p v-if="profileUpdateSuccessMessage" class="success-message text-kahoot-green-dark text-sm mb-4 text-center">{{ profileUpdateSuccessMessage }}</p>

          <BaseButton
            type="submit"
            variant="primary"
            :disabled="isUpdatingProfile"
            class="w-full bg-kahoot-orange hover:bg-kahoot-orange-dark"
          >
            {{ isUpdatingProfile ? 'Salvataggio...' : 'Salva Modifiche Profilo' }}
          </BaseButton>
        </form>
      </div>

      <!-- Card per Impostare/Modificare PIN -->
      <div class="profile-card pin-card bg-white rounded-lg shadow-md p-6">
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
      <!-- Nuova Card per Esportazione Dati GDPR -->
      <div class="profile-card gdpr-card bg-white rounded-lg shadow-md p-6 md:col-span-2"> <!-- Occupa tutta la larghezza -->
        <h2 class="text-xl font-semibold text-kahoot-blue mb-4 border-b pb-2">Gestione Dati Personali (GDPR)</h2>
        <p class="text-sm text-brand-gray-dark mb-4">
          In conformità con il Regolamento Generale sulla Protezione dei Dati (GDPR), puoi richiedere un'esportazione dei tuoi dati personali conservati sulla piattaforma.
        </p>
        <BaseButton
          @click="handleExportData"
          variant="secondary"
          :disabled="isLoadingData"
          class="mb-4"
        >
          {{ isLoadingData ? 'Esportazione in corso...' : 'Esporta i miei dati' }}
        </BaseButton>

        <!-- Indicatore di Caricamento -->
        <div v-if="isLoadingData" class="loading-indicator text-center my-4">
          <p class="text-brand-gray italic">Recupero dei dati in corso...</p>
          <!-- Potresti aggiungere uno spinner qui -->
        </div>

        <!-- Messaggio di Errore -->
        <div v-if="exportError" class="error-message bg-kahoot-red-light border-l-4 border-kahoot-red text-kahoot-red-dark p-4 my-4 rounded" role="alert">
          <p class="font-semibold">Errore Esportazione:</p>
          <p>{{ exportError }}</p>
        </div>

        <!-- Visualizzazione Dati Esportati -->
        <div v-if="exportedData" class="exported-data-container mt-4">
          <h3 class="text-lg font-semibold text-brand-gray-dark mb-2">Dati Esportati:</h3>
          <pre class="bg-gray-100 p-4 rounded text-xs overflow-auto max-h-96 border border-gray-300">{{ JSON.stringify(exportedData, null, 2) }}</pre>
          <BaseButton
            @click="downloadData"
            variant="primary"
            class="mt-4"
          >
            Scarica Dati (JSON)
          </BaseButton>
        </div>

        <!-- Sezione Richiesta Cancellazione -->
        <div class="deletion-request-section mt-6 pt-4 border-t border-gray-200">
           <h3 class="text-lg font-semibold text-kahoot-red mb-2">Richiesta Cancellazione Dati (Diritto all'Oblio)</h3>
           <p class="text-sm text-brand-gray-dark mb-4">
             Puoi richiedere la cancellazione definitiva di tutti i tuoi dati personali dalla piattaforma. Questa azione è irreversibile.
           </p>
           <BaseButton
             @click="handleRequestDeletion"
             variant="danger"
             :disabled="isRequestingDeletion"
             class="w-full md:w-auto"
           >
             {{ isRequestingDeletion ? 'Invio richiesta...' : 'Richiedi Cancellazione Dati' }}
           </BaseButton>

           <!-- Messaggi di Errore/Successo per la cancellazione -->
           <p v-if="deletionRequestErrorMessage" class="error-message text-kahoot-red text-sm mt-4 text-center">{{ deletionRequestErrorMessage }}</p>
           <p v-if="deletionRequestSuccessMessage" class="success-message text-kahoot-green-dark text-sm mt-4 text-center">{{ deletionRequestSuccessMessage }}</p>
        </div>

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