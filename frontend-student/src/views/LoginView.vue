<script setup lang="ts">
import LoginForm from '@/components/LoginForm.vue';
</script>

<template>
  <div class="login-view min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-purple-600 to-indigo-700 p-4">
    <h1 class="text-4xl font-bold text-white mb-8 text-center shadow-lg">Accesso Studente</h1>
    <LoginForm />
    <div class="mt-4 text-center">
      <a href="/docenti/login" class="text-sm text-indigo-200 hover:text-white transition-colors duration-200">
        Sei un docente? Accedi qui
      </a>
    </div>
  </div>
</template>

<style scoped>
/* Eventuali stili specifici aggiuntivi se necessari */
</style>