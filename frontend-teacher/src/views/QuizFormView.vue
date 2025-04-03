<template>
  <div class="quiz-form-view">
    <h1>{{ isEditing ? 'Modifica Quiz' : 'Crea Nuovo Quiz' }}</h1>
    <!-- Messaggio di successo -->
    <div v-if="successMessage" class="success-message bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4 rounded">
        {{ successMessage }}
    </div>
    <form @submit.prevent="saveQuiz">
      <div class="form-group">
        <label for="title">Titolo:</label>
        <input type="text" id="title" v-model="quizData.title" required />
      </div>
      <div class="form-group">
        <label for="description">Descrizione (Opzionale):</label>
        <textarea id="description" v-model="quizData.description"></textarea> <!-- Rimosso 'required' se presente -->
      </div>
      <div class="form-group">
        <label for="available_from">Disponibile Dal:</label>
        <input type="datetime-local" id="available_from" v-model="quizData.available_from" />
      </div>
      <div class="form-group">
        <label for="available_until">Disponibile Fino Al:</label>
        <input type="datetime-local" id="available_until" v-model="quizData.available_until" />
      </div>
      <div class="form-group">
        <label for="points_on_completion">Punti al Completamento:</label>
        <input type="number" id="points_on_completion" v-model.number="quizData.metadata.points_on_completion" min="0" class="form-input" />
      </div>
      <div class="form-group">
        <label for="completion_threshold_percent">Soglia Completamento (%):</label>
        <input type="number" id="completion_threshold_percent" v-model.number="quizData.metadata.completion_threshold_percent" min="0" max="100" step="0.1" class="form-input" />
        <p class="form-help-text">Percentuale minima (0-100) per considerare il quiz superato. Default: 100%.</p>
      </div>

      <!-- Aggiungere gestione errori -->
      <div v-if="error" class="error-message">{{ error }}</div>

      <div class="form-actions">
         <!-- Applicato stile Tailwind -->
        <button type="submit" :disabled="isSaving" class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mr-2 disabled:opacity-50 disabled:cursor-not-allowed">
          {{ isSaving ? 'Salvataggio...' : 'Salva Quiz' }}
        </button>
         <!-- Applicato stile Tailwind -->
        <button type="button" @click="cancel" class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">Annulla</button>
      </div>
    </form>

    <!-- Sezione Domande (da aggiungere in seguito se in modalità modifica) -->
    <div v-if="isEditing && quizId" class="questions-section">
        <h2>Domande del Quiz</h2>
        <div v-if="isLoadingQuestions" class="loading">Caricamento domande...</div>
        <div v-else-if="questionsError" class="error-message">
            Errore nel caricamento delle domande: {{ questionsError }}
        </div>
        <div v-else-if="questions.length > 0">
            <ul class="question-list">
                <QuestionEditor
                    v-for="question in questions"
                    :key="question.id"
                    :question="question"
                    @edit="handleEditQuestion"
                    @delete="handleDeleteQuestion"
                />
            </ul>
        </div>
        <div v-else>
            <p>Nessuna domanda ancora aggiunta a questo quiz.</p>
        </div>
        <!-- Pulsante Aggiungi Domanda -->
         <!-- Applicato stile Tailwind -->
        <button type="button" @click="addQuestion" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4">Aggiungi Domanda</button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createQuiz, fetchQuizDetails, updateQuiz, type QuizPayload, type Quiz } from '@/api/quizzes'; // Importa anche Quiz type
import { fetchQuestions, deleteQuestionApi, type Question } from '@/api/questions'; // Importa anche deleteQuestionApi
import QuestionEditor from '@/components/QuestionEditor.vue'; // Importa il nuovo componente

// Interfaccia temporanea per i dati del form
interface QuizFormData {
  title: string;
  description: string | null;
  available_from: string | null;
  available_until: string | null;
  metadata: { // Aggiunto metadata
    points_on_completion: number | null;
    completion_threshold_percent: number | null; // Aggiunto campo soglia
    // Aggiungere altri metadati qui se necessario (es. difficulty)
  };
}

const route = useRoute();
const router = useRouter();

const quizId = ref<number | null>(null);
const isEditing = computed(() => !!quizId.value);
const isSaving = ref(false);
const error = ref<string | null>(null); // Errore generale del form/quiz
const isLoading = ref(false); // Stato caricamento dati quiz
const successMessage = ref<string | null>(null); // Messaggio di successo

// Stato per le domande
const questions = ref<Question[]>([]);
const isLoadingQuestions = ref(false);
const questionsError = ref<string | null>(null);

