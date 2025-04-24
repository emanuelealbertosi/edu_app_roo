<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth' // Import the auth store for student
import { useRouter } from 'vue-router' // Import router for redirection

const authStore = useAuthStore()
const router = useRouter()

const studentCode = ref('') // Changed from username
const pin = ref('')         // Changed from password
const errorMessage = ref<string | null>(null)
const isLoading = ref(false); // Added loading state

const handleLogin = async () => {
  if (isLoading.value) return;

  errorMessage.value = null
  isLoading.value = true;

  try {
    await authStore.login(studentCode.value, pin.value); // Use student credentials
    // Redirect to dashboard after successful login
    await router.push({ name: 'dashboard' }); // Use named route if available, or '/dashboard'
  } catch (error: any) {
     console.error("Login component error:", error);
     // Detailed error handling from LoginForm.vue
     if (error.response) {
       switch (error.response.status) {
         case 400:
           errorMessage.value = 'Credenziali non valide. Ricontrolla codice studente e PIN.';
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
     } else {
       errorMessage.value = 'Impossibile connettersi al server. Verifica la tua connessione.';
     }
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="login-view min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-primary to-primary-dark p-4"> <!-- Purple gradient -->
    <h1 class="text-4xl font-bold text-white mb-8 text-center drop-shadow-lg">Accesso Studente</h1> <!-- Title updated -->
    <form @submit.prevent="handleLogin" class="bg-white bg-opacity-90 p-8 rounded-lg shadow-xl w-full max-w-sm">
       <h2 class="text-2xl font-bold text-center text-neutral-darkest mb-6">Login</h2> <!-- Darker text -->

       <!-- Error Message -->
       <div v-if="errorMessage" class="error-message bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4 rounded" role="alert">
         <p>{{ errorMessage }}</p>
       </div>

      <div class="form-group mb-4">
        <label for="studentCode" class="block text-neutral-darker text-sm font-bold mb-2">Codice Studente:</label> <!-- Label updated -->
        <input
          type="text"
          id="studentCode"
          v-model="studentCode"
          required
          :disabled="isLoading"
          autocomplete="username"
          class="shadow appearance-none border rounded w-full py-2 px-3 text-neutral-darker leading-tight focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-neutral-light" /> <!-- Focus color updated -->
      </div>
      <div class="form-group mb-6">
        <label for="pin" class="block text-neutral-darker text-sm font-bold mb-2">PIN:</label> <!-- Label updated -->
        <input
          type="password"
          id="pin"
          v-model="pin"
          required
          :disabled="isLoading"
          autocomplete="current-password"
          class="shadow appearance-none border rounded w-full py-2 px-3 text-neutral-darker leading-tight focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-neutral-light" /> <!-- Focus color updated -->
      </div>
      <button
        type="submit"
        :disabled="isLoading"
        class="w-full btn btn-primary py-2" > <!-- Button styled with primary color -->
        {{ isLoading ? 'Accesso in corso...' : 'Accedi' }} <!-- Button text updated -->
      </button>
    </form>
    <div class="mt-6 text-center"> <!-- Increased margin -->
      <a href="/docenti/login" class="text-sm text-primary-light hover:text-white hover:underline transition-colors duration-200"> <!-- Link color updated -->
        Sei un docente? Accedi qui
      </a>
    </div>
  </div>
</template>

<style scoped>
/* Specific styles if needed, but Tailwind classes should cover most */
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>