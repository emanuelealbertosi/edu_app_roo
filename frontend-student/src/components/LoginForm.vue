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
  } catch (error) {
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
  <form @submit.prevent="handleSubmit" class="login-form">
    <h2>Accedi</h2>
    
    <!-- Messaggio di errore -->
    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
    
    <div class="form-group">
      <label for="studentCode">Codice Studente:</label> <!-- Etichetta cambiata -->
      <input
        type="text"
        id="studentCode"
        v-model="studentCode"
        required
        :disabled="isLoading"
        autocomplete="username"
      />
    </div>
    
    <div class="form-group">
      <label for="pin">PIN:</label> <!-- Etichetta cambiata -->
      <input
        type="password"
        id="pin"
        v-model="pin"
        required
        :disabled="isLoading"
        autocomplete="current-password"
      />
    </div>
    
    <button
      type="submit"
      :disabled="isLoading"
      :class="{ 'loading': isLoading }"
    >
      {{ isLoading ? 'Accesso in corso...' : 'Accedi' }}
    </button>
  </form>
</template>

<style scoped>
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 2rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #f9f9f9;
  max-width: 400px;
  margin: auto;
}

.form-group {
  display: flex;
  flex-direction: column;
}

label {
  margin-bottom: 0.5rem;
  font-weight: bold;
}

input {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  padding: 0.75rem;
  background-color: var(--vt-c-indigo); /* Usa un colore dal tema di default di Vue */
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

button:hover {
  opacity: 0.9;
}
</style>

<style scoped>
.error-message {
  background-color: #ffebee;
  color: #b71c1c;
  padding: 0.75rem;
  border-radius: 4px;
  border-left: 4px solid #f44336;
  margin-bottom: 1rem;
}

button.loading {
  background-color: #9fa8da;
  cursor: not-allowed;
}
</style>