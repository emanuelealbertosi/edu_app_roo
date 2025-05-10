<template>
  <div class="fill-blank-question-editor">
    <h4>Domanda Fill in the Blank</h4>

    <!-- Textarea per il testo della domanda -->
    <div class="form-group">
      <label for="question-text">Testo della Domanda:</label>
      <textarea
        id="question-text"
        v-model="questionText"
        class="form-control"
        rows="3"
        placeholder="Inserisci il testo della domanda, usa tre o più underscore (es. ___) per indicare uno spazio vuoto."
        @input="parseQuestionText"
      ></textarea>
      <small class="form-text text-muted">
        Usa tre o più underscore (es. ___ , _____) per definire gli spazi da compilare.
      </small>
    </div>

    <!-- Pulsante per aprire la modale di definizione blanks -->
    <BaseButton
      v-if="questionText.trim() !== '' && detectedBlanks.length > 0"
      class="btn-primary mt-2"
      @click="openDefineBlanksModal"
    >
      Definisci Risposte per gli Spazi Vuoti ({{ detectedBlanks.length }})
    </BaseButton>
    <p v-else-if="questionText.trim() !== '' && detectedBlanks.length === 0" class="text-warning mt-2">
      Nessuno spazio vuoto (___) rilevato nel testo.
    </p>

    <!-- Modale per definire le risposte -->
    <BaseModal
      :show="isDefineBlanksModalOpen"
      title="Definisci Risposte per gli Spazi Vuoti"
      @close="closeDefineBlanksModal"
    >
      <div v-if="currentBlanks.length > 0">
        <p>Testo originale con segnaposto:</p>
        <div class="original-text-preview p-2 mb-3 bg-light border rounded" v-html="textWithPlaceholdersPreview"></div>

        <div v-for="(blank, index) in currentBlanks" :key="blank.id" class="mb-3 p-2 border rounded">
          <h5>Spazio Vuoto #{{ index + 1 }}</h5>
          <div class="form-group">
            <label :for="`blank-answers-${blank.id}`">Risposte corrette (una per riga):</label>
            <textarea
              :id="`blank-answers-${blank.id}`"
              v-model="blank.correctAnswersInput"
              class="form-control"
              rows="2"
              placeholder="blu&#10;azzurro"
              @focus="setActiveBlank(blank.id)"
              @blur="clearActiveBlank"
            ></textarea>
          </div>
        </div>

        <div class="form-group form-check mt-3">
          <input
            id="case-sensitive-checkbox"
            v-model="isCaseSensitive"
            type="checkbox"
            class="form-check-input"
          />
          <label class="form-check-label" for="case-sensitive-checkbox">
            Valutazione Case-Sensitive (sensibile a maiuscole/minuscole)
          </label>
        </div>
      </div>
      <p v-else>Nessuno spazio vuoto da configurare.</p>
      <template #footer>
        <BaseButton class="btn-secondary" @click="closeDefineBlanksModal">Annulla</BaseButton>
        <BaseButton class="btn-primary" @click="saveBlanksConfiguration">Salva Configurazione Spazi Vuoti</BaseButton>
      </template>
    </BaseModal>

    <!-- Riepilogo configurazione (debug) -->
    <div v-if="configuredMetadata" class="mt-3 p-3 bg-light border rounded">
        <h5>Configurazione Attuale (Metadata):</h5>
        <pre>{{ JSON.stringify(configuredMetadata, null, 2) }}</pre>
    </div>

  </div>
</template>

<script setup lang="ts">
console.log('[FillBlankQuestionEditor SCRIPT SETUP] Component script is executing - TEST CHANGE');
import { ref, watch, computed, onMounted } from 'vue';
import BaseButton from '@/components/common/BaseButton.vue'; // Assicurati che il percorso sia corretto
import BaseModal from '@/components/common/BaseModal.vue';   // Assicurati che il percorso sia corretto

interface Blank {
  id: string;
  correct_answers: string[];
  order: number;
}

export interface FillBlankMetadata { // Aggiunto export
  text_with_placeholders: string;
  blanks: Blank[];
  case_sensitive: boolean;
  points?: number; // Points potrebbero essere gestiti a livello superiore
}

interface DetectedBlank {
  originalText: string; // Es. "___" o "_____"
  order: number;
}

interface CurrentBlankConfig {
  id: string;
  order: number;
  correctAnswersInput: string; // Stringa multiriga per l'input dell'utente
}

const props = defineProps<{
  initialMetadata?: FillBlankMetadata | null;
  initialQuestionText?: string;
}>();

const emit = defineEmits<{
  (e: 'update:metadata', metadata: FillBlankMetadata | null): void
}>();

