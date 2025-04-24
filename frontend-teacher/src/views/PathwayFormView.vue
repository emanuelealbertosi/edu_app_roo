<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-2xl font-semibold text-gray-900 mb-6">
      {{ isEditing ? 'Modifica Percorso' : 'Crea Nuovo Percorso' }}
    </h1>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-10">
      <p class="text-gray-500">Caricamento dati percorso...</p>
    </div>

    <!-- Error State (Generale) -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <!-- Form -->
    <form v-else @submit.prevent="savePathway" class="space-y-6 bg-white p-8 rounded-lg shadow-md max-w-4xl mx-auto mb-8">
      <!-- Title -->
      <div>
        <label for="title" class="block text-sm font-medium text-gray-700 mb-1">Titolo</label>
        <input type="text" id="title" v-model="pathwayData.title" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
      </div>

      <!-- Description -->
      <div>
        <label for="description" class="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
        <textarea id="description" v-model="pathwayData.description" rows="3"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"></textarea>
      </div>

      <!-- Points on Completion -->
      <div>
        <label for="points_on_completion" class="block text-sm font-medium text-gray-700 mb-1">Punti al Completamento Percorso</label>
        <input type="number" id="points_on_completion" v-model.number="pointsOnCompletion" min="0" placeholder="Es: 50"
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
        <p class="mt-2 text-xs text-gray-500">Punti assegnati allo studente al primo completamento del percorso.</p>
      </div>

      <!-- TODO: Aggiungere gestione altri metadata se necessario -->

      <!-- Form Actions -->
      <div class="flex justify-end space-x-3 border-t border-gray-200 pt-6">
        <button type="button" @click="cancel"
                class="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
          Annulla
        </button>
        <button type="submit" :disabled="isSaving"
                :class="['py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
                         isSaving ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700']">
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche Percorso' : 'Crea Percorso') }}
        </button>
      </div>
    </form>

    <!-- Quizzes Section (only in editing mode) -->
    <div v-if="isEditing && pathwayId && !isLoading" class="bg-white p-8 rounded-lg shadow-md max-w-4xl mx-auto">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Quiz nel Percorso</h2>

        <!-- Loading Available Quizzes State -->
        <div v-if="isLoadingQuizzes" class="text-center py-4">
            <p class="text-gray-500 text-sm italic">Caricamento quiz disponibili...</p>
        </div>
        <!-- Error Loading Available Quizzes State -->
        <div v-else-if="quizzesError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded relative mb-4 text-sm" role="alert">
            {{ quizzesError }}
        </div>

        <!-- Pathway Quizzes List -->
        <div class="mb-6 border-b border-gray-200 pb-6">
            <h3 class="text-lg font-medium text-gray-900 mb-3">Quiz Attualmente Inclusi</h3>
            <ul v-if="sortedQuizDetails.length > 0" class="space-y-3">
                <li v-for="quizDetail in sortedQuizDetails" :key="quizDetail.id" class="flex justify-between items-center p-3 bg-gray-50 rounded-md border border-gray-200">
                   <span class="text-sm text-gray-800">
                       <span class="font-semibold mr-2">({{ quizDetail.order }})</span> {{ quizDetail.quiz_title }}
                   </span>
                   <button @click="removeQuiz(quizDetail.id)" type="button"
                           class="text-red-600 hover:text-red-800 text-sm font-medium focus:outline-none">
                       Rimuovi
                   </button>
                   <!-- TODO: Aggiungere UI per modificare ordine (es. drag and drop o bottoni su/giù) -->
                </li>
            </ul>
            <p v-else class="text-sm text-gray-500 italic">Nessun quiz aggiunto a questo percorso.</p>
        </div>

        <!-- Add Quiz Section -->
        <div class="add-quiz-section">
            <h3 class="text-lg font-medium text-gray-900 mb-3">Aggiungi Quiz al Percorso</h3>
            <div class="flex items-center space-x-3">
                <select id="quiz-to-add" v-model="selectedQuizToAdd" :disabled="isLoadingQuizzes || isAddingQuiz"
                        class="flex-grow mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                    <option value="">Seleziona un quiz...</option>
                    <option v-for="quiz in availableQuizzes" :key="quiz.id" :value="quiz.id">
                        {{ quiz.title }}
                    </option>
                </select>
                <button @click="addSelectedQuiz" type="button" :disabled="!selectedQuizToAdd || isAddingQuiz"
                        :class="['inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
                                 (!selectedQuizToAdd || isAddingQuiz) ? 'bg-indigo-300 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700']">
                    <svg v-if="isAddingQuiz" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {{ isAddingQuiz ? 'Aggiungo...' : 'Aggiungi' }}
                </button>
            </div>
             <div v-if="addQuizError" class="text-red-600 text-sm mt-2">{{ addQuizError }}</div>
        </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createPathway, fetchPathwayDetails, updatePathway, addQuizToPathway, removeQuizFromPathway, type PathwayPayload, type Pathway, type PathwayQuizDetail } from '@/api/pathways';
