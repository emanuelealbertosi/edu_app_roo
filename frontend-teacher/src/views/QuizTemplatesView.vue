<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa API per i template del docente, il tipo QuizTemplate e la nuova funzione di upload
import { fetchTeacherQuizTemplates, deleteTeacherQuizTemplate, uploadQuizTemplateFromFile, type QuizTemplate } from '@/api/quizzes'; // Aggiunto uploadQuizTemplateFromFile
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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

<template>
  <div class="quiz-templates-view p-4 md:p-6"> <!-- Padding ok -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Gestione Template Quiz</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <p class="opacity-90">Qui puoi visualizzare, creare e modificare i tuoi template di quiz.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>
    <div class="actions mb-6 flex space-x-2"> <!-- Margin e flex ok -->
      <BaseButton variant="primary" @click="createNewQuizTemplate">Crea Nuovo Template</BaseButton> <!-- Usa BaseButton -->
      <BaseButton variant="success" @click="toggleUploadForm">Carica Template da File</BaseButton> <!-- Usa BaseButton -->
    </div>

    <!-- Form di Upload (mostrato/nascosto) -->
    <div v-if="showUploadForm" class="upload-form mt-4 p-4 border border-neutral-DEFAULT rounded-lg bg-neutral-lightest shadow-sm mb-6"> <!-- Stili form aggiornati -->
      <h2 class="text-lg font-semibold mb-3 text-neutral-darkest">Carica Template da File (.pdf, .docx, .md)</h2> <!-- Stile titolo aggiornato -->
      <form @submit.prevent="submitUploadForm">
        <div class="mb-4"> <!-- Margin ok -->
          <label for="templateTitle" class="block text-sm font-medium text-neutral-darker mb-1">Titolo del Template:</label> <!-- Stile label aggiornato -->
          <input type="text" id="templateTitle" v-model="uploadTitle" required class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2"> <!-- Stili input aggiornati -->
        </div>
        <div class="mb-4"> <!-- Margin ok -->
          <label for="templateFile" class="block text-sm font-medium text-neutral-darker mb-1">Seleziona File:</label> <!-- Stile label aggiornato -->
          <input type="file" id="templateFile" @change="handleFileUpload" accept=".pdf,.docx,.md" required class="block w-full text-sm text-neutral-darker file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20 cursor-pointer"> <!-- Stili input file aggiornati -->
        </div>
        <div class="flex justify-end space-x-3"> <!-- Spazio ok -->
           <BaseButton type="button" variant="secondary" @click="toggleUploadForm">Annulla</BaseButton> <!-- Usa BaseButton -->
           <BaseButton type="submit" variant="success" :disabled="isUploading"> <!-- Usa BaseButton -->
             <span v-if="isUploading">
               <!-- Sostituito spinner FontAwesome con uno SVG o si potrebbe usare un componente Spinner -->
               <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                 <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
               </svg>
               Caricamento...
             </span>
             <span v-else>Carica Template</span>
           </BaseButton>
        </div>
        <p v-if="uploadError" class="text-error text-sm mt-3">{{ uploadError }}</p> <!-- Stile errore aggiornato -->
      </form>
    </div>
    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento template quiz...</div> <!-- Stile loading aggiornato -->
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert"> <!-- Stile errore aggiornato -->
       <strong class="font-bold">Errore!</strong>
       <span class="block sm:inline"> Errore nel caricamento dei template quiz: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="templates.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white"> <!-- Stile tabella aggiornato -->
        <thead class="bg-neutral-lightest"> <!-- Stile thead aggiornato -->
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Titolo</th> <!-- Stile th aggiornato -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT"> <!-- Stile tbody aggiornato -->
          <tr v-for="template in templates" :key="template.id" class="hover:bg-neutral-lightest transition-colors duration-150"> <!-- Usa variabile 'template', stile tr aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ template.title }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ template.description || '-' }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ new Date(template.created_at).toLocaleDateString() }}</td> <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"> <!-- Spazio ok -->
              <BaseButton variant="warning" size="sm" @click="editQuizTemplate(template.id)">Modifica</BaseButton> <!-- Usa BaseButton -->
              <BaseButton variant="danger" size="sm" @click="deleteQuizTemplate(template.id)">Elimina</BaseButton> <!-- Usa BaseButton -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark"> <!-- Stile no templates aggiornato -->
      Nessun template di quiz trovato.
    </div>
  </div>
</template>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
/* Puoi aggiungere qui stili molto specifici se necessario */

/* Stile per spinner (se usi Font Awesome) - Rimosso perché usato SVG */
/* @keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.fa-spinner {
  animation: spin 1s linear infinite;
} */
</style>