const questionText = ref(props.initialQuestionText || '');
const detectedBlanks = ref<DetectedBlank[]>([]);
const isDefineBlanksModalOpen = ref(false);
const currentBlanks = ref<CurrentBlankConfig[]>([]);
const isCaseSensitive = ref(false);
const configuredMetadata = ref<FillBlankMetadata | null>(null);
const activeBlankId = ref<string | null>(null); // Variabile per il blank attivo

const BLANK_PLACEHOLDER_REGEX = /_{3,}/g; // Regex per trovare 3 o più underscore

const parseQuestionText = () => {
  const matches = [...questionText.value.matchAll(BLANK_PLACEHOLDER_REGEX)];
  detectedBlanks.value = matches.map((match, index) => ({
    originalText: match[0],
    order: index,
  }));
  // Se il testo cambia e ci sono già metadati configurati, potremmo volerli invalidare o aggiornare.
  // Per ora, se il testo cambia, l'utente dovrà ricliccare "Definisci Risposte".
  // Potremmo anche resettare configuredMetadata.value = null se detectedBlanks cambia significativamente.
};

const textWithPlaceholdersPreview = computed(() => {
  if (!questionText.value) return '';
  let order = 0;
  return questionText.value.replace(BLANK_PLACEHOLDER_REGEX, () => {
    const currentBlankRenderId = `blank_${order}`;
    const placeholder = `{${currentBlankRenderId}}`;
    order++;
    const isActive = activeBlankId.value === currentBlankRenderId;
    const activeClass = isActive ? 'active-placeholder' : '';
    return `<strong class="text-primary placeholder-tag ${activeClass}">${placeholder}</strong>`;
  });
});

const generateTextWithPlaceholders = () => {
  if (!questionText.value) return '';
  let order = 0;
  return questionText.value.replace(BLANK_PLACEHOLDER_REGEX, () => `{blank_${order++}}`);
};

const openDefineBlanksModal = () => {
  if (detectedBlanks.value.length === 0) return;

  // Se ci sono metadati esistenti e il numero di blank corrisponde, pre-popoliamo
  if (
    configuredMetadata.value &&
    Array.isArray(configuredMetadata.value.blanks) &&
    configuredMetadata.value.blanks.length === detectedBlanks.value.length
  ) {
    currentBlanks.value = configuredMetadata.value.blanks.map(b => ({
      id: b.id,
      order: b.order,
      correctAnswersInput: b.correct_answers.join('\n'),
    }));
    isCaseSensitive.value = configuredMetadata.value.case_sensitive;
  } else {
    // Altrimenti, inizializziamo da zero basandoci sui detectedBlanks
    currentBlanks.value = detectedBlanks.value.map((blank, index) => ({
      id: `blank_${index}`,
      order: blank.order,
      correctAnswersInput: '',
    }));
    isCaseSensitive.value = false; // Default
  }
  isDefineBlanksModalOpen.value = true;
};

const closeDefineBlanksModal = () => {
  isDefineBlanksModalOpen.value = false;
  // Non salviamo modifiche parziali dalla modale se si annulla
};

const saveBlanksConfiguration = () => {
  const text_with_placeholders = generateTextWithPlaceholders();
  const blanks: Blank[] = currentBlanks.value.map(cb => ({
    id: cb.id,
    correct_answers: cb.correctAnswersInput.split('\n').map(s => s.trim()).filter(s => s !== ''),
    order: cb.order,
  }));

  const newMetadata: FillBlankMetadata = {
    text_with_placeholders,
    blanks,
    case_sensitive: isCaseSensitive.value,
  };
  // Se i punti sono gestiti qui, aggiungerli:
  if (props.initialMetadata?.points !== undefined) {
    newMetadata.points = props.initialMetadata.points;
  } else if (configuredMetadata.value?.points !== undefined) {
    newMetadata.points = configuredMetadata.value.points;
  } else {
    newMetadata.points = 1; // Default points
  }

  configuredMetadata.value = newMetadata;
  emit('update:metadata', newMetadata); // L'errore qui era un falso positivo del linter, la definizione di emit corretta lo risolve.
  closeDefineBlanksModal();
};

const setActiveBlank = (blankId: string) => {
  activeBlankId.value = blankId;
};

const clearActiveBlank = () => {
  activeBlankId.value = null;
};

watch(questionText, () => {
  parseQuestionText();
  // Se il testo della domanda cambia, la configurazione esistente dei blank potrebbe non essere più valida.
  // L'utente dovrà cliccare di nuovo "Definisci Risposte".
  // Potremmo resettare `configuredMetadata` se il numero di blank cambia.
  if (configuredMetadata.value && Array.isArray(configuredMetadata.value.blanks) && detectedBlanks.value.length !== configuredMetadata.value.blanks.length) {
      // console.warn("Il numero di blank rilevati è cambiato. La configurazione precedente potrebbe non essere valida.");
      // configuredMetadata.value = null; // Opzionale: resetta i metadati se il numero di blank cambia.
      // emit('update:metadata', null); // Se si resetta, emettere l'aggiornamento.
  }
});

