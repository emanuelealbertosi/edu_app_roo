<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-100">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
      <h2 class="text-2xl font-bold text-center text-gray-900">Registrazione al Gruppo</h2>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label for="token" class="block text-sm font-medium text-gray-700">Token di Registrazione</label>
          <input
            id="token"
            v-model="groupToken"
            type="text"
            required
            readonly
            disabled
            class="block w-full px-3 py-2 mt-1 text-gray-500 bg-gray-200 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
          <p v-if="!groupToken" class="text-xs text-red-600 mt-1">Token mancante o non valido nell'URL.</p>
        </div>
        <div>
          <label for="firstName" class="block text-sm font-medium text-gray-700">Nome</label>
          <input
            id="firstName"
            v-model="firstName"
            type="text"
            required
            autocomplete="given-name"
            class="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div>
          <label for="lastName" class="block text-sm font-medium text-gray-700">Cognome</label>
          <input
            id="lastName"
            v-model="lastName"
            type="text"
            required
            autocomplete="family-name"
            class="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div>
          <label for="pin" class="block text-sm font-medium text-gray-700">PIN (numerico)</label>
          <input
            id="pin"
            v-model="pin"
            type="password"
            inputmode="numeric"
            pattern="\d*"
            required
            autocomplete="new-password"
            class="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
           <p class="text-xs text-gray-500 mt-1">Inserisci il PIN numerico che userai per accedere.</p>
        </div>

        <!-- Inizio Campi GDPR Età -->
        <div>
          <label for="birthDate" class="block text-sm font-medium text-gray-700">Data di Nascita</label>
          <input
            id="birthDate"
            v-model="birthDate"
            type="date"
            required
            autocomplete="bday"
            class="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
          <p v-if="age === -1" class="text-xs text-red-600 mt-1">La data di nascita non può essere nel futuro.</p>
          <p v-else-if="age !== null && age < 0 && age !== -1" class="text-xs text-red-600 mt-1">Data di nascita non valida.</p>
        </div>

        <div v-if="requiresParentalConsent">
           <p class="text-sm text-yellow-700 bg-yellow-100 p-3 rounded-md mb-4">
              Poiché hai meno di {{ MIN_CONSENT_AGE }} anni, è necessario il consenso di un genitore o tutore.
              Inserisci l'indirizzo email del genitore a cui invieremo una richiesta di verifica. L'account sarà utilizzabile solo dopo la conferma del genitore.
           </p>
          <label for="parentEmail" class="block text-sm font-medium text-gray-700">Email del Genitore/Tutore</label>
          <input
            id="parentEmail"
            v-model="parentEmail"
            type="email"
            :required="requiresParentalConsent"
            autocomplete="email"
            class="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <!-- Fine Campi GDPR Età -->

        <!-- Checkbox GDPR -->
        <div class="space-y-2">
           <div class="flex items-start">
                <input
                  id="acceptPrivacyPolicy"
                  v-model="acceptPrivacyPolicy"
                  type="checkbox"
                  required
                  class="w-4 h-4 mt-1 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <label for="acceptPrivacyPolicy" class="ml-2 block text-sm text-gray-900">
                  Dichiaro di aver letto e accettato l'
                  <router-link :to="{ name: 'privacy-policy' }" target="_blank" class="font-medium text-indigo-600 hover:text-indigo-500">Informativa sulla Privacy</router-link>.
                </label>
            </div>
             <div class="flex items-start">
                <input
                  id="acceptTermsOfService"
                  v-model="acceptTermsOfService"
                  type="checkbox"
                  required
                  class="w-4 h-4 mt-1 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <label for="acceptTermsOfService" class="ml-2 block text-sm text-gray-900">
                  Dichiaro di aver letto e accettato i
                  <router-link :to="{ name: 'terms-of-service' }" target="_blank" class="font-medium text-indigo-600 hover:text-indigo-500">Termini di Servizio</router-link>.
                </label>
            </div>
        </div>
        <!-- Fine Checkbox GDPR -->

        <div v-if="errorMessage" class="p-3 text-sm text-red-700 bg-red-100 rounded-md">
          {{ errorMessage }}
        </div>

        <div>
          <button
            type="submit"
            :disabled="isLoading || !groupToken"
            class="flex justify-center w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading">Registrazione in corso...</span>
            <span v-else>Registrati e Accedi</span>
          </button>
        </div>
         <div class="text-center text-sm">
            <router-link :to="{ name: 'login' }" class="font-medium text-indigo-600 hover:text-indigo-500"> <!-- Corretto nome rotta: 'login' minuscolo -->
              Hai già un account? Accedi
            </router-link>
          </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { registerStudentWithGroupToken, type GroupTokenRegistrationPayload } from '@/api/registration'; // Importa anche il tipo
