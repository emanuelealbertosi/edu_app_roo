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
           <router-link :to="{ name: 'login' }" class="btn btn-primary">Vai al Login</router-link>
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
          <label for="date-of-birth" class="sr-only">Data di Nascita</label>
          <input
            id="date-of-birth"
            v-model="dateOfBirth"
            name="date-of-birth"
            type="date"
            required
            class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            placeholder="Data di Nascita"
          >
          <p v-if="dateOfBirth && isUnderage !== null && !isUnderage" class="mt-1 text-xs text-green-600">Età verificata (maggiore o uguale a 14 anni).</p>
          <p v-if="dateOfBirth && isUnderage" class="mt-1 text-xs text-orange-600">Età inferiore a 14 anni. È richiesta l'email del genitore/tutore.</p>
        </div>
        <div v-if="isUnderage">
           <label for="parent-email" class="sr-only">Email Genitore/Tutore</label>
           <input
             id="parent-email"
             v-model="parentEmail"
             name="parent-email"
             type="email"
             :required="isUnderage"
             class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
             placeholder="Email Genitore/Tutore (obbligatoria)"
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

        <!-- Checkbox Accettazione Policy -->
        <div class="space-y-2">
           <div class="flex items-start">
             <div class="flex items-center h-5">
               <input
                 id="accept-privacy"
                 v-model="acceptPrivacy"
                 name="accept-privacy"
                 type="checkbox"
                 required
                 class="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
               >
             </div>
             <div class="ml-3 text-sm">
               <label for="accept-privacy" class="font-medium text-gray-700">
                 Ho letto e accetto l'<a href="#privacy" target="_blank" class="text-indigo-600 hover:text-indigo-500 underline">Informativa Privacy</a>*
               </label>
             </div>
           </div>
           <div class="flex items-start">
             <div class="flex items-center h-5">
               <input
                 id="accept-terms"
                 v-model="acceptTerms"
                 name="accept-terms"
                 type="checkbox"
                 required
                 class="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
               >
             </div>
             <div class="ml-3 text-sm">
               <label for="accept-terms" class="font-medium text-gray-700">
                 Ho letto e accetto i <a href="#terms" target="_blank" class="text-indigo-600 hover:text-indigo-500 underline">Termini di Servizio</a>*
               </label>
             </div>
           </div>
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
            :disabled="isLoading || !token || pin !== confirmPin || !acceptPrivacy || !acceptTerms || !dateOfBirth || isUnderage === null || (isUnderage === true && !parentEmail)"
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
        <router-link :to="{ name: 'login' }" class="font-medium text-indigo-600 hover:text-indigo-500">
          Hai già un account? Accedi
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'; // Import computed
import { useRoute, useRouter } from 'vue-router';
// Usa percorso relativo invece dell'alias @ per sicurezza
import { registerStudentWithToken } from '../api/registration';

const route = useRoute();
const router = useRouter();

const token = ref<string | null>(null);
const firstName = ref('');
const lastName = ref('');
const pin = ref('');
const confirmPin = ref('');
const dateOfBirth = ref(''); // Aggiunto ref per data di nascita
const parentEmail = ref(''); // Aggiunto ref per email genitore
const isLoading = ref(false);
const error = ref<string | null>(null);
const registrationSuccess = ref(false);
const registeredStudentName = ref('');
const registeredStudentCode = ref('');
const acceptPrivacy = ref(false); // Stato checkbox Privacy
const acceptTerms = ref(false); // Stato checkbox Termini

// --- Logica Verifica Età ---
const MIN_CONSENT_AGE = 14;

const calculateAge = (dobString: string): number | null => {
  if (!dobString) return null;
  try {
    const dob = new Date(dobString);
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const m = today.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
      age--;
    }
    return age;
  } catch (e) {
    console.error("Error parsing date:", e);
    return null; // Ritorna null se la data non è valida
  }
};

