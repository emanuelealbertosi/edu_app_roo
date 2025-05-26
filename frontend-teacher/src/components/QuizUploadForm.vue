<template>
  <div class="p-4 border rounded-lg shadow-sm bg-white">
    <h3 class="text-lg font-semibold mb-4">Carica Quiz da File</h3>
    <form @submit.prevent="handleUpload">
      <div class="mb-4">
        <label for="quiz-title" class="block text-sm font-medium text-gray-700 mb-1">Titolo del Quiz:</label>
        <input
          type="text"
          id="quiz-title"
          v-model="quizTitle"
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="Inserisci il titolo del nuovo quiz"
        />
      </div>

      <div class="mb-4">
        <label for="quiz-file" class="block text-sm font-medium text-gray-700 mb-1">Seleziona File:</label>
        <div class="flex items-center space-x-2">
          <input
            type="file"
            id="quiz-file"
            @change="handleFileChange"
            required
            accept=".pdf,.docx,.md"
            class="flex-grow w-full text-sm text-gray-500
                   file:mr-4 file:py-2 file:px-4
                   file:rounded-md file:border-0
                   file:text-sm file:font-semibold
                   file:bg-indigo-50 file:text-indigo-700
                   hover:file:bg-indigo-100"
          />
          <button
            type="button"
            @click="openHelpModal"
            class="p-2 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500"
            aria-label="Mostra aiuto formato file"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-600">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
            </svg>
          </button>
        </div>
        <p class="mt-1 text-xs text-gray-500">Tipi di file supportati: PDF, Markdown (.md), DOCX<sup class="text-indigo-700">beta</sup></p>
      </div>

      <div v-if="errorMessage" class="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
        <p class="font-semibold">Errore durante l'upload:</p>
        <p>{{ errorMessage }}</p>
      </div>

       <div v-if="successMessage" class="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
        <p>{{ successMessage }}</p>
        <!-- Temporaneamente rimosso il router-link per debug indicatore caricamento -->
        <!--
        <router-link
            v-if="createdQuizId"
            :to="{ name: 'QuizEdit', params: { id: createdQuizId } }"
            class="text-indigo-600 hover:text-indigo-800 font-medium underline ml-2"
        >
            Modifica il quiz creato
        </router-link>
        -->
      </div>

      <!-- Indicatore di caricamento più evidente -->
      <div v-if="isLoading" class="mb-4 text-center text-indigo-600 font-medium">
        <p>Caricamento del file e creazione del quiz in corso...</p>
        <p class="text-sm text-gray-500">(Potrebbe richiedere alcuni istanti)</p>
        <!-- Qui potresti inserire una vera progress bar se avessi l'avanzamento dall'API -->
      </div>

      <button
        type="submit"
        :disabled="isLoading || !selectedFile || !quizTitle"
        class="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <!-- Rimosso lo span di caricamento da qui, gestito sopra -->
        Carica e Crea Quiz
      </button>
    </form>

    <!-- Modale di Aiuto Formato File -->
    <div v-if="isHelpModalVisible" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div class="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
          <h4 class="text-xl font-semibold">Formato File per Importazione Template Quiz</h4>
          <button @click="closeHelpModal" class="p-1 rounded-full hover:bg-gray-200">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 text-gray-600">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="prose max-w-none text-sm">
          <p>Per importare un template di quiz da file di testo, assicurati che il contenuto segua queste regole:</p>
          
          <h5 class="font-semibold mt-3 mb-1">Struttura Generale:</h5>
          <ul>
            <li>Ogni domanda deve iniziare con un numero seguito da un punto (es. <code>1.</code>, <code>2.</code>).</li>
            <li>Il testo della domanda segue immediatamente sulla stessa riga.</li>
            <li>Lascia una riga vuota tra una domanda e l'altra per maggiore leggibilità (opzionale, ma consigliato).</li>
          </ul>

          <h5 class="font-semibold mt-3 mb-1">Tipi di Domande Supportati:</h5>
          
          <strong class="block mt-2">1. Risposta Multipla (Scelta Singola o Multipla)</strong>
          <ul>
            <li>Le opzioni di risposta seguono la domanda, ognuna su una nuova riga.</li>
            <li>Ogni opzione inizia con una lettera seguita da una parentesi chiusa (es. <code>A)</code>, <code>B)</code>).</li>
            <li>Per indicare una <strong>risposta corretta</strong>, anteponi un asterisco (<code>*</code>) alla lettera (es. <code>*A)</code>).</li>
            <li>Se una sola opzione è marcata con <code>*</code>, la domanda sarà di tipo "Scelta Singola".</li>
            <li>Se più opzioni sono marcate con <code>*</code>, la domanda sarà di tipo "Scelta Multipla".</li>
          </ul>
          <p class="italic text-xs">Esempio (Scelta Singola):</p>
          <pre class="bg-gray-100 p-2 rounded text-xs">1. Qual è la capitale dell'Italia?\n*A) Roma\nB) Parigi\nC) Berlino</pre>
          <p class="italic text-xs mt-1">Esempio (Scelta Multipla):</p>
          <pre class="bg-gray-100 p-2 rounded text-xs">2. Quali dei seguenti sono colori primari?\n*A) Rosso\nB) Verde\n*C) Blu</pre>

          <strong class="block mt-3">2. Fill-in-the-Blank (Completamento Spazi Vuoti)</strong>
          <ul>
            <li>Nel testo della domanda, indica uno o più spazi da riempire usando una sequenza di tre o più underscore (es. <code>___</code>).</li>
            <li>Le righe successive che iniziano con <code>lettera)</code> (es. <code>A)</code>, <code>B)</code>) forniscono le risposte corrette per ciascun blank, in ordine sequenziale.
                (<code>A)</code> per il primo <code>___</code>, <code>B)</code> per il secondo, ecc.).</li>
            <li>Per ogni blank, puoi specificare più risposte corrette alternative separandole con due punti e virgola (<code>;;</code>).</li>
            <li>Il controllo delle risposte è <em>case-insensitive</em>.</li>
          </ul>
          <p class="italic text-xs">Esempio (Singolo Blank, più alternative):</p>
          <pre class="bg-gray-100 p-2 rounded text-xs">3. Il sole sorge a ___.\nA) Est;;Levante</pre>
          <p class="italic text-xs mt-1">Esempio (Multipli Blank):</p>
          <pre class="bg-gray-100 p-2 rounded text-xs">4. La capitale della Francia è ___ e la sua moneta è l'___.\nA) Parigi\nB) Euro;;euro</pre>

          <strong class="block mt-3">3. Risposta Aperta</strong>
          <ul>
            <li>Una domanda è considerata a risposta aperta se inizia con <code>numero.</code> ma non contiene <code>___</code> e non ha righe successive che iniziano con <code>lettera)</code>.</li>
          </ul>
          <p class="italic text-xs">Esempio:</p>
          <pre class="bg-gray-100 p-2 rounded text-xs">5. Descrivi il processo della fotosintesi.</pre>
          
          <h5 class="font-semibold mt-4 mb-1">Esempio File Completo:</h5>
          <pre class="bg-gray-100 p-2 rounded text-xs">1. Qual è la capitale della Spagna?\nA) Lisbona\n*B) Madrid\nC) Roma\n\n2. Il gatto fa ___ e il topo scappa nella ___.\nA) miao;;meow\nB) tana;;buca;;buco\n\n3. Spiega la teoria della relatività ristretta.\n\n4. Seleziona i mammiferi:\n*A) Balena\nB) Squalo\n*C) Cane\nD) Coccodrillo</pre>
        </div>
        <div class="mt-6 text-right">
          <button
            @click="closeHelpModal"
            class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Chiudi
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, defineEmits } from 'vue'; // Aggiunto defineEmits
import { useRouter } from 'vue-router'; // Importa useRouter per il reindirizzamento
// Modificato l'import per usare uploadQuizTemplateFromFile e QuizTemplate
import { uploadQuizTemplateFromFile, type QuizTemplate } from '@/api/quizzes';

