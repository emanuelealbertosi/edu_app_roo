<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
// TODO: Importare la funzione API per aggiornare la password quando sarà disponibile
// import { updateUserPassword } from '@/api/user'; 

const authStore = useAuthStore();

// State per il form cambio password
const currentPassword = ref('');
const newPassword = ref('');
const confirmNewPassword = ref('');
const passwordSuccessMessage = ref<string | null>(null);
const passwordErrorMessage = ref<string | null>(null);
const isChangingPassword = ref(false);

// Computed per info utente (opzionale, ma utile)
const teacherUsername = computed(() => authStore.user?.username ?? 'N/D');

// Funzione per gestire il cambio password
const handleChangePassword = async () => {
  passwordSuccessMessage.value = null;
  passwordErrorMessage.value = null;
  isChangingPassword.value = true;

  // Validazione base
  if (!currentPassword.value || !newPassword.value || !confirmNewPassword.value) {
      passwordErrorMessage.value = 'Tutti i campi sono obbligatori.';
      isChangingPassword.value = false;
      return;
  }
  if (newPassword.value.length < 8) { // Esempio: lunghezza minima password
    passwordErrorMessage.value = 'La nuova password deve contenere almeno 8 caratteri.';
    isChangingPassword.value = false;
    return;
  }
  if (newPassword.value !== confirmNewPassword.value) {
    passwordErrorMessage.value = 'La nuova password e la conferma non coincidono.';
    isChangingPassword.value = false;
    return;
  }

  try {
    // --- Chiamata API (da implementare) ---
    console.log('Tentativo di aggiornare la password...');
    // await authStore.updateTeacherPassword(currentPassword.value, newPassword.value); // Esempio store
    // await updateUserPassword(currentPassword.value, newPassword.value); // Esempio API diretta

    // Simula successo per ora
    await new Promise(resolve => setTimeout(resolve, 500)); 
    passwordSuccessMessage.value = 'Password aggiornata con successo!';
    currentPassword.value = ''; // Resetta i campi
    newPassword.value = '';
    confirmNewPassword.value = '';
    // --------------------------------------

  } catch (error: any) {
    console.error("Errore durante l'aggiornamento della password:", error);
    // Qui potresti voler controllare specifici codici di errore API (es. password attuale errata)
    passwordErrorMessage.value = error.message || "Si è verificato un errore durante l'aggiornamento della password.";
  } finally {
    isChangingPassword.value = false;
  }
};

</script>

<template>
  <div class="profile-view container mx-auto px-4 py-8">
    <header class="profile-header bg-white p-4 md:p-6 rounded-lg shadow-md mb-8">
      <h1 class="text-2xl md:text-3xl font-bold text-gray-800">Profilo Docente</h1>
      <p class="text-gray-600">Gestisci le impostazioni del tuo account.</p>
    </header>

    <div class="profile-content grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <!-- Card Info Utente (Opzionale) -->
      <div class="profile-card info-card bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-blue-700 mb-4 border-b pb-2">Informazioni Account</h2>
        <div class="info-item flex justify-between items-center py-2">
          <span class="info-label font-medium text-gray-600">Username:</span>
          <span class="info-value text-gray-800 font-mono">{{ teacherUsername }}</span>
        </div>
        
      </div>

      <!-- Card Cambio Password -->
      <div class="profile-card password-card bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-purple-700 mb-4 border-b pb-2">Cambia Password</h2>
        <form @submit.prevent="handleChangePassword">
          <div class="mb-4">
            <label for="currentPassword" class="block text-gray-700 text-sm font-bold mb-2">Password Attuale:</label>
            <input 
              type="password" 
              id="currentPassword" 
              v-model="currentPassword" 
              required 
              autocomplete="current-password"
              class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
            />
          </div>
          <div class="mb-4">
            <label for="newPassword" class="block text-gray-700 text-sm font-bold mb-2">Nuova Password (min. 8 caratteri):</label>
            <input 
              type="password" 
              id="newPassword" 
              v-model="newPassword" 
              required 
              minlength="8"
              autocomplete="new-password"
              class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
            />
          </div>
          <div class="mb-6">
            <label for="confirmNewPassword" class="block text-gray-700 text-sm font-bold mb-2">Conferma Nuova Password:</label>
            <input 
              type="password" 
              id="confirmNewPassword" 
              v-model="confirmNewPassword" 
              required 
              minlength="8"
              autocomplete="new-password"
              class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
            />
          </div>

          <!-- Messaggi di Errore/Successo -->
          <p v-if="passwordErrorMessage" class="error-message text-red-500 text-sm mb-4 text-center">{{ passwordErrorMessage }}</p>
          <p v-if="passwordSuccessMessage" class="success-message text-green-600 text-sm mb-4 text-center">{{ passwordSuccessMessage }}</p>

          <button 
            type="submit" 
            :disabled="isChangingPassword" 
            class="w-full btn btn-primary bg-purple-600 hover:bg-purple-700 text-white" 
            :class="{ 'opacity-50 cursor-not-allowed': isChangingPassword }"
          >
            {{ isChangingPassword ? 'Salvataggio...' : 'Cambia Password' }}
          </button>
        </form>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* Stili specifici se necessari */
</style>