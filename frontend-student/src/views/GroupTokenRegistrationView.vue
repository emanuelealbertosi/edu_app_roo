<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-100">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
      <h2 class="text-2xl font-bold text-center text-gray-900">Registrazione al Gruppo</h2>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label for="token" class="block text-sm font-medium text-gray-700">Token di Registrazione</label>
          <input
            id="token"
            v-model="groupToken"
            type="text"
            required
            readonly
            disabled
            class="block w-full px-3 py-2 mt-1 text-gray-500 bg-gray-200 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
          <p v-if="!groupToken" class="text-xs text-red-600 mt-1">Token mancante o non valido nell'URL.</p>
        </div>
        <div>
          <label for="firstName" class="block text-sm font-medium text-gray-700">Nome</label>
          <input
            id="firstName"
            v-model="firstName"
            type="text"
            required
            autocomplete="given-name"
            class="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div>
          <label for="lastName" class="block text-sm font-medium text-gray-700">Cognome</label>
          <input
            id="lastName"
            v-model="lastName"
            type="text"
            required
            autocomplete="family-name"
            class="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div>
          <label for="pin" class="block text-sm font-medium text-gray-700">PIN (numerico)</label>
          <input
            id="pin"
            v-model="pin"
            type="password"
            inputmode="numeric"
            pattern="\d*"
            required
            autocomplete="new-password"
            class="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
           <p class="text-xs text-gray-500 mt-1">Inserisci il PIN numerico che userai per accedere.</p>
        </div>

        <div v-if="errorMessage" class="p-3 text-sm text-red-700 bg-red-100 rounded-md">
          {{ errorMessage }}
        </div>

        <div>
          <button
            type="submit"
            :disabled="isLoading || !groupToken"
            class="flex justify-center w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading">Registrazione in corso...</span>
            <span v-else>Registrati e Accedi</span>
          </button>
        </div>
         <div class="text-center text-sm">
            <router-link :to="{ name: 'Login' }" class="font-medium text-indigo-600 hover:text-indigo-500">
              Hai già un account? Accedi
            </router-link>
          </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { registerStudentWithGroupToken } from '@/api/registration';
import { useAuthStore } from '@/stores/auth'; // Assumiamo esista uno store auth
import { AxiosError } from 'axios';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore(); // Istanza dello store di autenticazione

const groupToken = ref<string>('');
const firstName = ref('');
const lastName = ref('');
const pin = ref('');
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);

onMounted(() => {
  // Prendi il token dalla route (assumendo che sia un parametro chiamato 'token')
  if (typeof route.params.token === 'string') {
    groupToken.value = route.params.token;
  } else {
      errorMessage.value = "Token di registrazione mancante o non valido nell'URL.";
      console.error("Token non trovato o non è una stringa:", route.params.token);
  }
});

const handleSubmit = async () => {
  if (!groupToken.value) {
      errorMessage.value = "Impossibile procedere senza un token valido.";
      return;
  }
  // Validazione base PIN numerico (aggiungere controlli più robusti se necessario)
  if (!/^\d+$/.test(pin.value)) {
      errorMessage.value = "Il PIN deve contenere solo cifre numeriche.";
      return;
  }


  isLoading.value = true;
  errorMessage.value = null;

  try {
    const payload = {
      group_token: groupToken.value,
      first_name: firstName.value,
      last_name: lastName.value,
      pin: pin.value,
    };

    const response = await registerStudentWithGroupToken(payload);

    // Registrazione avvenuta con successo, ora effettua il login automatico
    // Imposta manualmente lo stato di autenticazione nello store e salva in localStorage
    authStore.user = response.student; // Imposta i dati utente nello store
    authStore.token = response.access; // Imposta il token nello store
    // Nello store setup, isAuthenticated è un computed basato su token/user,
    // quindi impostare user e token dovrebbe essere sufficiente.
    // Non impostiamo direttamente isAuthenticated.value qui.

    // Salva manualmente in localStorage (similmente a quanto farebbe login)
    localStorage.setItem('auth_token', response.access);
    localStorage.setItem('user', JSON.stringify(response.student));
    // Nota: Il refresh token non viene usato attivamente in questo store, ma potresti salvarlo se necessario
    // localStorage.setItem('refresh_token', response.refresh);

    // Reindirizza alla dashboard o alla pagina principale post-login
    router.push({ name: 'Dashboard' }); // Assicurati che 'Dashboard' sia il nome corretto della route

  } catch (error) {
    console.error('Errore durante la registrazione con token di gruppo:', error);
    if (error instanceof AxiosError && error.response) {
        // Prova a estrarre un messaggio di errore specifico dal backend
        const backendError = error.response.data;
        if (typeof backendError === 'string') {
            errorMessage.value = backendError;
        } else if (backendError && typeof backendError.detail === 'string') {
             errorMessage.value = backendError.detail;
        } else if (backendError && typeof backendError.error === 'string') {
             errorMessage.value = backendError.error;
        }
         else {
            // Messaggio generico se non si trova un dettaglio specifico
            errorMessage.value = `Errore ${error.response.status}: Impossibile completare la registrazione. Controlla i dati inseriti o il token.`;
        }
    } else if (error instanceof Error) {
         errorMessage.value = error.message;
    }
    else {
      errorMessage.value = 'Si è verificato un errore sconosciuto durante la registrazione.';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Eventuali stili specifici */
</style>