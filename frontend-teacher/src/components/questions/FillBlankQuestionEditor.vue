<template>
  <div class="fill-blank-question-editor p-4 border border-neutral-DEFAULT rounded-lg bg-white shadow">
    <h4 class="text-lg font-semibold mb-3 text-neutral-darkest">Configurazione Domanda "Fill in the Blank"</h4>

    <!-- Textarea per il testo della domanda -->
    <div class="form-group mb-4">
      <label for="question-text" class="block text-sm font-medium text-neutral-darker mb-1">Testo della Domanda:</label>
      <textarea
        id="question-text"
        v-model="questionText"
        class="form-input shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border border-gray-400 rounded-md p-2 min-h-[100px]"
        rows="4"
        placeholder="Inserisci il testo della domanda, usa tre o più underscore (es. ___) per indicare uno spazio vuoto."
        @input="parseQuestionText"
      ></textarea>
      <ul class="form-help-text text-xs text-neutral-dark mt-2 list-disc list-inside">
        <li>Usa tre o più underscore (es. <code>___</code> , <code>_____</code>) per definire gli spazi da compilare.</li>
        <li>Ogni serie di underscore consecutivi verrà trattata come un singolo spazio vuoto.</li>
      </ul>
    </div>

    <!-- Pulsante per aprire la modale di definizione blanks -->
    <BaseButton
      v-if="questionText.trim() !== '' && detectedBlanks.length > 0"
      variant="primary"
      class="mt-2"
      @click="openDefineBlanksModal"
    >
      Definisci Risposte per gli Spazi Vuoti ({{ detectedBlanks.length }})
    </BaseButton>
    <p v-else-if="questionText.trim() !== '' && detectedBlanks.length === 0" class="text-warning-dark bg-warning/10 p-2 rounded-md text-sm mt-2">
      Nessuno spazio vuoto (<code>___</code>) rilevato nel testo. Assicurati di usare almeno tre underscore consecutivi.
    </p>

    <!-- Modale per definire le risposte -->
    <BaseModal
      :show="isDefineBlanksModalOpen"
      title="Definisci Risposte per gli Spazi Vuoti"
      @close="closeDefineBlanksModal"
      modal-size="xl"
    >
      <!-- Aggiunto padding p-6 al contenitore del corpo della modale -->
      <div v-if="currentBlanks.length > 0" class="space-y-5 p-6">
        <div>
          <p class="text-sm font-medium text-neutral-darker mb-1">Testo originale con segnaposto evidenziati:</p>
          <div class="original-text-preview p-3 mb-4 bg-neutral-lightest border border-gray-400 rounded-md text-sm" v-html="textWithPlaceholdersPreview"></div>
        </div>

        <div v-for="(blank, index) in currentBlanks" :key="blank.id" class="mb-4 p-4 border border-neutral-light rounded-lg bg-white shadow-sm">
          <h5 class="text-md font-semibold text-primary-dark mb-2">Spazio Vuoto #{{ index + 1 }}</h5>
          <div class="form-group">
            <label :for="`blank-answers-${blank.id}`" class="block text-sm font-medium text-neutral-darker mb-1">Risposte corrette (una per riga):</label>
            <textarea
              :id="`blank-answers-${blank.id}`"
              v-model="blank.correctAnswersInput"
              class="form-input shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border border-gray-400 rounded-md p-2 min-h-[60px]"
              rows="3"
              placeholder="Esempio:&#10;blu&#10;azzurro&#10;celeste"
              @focus="setActiveBlank(blank.id)"
              @blur="clearActiveBlank"
            ></textarea>
            <p class="form-help-text text-xs text-neutral-dark mt-1">Inserisci ogni possibile risposta corretta su una nuova riga.</p>
          </div>
        </div>

        <div class="form-group flex items-center mt-4">
          <input
            id="case-sensitive-checkbox"
            v-model="isCaseSensitive"
            type="checkbox"
            class="h-4 w-4 text-primary focus:ring-primary border border-gray-400 rounded"
          />
          <label for="case-sensitive-checkbox" class="ml-2 block text-sm font-medium text-neutral-darker">
            Valutazione Case-Sensitive (sensibile a maiuscole/minuscole)
          </label>
        </div>
      </div>
      <!-- Aggiunto padding p-6 anche al messaggio di fallback -->
      <p v-else class="text-neutral-dark p-6">Nessuno spazio vuoto da configurare.</p>
      <template #footer>
        <BaseButton variant="secondary" @click="closeDefineBlanksModal">Annulla</BaseButton>
        <BaseButton variant="primary" @click="saveBlanksConfiguration">Salva Configurazione Spazi Vuoti</BaseButton>
      </template>
    </BaseModal>

    <!-- Riepilogo configurazione -->
    <div v-if="configuredMetadata" class="mt-6 p-4 bg-neutral-lightest border border-neutral-DEFAULT rounded-lg">
        <h5 class="text-md font-semibold text-neutral-darkest mb-2">Configurazione Attuale Salvata:</h5>
        <div class="text-sm space-y-1">
            <p><strong>Testo con Segnaposto:</strong> <code class="bg-neutral-light p-1 rounded">{{ formattedTextWithPlaceholdersForDisplay }}</code></p>
            <p><strong>Case Sensitive:</strong> {{ configuredMetadata.case_sensitive ? 'Sì' : 'No' }}</p>
            <div v-if="configuredMetadata.blanks && configuredMetadata.blanks.length > 0">
                <strong>Spazi Vuoti Definiti:</strong>
                <ul class="list-disc list-inside ml-4 mt-1">
                    <li v-for="blank in configuredMetadata.blanks" :key="blank.id">
                        <strong>Spazio Vuoto #{{ blank.order + 1 }}</strong>:
                        <span v-if="blank.correct_answers.length > 0" class="italic text-success-dark">"{{ blank.correct_answers.join('", "') }}"</span>
                        <span v-else class="italic text-error-dark">(Nessuna risposta corretta definita)</span>
                    </li>
                </ul>
            </div>
            <p v-else class="italic text-neutral-dark">Nessuno spazio vuoto configurato nei metadati.</p>
        </div>
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
  (e: 'update:question-details', payload: { text: string, metadata: FillBlankMetadata } | null): void
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
    order++; // Incrementa prima per avere un numero 1-based
    const placeholderText = `[Spazio Vuoto #${order}]`;
    // L'ID per l'evidenziazione può rimanere basato su blank_N se la logica di setActiveBlank lo richiede,
    // oppure possiamo basarlo sull'ordine se più semplice. Per ora, manteniamo la logica di evidenziazione
    // basata su blank.id che è 'blank_0', 'blank_1', etc.
    const currentBlankInternalId = `blank_${order - 1}`; // ID interno per l'highlight
    const isActive = activeBlankId.value === currentBlankInternalId;
    const activeClass = isActive ? 'active-placeholder' : '';
    return `<strong class="placeholder-tag ${activeClass}">${placeholderText}</strong>`;
  });
});

