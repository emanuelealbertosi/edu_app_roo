<template>
  <div class="question-template-form-view">
    <h1>{{ isEditing ? 'Modifica Domanda Template' : 'Crea Nuova Domanda Template' }}</h1>
    <p v-if="quizTemplateId">Per Template Quiz ID: {{ quizTemplateId }}</p>

    <div v-if="isLoading" class="loading">Caricamento dati domanda...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>

    <form v-else @submit.prevent="saveQuestionTemplate">
      <div class="form-group">
        <label for="text">Testo Domanda:</label>
        <textarea id="text" v-model="questionData.text" required rows="4"></textarea>
      </div>

      <div class="form-group">
        <label for="question_type">Tipo Domanda:</label>
        <select id="question_type" v-model="questionData.question_type" required>
          <option value="MC_SINGLE">Scelta Multipla (Risposta Singola)</option>
          <option value="MC_MULTI">Scelta Multipla (Risposte Multiple)</option>
          <option value="TF">Vero/Falso</option>
          <option value="FILL_BLANK">Completamento Spazi Vuoti</option>
          <option value="OPEN_MANUAL">Risposta Aperta (Correzione Manuale)</option>
        </select>
      </div>

      <!-- Rimosso input manuale metadati JSON -->


      <!-- Sezione Opzioni Risposta (solo per tipi compatibili) -->
      <div v-if="isOptionBasedType" class="options-section">
        <h2>Opzioni di Risposta Template</h2>
        <TemplateAnswerOptionsEditor
             v-if="quizTemplateId && questionId"
             :quiz-template-id="quizTemplateId"
             :question-template-id="questionId"
             :question-type="questionData.question_type ?? ''"
           />
      </div>


      <div class="form-actions">
        <button type="submit" :disabled="isSaving" class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mr-2 disabled:opacity-50 disabled:cursor-not-allowed">
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche Domanda' : 'Crea Domanda') }}
        </button>
        <button type="button" @click="cancel" class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">Annulla</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
    fetchTeacherQuestionTemplateDetails, createTeacherQuestionTemplate, updateTeacherQuestionTemplate,
    type QuestionTemplate, type QuestionTemplatePayload
} from '@/api/templateQuestions';
import TemplateAnswerOptionsEditor from '@/components/TemplateAnswerOptionsEditor.vue'; // Importa il componente

const route = useRoute();
const router = useRouter();

const quizTemplateId = ref<number | null>(null);
const questionId = ref<number | null>(null); // ID della domanda template, se in modifica
const isEditing = computed(() => !!questionId.value);
const isLoading = ref(false);
const isSaving = ref(false);
const error = ref<string | null>(null);
// Rimosse variabili per metadata JSON manuale
// const metadataString = ref('');
// const metadataError = ref<string | null>(null);

// Tipi di domanda che usano opzioni
const OPTION_BASED_TYPES = ['MC_SINGLE', 'MC_MULTI', 'TF'];
const isOptionBasedType = computed(() => OPTION_BASED_TYPES.includes(questionData.question_type ?? '')); // Fallback a stringa vuota

const questionData = reactive<Partial<QuestionTemplatePayload>>({ // Usiamo Partial per i dati iniziali
  text: '',
  question_type: 'MC_SINGLE', // Default
  metadata: {}, // Mantenuto per struttura dati, ma non più editabile manualmente qui
});

// Rimosso watcher per metadataString


onMounted(async () => {
  const qtIdParam = route.params.templateId; // Assumendo che la rotta passi templateId
  const qIdParam = route.params.questionId; // Assumendo che la rotta passi questionId (se modifica)

  if (qtIdParam) {
      quizTemplateId.value = Number(qtIdParam);
      if (isNaN(quizTemplateId.value)) {
          error.value = "ID Template Quiz non valido nella URL.";
          quizTemplateId.value = null;
          return;
      }
  } else {
      error.value = "ID Template Quiz mancante nella URL.";
      return; // Non possiamo procedere senza templateId
  }

  if (qIdParam) {
    questionId.value = Number(qIdParam);
    if (!isNaN(questionId.value)) {
      await loadQuestionTemplateData(quizTemplateId.value, questionId.value);
    } else {
      console.error("ID Domanda Template non valido:", qIdParam);
      error.value = "ID Domanda Template fornito non valido.";
      questionId.value = null;
    }
  } else {
      // Modalità creazione, resetta dati (anche se già default)
      questionData.text = '';
      questionData.question_type = 'MC_SINGLE';
      questionData.metadata = {}; // Resetta metadata
      // Rimosso reset metadataString
  }
});

const loadQuestionTemplateData = async (qtId: number, qId: number) => {
  isLoading.value = true;
  error.value = null;
  try {
    const fetchedQuestion = await fetchTeacherQuestionTemplateDetails(qtId, qId);
    questionData.text = fetchedQuestion.text;
    questionData.question_type = fetchedQuestion.question_type;
    questionData.metadata = fetchedQuestion.metadata || {}; // Carica metadata esistente
    // Rimosso popolamento metadataString
  } catch (err: any) {
    console.error("Errore caricamento dati domanda template:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore caricamento dati domanda.';
  } finally {
    isLoading.value = false;
  }
};

const saveQuestionTemplate = async () => {
  if (!quizTemplateId.value) {
      error.value = "ID Template Quiz mancante.";
      return;
  }
  // Rimosso controllo metadataError

  isSaving.value = true;
  error.value = null;

  // Usa direttamente questionData.metadata (che è già un oggetto)
  const finalMetadata = questionData.metadata || {};


  const payload: QuestionTemplatePayload = {
    text: questionData.text as string, // Type assertion
    question_type: questionData.question_type as string, // Type assertion
    metadata: finalMetadata,
  };

  try {
    if (isEditing.value && questionId.value) {
      await updateTeacherQuestionTemplate(quizTemplateId.value, questionId.value, payload);
    } else {
      await createTeacherQuestionTemplate(quizTemplateId.value, payload);
    }
    // Torna alla vista del template quiz dopo salvataggio/creazione
    router.push({ name: 'quiz-template-edit', params: { id: quizTemplateId.value.toString() } });
  } catch (err: any) {
    console.error("Errore salvataggio domanda template:", err);
    if (err.response?.data && typeof err.response.data === 'object') {
        const errorDetails = Object.entries(err.response.data)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ');
        error.value = `Errore salvataggio: ${errorDetails}`;
    } else {
        error.value = err.response?.data?.detail || err.message || 'Errore salvataggio domanda.';
    }
  } finally {
    isSaving.value = false;
  }
};

const cancel = () => {
  if (quizTemplateId.value) {
    router.push({ name: 'quiz-template-edit', params: { id: quizTemplateId.value.toString() } });
  } else {
    router.push({ name: 'quiz-templates' }); // Fallback se manca ID
  }
};

</script>

<style scoped>
.question-template-form-view {
  padding: 20px;
  max-width: 700px;
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
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.form-group textarea {
  min-height: 80px; /* Ridotta altezza per testo domanda e metadata */
  resize: vertical;
  font-family: monospace; /* Utile per JSON */
}
.form-actions {
  margin-top: 20px;
}
.error-message {
  color: red;
  margin-top: 10px;
  font-weight: bold;
}
.error-message.small {
    font-size: 0.9em;
    font-weight: normal;
    margin-top: 5px;
}
.loading {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
.options-section {
    margin-top: 30px;
    padding-top: 15px;
    border-top: 1px dashed #ccc;
}
.form-help-text {
    font-size: 0.8rem;
    color: #666;
    margin-top: 4px;
}
</style>