// Rimuovi import dello store auth specifico studente
// import { useAuthStore } from '@/stores/auth';
import { useSharedAuthStore, type SharedUser } from '@/stores/sharedAuth'; // Importa store condiviso
import { AxiosError } from 'axios';

const route = useRoute();
const router = useRouter();
const sharedAuth = useSharedAuthStore(); // Istanza dello store condiviso

const groupToken = ref<string>('');
const firstName = ref('');
const lastName = ref('');
const pin = ref('');
const birthDate = ref(''); // Aggiunto per GDPR età
const parentEmail = ref(''); // Aggiunto per GDPR consenso parentale
const acceptPrivacyPolicy = ref(false); // Aggiunto per GDPR
const acceptTermsOfService = ref(false); // Aggiunto per GDPR
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);

// --- Inizio Modifiche GDPR Età ---
const MIN_CONSENT_AGE = 14; // O l'età definita dalla normativa locale/policy

const age = computed(() => {
  if (!birthDate.value) return null;
  try {
    const birth = new Date(birthDate.value);
    const today = new Date();
    // Controllo data futura semplice
    if (birth > today) return -1; // Usa un valore negativo per indicare data futura

    let calculatedAge = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
      calculatedAge--;
    }
    return calculatedAge;
  } catch (e) {
    console.error("Errore nel calcolo dell'età:", e);
    return null; // Gestisce date non valide o formati inattesi
  }
});

const requiresParentalConsent = computed(() => {
  // Richiede consenso se l'età è calcolata, valida (non negativa) e sotto il limite
  return age.value !== null && age.value >= 0 && age.value < MIN_CONSENT_AGE;
});
// --- Fine Modifiche GDPR Età ---

onMounted(() => {
  // Prendi il token dalla route in modo più sicuro
  const tokenParam = route.params?.token; // Accesso sicuro
  if (typeof tokenParam === 'string' && tokenParam) { // Controlla tipo e che non sia vuoto
    groupToken.value = tokenParam;
  } else {
      errorMessage.value = "Token di registrazione mancante o non valido nell'URL.";
      console.error("Token non trovato, non è una stringa, o è vuoto:", tokenParam);
  }
});