onMounted(() => {
  console.log('[FillBlankQuestionEditor] Mounted. Props received:');
  console.log('[FillBlankQuestionEditor] initialQuestionText:', props.initialQuestionText);
  console.log('[FillBlankQuestionEditor] initialMetadata:', JSON.stringify(props.initialMetadata));
  if (props.initialQuestionText) {
    questionText.value = props.initialQuestionText;
  }

  if (props.initialMetadata) {
    configuredMetadata.value = JSON.parse(JSON.stringify(props.initialMetadata)); // Deep copy
    
    // Se initialQuestionText non è fornito MA abbiamo text_with_placeholders nei metadati,
    // proviamo a usarlo per popolare questionText. Questo è un fallback.
    if (!props.initialQuestionText && configuredMetadata.value && configuredMetadata.value.text_with_placeholders) {
        questionText.value = configuredMetadata.value.text_with_placeholders.replace(/\{blank_\d+\}/g, '___');
    }

    if (configuredMetadata.value) {
      isCaseSensitive.value = configuredMetadata.value.case_sensitive;
    }
    // parseQuestionText() sarà chiamato dal watch su questionText se è cambiato,
    // o esplicitamente se non è cambiato ma i metadati sono presenti.

    // Se il numero di blank rilevati dal testo (aggiornato da initialQuestionText o metadati)
    // corrisponde a quelli nei metadati, popoliamo currentBlanks per la modale.
    // È importante che parseQuestionText sia già stato eseguito o venga eseguito prima di questo.
    // Lo spostiamo dopo il parseQuestionText() iniziale.

  } else if (!props.initialQuestionText) {
    // Nessun metadato iniziale e nessun testo iniziale, l'utente inizia da zero
    questionText.value = '';
  }
  
  parseQuestionText(); // Assicura che i blank siano rilevati dal testo iniziale
  console.log('[FillBlankQuestionEditor] After initial parseQuestionText:');
  console.log('[FillBlankQuestionEditor] internal questionText.value:', questionText.value);
  console.log('[FillBlankQuestionEditor] detectedBlanks.value:', JSON.stringify(detectedBlanks.value));

  // Ora che parseQuestionText è stato chiamato con il testo corretto, possiamo confrontare.
  if (props.initialMetadata && configuredMetadata.value && Array.isArray(configuredMetadata.value.blanks) && detectedBlanks.value.length === configuredMetadata.value.blanks.length) {
      currentBlanks.value = configuredMetadata.value.blanks.map(b => ({
          id: b.id,
          order: b.order,
          correctAnswersInput: b.correct_answers.join('\n'),
      }));
  // } else if (props.initialMetadata && configuredMetadata.value) { // Temporaneamente commentato per debug HMR
  //   console.log('[FillBlankQuestionEditor ONMOUNTED] configuredMetadata.value exists. Checking blanks:', JSON.stringify(configuredMetadata.value.blanks));
  //   if (configuredMetadata.value.blanks && configuredMetadata.value.blanks.length > 0) {
  //     console.warn("Metadati iniziali forniti, ma il testo della domanda (o il numero di blank rilevati) non corrisponde. Il docente potrebbe dover riconfigurare.");
  //   } else {
  //     console.log('[FillBlankQuestionEditor ONMOUNTED] configuredMetadata.value.blanks is not a valid array or is empty.');
  //   }
  }
});

// Watch per sincronizzare questionText se la prop initialQuestionText cambia dall'esterno
watch(() => props.initialQuestionText, (newText) => {
  if (newText !== undefined && newText !== questionText.value) {
    questionText.value = newText;
    // parseQuestionText() verrà chiamato dal watcher su questionText
  }
});

// Esporre metodi o ref se questo componente deve essere controllato da un genitore via template ref
// defineExpose({
//   getMetadata: () => configuredMetadata.value,
//   validate: () => { /* logica di validazione */ }
// });

</script>

<style scoped>
.fill-blank-question-editor {
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.form-group {
  margin-bottom: 1rem;
}

.original-text-preview {
  white-space: pre-wrap; /* Per mantenere gli spazi e andare a capo */
  word-wrap: break-word;
}

/* Stili per evidenziare i placeholder nella preview */
.placeholder-tag {
  padding: 0.1em 0.3em;
  border-radius: 0.2em;
  transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out;
}

.original-text-preview strong.text-primary {
  font-weight: bold;
  color: #007bff; /* Blu primario di Bootstrap */
}

.original-text-preview strong.active-placeholder {
  background-color: #007bff; /* Blu primario di Bootstrap */
  color: white;
  font-weight: bold;
}
</style>