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
  <div class="login-view">
    <h2>Teacher Login</h2>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="username">Username:</label>
        <input type="text" id="username" v-model="username" required />
      </div>
      <div class="form-group">
        <label for="password">Password:</label>
        <input type="password" id="password" v-model="password" required />
      </div>
      <button type="submit" :disabled="authStore.loading">
        {{ authStore.loading ? 'Logging in...' : 'Login' }}
      </button>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    </form>
  </div>
</template>

<style scoped>
.login-view {
  max-width: 400px;
  margin: 50px auto;
  padding: 2rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
}
.form-group {
  margin-bottom: 1rem;
}
label {
  display: block;
  margin-bottom: 0.5rem;
}
input {
  width: 100%;
  padding: 0.5rem;
  box-sizing: border-box;
}
button {
  padding: 0.75rem 1.5rem;
  cursor: pointer;
}
.error-message {
  color: red;
  margin-top: 1rem;
}
</style>