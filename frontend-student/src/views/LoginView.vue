<script setup lang="ts">
import LoginForm from '@/components/LoginForm.vue';
</script>

<template>
  <div class="login-view min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-kahoot-purple to-kahoot-blue p-4"> <!-- Gradiente aggiornato -->
    <h1 class="text-4xl font-bold text-white mb-8 text-center drop-shadow-lg">Accesso Studente</h1> <!-- Usato drop-shadow invece di shadow -->
    <LoginForm />
    <div class="mt-6 text-center"> <!-- Aumentato margine -->
      <a href="/docenti/login" class="text-sm text-kahoot-blue-light hover:text-white hover:underline transition-colors duration-200"> <!-- Colori link aggiornati -->
        Sei un docente? Accedi qui
      </a>
    </div>
  </div>
</template>

<style scoped>
/* Eventuali stili specifici aggiuntivi se necessari */
</style>