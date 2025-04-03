<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const studentCode = ref(''); // Cambiato da email
const pin = ref(''); // Cambiato da password
const errorMessage = ref('');
const isLoading = ref(false);

const authStore = useAuthStore();
const router = useRouter();

const handleSubmit = async () => {
  if (isLoading.value) return;
  
  errorMessage.value = '';
  isLoading.value = true;
  
  try {
    await authStore.login(studentCode.value, pin.value); // Usa i nuovi ref
    // Reindirizzo alla dashboard o homepage dopo il login
    router.push('/dashboard');
  } catch (error: any) { // Aggiunto : any per tipizzare l'errore
    console.error('Login failed:', error);
    // Gestione degli errori specifici
    if (error.response) {
      switch (error.response.status) {
        case 400:
          errorMessage.value = 'Credenziali non valide. Ricontrolla codice studente e PIN.'; // Messaggio aggiornato
          break;
        case 401:
          errorMessage.value = 'Autenticazione fallita. Verifica le tue credenziali.';
          break;
        case 429:
          errorMessage.value = 'Troppi tentativi. Riprova più tardi.';
          break;
        default:
          errorMessage.value = 'Si è verificato un errore durante il login.';
      }
    } else if (error.message) {
      errorMessage.value = `Errore: ${error.message}`;
    }
    else {
      errorMessage.value = 'Impossibile connettersi al server. Verifica la tua connessione.';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <form @submit.prevent="handleSubmit" class="login-form bg-white bg-opacity-90 p-8 rounded-lg shadow-xl w-full max-w-sm">
    <h2 class="text-2xl font-bold text-center text-gray-800 mb-6">Accedi</h2>

    <!-- Messaggio di errore -->
    <div v-if="errorMessage" class="error-message bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4 rounded" role="alert">
      <p>{{ errorMessage }}</p>
    </div>
    
    <div class="form-group mb-4">
      <label for="studentCode" class="block text-gray-700 text-sm font-bold mb-2">Codice Studente:</label>
      <input
        type="text"
        id="studentCode"
        v-model="studentCode"
        required
        :disabled="isLoading"
        autocomplete="username"
        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-200"
      />
    </div>
    
    <div class="form-group mb-6">
      <label for="pin" class="block text-gray-700 text-sm font-bold mb-2">PIN:</label>
      <input
        type="password"
        id="pin"
        v-model="pin"
        required
        :disabled="isLoading"
        autocomplete="current-password"
        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-200"
      />
    </div>
    
    <button
      type="submit"
      :disabled="isLoading"
      class="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition-colors duration-200"
      :class="{ 'opacity-50 cursor-not-allowed': isLoading }"
    >
      {{ isLoading ? 'Accesso in corso...' : 'Accedi' }}
    </button>
  </form>
</template>

<style scoped>
/* Rimuoviamo tutti gli stili precedenti */
</style>