const handleSubmit = async () => {
  errorMessage.value = null; // Resetta errore all'inizio

  if (!groupToken.value) {
      errorMessage.value = "Impossibile procedere senza un token valido.";
      return;
  }
  // Validazione base PIN numerico (aggiungere controlli più robusti se necessario)
  if (!/^\d+$/.test(pin.value)) {
      errorMessage.value = "Il PIN deve contenere solo cifre numeriche.";
      return;
  }
  // Validazione accettazione policy GDPR
  if (!acceptPrivacyPolicy.value || !acceptTermsOfService.value) {
      errorMessage.value = "È necessario accettare l'Informativa sulla Privacy e i Termini di Servizio per registrarsi.";
      return;
  }

  // --- Inizio Validazioni GDPR Età ---
  if (!birthDate.value) {
      errorMessage.value = "È necessario inserire la data di nascita.";
      return;
  }
  // Verifica data valida (non futura o palesemente errata)
  if (age.value === -1) { // Codice specifico per data futura
       errorMessage.value = "La data di nascita non può essere nel futuro.";
       return;
  }
  if (age.value !== null && age.value < 0) { // Altri errori di calcolo/validità
       errorMessage.value = "La data di nascita inserita non è valida.";
       return;
  }

  if (requiresParentalConsent.value && !parentEmail.value) {
      errorMessage.value = "È necessario inserire l'email di un genitore o tutore per i minori di " + MIN_CONSENT_AGE + " anni.";
      return;
  }
  // Semplice validazione formato email
  if (requiresParentalConsent.value && parentEmail.value && !/.+@.+\..+/.test(parentEmail.value)) {
       errorMessage.value = "L'indirizzo email del genitore non sembra valido.";
       return;
  }
  // --- Fine Validazioni GDPR Età ---


  isLoading.value = true;
  // errorMessage.value = null; // Spostato all'inizio

  try {
    // Usa l'interfaccia importata per garantire la corrispondenza dei tipi
    const payload: GroupTokenRegistrationPayload = {
      token: groupToken.value,
      first_name: firstName.value,
      last_name: lastName.value,
      pin: pin.value,
      // Usa i nomi corretti attesi dal backend/interfaccia API
      accept_privacy_policy: acceptPrivacyPolicy.value,
      accept_terms_of_service: acceptTermsOfService.value,
      date_of_birth: birthDate.value,
    };

     // Aggiungi l'email del genitore solo se necessario
    if (requiresParentalConsent.value) {
       // Assicurati che il tipo di payload permetta questa aggiunta o usa 'any'
       (payload as any).parent_email = parentEmail.value;
    }


    const response = await registerStudentWithGroupToken(payload);

    // Registrazione avvenuta con successo, ora effettua il login automatico
    // utilizzando lo store condiviso.

    // Mappa i dati della risposta a SharedUser
    const studentData = response.student; // Assumendo che la risposta abbia la chiave 'student'
    const sharedUserData: SharedUser = {
        id: studentData.id,
        student_code: studentData.student_code,
        first_name: studentData.first_name,
        last_name: studentData.last_name,
        role: 'STUDENT' // Imposta ruolo esplicitamente
    };

    // Salva nello store condiviso
    sharedAuth.setAuthData(response.access, response.refresh || null, sharedUserData);

    // Reindirizza alla dashboard usando Vue Router
    // Mostra un messaggio se è richiesta la verifica parentale (opzionale, dipende dal flusso desiderato)
    if (requiresParentalConsent.value) {
        console.log("Registrazione completata. In attesa di verifica parentale.");
        // Qui potresti mostrare un messaggio all'utente invece del redirect immediato
        // Ad esempio, potresti reindirizzare a una pagina specifica "Verifica Email Genitore Inviata"
        // o mostrare un popup/toast. Per ora, manteniamo il redirect alla dashboard
        // ma informiamo che l'account non sarà pienamente attivo fino alla verifica.
        // TODO: Considerare un flusso UI migliore per l'attesa della verifica parentale.
    }

    router.push({ name: 'dashboard' }); // Usa il nome della rotta dashboard

  } catch (error) {
    console.error('Errore durante la registrazione con token di gruppo:', error);
    if (error instanceof AxiosError && error.response) {
        // Prova a estrarre un messaggio di errore specifico dal backend
        const backendError = error.response.data;
        if (typeof backendError === 'string') {
            errorMessage.value = backendError;
        } else if (backendError && typeof backendError.detail === 'string') {
             errorMessage.value = backendError.detail;
        } else if (backendError && typeof backendError.error === 'string') {
             errorMessage.value = backendError.error;
        }
         else {
            // Messaggio generico se non si trova un dettaglio specifico
            errorMessage.value = `Errore ${error.response.status}: Impossibile completare la registrazione. Controlla i dati inseriti o il token.`;
        }
    } else if (error instanceof Error) {
         errorMessage.value = error.message;
    }
    else {
      errorMessage.value = 'Si è verificato un errore sconosciuto durante la registrazione.';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Eventuali stili specifici */
</style>