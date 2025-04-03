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
        <input
          type="file"
          id="quiz-file"
          @change="handleFileChange"
          required
          accept=".pdf,.docx,.md"
          class="w-full text-sm text-gray-500
                 file:mr-4 file:py-2 file:px-4
                 file:rounded-md file:border-0
                 file:text-sm file:font-semibold
                 file:bg-indigo-50 file:text-indigo-700
                 hover:file:bg-indigo-100"
        />
        <p class="mt-1 text-xs text-gray-500">Tipi di file supportati: PDF, DOCX, Markdown (.md)</p>
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
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router'; // Importa useRouter per il reindirizzamento
import { uploadQuiz } from '@/api/quizzes'; // Assicurati che il percorso sia corretto
import type { Quiz } from '@/api/quizzes'; // Importa l'interfaccia Quiz

const quizTitle = ref('');
const selectedFile = ref<File | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);
const createdQuizId = ref<number | null>(null); // Per salvare l'ID del quiz creato
const router = useRouter(); // Istanza del router

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    selectedFile.value = target.files[0];
    errorMessage.value = null; // Resetta errore se si seleziona un nuovo file
    successMessage.value = null; // Resetta successo
    createdQuizId.value = null;
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
  createdQuizId.value = null;

  try {
    const createdQuiz: Quiz = await uploadQuiz(selectedFile.value, quizTitle.value);
    successMessage.value = `Quiz "${createdQuiz.title}" creato con successo! ID: ${createdQuiz.id}. Ora puoi modificare le domande e impostare le risposte corrette.`;
    createdQuizId.value = createdQuiz.id; // Salva l'ID per il link
    console.log("Upload successful:", successMessage.value); // Log
    console.log("Upload successful:", successMessage.value); // Log
    // Opzionale: Resetta il form dopo successo
    // quizTitle.value = '';
    // selectedFile.value = null;
    // const fileInput = document.getElementById('quiz-file') as HTMLInputElement;
    // if (fileInput) fileInput.value = '';

    // Opzionale: Reindirizza alla pagina di modifica del quiz creato dopo un breve ritardo
    // setTimeout(() => {
    //   if (createdQuizId.value) {
    //     router.push({ name: 'QuizEdit', params: { quizId: createdQuizId.value } });
    //   }
    // }, 3000); // Reindirizza dopo 3 secondi

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