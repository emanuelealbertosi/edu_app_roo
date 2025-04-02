<template>
  <div class="pathway-form-view">
    <h1>{{ isEditing ? 'Modifica Percorso' : 'Crea Nuovo Percorso' }}</h1>
    <div v-if="isLoading" class="loading">Caricamento dati percorso...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>

    <form v-else @submit.prevent="savePathway">
      <div class="form-group">
        <label for="title">Titolo:</label>
        <input type="text" id="title" v-model="pathwayData.title" required />
      </div>
      <div class="form-group">
        <label for="description">Descrizione:</label>
        <textarea id="description" v-model="pathwayData.description"></textarea>
      </div>

      <!-- TODO: Aggiungere gestione metadata -->

      <div class="form-actions">
        <button type="submit" :disabled="isSaving">
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche' : 'Crea Percorso') }}
        </button>
        <button type="button" @click="cancel">Annulla</button>
      </div>
    </form>

    <!-- Sezione Quiz del Percorso (da aggiungere in seguito se in modalità modifica) -->
    <div v-if="isEditing && pathwayId" class="quizzes-section">
        <h2>Quiz nel Percorso</h2>
        <div v-if="isLoadingQuizzes" class="loading small">Caricamento quiz disponibili...</div>
        <div v-else-if="quizzesError" class="error-message small">{{ quizzesError }}</div>

        <!-- Lista Quiz nel Percorso -->
        <ul v-if="pathwayData.quiz_details.length > 0">
            <li v-for="quizDetail in sortedQuizDetails" :key="quizDetail.id">
               <span>({{ quizDetail.order }}) {{ quizDetail.quiz_title }}</span>
               <button @click="removeQuiz(quizDetail.id)" type="button" class="delete small">Rimuovi</button>
               <!-- TODO: Aggiungere UI per modificare ordine -->
            </li>
        </ul>
        <p v-else>Nessun quiz aggiunto a questo percorso.</p>

        <!-- Aggiunta Quiz -->
        <div class="add-quiz-section form-group">
            <label for="quiz-to-add">Aggiungi Quiz al Percorso:</label>
            <div class="add-quiz-controls">
                <select id="quiz-to-add" v-model="selectedQuizToAdd" :disabled="isLoadingQuizzes">
                    <option value="">Seleziona un quiz...</option>
                    <option v-for="quiz in availableQuizzes" :key="quiz.id" :value="quiz.id">
                        {{ quiz.title }}
                    </option>
                </select>
                <button @click="addSelectedQuiz" type="button" :disabled="!selectedQuizToAdd || isAddingQuiz">
                    {{ isAddingQuiz ? 'Aggiungo...' : 'Aggiungi Quiz' }}
                </button>
            </div>
             <div v-if="addQuizError" class="error-message small">{{ addQuizError }}</div>
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
    return [...pathwayData.quiz_details].sort((a, b) => a.order - b.order);
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

    // TODO: Implementare chiamata API `removeQuizFromPathway` quando disponibile nel backend
    // Per ora, simuliamo la rimozione locale e mostriamo un avviso.
    console.warn(`Simulazione rimozione relazione quiz ID ${pathwayQuizId}. API backend richiesta.`);
    pathwayData.quiz_details.splice(indexToRemove, 1);
    // try {
    //     await removeQuizFromPathway(pathwayId.value, pathwayQuizId);
    //     pathwayData.quiz_details.splice(indexToRemove, 1); // Rimuovi solo dopo successo API
    //     console.log(`Quiz (relazione ${pathwayQuizId}) rimosso dal percorso.`);
    // } catch (err: any) {
    //     console.error(`Errore rimozione quiz (relazione ${pathwayQuizId}):`, err);
    //     error.value = `Errore rimozione quiz: ${err.message || 'Errore sconosciuto'}`;
    // }
};

</script>

<style scoped>
/* Stili simili a QuizFormView */
.pathway-form-view {
  padding: 20px;
  max-width: 800px;
  margin: auto;
}
.form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.form-group textarea {
  min-height: 100px;
  resize: vertical;
}
.form-actions {
  margin-top: 20px;
}
.form-actions button {
  padding: 10px 15px;
  margin-right: 10px;
  cursor: pointer;
  border-radius: 4px;
  border: none;
}
.form-actions button[type="submit"] {
  background-color: #4CAF50;
  color: white;
}
.form-actions button[type="submit"]:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}
.form-actions button[type="button"] {
  background-color: #f44336;
  color: white;
}
.error-message {
  color: red;
  margin-top: 10px;
  font-weight: bold;
}
.loading {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
.quizzes-section {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}
.quizzes-section ul {
    list-style: none;
    padding: 0;
    margin-top: 15px;
}
.quizzes-section li {
    margin-bottom: 10px;
    padding: 10px;
    border: 1px solid #eee;
    border-radius: 4px;
    background-color: #f9f9f9;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.quizzes-section li span {
    flex-grow: 1;
    margin-right: 10px;
}
.quizzes-section li button.small {
    padding: 2px 6px;
    font-size: 0.8em;
}
.quizzes-section li button.delete {
    background-color: #f44336;
    color: white;
    border: none;
}
.quizzes-section li button.delete:hover {
     background-color: #d32f2f;
}

.add-quiz-section {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px dashed #ccc;
}
.add-quiz-controls {
    display: flex;
    gap: 10px;
    align-items: center;
}
.add-quiz-controls select {
    flex-grow: 1;
}
.add-quiz-controls button {
    padding: 8px 12px;
    white-space: nowrap;
}
</style>