const generateTextWithPlaceholders = () => {
  if (!questionText.value) return '';
  let order = 0;
  return questionText.value.replace(BLANK_PLACEHOLDER_REGEX, () => `[Spazio Vuoto #${++order}]`);
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
  // Emetti sia il testo aggiornato che i metadati
  emit('update:question-details', { text: questionText.value, metadata: newMetadata });
  closeDefineBlanksModal();
};

const setActiveBlank = (blankId: string) => {
  activeBlankId.value = blankId;
};

const clearActiveBlank = () => {
  activeBlankId.value = null;
};

// Proprietà calcolata per formattare text_with_placeholders per la visualizzazione
const formattedTextWithPlaceholdersForDisplay = computed(() => {
  if (configuredMetadata.value?.text_with_placeholders) {
    let text = configuredMetadata.value.text_with_placeholders;
    // Controlla se usa il vecchio formato {blank_X}
    if (/\{blank_\d+\}/.test(text)) {
      let order = 0;
      text = text.replace(/\{blank_(\d+)\}/g, () => {
        order++;
        return `[Spazio Vuoto #${order}]`;
      });
    }
    return text;
  }
  return '';
});

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
/* Gli stili principali sono ora gestiti da classi Tailwind nel template.
   Possiamo mantenere stili specifici qui se necessario. */

.original-text-preview :deep(strong.placeholder-tag) {
  /* :deep per applicare stili a contenuto generato da v-html */
  padding: 0.1em 0.3em;
  border-radius: 0.2em;
  font-weight: bold;
  transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out;
  /* Usa le variabili CSS di Tailwind se definite, o colori diretti */
  background-color: theme('colors.primary.light'); /* Corretto da lightest a light */
  color: theme('colors.primary.dark');
  border: 1px dashed theme('colors.primary.DEFAULT');
}

.original-text-preview :deep(strong.active-placeholder) {
  background-color: theme('colors.primary.DEFAULT');
  color: theme('colors.white');
}

/* Stile per il testo con `code` inline */
code {
  background-color: theme('colors.neutral.light');
  padding: 0.1em 0.3em;
  border-radius: 0.2em;
  font-family: theme('fontFamily.mono');
  font-size: theme('fontSize.xs');
}
</style>