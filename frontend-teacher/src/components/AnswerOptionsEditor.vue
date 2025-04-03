<template>
  <div class="answer-options-editor">
    <h4>Opzioni di Risposta</h4>
    <div v-if="isLoading" class="loading">Caricamento opzioni...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <ul v-else class="options-list">
      <!-- Usiamo l'ID reale se disponibile, altrimenti il tempId come chiave -->
      <li v-for="(option, index) in localOptions" :key="option.id || option.tempId">
        <input
          type="text"
          v-model="option.text"
          placeholder="Testo opzione"
          @change="handleOptionChange(index)"
          class="border rounded px-2 py-1 flex-grow"
        />
        <input
          :type="allowMultipleCorrect ? 'checkbox' : 'radio'"
          :name="'is_correct_' + questionId"
          :checked="option.is_correct"
          @change="toggleCorrect(index)"
          :disabled="!option.text"
          class="ml-2 cursor-pointer"
        />
        <label class="ml-1 mr-3 whitespace-nowrap">Corretta</label>
        <input
            type="number"
            v-model.number="option.order"
            min="0"
            placeholder="Ordine"
            class="order-input border rounded px-2 py-1 w-16"
            @change="handleOptionChange(index)"
        />
        <!-- Stile Tailwind per bottone Rimuovi -->
        <button
            type="button"
            @click="removeOption(index)"
            class="delete-button bg-red-500 hover:bg-red-700 text-white text-xs font-bold py-1 px-2 rounded ml-2"
        >
            Rimuovi
        </button>
      </li>
    </ul>
    <!-- Stile Tailwind per bottone Aggiungi -->
    <button
        type="button"
        @click="addOption"
        class="add-button bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-3 rounded mt-3"
    >
        Aggiungi Opzione
    </button>
    <!-- Bottone Salva Modifiche Opzioni Rimosso -->
    <!-- Messaggio di stato salvataggio -->
     <span v-if="isSaving" class="ml-4 text-sm italic text-gray-600">Salvataggio...</span>
     <span v-if="saveError" class="ml-4 text-sm font-semibold text-red-600">Errore: {{ saveError }}</span>
     <span v-if="saveSuccess" class="ml-4 text-sm font-semibold text-green-600">Opzioni salvate!</span>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, nextTick, computed, reactive } from 'vue'; // Aggiunto reactive
import type { AnswerOption, AnswerOptionPayload } from '@/api/questions';
import { createAnswerOption, updateAnswerOption, deleteAnswerOptionApi } from '@/api/questions';
import { debounce } from 'lodash-es'; // Importa debounce

// Interfaccia interna per gestire ID temporanei e stato modificato
interface LocalAnswerOption extends Partial<AnswerOption> {
  text: string;
  is_correct: boolean;
  order: number;
  tempId?: string; // Per nuove opzioni non ancora salvate
  isNew?: boolean;
  isChanged?: boolean;
  isDeleted?: boolean;
}

const props = defineProps<{
  quizId: number;
  questionId: number;
  initialOptions: AnswerOption[];
  questionType: string; // Per determinare se permettere selezione multipla
}>();

const emit = defineEmits(['options-saved', 'error']);

// Usiamo reactive per permettere modifiche dirette e reattività
const localOptions = ref<LocalAnswerOption[]>([]);
const isLoading = ref(false); // Potrebbe non servire se le opzioni sono caricate dal padre
const error = ref<string | null>(null); // Errore caricamento iniziale (se applicabile)
const saveError = ref<string | null>(null); // Errore durante il salvataggio
const isSaving = ref(false);
const saveSuccess = ref(false); // Flag per messaggio successo
// hasChanges non è più necessario per abilitare il bottone, ma utile internamente
// const hasChanges = ref(false);

const allowMultipleCorrect = computed(() => props.questionType === 'MC_MULTI');

