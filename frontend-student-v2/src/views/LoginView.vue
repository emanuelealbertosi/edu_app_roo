<template>
  <div class="flex justify-center items-center mt-10">
    <div class="card w-96 bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title justify-center">Login Studente v2</h2>
        <form @submit.prevent="handleLogin">
          <!-- Username -->
          <div class="form-control w-full max-w-xs">
            <label class="label">
              <span class="label-text">Username</span>
            </label>
            <input
              v-model="username"
              type="text"
              placeholder="Il tuo username"
              class="input input-bordered w-full max-w-xs"
              required
            />
          </div>
          <!-- Password -->
          <div class="form-control w-full max-w-xs mt-4">
            <label class="label">
              <span class="label-text">Password</span>
            </label>
            <input
              v-model="password"
              type="password"
              placeholder="La tua password"
              class="input input-bordered w-full max-w-xs"
              required
            />
            <!-- Potremmo aggiungere un link "Password dimenticata?" qui -->
          </div>
          <!-- Submit Button -->
          <div class="form-control mt-6">
            <button type="submit" class="btn btn-primary" :disabled="isLoading">
              <span v-if="isLoading" class="loading loading-spinner loading-sm"></span>
              {{ isLoading ? 'Accesso...' : 'Accedi' }}
            </button>
          </div>
        </form>
        <!-- Eventuale messaggio di errore -->
        <p v-if="authStore.loginError" class="text-error mt-4 text-center">{{ authStore.loginError }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '../stores/auth'; // Importa lo store
import { useRouter } from 'vue-router'; // Importa il router

const username = ref('');
const password = ref('');
const isLoading = ref(false); // Aggiungi stato di caricamento
const authStore = useAuthStore(); // Usa lo store
const router = useRouter(); // Usa il router

const handleLogin = async () => {
  isLoading.value = true; // Inizia caricamento
  // Non serve resettare l'errore qui, lo fa lo store
  console.log('Attempting login with:', username.value, password.value);

  const success = await authStore.login(username.value, password.value);

  isLoading.value = false; // Fine caricamento

  if (success) {
    console.log('Login successful, redirecting to home...');
    router.push('/'); // Reindirizza alla home dopo login riuscito
  } else {
    console.log('Login failed, error message should be displayed.');
    // L'errore viene gestito e mostrato tramite authStore.loginError
  }
};
</script>

<style scoped>
/* Stili specifici per la vista di login se necessari */
</style>