<template>
  <div class="students-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-4">Gestione Studenti</h1> <!-- Styled heading -->
    <p class="text-gray-600 mb-6">Elenco degli studenti associati al tuo account.</p> <!-- Styled paragraph -->

    <!-- Sezione Generazione Link Registrazione -->
    <div class="mb-6 p-4 border rounded-lg bg-gray-50">
      <h2 class="text-lg font-medium mb-2">Link Registrazione Studenti</h2>
      <p class="text-sm text-gray-600 mb-3">Genera un link univoco da condividere con i nuovi studenti per permettere loro di registrarsi e associarsi automaticamente a te.</p>
      <button
        @click="generateRegistrationLink"
        :disabled="isGeneratingLink"
        class="btn btn-primary"
      >
        <span v-if="isGeneratingLink">Generazione in corso...</span>
        <span v-else>Genera Nuovo Link</span>
      </button>
      <div v-if="generationError" class="mt-3 text-red-600 text-sm">
        Errore nella generazione del link: {{ generationError }}
      </div>
      <div v-if="generatedLink" class="mt-4">
        <label for="registration-link" class="block text-sm font-medium text-gray-700 mb-1">Link Generato (valido per 7 giorni):</label>
        <div class="flex items-center space-x-2">
          <input
            id="registration-link"
            type="text"
            :value="generatedLink"
            readonly
            class="flex-grow p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-gray-100"
          />
          <button @click="copyLinkToClipboard" class="btn btn-secondary btn-sm">
            Copia
          </button>
        </div>
         <p v-if="copySuccessMessage" class="mt-2 text-sm text-green-600">{{ copySuccessMessage }}</p>
      </div>
    </div>

    <!-- Elenco Studenti Esistenti -->
    <h2 class="text-xl font-semibold mb-4 mt-8">Studenti Esistenti</h2>
    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento studenti...</div> <!-- Styled loading -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento degli studenti: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="students.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-gray-200 bg-white">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cognome</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Codice Studente</th> <!-- Ripristinato -->
            <!-- <th>Username</th> --> <!-- Rimosso come da richiesta -->
            <!-- Aggiungere altre colonne se necessario -->
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="student in students" :key="student.id" class="hover:bg-gray-50 transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ student.first_name }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ student.last_name }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ student.student_code }}</td> <!-- Ripristinato -->
            <!-- <td>{{ student.username }}</td> --> <!-- Rimosso come da richiesta -->
            <!-- Aggiungere altre celle se necessario -->
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-gray-500"> <!-- Styled no students -->
      Nessuno studente trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'; // Aggiungi nextTick
import { fetchStudents, type Student } from '@/api/students'; // Importa la funzione API e il tipo
import { createRegistrationToken, type RegistrationTokenResponse } from '@/api/registrationTokens'; // Importa API per token

const students = ref<Student[]>([]); // Conterrà l'elenco degli studenti
const isLoading = ref(false); // Stato di caricamento
const error = ref<string | null>(null); // Messaggio di errore caricamento studenti

// Stato per generazione link
const generatedLink = ref<string | null>(null);
const isGeneratingLink = ref(false);
const generationError = ref<string | null>(null);
const copySuccessMessage = ref<string | null>(null);

onMounted(async () => {
  isLoading.value = true;
  error.value = null;
  try {
    students.value = await fetchStudents();
    // console.log('Studenti ricevuti:', students.value); // Rimosso log di debug
  } catch (err: any) {
    console.error("Errore nel recupero degli studenti:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
    // Potresti voler gestire tipi specifici di errore qui (es. 401, 403)
  } finally {
    isLoading.value = false;
  }
});

async function generateRegistrationLink() {
  isGeneratingLink.value = true;
  generationError.value = null;
  generatedLink.value = null; // Resetta link precedente
  copySuccessMessage.value = null; // Resetta messaggio copia

  try {
    const response: RegistrationTokenResponse = await createRegistrationToken();
    generatedLink.value = response.registration_link; // Usa il link completo dalla risposta
  } catch (err: any) {
    console.error("Errore nella generazione del link:", err);
    generationError.value = err.response?.data?.detail || err.message || 'Si è verificato un errore sconosciuto.';
  } finally {
    isGeneratingLink.value = false;
  }
}

async function copyLinkToClipboard() {
  if (!generatedLink.value) return;

  try {
    await navigator.clipboard.writeText(generatedLink.value);
    copySuccessMessage.value = 'Link copiato negli appunti!';
    // Nasconde il messaggio dopo qualche secondo
    setTimeout(() => {
      copySuccessMessage.value = null;
    }, 3000);
  } catch (err) {
    console.error('Errore nella copia del link:', err);
    // Potresti mostrare un messaggio di errore all'utente qui
    copySuccessMessage.value = 'Errore durante la copia.';
     setTimeout(() => {
      copySuccessMessage.value = null;
    }, 3000);
  }
}
</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
/* Puoi aggiungere qui stili molto specifici se necessario */
</style>