import { fetchQuizzes, type Quiz } from '@/api/quizzes'; // Importa API Quiz

// Interfaccia estesa per i dati locali che include quiz_details
interface PathwayFormData extends PathwayPayload {
    quiz_details: PathwayQuizDetail[]; // Aggiunto per visualizzazione
}

const route = useRoute();
const router = useRouter();

const pathwayId = ref<number | null>(null);
const isEditing = computed(() => !!pathwayId.value);
const isLoading = ref(false);
const isSaving = ref(false); // Salvataggio dati percorso
const error = ref<string | null>(null); // Errore caricamento/salvataggio percorso

// Stato per gestione quiz nel percorso
const availableQuizzes = ref<Quiz[]>([]);
const isLoadingQuizzes = ref(false);
const quizzesError = ref<string | null>(null);
const selectedQuizToAdd = ref<number | ''>('');
const isAddingQuiz = ref(false);
const addQuizError = ref<string | null>(null);

// Usiamo reactive per l'oggetto del form
const pathwayData = reactive<PathwayFormData>({
  title: '',
  description: null,
  metadata: {},
  quiz_details: [], // Inizializza vuoto
});


// Calcola i quiz ordinati per visualizzazione
const sortedQuizDetails = computed(() => {
    // Clona l'array prima di ordinarlo per non mutare l'originale reattivo direttamente
    // Clona l'array prima di ordinarlo per non mutare l'originale reattivo direttamente
    return [...pathwayData.quiz_details].sort((a, b) => a.order - b.order);
});

// Computed property per gestire points_on_completion nei metadata
const pointsOnCompletion = computed({
  get: () => pathwayData.metadata?.points_on_completion ?? null, // Restituisce null se non definito
  set: (value) => {
    // Assicurati che metadata esista
    if (!pathwayData.metadata) {
      pathwayData.metadata = {};
    }
    // Aggiorna o rimuovi la proprietà
    if (value === null || value === '' || isNaN(Number(value))) {
      // Se il valore è nullo, vuoto o non un numero, rimuovi la chiave o impostala a null
      // delete pathwayData.metadata.points_on_completion; // Opzione 1: rimuovi
      pathwayData.metadata.points_on_completion = null; // Opzione 2: imposta a null
    } else {
      pathwayData.metadata.points_on_completion = Number(value); // Imposta il valore numerico
    }
  }
});

onMounted(async () => {
  const idParam = route.params.id;
  if (idParam) {
    pathwayId.value = Number(idParam);
    if (!isNaN(pathwayId.value)) {
      await loadPathwayData(pathwayId.value);
    } else {
      console.error("ID Percorso non valido:", idParam);
      error.value = "ID Percorso non valido.";
      pathwayId.value = null;
    }
  }
  // Carica anche i quiz disponibili se siamo in modifica
  if (isEditing.value) {
      await loadAvailableQuizzes();
  }
});

