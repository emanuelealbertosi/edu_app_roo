<template>
  <div class="question-template-form-view">
    <div class="flex justify-between items-center mb-2">
      <h1 class="text-2xl font-semibold">{{ isEditing ? 'Modifica Domanda Template' : 'Crea Nuova Domanda Template' }}</h1>
      <!-- Indicatore Autosave -->
      <span v-if="isEditing" class="text-sm italic" :class="{
        'text-gray-500': autoSaveStatus === 'idle',
        'text-blue-600': autoSaveStatus === 'saving',
        'text-green-600': autoSaveStatus === 'saved',
        'text-red-600': autoSaveStatus === 'error'
      }">
        <template v-if="autoSaveStatus === 'saving'">Salvataggio...</template>
        <template v-else-if="autoSaveStatus === 'saved'">Salvato ✓</template>
        <template v-else-if="autoSaveStatus === 'error'">Errore salvataggio!</template>
        <!-- Nessun testo per 'idle' -->
      </span>
    </div>
    <p v-if="quizTemplateId" class="text-sm text-gray-600 mb-4">Per Template Quiz ID: {{ quizTemplateId }}</p>

    <div v-if="isLoading" class="loading">Caricamento dati domanda...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>

    <form v-else @submit.prevent="saveQuestionTemplate" class="space-y-4">
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


      <!-- Navigazione Sequenziale (solo in modifica) -->
      <div v-if="isEditing && allQuestionIds.length > 1" class="navigation-actions mt-6 flex justify-between items-center border-t pt-4">
        <button
          type="button"
          @click="goToPreviousQuestion"
          :disabled="!hasPreviousQuestion"
          class="btn btn-primary"
        >
          &lt; Precedente
        </button>
        <span class="text-sm text-gray-600">
          Domanda {{ currentQuestionIndex + 1 }} di {{ allQuestionIds.length }}
        </span>
        <button
          type="button"
          @click="goToNextQuestion"
          :disabled="!hasNextQuestion"
          class="btn btn-primary"
        >
          Successiva &gt;
        </button>
      </div>

      <!-- Azioni Principali Form -->
      <div class="form-actions mt-6 flex justify-end space-x-3 border-t pt-4">
        <button
          type="button"
          @click="cancel"
          class="btn btn-secondary"
        >
          {{ isEditing ? 'Torna al Template' : 'Annulla Creazione' }}
        </button>
        <button
          type="submit"
          :disabled="isSaving"
          class="btn btn-success"
        >
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche' : 'Crea Domanda') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import debounce from 'lodash-es/debounce'; // Importa debounce
import {
    fetchTeacherQuestionTemplateDetails, createTeacherQuestionTemplate, updateTeacherQuestionTemplate,
    // Potrebbe servire un endpoint per fetchare solo gli ID delle domande del template
    // fetchQuestionTemplateIdsForQuizTemplate,
    type QuestionTemplate, type QuestionTemplatePayload
} from '@/api/templateQuestions';
import TemplateAnswerOptionsEditor from '@/components/TemplateAnswerOptionsEditor.vue';

const route = useRoute();
const router = useRouter();

const quizTemplateId = ref<number | null>(null);
const questionId = ref<number | null>(null); // ID della domanda template, se in modifica
const isEditing = computed(() => !!questionId.value);
const isLoading = ref(false);
const isSaving = ref(false);
const error = ref<string | null>(null);
const autoSaveStatus = ref<'idle' | 'saving' | 'saved' | 'error'>('idle');

// Stato per la navigazione sequenziale
const allQuestionIds = ref<number[]>([]); // Da popolare (es. con chiamata API)
const currentQuestionIndex = computed(() => {
  if (!questionId.value || allQuestionIds.value.length === 0) return -1;
  return allQuestionIds.value.indexOf(questionId.value);
});
const hasPreviousQuestion = computed(() => currentQuestionIndex.value > 0);
const hasNextQuestion = computed(() => currentQuestionIndex.value !== -1 && currentQuestionIndex.value < allQuestionIds.value.length - 1);

// Rimosse variabili per metadata JSON manuale

// Tipi di domanda che usano opzioni
const OPTION_BASED_TYPES = ['MC_SINGLE', 'MC_MULTI', 'TF'];
const isOptionBasedType = computed(() => OPTION_BASED_TYPES.includes(questionData.question_type ?? '')); // Fallback a stringa vuota

const questionData = reactive<Partial<QuestionTemplatePayload>>({ // Usiamo Partial per i dati iniziali
  text: '',
  question_type: 'MC_SINGLE', // Default
  metadata: {}, // Mantenuto per struttura dati, ma non più editabile manualmente qui
});

