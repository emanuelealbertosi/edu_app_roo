<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth' // Import the auth store
import { useRouter } from 'vue-router' // Import router for potential redirection (already handled in store)

const authStore = useAuthStore()
const router = useRouter() // Get router instance if needed elsewhere

const username = ref('')
const password = ref('')
const errorMessage = ref<string | null>(null)

const handleLogin = async () => {
  errorMessage.value = null
  try {
    await authStore.login(username.value, password.value);
    // Redirect manually after successful login
    await new Promise(resolve => setTimeout(resolve, 100)); // Piccolo ritardo per sicurezza
    console.log('[LoginView] Login successful. isAuthenticated:', authStore.isAuthenticated); // Log stato auth
    await router.push({ name: 'dashboard' }); // Aggiunto redirect qui
  } catch (error: any) {
     console.error("Login component error:", error);
     errorMessage.value = error.message || 'Login failed. Please check credentials.';
  }
}
</script>

<template>
  <div class="login-view min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-purple-600 to-indigo-700 p-4">
    <h1 class="text-4xl font-bold text-white mb-8 text-center shadow-lg">Accesso Docente</h1>
    <form @submit.prevent="handleLogin" class="bg-white bg-opacity-90 p-8 rounded-lg shadow-xl w-full max-w-sm">
       <h2 class="text-2xl font-bold text-center text-gray-800 mb-6">Login</h2>
      <div class="form-group mb-4">
        <label for="username" class="block text-gray-700 text-sm font-bold mb-2">Username:</label>
        <input type="text" id="username" v-model="username" required class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-200" />
      </div>
      <div class="form-group mb-6">
        <label for="password" class="block text-gray-700 text-sm font-bold mb-2">Password:</label>
        <input type="password" id="password" v-model="password" required class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-200" />
      </div>
      <button type="submit" :disabled="authStore.loading" class="w-full btn btn-primary" :class="{ 'opacity-50 cursor-not-allowed': authStore.loading }">
        {{ authStore.loading ? 'Accesso in corso...' : 'Login' }}
      </button>
      <p v-if="errorMessage" class="error-message text-red-500 text-sm mt-4 text-center">{{ errorMessage }}</p>
    </form>
  </div>
</template>

<style scoped>
/* Rimuoviamo gli stili precedenti */
</style>