<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
      <h2 class="text-2xl font-bold text-center mb-6 text-gray-700">Accesso Studente</h2>
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="student-code" class="block text-sm font-medium text-gray-600 mb-1">Codice Studente:</label>
          <input
            id="student-code"
            v-model="studentCode"
            type="text"
            required
            placeholder="Inserisci il tuo codice"
            inputmode="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-cyan-500 focus:border-cyan-500"
          />
        </div>
        <div>
          <label for="pin" class="block text-sm font-medium text-gray-600 mb-1">PIN:</label>
          <input
            id="pin"
            v-model="pin"
            type="password"
            required
            placeholder="Inserisci il tuo PIN"
            inputmode="numeric"
            pattern="\d*"
            maxlength="8"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-cyan-500 focus:border-cyan-500"
          />
        </div>
        <div v-if="authStore.loginError" class="text-red-500 text-sm text-center">
          {{ authStore.loginError }}
        </div>
        <button
          type="submit"
          :disabled="authStore.isLoading"
          class="w-full py-2 px-4 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition duration-150 ease-in-out"
        >
          {{ authStore.isLoading ? 'Accesso in corso...' : 'Accedi' }}
        </button>
      </form>
      <div class="mt-6 text-center text-sm text-gray-600">
        Sei un Docente o Admin?
        <router-link :to="{ name: 'teacher-admin-login' }" class="font-medium text-cyan-600 hover:text-cyan-500">Accedi qui</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const studentCode = ref('');
const pin = ref('');
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const handleLogin = async () => {
  const credentials = {
      identifier: studentCode.value,
      pin: pin.value,
  };
  const success = await authStore.login(credentials, 'student');
  if (success) {
    const redirectPath = route.query.redirect as string || '/';
    router.push(redirectPath);
  }
};
</script>
