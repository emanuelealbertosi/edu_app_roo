<template>
  <div class="quiz-templates-view"> <!-- Rinominato selettore CSS -->
    <h1>Gestione Template Quiz</h1> <!-- Titolo aggiornato -->
    <p>Qui puoi visualizzare, creare e modificare i tuoi template di quiz.</p> <!-- Descrizione aggiornata -->
    <div class="actions">
      <!-- Applicato stile Tailwind -->
      <button @click="createNewQuizTemplate" class="btn btn-primary mr-2">Crea Nuovo Template</button>
      <!-- Aggiunto pulsante Carica da File -->
      <button @click="toggleUploadForm" class="btn btn-success">Carica Template da File</button>
    </div>

    <!-- Form di Upload (mostrato/nascosto) -->
    <div v-if="showUploadForm" class="upload-form mt-4 p-4 border rounded bg-gray-100">
      <h2 class="text-lg font-semibold mb-2">Carica Template da File (.pdf, .docx, .md)</h2>
      <form @submit.prevent="submitUploadForm">
        <div class="mb-3">
          <label for="templateTitle" class="block text-sm font-medium text-gray-700 mb-1">Titolo del Template:</label>
          <input type="text" id="templateTitle" v-model="uploadTitle" required class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2">
        </div>
        <div class="mb-3">
          <label for="templateFile" class="block text-sm font-medium text-gray-700 mb-1">Seleziona File:</label>
          <input type="file" id="templateFile" @change="handleFileUpload" accept=".pdf,.docx,.md" required class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
        </div>
        <div class="flex justify-end space-x-2">
           <button type="button" @click="toggleUploadForm" class="btn btn-secondary">Annulla</button>
           <button type="submit" :disabled="isUploading" class="btn btn-success">
             {{ isUploading ? 'Caricamento...' : 'Carica Template' }}
           </button>
        </div>
        <p v-if="uploadError" class="text-red-500 text-sm mt-2">{{ uploadError }}</p>
      </form>
    </div>
    <div v-if="isLoading" class="loading">Caricamento template quiz...</div> <!-- Testo aggiornato -->
    <div v-else-if="error" class="error-message">
      Errore nel caricamento dei template quiz: {{ error }} <!-- Testo aggiornato -->
    </div>
    <div v-else-if="templates.length > 0" class="quizzes-list"> <!-- Usa variabile 'templates' -->
      <!-- Tabella o lista dei template quiz -->
      <ul>
        <!-- Tabella o lista dei template quiz -->
        <table>
          <thead>
            <tr>
              <th>Titolo</th>
              <th>Descrizione</th>
              <th>Creato il</th>
              <th>Azioni</th>
              <th>Statistiche</th> <!-- Nuova colonna -->
            </tr>
          </thead>
          <tbody>
            <tr v-for="template in templates" :key="template.id"> <!-- Usa variabile 'template' -->
              <td>{{ template.title }}</td>
              <td>{{ template.description || '-' }}</td>
              <td>{{ new Date(template.created_at).toLocaleDateString() }}</td>
              <td>
                <!-- Applicato stile Tailwind -->
                <button @click="editQuizTemplate(template.id)" class="btn btn-warning text-sm mr-2">Modifica</button> <!-- Funzione aggiornata -->
                <!-- Applicato stile Tailwind -->
                <button @click="deleteQuizTemplate(template.id)" class="btn btn-danger text-sm mr-2">Elimina</button> <!-- Funzione aggiornata -->
                <!-- Pulsante Statistiche -->
                <button @click="showStats(template.id)" class="btn btn-info btn-sm">Statistiche</button>
              </td>
           </tr>
         </tbody>
        </table>
      </ul>
    </div>
    <div v-else class="no-quizzes">
      Nessun template di quiz trovato. <!-- Testo aggiornato -->
    </div>

    <!-- Sezione Statistiche (mostrata condizionalmente) -->
    <div v-if="selectedTemplateStats || isLoadingStats || statsError" class="stats-section mt-6 p-4 border rounded shadow-md bg-gray-50">
      <div class="flex justify-between items-center mb-3">
        <h2 class="text-lg font-semibold">Statistiche Template: {{ selectedTemplateStats?.template_title || 'Caricamento...' }}</h2>
        <button @click="closeStats" class="btn btn-secondary btn-xs">Chiudi</button>
      </div>

      <div v-if="isLoadingStats" class="loading">Caricamento statistiche...</div>
      <div v-else-if="statsError" class="error-message">Errore caricamento statistiche: {{ statsError }}</div>
      <div v-else-if="selectedTemplateStats">
        <dl class="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <div class="bg-white px-2 py-1 rounded border">
            <dt class="font-medium text-gray-500">Istanze Create</dt>
            <dd class="text-gray-900 font-semibold">{{ selectedTemplateStats.total_instances_created }}</dd>
          </div>
          <div class="bg-white px-2 py-1 rounded border">
            <dt class="font-medium text-gray-500">Assegnazioni Totali</dt>
            <dd class="text-gray-900 font-semibold">{{ selectedTemplateStats.total_assignments }}</dd>
          </div>
          <div class="bg-white px-2 py-1 rounded border">
            <dt class="font-medium text-gray-500">Tentativi Totali</dt>
            <dd class="text-gray-900 font-semibold">{{ selectedTemplateStats.total_attempts }}</dd>
          </div>
          <div class="bg-white px-2 py-1 rounded border">
            <dt class="font-medium text-gray-500">Punteggio Medio (Completati)</dt>
            <dd class="text-gray-900 font-semibold">{{ selectedTemplateStats.average_score?.toFixed(1) ?? 'N/A' }}</dd>
          </div>
          <div class="bg-white px-2 py-1 rounded border">
            <dt class="font-medium text-gray-500">% Completamento</dt>
            <dd class="text-gray-900 font-semibold">{{ selectedTemplateStats.completion_rate?.toFixed(1) ?? 'N/A' }}%</dd>
          </div>
        </dl>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa API per i template del docente, statistiche, tipi e upload