// Usiamo reactive per l'oggetto del form
const quizData = reactive<QuizFormData>({
  title: '',
  description: null,
  available_from: null,
  available_until: null,
  metadata: { // Inizializza metadata
    points_on_completion: null,
    completion_threshold_percent: 100.0 // Impostato default a 100.0
  }
});

onMounted(async () => {
  const idParam = route.params.id;
  if (idParam && idParam !== 'new') { // Controlla che non sia 'new'
    quizId.value = Number(idParam);
    if (!isNaN(quizId.value)) {
      // ID valido, carica dati quiz e domande
      await loadQuizData(quizId.value);
      await loadQuestions(quizId.value);
    } else {
      // ID non valido (non numerico)
      console.error("ID Quiz non valido (non numerico):", idParam);
      error.value = "ID Quiz fornito nella URL non è valido.";
      quizId.value = null; // Resetta ID
    }
  } else {
      // Siamo in modalità creazione
      quizId.value = null;
  }
});

const loadQuizData = async (id: number) => {
  isLoading.value = true;
  error.value = null;
  try {
    const fetchedQuiz = await fetchQuizDetails(id); // Usa la funzione API reale
    quizData.title = fetchedQuiz.title;
    quizData.description = fetchedQuiz.description;
    // Assicurati che i campi metadata, source_template etc. siano gestiti se necessario
    quizData.available_from = formatDateTimeForInput(fetchedQuiz.available_from);
    quizData.available_until = formatDateTimeForInput(fetchedQuiz.available_until);
    // Carica i metadati esistenti
    quizData.metadata.points_on_completion = fetchedQuiz.metadata?.points_on_completion ?? null;
    // Carica anche la soglia esistente, o usa il default 100 se non presente
    // Converti da 0-1 a 0-100 se necessario (assumendo che l'API restituisca 0-1)
    const threshold_api = fetchedQuiz.metadata?.completion_threshold;
    quizData.metadata.completion_threshold_percent = threshold_api !== undefined && threshold_api !== null ? threshold_api * 100 : 100.0;

  } catch (err: any) {
    console.error("Errore nel caricamento del quiz:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore nel caricamento dei dati del quiz.';
  } finally {
    isLoading.value = false;
  }
};

const loadQuestions = async (id: number) => {
    isLoadingQuestions.value = true;
    questionsError.value = null;
    try {
        questions.value = await fetchQuestions(id);
    } catch (err: any) {
        console.error(`Errore nel caricamento delle domande per il quiz ${id}:`, err);
        questionsError.value = err.response?.data?.detail || err.message || 'Errore nel caricamento delle domande.';
    } finally {
        isLoadingQuestions.value = false;
    }
};

const saveQuiz = async () => {
  isSaving.value = true;
  error.value = null;
  successMessage.value = null; // Resetta messaggio successo

  // Prepara il payload assicurandosi che metadata sia un oggetto valido
  // e convertendo le date nel formato ISO atteso dall'API
  // Converti la soglia da % (0-100) a decimale (0-1) per l'API
  const threshold_percent = quizData.metadata.completion_threshold_percent;
  const completion_threshold = threshold_percent === null || isNaN(Number(threshold_percent)) ? 1.0 : Number(threshold_percent) / 100; // Default a 1 (100%) se non valido

  const payload: QuizPayload = {
      title: quizData.title,
      description: quizData.description,
      available_from: quizData.available_from ? new Date(quizData.available_from).toISOString() : null,
      available_until: quizData.available_until ? new Date(quizData.available_until).toISOString() : null,
      metadata: {
          points_on_completion: quizData.metadata.points_on_completion === null || isNaN(Number(quizData.metadata.points_on_completion)) ? 0 : Number(quizData.metadata.points_on_completion),
          completion_threshold: completion_threshold, // Invia come decimale 0-1
          // Aggiungere altri metadati qui se necessario
      },
  };

  try {
    let savedQuiz: Quiz | null = null;
    if (isEditing.value && quizId.value) {
      savedQuiz = await updateQuiz(quizId.value, payload);
      // Ricarica i dati dopo l'aggiornamento per mostrare eventuali cambiamenti fatti dal backend
      await loadQuizData(quizId.value);
      successMessage.value = "Quiz aggiornato con successo!";
    } else {
      savedQuiz = await createQuiz(payload); // Usa la funzione API reale
      successMessage.value = "Quiz creato con successo! Ora puoi aggiungere domande.";
      // Aggiorna l'URL e lo stato per riflettere la modalità di modifica senza ricaricare la pagina
      quizId.value = savedQuiz.id;
      router.replace({ name: 'quiz-edit', params: { id: savedQuiz.id.toString() } }); // Usa replace per non aggiungere alla history
      // Carica le domande (saranno vuote)
      await loadQuestions(savedQuiz.id);
    }

    // Nascondi il messaggio di successo dopo qualche secondo
    setTimeout(() => {
        successMessage.value = null;
    }, 3000);

    // Rimosso: router.push({ name: 'quizzes' });
  } catch (err: any) {
    console.error("Errore durante il salvataggio del quiz:", err);
    // Tenta di estrarre errori specifici dei campi se disponibili
    if (err.response?.data && typeof err.response.data === 'object') {
        const errorDetails = Object.entries(err.response.data)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ');
        error.value = `Errore salvataggio: ${errorDetails}`;
    } else {
        error.value = err.response?.data?.detail || err.message || 'Errore durante il salvataggio del quiz.';
    }
  } finally {
    isSaving.value = false;
  }
};

const cancel = () => {
  router.push({ name: 'quizzes' }); // Torna alla lista
};

// Funzione helper per formattare le date ISO per l'input datetime-local
// Nota: l'input datetime-local richiede 'YYYY-MM-DDTHH:mm'
const formatDateTimeForInput = (isoString: string | null): string | null => {
  if (!isoString) return null;
  try {
    const date = new Date(isoString);
    // Estrai le parti e formatta (attenzione ai fusi orari se necessario)
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  } catch (e) {
    console.error("Errore formattazione data:", e);
    return null;
  }
};

const addQuestion = () => {
    console.log("Add Question button clicked. Attempting navigation..."); // Log
    if (!quizId.value) return;
    // Passa il numero attuale di domande come query param per l'ordine default
    const defaultOrder = questions.value.length;
    router.push({
        name: 'question-new',
        params: { quizId: quizId.value.toString() },
        query: { defaultOrder: defaultOrder } // Aggiunto query param
    });
};

const handleEditQuestion = (questionId: number) => {
    if (!quizId.value) return; // Assicurati che quizId sia definito
    // Naviga alla rotta per modificare la domanda specifica
    router.push({ name: 'question-edit', params: { quizId: quizId.value.toString(), questionId: questionId.toString() } });
};

const handleDeleteQuestion = async (questionId: number) => {
    if (!quizId.value) return; // Assicurati che quizId sia definito

    if (!confirm(`Sei sicuro di voler eliminare la domanda con ID ${questionId}?`)) {
        return;
    }

    questionsError.value = null; // Resetta errore precedente
    try {
        await deleteQuestionApi(quizId.value, questionId);
        // Ricarica l'elenco delle domande dal backend per riflettere il nuovo ordine
        await loadQuestions(quizId.value);
        console.log(`Domanda ${questionId} eliminata e lista domande ricaricata.`);
        // Mostra notifica successo (opzionale)
        successMessage.value = `Domanda ${questionId} eliminata con successo.`;
         setTimeout(() => { successMessage.value = null; }, 3000);
    } catch (err: any) {
        console.error(`Errore durante l'eliminazione della domanda ${questionId}:`, err);
        // Mostra errore all'utente
        questionsError.value = `Errore eliminazione domanda: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    }
};

</script>

<style scoped>
.quiz-form-view {
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
.form-group textarea,
.form-group input[type="datetime-local"],
.form-group input[type="number"].form-input { /* Applica stile anche agli input number */
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box; /* Include padding and border in element's total width and height */
}

.form-help-text {
    font-size: 0.8rem;
    color: #666;
    margin-top: 4px;
}

.form-group textarea {
  min-height: 100px;
  resize: vertical;
}

.form-actions {
  margin-top: 20px;
}

/* Stili per i bottoni ora gestiti da Tailwind nel template */
/*
.form-actions button { ... }
.form-actions button[type="submit"] { ... }
.form-actions button[type="submit"]:disabled { ... }
.form-actions button[type="button"] { ... }
*/

.error-message {
  color: red;
  margin-top: 10px;
  font-weight: bold;
}
.success-message {
  /* Stili Tailwind applicati direttamente nel template */
  margin-bottom: 15px;
}

.questions-section {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}

.questions-section .question-list { /* Stile specifico per la lista di QuestionEditor */
    list-style: none;
    padding: 0;
    margin-top: 15px;
}

/* Rimuovi lo stile li generico se non serve più altrove */
/* .questions-section li { ... } */

/* Stile bottone Aggiungi Domanda gestito da Tailwind */
/* .questions-section button { ... } */

</style>