const emit = defineEmits(['upload-successful']); // Definisci l'evento

const quizTitle = ref('');
const selectedFile = ref<File | null>(null);
const isHelpModalVisible = ref(false); // Variabile per la modale di aiuto

const openHelpModal = () => {
  isHelpModalVisible.value = true;
};

const closeHelpModal = () => {
  isHelpModalVisible.value = false;
};
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);
// createdQuizId non è più necessario qui, la gestione avviene nella vista genitore
// const createdQuizId = ref<number | null>(null);
const router = useRouter(); // Istanza del router, potrebbe non essere più necessaria se non c'è reindirizzamento da qui

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    selectedFile.value = target.files[0];
    errorMessage.value = null; // Resetta errore se si seleziona un nuovo file
    successMessage.value = null; // Resetta successo
    // createdQuizId.value = null; // Non più necessario
  } else {
    selectedFile.value = null;
  }
};

const handleUpload = async () => {
  if (!selectedFile.value || !quizTitle.value) {
    errorMessage.value = 'Per favore, inserisci un titolo e seleziona un file.';
    return;
  }

  console.log("handleUpload started"); // Log
  isLoading.value = true;
  console.log("isLoading set to true"); // Log
  errorMessage.value = null;
  successMessage.value = null;
  // createdQuizId.value = null; // Non più necessario

  try {
    // Modificata la chiamata API e il tipo di dato atteso
    const createdTemplate: QuizTemplate = await uploadQuizTemplateFromFile(selectedFile.value, quizTitle.value);
    successMessage.value = `Template Quiz "${createdTemplate.title}" creato con successo! ID: ${createdTemplate.id}. Apparirà nella lista dei template.`;
    // createdQuizId.value = createdTemplate.id; // Non più necessario per il link diretto da qui
    console.log("Upload successful:", successMessage.value); // Log
    
    emit('upload-successful'); // Emetti l'evento
    
    // Opzionale: Resetta il form dopo successo
    quizTitle.value = ''; // Resetta il titolo
    selectedFile.value = null; // Resetta il file selezionato
    const fileInput = document.getElementById('quiz-file') as HTMLInputElement;
    if (fileInput) fileInput.value = ''; // Resetta l'input file nativo

    // La logica di reindirizzamento o gestione del template creato è ora responsabilità della vista genitore
    // che ascolta 'upload-successful'.
    // Il router-link per la modifica era già commentato.

    // isLoading viene impostato a false nel blocco finally

  } catch (error: any) {
     console.error("Upload error caught:", error); // Log
     if (error.response && error.response.data) {
         // Prova a estrarre un messaggio di errore più specifico dal backend
         const backendError = error.response.data;
         if (typeof backendError === 'string') {
             errorMessage.value = backendError;
         } else if (backendError.detail) {
             errorMessage.value = backendError.detail;
         } else if (backendError.file) {
             errorMessage.value = `Errore nel campo file: ${backendError.file.join(', ')}`;
         } else if (backendError.title) {
              errorMessage.value = `Errore nel campo titolo: ${backendError.title.join(', ')}`;
         } else {
             // Fallback per errori strutturati ma non riconosciuti
             errorMessage.value = `Errore dal backend: ${JSON.stringify(backendError)}`;
         }
     } else if (error.request) {
         errorMessage.value = 'Nessuna risposta dal server. Verifica la connessione o lo stato del backend.';
     } else {
         errorMessage.value = `Errore durante l'invio della richiesta: ${error.message}`;
     }
     console.log("Error message set:", errorMessage.value); // Log
     // isLoading viene impostato a false nel blocco finally
  } finally {
    // Manteniamo il finally come sicurezza aggiuntiva, anche se potrebbe essere ridondante ora
    isLoading.value = false;
    console.log("Finally block executed, isLoading set to:", isLoading.value); // Log
  }
};
</script>

<style scoped>
/* Aggiungi qui eventuali stili specifici se necessario */
</style>