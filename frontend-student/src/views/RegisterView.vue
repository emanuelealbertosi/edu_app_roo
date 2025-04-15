<template>
  <div class="register-view container mx-auto p-4 md:p-8 max-w-md">
    <h1 class="text-2xl font-bold text-center mb-6">Registrazione Studente</h1>

    <div v-if="isLoading" class="text-center text-gray-600">
      Verifica invito in corso...
    </div>

    <div v-else-if="validationError" class="error-message text-center">
      <p>Errore nella validazione dell'invito:</p>
      <p class="font-mono text-sm">{{ validationError }}</p>
      <p class="mt-4">Richiedi un nuovo link di invito al tuo docente.</p>
      <router-link to="/login" class="btn btn-secondary mt-4">Torna al Login</router-link>
    </div>

    <div v-else-if="tokenInfo" class="registration-form">
      <p class="text-center mb-4 text-gray-700">
        Stai per registrarti sotto la guida di
        <strong class="font-semibold">{{ tokenInfo.teacher_name }}</strong>.
        <span v-if="tokenInfo.group_name"> Sarai aggiunto/a al gruppo <strong class="font-semibold">{{ tokenInfo.group_name }}</strong>.</span>
      </p>

      <form @submit.prevent="handleRegister">
        <div class="form-group mb-4">
          <label for="first-name" class="block text-sm font-medium text-gray-700 mb-1">Nome:</label>
          <input type="text" id="first-name" v-model="firstName" class="w-full p-2 border rounded shadow-sm focus:ring-indigo-500 focus:border-indigo-500" required>
        </div>
        <div class="form-group mb-4">
          <label for="last-name" class="block text-sm font-medium text-gray-700 mb-1">Cognome:</label>
          <input type="text" id="last-name" v-model="lastName" class="w-full p-2 border rounded shadow-sm focus:ring-indigo-500 focus:border-indigo-500" required>
        </div>
        <div class="form-group mb-6">
          <label for="pin" class="block text-sm font-medium text-gray-700 mb-1">Crea PIN (min. 4 cifre):</label>
          <input type="password" id="pin" v-model="pin" inputmode="numeric" pattern="[0-9]*" class="w-full p-2 border rounded shadow-sm focus:ring-indigo-500 focus:border-indigo-500" required minlength="4">
           <p v-if="pin && pin.length < 4" class="text-red-500 text-xs mt-1">Il PIN deve avere almeno 4 cifre.</p>
        </div>

        <div v-if="registrationError" class="error-message mb-4">
          Errore durante la registrazione: {{ registrationError }}
        </div>

        <button type="submit" :disabled="isRegistering || !isFormValid" class="btn btn-primary w-full" >
          {{ isRegistering ? 'Registrazione in corso...' : 'Registrati' }}
        </button>
      </form>
       <div class="text-center mt-4">
         <router-link to="/login" class="text-sm text-indigo-600 hover:underline">Hai già un account? Accedi</router-link>
       </div>
    </div>

     <div v-if="registrationSuccess" class="success-message text-center p-4 bg-green-100 border border-green-300 rounded">
        <h2 class="text-xl font-semibold text-green-800 mb-2">Registrazione Completata!</h2>
        <p>Conserva queste credenziali in un posto sicuro!</p>
        <p class="mt-2"><strong>Codice Studente (Username):</strong> <code class="font-mono bg-green-200 px-1 rounded">{{ registeredStudentCode }}</code></p>
        <p class="mt-1"><strong>PIN:</strong> (Quello che hai appena inserito)</p>
        <p class="text-sm text-gray-600 mt-2">Ora puoi accedere con queste credenziali.</p>
        <router-link to="/login" class="btn btn-primary mt-4">Vai al Login</router-link>
     </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AuthService from '@/api/auth'; // Importa il servizio di autenticazione

interface TokenInfo {
  teacher_name: string;
  group_name: string | null;
}

const route = useRoute();
const router = useRouter();

const token = ref<string | null>(null);
const tokenInfo = ref<TokenInfo | null>(null);
const isLoading = ref(true);
const validationError = ref<string | null>(null);

const firstName = ref('');
const lastName = ref('');
const pin = ref('');
const isRegistering = ref(false);
const registrationError = ref<string | null>(null);
const registrationSuccess = ref(false);
const registeredStudentCode = ref<string | null>(null);

const isFormValid = computed(() => {
    return firstName.value && lastName.value && pin.value && pin.value.length >= 4;
});

onMounted(async () => {
  const routeToken = route.params.token;
  if (typeof routeToken !== 'string') {
    validationError.value = "Token di registrazione mancante o non valido nell'URL.";
    isLoading.value = false;
    return;
  }
  token.value = routeToken;

  // Valida il token
  try {
    tokenInfo.value = await AuthService.validateRegistrationToken(token.value);
  } catch (error: any) {
    console.error("Errore validazione token:", error);
    validationError.value = error.response?.data?.detail || error.message || "Token non valido o scaduto.";
  } finally {
    isLoading.value = false;
  }
});

const handleRegister = async () => {
  if (!isFormValid.value || !token.value) return;

  isRegistering.value = true;
  registrationError.value = null;
  registrationSuccess.value = false;

  try {
    const payload = {
      token: token.value,
      first_name: firstName.value,
      last_name: lastName.value,
      pin: pin.value
    };
    const registeredStudent = await AuthService.completeRegistration(payload);
    registeredStudentCode.value = registeredStudent.student_code; // Salva il codice per mostrarlo
    registrationSuccess.value = true; // Mostra messaggio di successo
    // Non reindirizzare subito, mostra il codice studente
    // router.push('/login');
  } catch (error: any) {
    console.error("Errore registrazione:", error);
    registrationError.value = error.response?.data?.detail || error.response?.data?.pin?.[0] || error.response?.data?.token?.[0] || error.message || "Errore sconosciuto durante la registrazione.";
  } finally {
    isRegistering.value = false;
  }
};
</script>

<style scoped>
.register-view {
  /* Stili specifici se necessario */
}
.error-message {
  color: #dc2626; /* red-600 */
  background-color: #fee2e2; /* red-100 */
  border: 1px solid #fca5a5; /* red-300 */
  padding: 0.75rem; /* p-3 */
  border-radius: 0.375rem; /* rounded-md */
  margin-bottom: 1rem; /* mb-4 */
}
.success-message {
   color: #065f46; /* green-800 */
}
</style>