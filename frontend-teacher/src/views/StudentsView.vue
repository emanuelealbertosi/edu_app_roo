<template>
  <!-- Padding ok -->
  <div class="students-view p-4 md:p-6">
    <!-- Stile titolo aggiornato -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Gestione Studenti</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <!-- Stile paragrafo aggiornato -->
      <p class="opacity-90">Elenco degli studenti associati al tuo account.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>

    <!-- Sezione Generazione Link Registrazione -->
    <!-- Stili sezione aggiornati -->
    <div class="mb-6 p-4 border border-neutral-DEFAULT rounded-lg bg-neutral-lightest">
      <!-- Stile titolo aggiornato -->
      <h2 class="text-lg font-medium mb-2 text-neutral-darkest">Link Registrazione Studenti</h2>
      <!-- Stile paragrafo aggiornato -->
      <p class="text-sm text-neutral-dark mb-3">Genera un link univoco da condividere con i nuovi studenti per permettere loro di registrarsi e associarsi automaticamente a te.</p>
      <!-- Usa BaseButton -->
      <BaseButton
        variant="primary"
        @click="generateRegistrationLink"
        :disabled="isGeneratingLink"
      >
        <span v-if="isGeneratingLink">Generazione in corso...</span>
        <span v-else>Genera Nuovo Link</span>
      </BaseButton>
      <!-- Stile errore aggiornato -->
      <div v-if="generationError" class="mt-3 text-error text-sm">
        Errore nella generazione del link: {{ generationError }}
      </div>
      <div v-if="generatedLink" class="mt-4">
        <!-- Stile label aggiornato -->
        <label for="registration-link" class="block text-sm font-medium text-neutral-darker mb-1">Link Generato (valido per 7 giorni):</label>
        <div class="flex items-center space-x-2">
          <input
            id="registration-link"
            type="text"
            :value="generatedLink"
            readonly
            class="flex-grow p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary sm:text-sm bg-neutral-light"
          />
          <!-- Usa BaseButton -->
          <BaseButton variant="secondary" size="sm" @click="copyLinkToClipboard">
            Copia
          </BaseButton>
        </div>
         <!-- Stile successo aggiornato -->
         <p v-if="copySuccessMessage" class="mt-2 text-sm text-success-dark">{{ copySuccessMessage }}</p>
      </div>
    </div>

    <!-- Elenco Studenti Esistenti -->
    <!-- Stile titolo aggiornato -->
    <h2 class="text-xl font-semibold mb-4 mt-8 text-neutral-darkest">Studenti Esistenti</h2>
    <!-- Stile loading aggiornato -->
    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento studenti...</div>
    <!-- Stile errore aggiornato -->
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento degli studenti: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="students.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <!-- Stile tabella aggiornato -->
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white">
        <!-- Stile thead aggiornato -->
        <thead class="bg-neutral-lightest">
          <tr>
            <!-- Stile th aggiornato -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Nome</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Cognome</th>
            <!-- Ripristinato -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Codice Studente</th>
            <!-- Rimosso come da richiesta -->
            <!-- <th>Username</th> -->
            <!-- Aggiungere altre colonne se necessario -->
          </tr>
        </thead>
        <!-- Stile tbody aggiornato -->
        <tbody class="bg-white divide-y divide-neutral-DEFAULT">
          <!-- Stile tr aggiornato -->
          <tr v-for="student in students" :key="student.id" class="hover:bg-neutral-lightest transition-colors duration-150">
            <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ student.first_name }}</td>
            <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ student.last_name }}</td>
            <!-- Ripristinato, stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ student.student_code }}</td>
            <!-- Rimosso come da richiesta -->
            <!-- <td>{{ student.username }}</td> -->
            <!-- Aggiungere altre celle se necessario -->
          </tr>
        </tbody>
      </table>
    </div>
    <!-- Stile no students aggiornato -->
    <div v-else class="text-center py-10 text-neutral-dark">
      Nessuno studente trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'; // Aggiungi nextTick
import { fetchStudents, type Student } from '@/api/students'; // Importa la funzione API e il tipo
import { createRegistrationToken, type RegistrationTokenResponse } from '@/api/registrationTokens'; // Importa API per token
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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