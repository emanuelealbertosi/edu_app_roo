<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-400 via-pink-500 to-red-500 px-4 py-12">
    <div class="max-w-md w-full bg-white rounded-lg shadow-xl p-8 space-y-6">
      <div class="text-center">
        <h2 class="text-3xl font-extrabold text-gray-900">Registrazione Studente</h2>
        <p class="mt-2 text-sm text-gray-600">
          Completa i campi per creare il tuo account.
        </p>
      </div>

      <div v-if="registrationSuccess" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">Registrazione completata!</strong>
        <span class="block sm:inline"> Benvenuto/a, {{ registeredStudentName }}! Il tuo codice studente è: <strong>{{ registeredStudentCode }}</strong>. Ora puoi effettuare il login.</span>
        <div class="mt-4 text-center">
           <router-link :to="{ name: 'Login' }" class="btn btn-primary">Vai al Login</router-link>
        </div>
      </div>

      <form v-else @submit.prevent="handleRegistration" class="space-y-4">
        <input type="hidden" name="remember" value="true">

        <div>
          <label for="first-name" class="sr-only">Nome</label>
          <input
            id="first-name"
            v-model="firstName"
            name="first-name"
            type="text"
            required
            class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            placeholder="Nome"
          >
        </div>
        <div>
          <label for="last-name" class="sr-only">Cognome</label>
          <input
            id="last-name"
            v-model="lastName"
            name="last-name"
            type="text"
            required
            class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            placeholder="Cognome"
          >
        </div>
         <div>
          <label for="pin" class="sr-only">PIN (min. 4 cifre)</label>
          <input
            id="pin"
            v-model="pin"
            name="pin"
            type="password"
            required
            minlength="4"
            pattern="\d{4,}"
            title="Inserisci almeno 4 cifre numeriche"
            class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            placeholder="Crea un PIN (min. 4 cifre)"
          >
        </div>
         <div>
          <label for="confirm-pin" class="sr-only">Conferma PIN</label>
          <input
            id="confirm-pin"
            v-model="confirmPin"
            name="confirm-pin"
            type="password"
            required
            class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            placeholder="Conferma PIN"
          >
        </div>

        <div v-if="error" class="text-red-600 text-sm text-center">
          {{ error }}
        </div>
         <div v-if="!token" class="text-red-600 text-sm text-center font-semibold">
          Token di registrazione mancante o non valido nell'URL.
        </div>

        <div>
          <button
            type="submit"
            :disabled="isLoading || !token || pin !== confirmPin"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="absolute left-0 inset-y-0 flex items-center pl-3">
              <!-- Heroicon name: solid/lock-closed -->
              <svg class="h-5 w-5 text-indigo-500 group-hover:text-indigo-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
              </svg>
            </span>
            <span v-if="isLoading">Registrazione in corso...</span>
            <span v-else>Registrati</span>
          </button>
        </div>
      </form>
       <div class="text-center text-sm">
        <router-link :to="{ name: 'Login' }" class="font-medium text-indigo-600 hover:text-indigo-500">
          Hai già un account? Accedi
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { registerStudentWithToken } from '@/api/registration';

const route = useRoute();
const router = useRouter();

const token = ref<string | null>(null);
const firstName = ref('');
const lastName = ref('');
const pin = ref('');
const confirmPin = ref('');
const isLoading = ref(false);
const error = ref<string | null>(null);
const registrationSuccess = ref(false);
const registeredStudentName = ref('');
const registeredStudentCode = ref('');

onMounted(() => {
  // Estrai il token dalla query string dell'URL
  const queryToken = route.query.token;
  if (typeof queryToken === 'string' && queryToken) {
    token.value = queryToken;
  } else {
    error.value = 'Token di registrazione mancante o non valido.';
    // Potresti reindirizzare o mostrare un errore più evidente
  }
});

const handleRegistration = async () => {
  if (!token.value) {
    error.value = 'Token di registrazione non valido.';
    return;
  }
  if (pin.value !== confirmPin.value) {
    error.value = 'I PIN inseriti non coincidono.';
    return;
  }
  if (pin.value.length < 4 || !/^\d+$/.test(pin.value)) {
      error.value = 'Il PIN deve contenere almeno 4 cifre numeriche.';
      return;
  }


  isLoading.value = true;
  error.value = null;
  registrationSuccess.value = false;

  try {
    const payload = {
      token: token.value,
      first_name: firstName.value,
      last_name: lastName.value,
      pin: pin.value,
    };
    const response = await registerStudentWithToken(payload);
    registrationSuccess.value = true;
    registeredStudentName.value = response.full_name;
    registeredStudentCode.value = response.student_code;
    // Non fare il login automatico, mostra messaggio e link al login
    // Potresti reindirizzare al login dopo un timeout
    // setTimeout(() => router.push({ name: 'Login' }), 5000);

  } catch (err: any) {
    console.error("Errore durante la registrazione:", err);
    if (err.response?.data) {
        // Prova a estrarre messaggi di errore specifici dal backend
        const backendErrors = err.response.data;
        if (typeof backendErrors === 'object' && backendErrors !== null) {
            // Concatena i messaggi di errore dai campi (es. token, pin)
            error.value = Object.entries(backendErrors)
                .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
                .join('; ');
        } else {
             error.value = backendErrors.detail || 'Errore durante la registrazione.';
        }
    } else {
        error.value = err.message || 'Si è verificato un errore sconosciuto durante la registrazione.';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Aggiungi stili specifici se necessario, ma Tailwind dovrebbe coprire la maggior parte */
</style>