// --- Autosalvataggio ---
const performAutoSave = async () => {
  if (!isEditing.value || !quizTemplateId.value || !questionId.value) return; // Salva solo in modifica
  
  autoSaveStatus.value = 'saving';
  console.log("Autosaving question template..."); // Debug

  // Prepara payload (simile a saveQuestionTemplate ma senza navigazione)
  const finalMetadata = questionData.metadata || {};
  const payload: QuestionTemplatePayload = {
    text: questionData.text as string,
    question_type: questionData.question_type as string,
    metadata: finalMetadata,
  };

  try {
    // Usiamo sempre update perché siamo in modalità modifica
    await updateTeacherQuestionTemplate(quizTemplateId.value, questionId.value, payload);
    autoSaveStatus.value = 'saved';
    // Resetta lo stato dopo un po'
    setTimeout(() => { autoSaveStatus.value = 'idle'; }, 2000);
  } catch (err: any) {
    console.error("Errore autosalvataggio:", err);
    autoSaveStatus.value = 'error';
    // Non mostriamo l'errore dettagliato qui per non essere invasivi,
    // l'utente vedrà l'errore completo al salvataggio manuale se persiste.
    // Resetta lo stato dopo un po'
    setTimeout(() => { autoSaveStatus.value = 'idle'; }, 3000);
  }
};

// Crea la versione debounced della funzione di salvataggio
const debouncedSave = debounce(performAutoSave, 1500); // Salva dopo 1.5s di inattività

// Watcher per triggerare l'autosalvataggio
// Usiamo deep: true per osservare cambiamenti negli oggetti (es. metadata)
// Aggiungiamo un flag per evitare il trigger al caricamento iniziale
const isInitialLoadDone = ref(false);
watch(questionData, (newValue, oldValue) => {
  if (isInitialLoadDone.value && isEditing.value) {
    autoSaveStatus.value = 'idle'; // Resetta stato se utente modifica di nuovo
    debouncedSave();
  }
}, { deep: true });

// --- Navigazione Sequenziale ---
const goToQuestion = (index: number) => {
  if (index >= 0 && index < allQuestionIds.value.length) {
    const nextQuestionId = allQuestionIds.value[index];
    // Naviga alla stessa rotta ma con ID domanda diverso
    router.push({
      name: 'edit-question-template', // Assicurati che il nome rotta sia corretto
      params: {
        templateId: quizTemplateId.value?.toString(),
        questionId: nextQuestionId.toString()
      }
    });
  }
};

const goToPreviousQuestion = () => {
  if (hasPreviousQuestion.value) {
    goToQuestion(currentQuestionIndex.value - 1);
  }
};

const goToNextQuestion = () => {
  if (hasNextQuestion.value) {
    goToQuestion(currentQuestionIndex.value + 1);
  }
};

const fetchAllQuestionIds = async (qtId: number) => {
    // --- Placeholder: Implementare chiamata API per ottenere gli ID ---
    console.warn("fetchAllQuestionIds non implementato - usare dati fittizi per ora");
    // Esempio dati fittizi (da sostituire con chiamata API reale)
    // const ids = await fetchQuestionTemplateIdsForQuizTemplate(qtId);
    // allQuestionIds.value = ids;
    // Esempio:
    // Simula una chiamata API che restituisce ID basati sull'ID del template
    if (qtId === 1) { // ID template fittizio
        allQuestionIds.value = [10, 15, 20, 25]; // ID domande fittizi
    } else {
        allQuestionIds.value = [30, 31, 32]; // Altri ID fittizi
    }
    console.log("ID domande caricati (fittizi):", allQuestionIds.value);
    // --- Fine Placeholder ---
};

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
      // Dopo aver caricato i dati, recupera gli ID per la navigazione
      await fetchAllQuestionIds(quizTemplateId.value);
    } else {
      console.error("ID Domanda Template non valido:", qIdParam);
      error.value = "ID Domanda Template fornito non valido.";
      questionId.value = null;
    }
  } else {
      // Modalità creazione
      questionData.text = '';
      questionData.question_type = 'MC_SINGLE';
      questionData.metadata = {};
      // In modalità creazione, non ha senso caricare gli ID per la navigazione
      allQuestionIds.value = [];
  }
  // Segnala che il caricamento iniziale è completo per abilitare l'autosave
  isInitialLoadDone.value = true;
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
    // Non navigare via dopo il salvataggio manuale se siamo in modifica,
    // l'utente potrebbe voler usare i bottoni di navigazione.
    // Naviga solo se stiamo creando una nuova domanda.
    if (!isEditing.value) {
        router.push({ name: 'quiz-template-edit', params: { id: quizTemplateId.value.toString() } });
    } else {
        // Mostra feedback salvataggio manuale riuscito
        autoSaveStatus.value = 'saved';
        setTimeout(() => { autoSaveStatus.value = 'idle'; }, 2000);
    }
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