const isUnderage = computed(() => {
  const age = calculateAge(dateOfBirth.value);
  // Ritorna null se l'età non può essere calcolata (data non inserita o non valida)
  if (age === null) return null;
  return age < MIN_CONSENT_AGE;
});
// --- Fine Logica Verifica Età ---


onMounted(() => {
  // Estrai il token dalla query string dell'URL
  const queryToken = route.query.token;
  console.log('Extracted token from query:', queryToken); // Log per debug
  if (typeof queryToken === 'string' && queryToken) {
    token.value = queryToken;
    console.log('Token value set:', token.value); // Log per debug
  } else {
    error.value = 'Token di registrazione mancante o non valido.';
    console.error('Failed to extract token from route query.'); // Log errore
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

  // Verifica accettazione policy
  if (!acceptPrivacy.value || !acceptTerms.value) {
      error.value = 'È necessario accettare l\'Informativa Privacy e i Termini di Servizio per registrarsi.';
      return;
  }
   if (!dateOfBirth.value) {
      error.value = 'La data di nascita è obbligatoria.';
      return;
  }
  if (isUnderage.value === null) {
      error.value = 'Formato data di nascita non valido.';
      return;
  }
  if (isUnderage.value && !parentEmail.value) {
      error.value = 'L\'email del genitore/tutore è obbligatoria per gli utenti minorenni.';
      return;
  }
  // Validazione semplice formato email genitore (se inserita)
  if (parentEmail.value && !/\S+@\S+\.\S+/.test(parentEmail.value)) {
       error.value = 'Formato email genitore non valido.';
       return;
   }


  isLoading.value = true;
  error.value = null;
  registrationSuccess.value = false;
  let response: any = null; // Dichiara response qui per renderla accessibile dopo il try

  try {
    // Costruisci il payload includendo i nuovi campi
    const payload: any = { // Usiamo 'any' temporaneamente, meglio definire un tipo
      token: token.value,
      first_name: firstName.value,
      last_name: lastName.value,
      pin: pin.value,
      date_of_birth: dateOfBirth.value, // Aggiunto campo data nascita
      accept_privacy_policy: acceptPrivacy.value, // Rinominato per coerenza con BE
      accept_terms_of_service: acceptTerms.value, // Rinominato per coerenza con BE
    };
    // Aggiungi parent_email solo se necessario (minorenne)
    if (isUnderage.value) {
      payload.parent_email = parentEmail.value;
    }

    // Chiama l'API e salva la risposta
    response = await registerStudentWithToken(payload)

    // Gestione risposta: Se minorenne, mostra messaggio diverso
    if (isUnderage.value) {
        // Mostra messaggio che indica la necessità di verifica parentale
        error.value = null // Pulisci errori precedenti
        // Non impostare registrationSuccess a true, ma mostra un messaggio informativo
        // Potremmo usare una variabile di stato diversa, es. 'pendingVerification'
        alert(`Registrazione avviata. È stata inviata un'email a ${parentEmail.value} per ottenere il consenso parentale. L'account sarà attivo solo dopo la verifica.`)
        // Reindirizza al login o a una pagina informativa
        router.push({ name: 'login' })
    } else {
        // Registrazione completata per maggiorenne
        registrationSuccess.value = true
        registeredStudentName.value = response.full_name
        registeredStudentCode.value = response.student_code
    }
    // Non fare il login automatico, mostra messaggio e link al login
    // Rimosso blocco duplicato e catch duplicato

  } catch (err: any) { // Blocco catch corretto
    console.error("Errore durante la registrazione:", err)
    if (err.response?.data) {
        const backendErrors = err.response.data;
        if (typeof backendErrors === 'object' && backendErrors !== null) {
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
/* Aggiungi stili specifici se necessario */
.btn {
  /* Stili base per i bottoni se non usi una libreria UI come Tailwind */
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease-in-out;
}
.btn-primary {
  background-color: #4f46e5; /* Indigo-600 */
  color: white;
}
.btn-primary:hover {
  background-color: #4338ca; /* Indigo-700 */
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>