<template>
  <div class="question-template-form-view">
    <div class="flex justify-between items-center mb-2">
      <h1 class="text-2xl font-semibold mb-4">{{ isEditing ? 'Modifica Domanda Template' : 'Crea Nuova Domanda Template' }}</h1>
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
        <label for="text" class="block text-sm font-medium text-gray-700 mb-1">Testo Domanda:</label>
        <textarea id="text" v-model="questionData.text" required rows="4" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"></textarea>
      </div>

      <div class="form-group">
        <label for="question_type" class="block text-sm font-medium text-gray-700 mb-1">Tipo Domanda:</label>
        <select id="question_type" v-model="questionData.question_type" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
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
import { ref, onMounted, computed, reactive, watch, defineProps, defineEmits } from 'vue'; // Aggiunto defineProps, defineEmits
import { useRoute, useRouter } from 'vue-router';
import debounce from 'lodash-es/debounce'; // Importa debounce
import {
    fetchTeacherQuestionTemplateDetails, createTeacherQuestionTemplate, updateTeacherQuestionTemplate,
    fetchQuestionTemplateIdsForQuizTemplate, // Assicurati che questa sia importata
    type QuestionTemplate, type QuestionTemplatePayload
} from '@/api/templateQuestions';
import TemplateAnswerOptionsEditor from '@/components/TemplateAnswerOptionsEditor.vue';

// Props & Emits per la modalità modale
const props = defineProps({
  templateIdProp: { // Rinominato per chiarezza
    type: Number,
    default: null
  },
  questionIdProp: { // Prop per l'ID della domanda da modificare in modale
    type: Number,
    default: null
  },
  isInModal: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['close-modal', 'question-created', 'question-updated']); // Aggiunto 'question-updated'

const route = useRoute();
const router = useRouter();

// Usa la prop se disponibile (modal mode), altrimenti leggi dalla rotta
const quizTemplateId = computed(() => props.isInModal ? props.templateIdProp : (route.params.templateId ? Number(route.params.templateId) : null));
const questionId = ref<number | null>(null); // ID della domanda template (riportato a ref)
const isEditing = computed(() => !!questionId.value); // Determina se stiamo modificando (in modale o no)
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
      name: 'quiz-template-question-edit', // Nome corretto della rotta per modificare una domanda specifica
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
    console.log(`Tentativo di fetch degli ID domande per il template ${qtId}...`);
    try {
        // Chiama la funzione API reale (da implementare)
        const ids = await fetchQuestionTemplateIdsForQuizTemplate(qtId);
        allQuestionIds.value = ids;
        console.log("ID domande caricati:", allQuestionIds.value);

        // Verifica se l'ID corrente è presente nell'array caricato
        if (questionId.value && !allQuestionIds.value.includes(questionId.value)) {
            console.warn(`L'ID domanda corrente (${questionId.value}) non è stato trovato negli ID caricati per il template ${qtId}. Potrebbe essere un errore o la domanda è stata eliminata.`);
            // Potresti voler gestire questo caso, ad esempio reindirizzando o mostrando un errore
        }

    } catch (err) {
        console.error("Errore durante il fetch degli ID delle domande:", err);
        error.value = "Impossibile caricare la sequenza delle domande per la navigazione.";
        allQuestionIds.value = []; // Resetta in caso di errore
    }
};

// Rimosso watcher per metadataString


onMounted(async () => {
  // Determina l'ID del template (usa computed property quizTemplateId)
  if (!quizTemplateId.value || isNaN(quizTemplateId.value)) {
      error.value = "ID Template Quiz mancante o non valido.";
      return;
  }
  const currentTemplateId = quizTemplateId.value; // Usa il valore dal computed

  // Determina l'ID della domanda (se presente) e imposta il ref
  const currentQuestionIdParam = props.isInModal ? props.questionIdProp : route.params.questionId;
  const currentQuestionId = currentQuestionIdParam ? Number(currentQuestionIdParam) : null;

  if (currentQuestionId && !isNaN(currentQuestionId)) {
      // Modalità Modifica (in modale o no)
      questionId.value = currentQuestionId; // Imposta il ref
      await loadQuestionTemplateData(currentTemplateId, currentQuestionId);
      if (!props.isInModal) {
          // Carica ID per navigazione solo se non siamo in modale
          await fetchAllQuestionIds(currentTemplateId);
      } else {
          allQuestionIds.value = []; // No navigazione in modale
      }
  } else {
      // Modalità Creazione (in modale o no)
      questionId.value = null; // Assicura che sia null
      resetFormData();
      allQuestionIds.value = []; // No navigazione in creazione
  }

  // Segnala che il caricamento iniziale è completo per abilitare l'autosave (solo in edit mode)
  isInitialLoadDone.value = isEditing.value; // isEditing ora usa il ref questionId
});

// Funzione helper per resettare i dati del form
const resetFormData = () => {
    questionData.text = '';
    questionData.question_type = 'MC_SINGLE';
    questionData.metadata = {};
};

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
    // Usa quizTemplateId.value e questionId.value (che ora è un ref)
    if (isEditing.value && questionId.value && quizTemplateId.value) {
      // --- MODIFICA ---
      await updateTeacherQuestionTemplate(quizTemplateId.value, questionId.value, payload);
      if (props.isInModal) {
        emit('question-updated'); // Emetti evento specifico per update in modale
      } else {
        // Mostra feedback salvataggio manuale riuscito (fuori modale)
        autoSaveStatus.value = 'saved';
        setTimeout(() => { autoSaveStatus.value = 'idle'; }, 2000);
      }
    } else if (!isEditing.value && quizTemplateId.value) {
      // --- CREAZIONE ---
      await createTeacherQuestionTemplate(quizTemplateId.value, payload);
      if (props.isInModal) {
        emit('question-created'); // Emetti evento specifico per create in modale
      } else {
        // Naviga solo se stiamo creando FUORI dalla modale
        router.push({ name: 'quiz-template-edit', params: { id: quizTemplateId.value.toString() } });
      }
    } else {
        // Caso imprevisto (es. manca quizTemplateId o questionId in modifica)
        throw new Error("Stato non valido per il salvataggio.");
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
  if (props.isInModal) {
    emit('close-modal'); // Emetti evento per chiudere la modale
  } else {
    // Comportamento precedente: torna alla lista o al template
    if (quizTemplateId.value) {
      router.push({ name: 'quiz-template-edit', params: { id: quizTemplateId.value.toString() } });
    } else {
      router.push({ name: 'quiz-templates' }); // Fallback
    }
  }
};

</script>

<style scoped>
/* Rimuoviamo la maggior parte degli stili scoped, ora gestiti da Tailwind. */
/* Eventuali stili specifici che Tailwind non copre facilmente possono rimanere qui. */

/* Esempio: stile per l'indicatore di autosave se necessario */
/* .animate-pulse { ... } */
</style>