import {
  fetchTeacherQuizTemplates,
  deleteTeacherQuizTemplate,
  uploadQuizTemplateFromFile,
  fetchQuizTemplateStats, // Importa funzione statistiche
  type QuizTemplate,
  type QuizTemplateStats // Importa tipo statistiche
} from '@/api/quizzes';

const templates = ref<QuizTemplate[]>([]); // Rinominato e usa tipo QuizTemplate
const isLoading = ref(false); // Loading lista template
const router = useRouter();
const error = ref<string | null>(null);
const showUploadForm = ref(false); // Stato per mostrare/nascondere il form
const uploadFile = ref<File | null>(null);
const uploadTitle = ref('');
const isUploading = ref(false);
const uploadError = ref<string | null>(null);

// Stato per statistiche
const selectedTemplateStats = ref<QuizTemplateStats | null>(null);
const isLoadingStats = ref(false);
const statsError = ref<string | null>(null);

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

// --- Funzioni Statistiche ---

const showStats = async (templateId: number) => {
  selectedTemplateStats.value = null; // Resetta precedente
  statsError.value = null;
  isLoadingStats.value = true;
  try {
    selectedTemplateStats.value = await fetchQuizTemplateStats(templateId);
  } catch (err: any) {
    console.error(`Errore recupero statistiche per template ${templateId}:`, err);
    statsError.value = err.response?.data?.detail || err.message || 'Errore sconosciuto';
  } finally {
    isLoadingStats.value = false;
  }
};

const closeStats = () => {
  selectedTemplateStats.value = null;
  statsError.value = null;
  isLoadingStats.value = false;
};

</script>

<style scoped>
/* Stili simili a QuizzesView, ma con selettore aggiornato */
.quiz-templates-view {
  padding: 20px;
}

.loading,
.error-message,
.no-quizzes { /* Mantenuto nome classe per semplicità */
  margin-top: 20px;
  font-style: italic;
  color: #666;
}

.error-message {
  color: red;
  font-weight: bold;
}

.quizzes-list { /* Mantenuto nome classe per semplicità */
  margin-top: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}

.actions {
  margin-bottom: 20px;
}
.stats-section {
  /* Stili aggiuntivi se necessario */
}
</style>