// Funzione per inizializzare o resettare le opzioni locali
const initializeOptions = (options: AnswerOption[]) => {
    // Filtra le opzioni già marcate come eliminate se presenti nello stato precedente
    const currentNonDeleted = localOptions.value.filter(opt => !opt.isDeleted).map(opt => opt.id);
    localOptions.value = options
        .filter(opt => currentNonDeleted.includes(opt.id) || !localOptions.value.some(lOpt => lOpt.id === opt.id)) // Mantieni solo quelle non marcate per eliminazione
        .map(opt => reactive({ // Usa reactive per ogni opzione
            ...opt,
            isChanged: false,
            isNew: false,
            isDeleted: false
        }));
    // hasChanges.value = false; // Non più necessario per il bottone
};

// Guarda le opzioni iniziali passate come prop
watch(() => props.initialOptions, (newOptions) => {
    initializeOptions(newOptions);
}, { immediate: true, deep: true }); // immediate per caricare subito, deep per array/oggetti

// Funzione per generare ID temporanei
const generateTempId = () => `temp_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

const addOption = () => {
  const newOrder = localOptions.value.length > 0 ? Math.max(...localOptions.value.map(o => o.order)) + 1 : 0;
  const newOption = reactive<LocalAnswerOption>({ // Crea come oggetto reactive
    tempId: generateTempId(),
    text: '',
    is_correct: false,
    order: newOrder,
    isNew: true,
    isChanged: true, // Marcata come modificata perché nuova
    isDeleted: false,
  });
  localOptions.value.push(newOption);
  // Non chiamiamo saveOptions qui, aspettiamo che l'utente inserisca il testo
};

const removeOption = async (index: number) => {
  const option = localOptions.value[index];
  if (option.isNew) {
    // Se è una nuova opzione non salvata, rimuovila direttamente dall'array locale
    localOptions.value.splice(index, 1);
  } else if (option.id) {
    // Se è un'opzione esistente, marcala per l'eliminazione e chiamiamo l'API
    option.isDeleted = true; // Marca logicamente
    await saveOptions(); // Salva le modifiche (che includono l'eliminazione)
  }
};

const toggleCorrect = (index: number) => {
  if (!allowMultipleCorrect.value) {
    // Radio button logic: Set only the clicked one to true
    localOptions.value.forEach((opt, i) => {
      opt.is_correct = (i === index);
      if (i !== index) markAsChanged(i); // Marca gli altri come cambiati se il loro stato è cambiato
    });
  } else {
    // Checkbox logic: Toggle the clicked one
    localOptions.value[index].is_correct = !localOptions.value[index].is_correct;
  }
  markAsChanged(index); // Marca quella cliccata come cambiata
  debouncedSaveOptions(); // Salva automaticamente con debounce
};

const markAsChanged = (index: number) => {
    if (index < localOptions.value.length && !localOptions.value[index].isNew) { // Controllo esistenza indice
        localOptions.value[index].isChanged = true;
    }
    // hasChanges.value = true; // Non più necessario per il bottone
};

// Funzione chiamata quando testo o ordine cambiano
const handleOptionChange = (index: number) => {
    markAsChanged(index);
    debouncedSaveOptions(); // Salva automaticamente con debounce
};

// Funzione di salvataggio con debounce per evitare chiamate API troppo frequenti
const debouncedSaveOptions = debounce(async () => {
    await saveOptions();
}, 1000); // Aspetta 1 secondo dopo l'ultima modifica prima di salvare

const saveOptions = async () => {
  if (isSaving.value) return; // Evita salvataggi concorrenti

  isSaving.value = true;
  saveError.value = null;
  saveSuccess.value = false;
  const promises = [];
  const optionsToKeepLocally: LocalAnswerOption[] = []; // Opzioni da mantenere dopo il salvataggio

  // Filtra prima le opzioni valide (con testo)
  const validOptions = localOptions.value.filter(opt => opt.text.trim() || opt.isDeleted);

  for (const option of validOptions) {
    // Se è marcata per eliminazione e ha un ID, eliminala
    if (option.isDeleted && option.id) {
      promises.push(
          deleteAnswerOptionApi(props.quizId, props.questionId, option.id)
            .catch(err => { // Cattura errore specifico per questa promise
                console.error(`Errore eliminazione opzione ${option.id}:`, err);
                throw err; // Rilancia per bloccare Promise.all
            })
      );
      // Non aggiungerla a optionsToKeepLocally
    }
    // Se è nuova, non eliminata e ha testo, creala
    else if (option.isNew && !option.isDeleted && option.text.trim()) {
      const payload: AnswerOptionPayload = { text: option.text, is_correct: option.is_correct, order: option.order };
      promises.push(
          createAnswerOption(props.quizId, props.questionId, payload)
            .then(savedOption => {
                // Aggiorna l'opzione locale con i dati reali (ID) e resetta stati
                Object.assign(option, { ...savedOption, isNew: false, isChanged: false, tempId: undefined });
                optionsToKeepLocally.push(option); // Mantienila
            })
            .catch(err => {
                console.error(`Errore creazione opzione '${option.text}':`, err);
                optionsToKeepLocally.push(option); // Mantieni l'opzione locale anche se fallisce la creazione per ora
                throw err;
            })
      );
    }
    // Se è cambiata, ha un ID, non è eliminata e ha testo, aggiornala
    else if (option.isChanged && option.id && !option.isDeleted && option.text.trim()) {
      const payload: AnswerOptionPayload = { text: option.text, is_correct: option.is_correct, order: option.order };
      promises.push(
          updateAnswerOption(props.quizId, props.questionId, option.id, payload)
            .then(savedOption => {
                // Aggiorna l'opzione locale e resetta stato
                Object.assign(option, { ...savedOption, isChanged: false });
                optionsToKeepLocally.push(option); // Mantienila
            })
            .catch(err => {
                console.error(`Errore aggiornamento opzione ${option.id}:`, err);
                optionsToKeepLocally.push(option); // Mantieni l'opzione locale
                throw err;
            })
      );
    }
    // Se non è cambiata, non è nuova, non è eliminata, mantienila
    else if (!option.isNew && !option.isChanged && !option.isDeleted && option.id) {
        optionsToKeepLocally.push(option);
    }
    // Ignora opzioni nuove senza testo o marcate per eliminazione senza ID
  }


  try {
    await Promise.all(promises);
    // Riordina le opzioni rimaste per sicurezza
    optionsToKeepLocally.sort((a, b) => a.order - b.order);
    // Aggiorna l'array locale solo con le opzioni mantenute/aggiornate/create
    localOptions.value = optionsToKeepLocally.map(opt => reactive(opt)); // Assicura reattività
    emit('options-saved', localOptions.value.filter(opt => !!opt.id)); // Emetti solo quelle con ID
    console.log("Opzioni salvate con successo.");
    saveSuccess.value = true; // Mostra messaggio successo
    setTimeout(() => saveSuccess.value = false, 2000); // Nascondi dopo 2 sec
  } catch (err: any) {
    console.error("Errore durante il salvataggio delle opzioni:", err);
    saveError.value = `Errore salvataggio opzioni: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    emit('error', saveError.value); // Notifica il padre dell'errore
     // Non resettare le opzioni locali in caso di errore per permettere correzione
  } finally {
    isSaving.value = false;
  }
};

</script>

<style scoped>
.answer-options-editor {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px dashed #ccc;
}

.options-list {
  list-style: none;
  padding: 0;
}

.options-list li {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 10px; /* Spazio tra gli elementi */
}

/* Stili input gestiti da Tailwind */
/* .options-list input[type="text"] { ... } */
/* .options-list input[type="radio"], .options-list input[type="checkbox"] { ... } */
/* .options-list label { ... } */
/* .options-list .order-input { ... } */

/* Stile bottone Rimuovi gestito da Tailwind */
/* .options-list button.delete { ... } */
/* .options-list button.delete:hover { ... } */

/* Stile bottone Aggiungi gestito da Tailwind */
/* button { ... } */

.error-message {
  color: red;
  margin-top: 10px;
  font-size: 0.9em;
}
.loading {
    font-style: italic;
    color: #666;
}
</style>