const loadPathwayData = async (id: number) => {
  isLoading.value = true;
  error.value = null;
  try {
    const fetchedPathway = await fetchPathwayDetails(id);
    pathwayData.title = fetchedPathway.title;
    pathwayData.description = fetchedPathway.description;
    pathwayData.metadata = fetchedPathway.metadata || {};
    pathwayData.quiz_details = fetchedPathway.quiz_details || []; // Carica i quiz associati
  } catch (err: any) {
    console.error("Errore nel caricamento del percorso:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore nel caricamento dei dati del percorso.';
  } finally {
    isLoading.value = false;
  }
};

const savePathway = async () => {
  isSaving.value = true;
  error.value = null;

  // Prepara il payload senza quiz_details (gestiti separatamente)
  const payload: PathwayPayload = {
    title: pathwayData.title,
    description: pathwayData.description,
    metadata: pathwayData.metadata && Object.keys(pathwayData.metadata).length > 0 ? pathwayData.metadata : {},
  };

  try {
    let savedPathway: Pathway;
    if (isEditing.value && pathwayId.value) {
      savedPathway = await updatePathway(pathwayId.value, payload);
    } else {
      savedPathway = await createPathway(payload);
      // Se creato, naviga alla modifica per aggiungere quiz? O torna alla lista?
      // Per ora torna alla lista.
    }
    // TODO: Gestire salvataggio/aggiornamento dei quiz nel percorso qui o dopo la navigazione
    router.push({ name: 'pathways' });
  } catch (err: any) {
    console.error("Errore durante il salvataggio del percorso:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore durante il salvataggio del percorso.';
  } finally {
    isSaving.value = false;
  }
};

const cancel = () => {
  router.push({ name: 'pathways' }); // Torna alla lista
};

// --- Logica Gestione Quiz nel Percorso ---

const loadAvailableQuizzes = async () => {
    isLoadingQuizzes.value = true;
    quizzesError.value = null;
    try {
        // Filtra i quiz già presenti nel percorso? Forse non necessario, l'API add dovrebbe gestire duplicati.
        availableQuizzes.value = await fetchQuizzes();
    } catch (err: any) {
        console.error("Errore caricamento quiz disponibili:", err);
        quizzesError.value = "Impossibile caricare l'elenco dei quiz.";
    } finally {
        isLoadingQuizzes.value = false;
    }
};

const addSelectedQuiz = async () => {
    if (!selectedQuizToAdd.value || !pathwayId.value) return;

    isAddingQuiz.value = true;
    addQuizError.value = null;
    const quizId = selectedQuizToAdd.value;

    // Calcola il prossimo ordine disponibile
    const nextOrder = pathwayData.quiz_details.length > 0
        ? Math.max(...pathwayData.quiz_details.map(q => q.order)) + 1
        : 0;

    try {
        const newPathwayQuizDetail = await addQuizToPathway(pathwayId.value, quizId, nextOrder);
        // Aggiungi il nuovo dettaglio alla lista locale
        pathwayData.quiz_details.push(newPathwayQuizDetail);
        selectedQuizToAdd.value = ''; // Resetta il dropdown
        console.log(`Quiz ${quizId} aggiunto al percorso ${pathwayId.value}`);
    } catch (err: any) {
        console.error(`Errore aggiunta quiz ${quizId} al percorso:`, err);
        addQuizError.value = `Errore aggiunta quiz: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    } finally {
        isAddingQuiz.value = false;
    }
};

const removeQuiz = async (pathwayQuizId: number) => {
    // pathwayQuizId è l'ID della relazione PathwayQuiz
    if (!pathwayId.value) return;

    // Trova l'indice per rimuoverlo ottimisticamente o dopo conferma API
    const indexToRemove = pathwayData.quiz_details.findIndex(detail => detail.id === pathwayQuizId);
    if (indexToRemove === -1) return;

    const quizTitle = pathwayData.quiz_details[indexToRemove].quiz_title;
    if (!confirm(`Sei sicuro di voler rimuovere il quiz "${quizTitle}" da questo percorso?`)) {
        return;
    }

    // Chiama l'API per rimuovere la relazione quiz-percorso
    try {
        await removeQuizFromPathway(pathwayId.value, pathwayQuizId);
        // Rimuovi dalla lista locale SOLO dopo successo API
        pathwayData.quiz_details.splice(indexToRemove, 1);
        console.log(`Quiz (relazione ${pathwayQuizId}) rimosso dal percorso ${pathwayId.value}.`);
        // Potresti voler mostrare un messaggio di successo all'utente
    } catch (err: any) {
        console.error(`Errore rimozione quiz (relazione ${pathwayQuizId}) dal percorso ${pathwayId.value}:`, err);
        // Mostra l'errore all'utente (potresti usare una variabile ref dedicata per gli errori di questa sezione)
        addQuizError.value = `Errore rimozione quiz: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    }
};

</script>

<style scoped>
/* Rimuoviamo la maggior parte degli stili scoped, ora gestiti da Tailwind. */
/* Eventuali stili specifici che Tailwind non copre facilmente possono rimanere qui. */

/* Esempio: stile per il bottone di rimozione quiz se necessario */
/* .quizzes-section li button { ... } */
</style>