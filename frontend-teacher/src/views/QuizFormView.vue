<template>
  <div class="quiz-form-view">
    <h1>{{ isEditing ? 'Modifica Quiz' : 'Crea Nuovo Quiz' }}</h1>
    <form @submit.prevent="saveQuiz">
      <div class="form-group">
        <label for="title">Titolo:</label>
        <input type="text" id="title" v-model="quizData.title" required />
      </div>
      <div class="form-group">
        <label for="description">Descrizione:</label>
        <textarea id="description" v-model="quizData.description"></textarea>
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
        <input type="number" id="points_on_completion" v-model.number="quizData.metadata.points_on_completion" min="0" />
      </div>

      <!-- Aggiungere gestione errori -->
      <div v-if="error" class="error-message">{{ error }}</div>

      <div class="form-actions">
        <button type="submit" :disabled="isSaving">
          {{ isSaving ? 'Salvataggio...' : 'Salva Quiz' }}
        </button>
        <button type="button" @click="cancel">Annulla</button>
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
        <!-- Pulsante Aggiungi Domanda (da implementare) -->
        <button type="button" @click="addQuestion">Aggiungi Domanda</button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createQuiz, fetchQuizDetails, updateQuiz, type QuizPayload } from '@/api/quizzes';
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
    // Aggiungere altri metadati qui se necessario (es. difficulty, threshold)
  };
}

const route = useRoute();
const router = useRouter();

const quizId = ref<number | null>(null);
const isEditing = computed(() => !!quizId.value);
const isSaving = ref(false);
const error = ref<string | null>(null); // Errore generale del form/quiz
const isLoading = ref(false); // Stato caricamento dati quiz

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
    points_on_completion: null
  }
});

onMounted(async () => {
  const idParam = route.params.id;
  if (idParam) {
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

  // Prepara i dati da inviare (converti date se necessario)
  // Prepara il payload assicurandosi che metadata sia un oggetto valido
  // e convertendo le date nel formato ISO atteso dall'API
  const payload: QuizPayload = {
      title: quizData.title,
      description: quizData.description,
      available_from: quizData.available_from ? new Date(quizData.available_from).toISOString() : null,
      available_until: quizData.available_until ? new Date(quizData.available_until).toISOString() : null,
      // Includi i metadati nel payload, assicurandoti che points_on_completion sia un numero o null
      metadata: {
          points_on_completion: quizData.metadata.points_on_completion === null || isNaN(quizData.metadata.points_on_completion) ? 0 : Number(quizData.metadata.points_on_completion)
          // Aggiungere altri metadati qui se necessario
      },
  };

  try {
    if (isEditing.value && quizId.value) {
      // Usa Partial<QuizPayload> per l'aggiornamento parziale
      await updateQuiz(quizId.value, payload);
    } else {
      const newQuiz = await createQuiz(payload); // Usa la funzione API reale
      // Opzionale: potresti voler navigare alla pagina di modifica del nuovo quiz
      // router.push({ name: 'quiz-edit', params: { id: newQuiz.id } });
      // Per ora, torniamo alla lista
    }
    // Naviga indietro alla lista o alla vista dettaglio del quiz
    router.push({ name: 'quizzes' });
  } catch (err: any) {
    console.error("Errore durante il salvataggio del quiz:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore durante il salvataggio del quiz.';
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

    try {
        await deleteQuestionApi(quizId.value, questionId);
        // Rimuovi la domanda dalla lista locale
        questions.value = questions.value.filter(q => q.id !== questionId);
        console.log(`Domanda ${questionId} eliminata.`);
        // Mostra notifica successo (opzionale)
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
.form-group input[type="datetime-local"] {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box; /* Include padding and border in element's total width and height */
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
  background-color: #4CAF50; /* Green */
  color: white;
}
.form-actions button[type="submit"]:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

.form-actions button[type="button"] {
  background-color: #f44336; /* Red */
  color: white;
}

.error-message {
  color: red;
  margin-top: 10px;
  font-weight: bold;
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

.questions-section button {
    margin-top: 15px;
    padding: 8px 12px;
    cursor: pointer;
}
</style>