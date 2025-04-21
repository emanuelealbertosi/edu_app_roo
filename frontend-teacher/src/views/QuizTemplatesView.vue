<template>
  <div class="quiz-templates-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-4">Gestione Template Quiz</h1> <!-- Styled heading -->
    <p class="text-gray-600 mb-6">Qui puoi visualizzare, creare e modificare i tuoi template di quiz.</p> <!-- Styled paragraph -->
    <div class="actions mb-6 flex space-x-2"> <!-- Added margin and flex for buttons -->
      <button @click="createNewQuizTemplate" class="btn btn-primary">Crea Nuovo Template</button>
      <button @click="toggleUploadForm" class="btn btn-success">Carica Template da File</button>
    </div>

    <!-- Form di Upload (mostrato/nascosto) -->
    <div v-if="showUploadForm" class="upload-form mt-4 p-4 border rounded bg-gray-50 shadow-sm mb-6"> <!-- Styled form container -->
      <h2 class="text-lg font-semibold mb-3">Carica Template da File (.pdf, .docx, .md)</h2>
      <form @submit.prevent="submitUploadForm">
        <div class="mb-4"> <!-- Increased margin -->
          <label for="templateTitle" class="block text-sm font-medium text-gray-700 mb-1">Titolo del Template:</label>
          <input type="text" id="templateTitle" v-model="uploadTitle" required class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2">
        </div>
        <div class="mb-4"> <!-- Increased margin -->
          <label for="templateFile" class="block text-sm font-medium text-gray-700 mb-1">Seleziona File:</label>
          <input type="file" id="templateFile" @change="handleFileUpload" accept=".pdf,.docx,.md" required class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"> <!-- Added cursor-pointer -->
        </div>
        <div class="flex justify-end space-x-3"> <!-- Increased space -->
           <button type="button" @click="toggleUploadForm" class="btn btn-secondary">Annulla</button>
           <button type="submit" :disabled="isUploading" class="btn btn-success">
             <span v-if="isUploading">
               <i class="fas fa-spinner fa-spin mr-1"></i> Caricamento... <!-- Added spinner -->
             </span>
             <span v-else>Carica Template</span>
           </button>
        </div>
        <p v-if="uploadError" class="text-red-600 text-sm mt-3">{{ uploadError }}</p> <!-- Adjusted color and margin -->
      </form>
    </div>
    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento template quiz...</div> <!-- Styled loading -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
       <strong class="font-bold">Errore!</strong>
       <span class="block sm:inline"> Errore nel caricamento dei template quiz: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="templates.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-gray-200 bg-white">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titolo</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="template in templates" :key="template.id" class="hover:bg-gray-50 transition-colors duration-150"> <!-- Usa variabile 'template' -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ template.title }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ template.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ new Date(template.created_at).toLocaleDateString() }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Added space-x-2 -->
              <button @click="editQuizTemplate(template.id)" class="btn btn-warning btn-sm">Modifica</button> <!-- Added btn-sm -->
              <button @click="deleteQuizTemplate(template.id)" class="btn btn-danger btn-sm">Elimina</button> <!-- Added btn-sm -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-gray-500"> <!-- Styled no templates -->
      Nessun template di quiz trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa API per i template del docente, il tipo QuizTemplate e la nuova funzione di upload
import { fetchTeacherQuizTemplates, deleteTeacherQuizTemplate, uploadQuizTemplateFromFile, type QuizTemplate } from '@/api/quizzes'; // Aggiunto uploadQuizTemplateFromFile

const templates = ref<QuizTemplate[]>([]); // Rinominato e usa tipo QuizTemplate
const isLoading = ref(false);
const router = useRouter();
const error = ref<string | null>(null);
const showUploadForm = ref(false); // Stato per mostrare/nascondere il form
const uploadFile = ref<File | null>(null);
const uploadTitle = ref('');
const isUploading = ref(false);
const uploadError = ref<string | null>(null);

const loadTemplates = async () => {
   isLoading.value = true;
   error.value = null;
   try {
       templates.value = await fetchTeacherQuizTemplates(); // Usa API per template docente
   } catch (err: any) {
       console.error("Errore nel recupero dei template quiz:", err); // Messaggio aggiornato
       error.value = err.message || 'Si è verificato un errore sconosciuto.';
   } finally {
       isLoading.value = false;
   }
};

onMounted(loadTemplates); // Chiama la funzione per caricare i dati al mount

// Funzioni aggiornate per template
const editQuizTemplate = (id: number) => {
  // Naviga alla rotta di modifica del template
  router.push({ name: 'quiz-template-edit', params: { id: id.toString() } }); // Nome rotta aggiornato
};

const deleteQuizTemplate = async (id: number) => {
  if (!confirm(`Sei sicuro di voler eliminare il template quiz con ID ${id}?`)) { // Testo aggiornato
    return;
  }
  try {
    await deleteTeacherQuizTemplate(id); // Usa API per template docente
    templates.value = templates.value.filter(template => template.id !== id); // Aggiorna variabile 'templates'
    console.log(`Template quiz ${id} eliminato con successo.`); // Messaggio aggiornato
  } catch (err: any) {
    console.error(`Errore durante l'eliminazione del template quiz ${id}:`, err); // Messaggio aggiornato
    error.value = `Errore durante l'eliminazione del template quiz: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`; // Messaggio aggiornato
  }
};

const createNewQuizTemplate = () => {
  router.push({ name: 'quiz-template-new' }); // Naviga alla rotta di creazione template
};

// Funzioni per il form di upload
const toggleUploadForm = () => {
  showUploadForm.value = !showUploadForm.value;
  // Resetta i campi e gli errori quando si apre/chiude
  uploadFile.value = null;
  uploadTitle.value = '';
  uploadError.value = null;
  const fileInput = document.getElementById('templateFile') as HTMLInputElement;
  if (fileInput) {
      fileInput.value = ''; // Resetta l'input file visivamente
  }
};

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    uploadFile.value = target.files[0];
    uploadError.value = null; // Resetta errore se si seleziona un file
  } else {
    uploadFile.value = null;
  }
};

const submitUploadForm = async () => {
  if (!uploadFile.value || !uploadTitle.value) {
    uploadError.value = 'Per favore, seleziona un file e inserisci un titolo.';
    return;
  }

  isUploading.value = true;
  uploadError.value = null;

  try {
    const newTemplate = await uploadQuizTemplateFromFile(uploadFile.value, uploadTitle.value);
    console.log('Template caricato con successo:', newTemplate);
    toggleUploadForm(); // Chiudi il form
    await loadTemplates(); // Ricarica la lista dei template
    // Potresti aggiungere un messaggio di successo qui (es. con una libreria di notifiche)
  } catch (err: any) {
    console.error('Errore durante l\'upload del template:', err);
    uploadError.value = `Errore upload: ${err.response?.data?.detail || err.response?.data?.file?.[0] || err.response?.data?.title?.[0] || err.message || 'Errore sconosciuto'}`;
  } finally {
    isUploading.value = false;
  }
};
</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
/* Puoi aggiungere qui stili molto specifici se necessario */

/* Stile per spinner (se usi Font Awesome) */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.fa-spinner {
  animation: spin 1s linear infinite;
}
</style>