<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
      <h2 class="text-2xl font-bold text-center mb-6 text-gray-700">Accesso Docente / Admin</h2>
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="login-identifier" class="block text-sm font-medium text-gray-600 mb-1">Username:</label>
          <input
            id="login-identifier"
            v-model="identifier"
            type="text"
            required
            placeholder="Inserisci username"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div>
          <label for="password" class="block text-sm font-medium text-gray-600 mb-1">Password:</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            placeholder="Inserisci password"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div v-if="authStore.loginError" class="text-red-500 text-sm text-center">
          {{ authStore.loginError }}
        </div>
        <button
          type="submit"
          :disabled="authStore.isLoading"
          class="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition duration-150 ease-in-out"
        >
          {{ authStore.isLoading ? 'Accesso in corso...' : 'Accedi' }}
        </button>
      </form>
      <div class="mt-6 text-center text-sm text-gray-600">
        Sei uno Studente?
        <router-link :to="{ name: 'student-login' }" class="font-medium text-indigo-600 hover:text-indigo-500">Accedi qui</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
// Rimosso import { useRouter, useRoute } da 'vue-router' perché non sono più usati
import { useAuthStore } from '@/stores/auth';

const identifier = ref('');
const password = ref('');
const authStore = useAuthStore();
// Rimosse dichiarazioni const router = useRouter(); e const route = useRoute();

const handleLogin = async () => {
  const credentials = {
      identifier: identifier.value,
      password: password.value,
  };
  // Lasciamo che sia l'azione login nello store a gestire il redirect
  await authStore.login(credentials, 'teacher-admin');
  // Non è necessario controllare 'success' qui, l'azione login gestisce
  // già il redirect in caso di successo o mostra l'errore altrimenti.
};
</script>
