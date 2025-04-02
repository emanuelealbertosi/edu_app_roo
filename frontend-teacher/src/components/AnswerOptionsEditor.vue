<template>
  <div class="answer-options-editor">
    <h4>Opzioni di Risposta</h4>
    <div v-if="isLoading" class="loading">Caricamento opzioni...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <ul v-else class="options-list">
      <li v-for="(option, index) in localOptions" :key="option.tempId || option.id">
        <input
          type="text"
          v-model="option.text"
          placeholder="Testo opzione"
          @change="markAsChanged(index)"
        />
        <input
          :type="allowMultipleCorrect ? 'checkbox' : 'radio'"
          :name="'is_correct_' + questionId"
          :checked="option.is_correct"
          @change="toggleCorrect(index)"
          :disabled="!option.text"
        />
        <label>Corretta</label>
        <input
            type="number"
            v-model.number="option.order"
            min="0"
            placeholder="Ordine"
            class="order-input"
            @change="markAsChanged(index)"
        />
        <button type="button" @click="removeOption(index)" class="delete">Rimuovi</button>
      </li>
    </ul>
    <button type="button" @click="addOption">Aggiungi Opzione</button>
    <button type="button" @click="saveOptions" :disabled="!hasChanges || isSaving">
      {{ isSaving ? 'Salvataggio Opzioni...' : 'Salva Modifiche Opzioni' }}
    </button>
    <div v-if="saveError" class="error-message">{{ saveError }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, nextTick, computed } from 'vue'; // Aggiunto import computed
import type { AnswerOption, AnswerOptionPayload } from '@/api/questions';
import { createAnswerOption, updateAnswerOption, deleteAnswerOptionApi } from '@/api/questions';

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

const localOptions = ref<LocalAnswerOption[]>([]);
const isLoading = ref(false); // Potrebbe non servire se le opzioni sono caricate dal padre
const error = ref<string | null>(null); // Errore caricamento iniziale (se applicabile)
const saveError = ref<string | null>(null); // Errore durante il salvataggio
const isSaving = ref(false);
const hasChanges = ref(false);

const allowMultipleCorrect = computed(() => props.questionType === 'MC_MULTI');

// Funzione per inizializzare o resettare le opzioni locali
const initializeOptions = (options: AnswerOption[]) => {
    localOptions.value = options.map(opt => ({ ...opt, isChanged: false, isNew: false, isDeleted: false }));
    hasChanges.value = false; // Resetta lo stato modificato
};

// Guarda le opzioni iniziali passate come prop
watch(() => props.initialOptions, (newOptions) => {
    initializeOptions(newOptions);
}, { immediate: true, deep: true }); // immediate per caricare subito, deep per array/oggetti

// Funzione per generare ID temporanei
const generateTempId = () => `temp_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

const addOption = () => {
  const newOrder = localOptions.value.length > 0 ? Math.max(...localOptions.value.map(o => o.order)) + 1 : 0;
  localOptions.value.push({
    tempId: generateTempId(),
    text: '',
    is_correct: false,
    order: newOrder,
    isNew: true,
    isChanged: true, // Marcata come modificata perché nuova
    isDeleted: false,
  });
  hasChanges.value = true;
};

const removeOption = (index: number) => {
  const option = localOptions.value[index];
  if (option.isNew) {
    // Se è una nuova opzione non salvata, rimuovila direttamente
    localOptions.value.splice(index, 1);
  } else {
    // Altrimenti, marcala per l'eliminazione
    option.isDeleted = true;
  }
  hasChanges.value = true;
  // Rimuovi visivamente l'opzione marcata per l'eliminazione
  // Questo è opzionale, potresti volerla mostrare barrata
  localOptions.value = localOptions.value.filter(opt => !opt.isDeleted);
};

const toggleCorrect = (index: number) => {
  let changed = false; // Flag per tracciare se qualcosa è cambiato
  if (!allowMultipleCorrect.value) {
    // Radio button logic: Set only the clicked one to true
    localOptions.value.forEach((opt, i) => {
      const shouldBeCorrect = (i === index);
      if (opt.is_correct !== shouldBeCorrect) { // Controlla se lo stato cambia effettivamente
          opt.is_correct = shouldBeCorrect;
          if (!opt.isNew) { // Marca le opzioni esistenti come modificate se il loro stato è cambiato
              opt.isChanged = true;
              changed = true;
          } else if (shouldBeCorrect) { // Marca una nuova opzione come modificata solo se diventa true
              changed = true; // Impostare un nuovo radio a true è una modifica
          }
      }
    });
    // Assicura che l'opzione cliccata (se esistente) sia marcata come modificata
    // per includerla nel ciclo di salvataggio, anche se il suo stato booleano non è cambiato
    // (potrebbe essere già stata 'true' e l'utente ci ha cliccato di nuovo)
    if (!localOptions.value[index].isNew) {
        markAsChanged(index); // Usa la funzione helper per marcare e impostare hasChanges
    } else if (changed) {
        // Se una nuova opzione è diventata true, assicurati che hasChanges sia true
        hasChanges.value = true;
    }

  } else {
    // Checkbox logic: Toggle the clicked one
    localOptions.value[index].is_correct = !localOptions.value[index].is_correct;
    markAsChanged(index); // Marca questa specifica come modificata
  }
};

const markAsChanged = (index: number) => {
    if (!localOptions.value[index].isNew) { // Non marcare come 'changed' se è già 'new'
        localOptions.value[index].isChanged = true;
    }
    hasChanges.value = true;
};

const saveOptions = async () => {
  isSaving.value = true;
  saveError.value = null;
  const promises = [];
  const finalOptions: AnswerOption[] = []; // Lista delle opzioni dopo il salvataggio

  for (const option of localOptions.value) {
    const payload: AnswerOptionPayload = {
        text: option.text,
        is_correct: option.is_correct,
        order: option.order,
    };

    if (option.isDeleted && option.id) {
      // Elimina opzione esistente
      promises.push(deleteAnswerOptionApi(props.quizId, props.questionId, option.id));
    } else if (option.isNew && !option.isDeleted) {
      // Crea nuova opzione
      promises.push(
          createAnswerOption(props.quizId, props.questionId, payload)
            .then(savedOption => finalOptions.push(savedOption)) // Aggiungi l'opzione salvata
      );
    } else if (option.isChanged && option.id && !option.isDeleted) {
      // Aggiorna opzione esistente
      promises.push(
          updateAnswerOption(props.quizId, props.questionId, option.id, payload)
            .then(savedOption => finalOptions.push(savedOption)) // Aggiungi l'opzione salvata
      );
    } else if (option.id && !option.isDeleted) {
        // Opzione non modificata, aggiungila alla lista finale
        finalOptions.push(option as AnswerOption);
    }
  }

  // Gestione opzioni marcate per eliminazione ma non ancora processate (se non filtrate prima)
  const optionsToDelete = props.initialOptions.filter(initialOpt =>
    localOptions.value.find(localOpt => localOpt.id === initialOpt.id && localOpt.isDeleted)
  );
  for (const option of optionsToDelete) {
      if (option.id) {
          promises.push(deleteAnswerOptionApi(props.quizId, props.questionId, option.id));
      }
  }


  try {
    await Promise.all(promises);
    // Riordina finalOptions per sicurezza, anche se l'API dovrebbe restituirle ordinate
    finalOptions.sort((a, b) => a.order - b.order);
    // Emetti evento con le opzioni aggiornate (o ricarica dal padre)
    emit('options-saved', finalOptions);
    // Resetta lo stato locale basandosi sulle opzioni salvate
    initializeOptions(finalOptions);
    console.log("Opzioni salvate con successo.");
  } catch (err: any) {
    console.error("Errore durante il salvataggio delle opzioni:", err);
    saveError.value = `Errore salvataggio opzioni: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    emit('error', saveError.value); // Notifica il padre dell'errore
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

.options-list input[type="text"] {
  flex-grow: 1; /* Occupa lo spazio rimanente */
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 3px;
}

.options-list input[type="radio"],
.options-list input[type="checkbox"] {
  margin-left: 5px;
  cursor: pointer;
}
.options-list label {
    margin-left: -5px; /* Avvicina label a checkbox/radio */
    margin-right: 10px;
    white-space: nowrap;
}

.options-list .order-input {
    width: 60px; /* Larghezza fissa per ordine */
    padding: 6px;
    border: 1px solid #ccc;
    border-radius: 3px;
}


.options-list button.delete {
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 3px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 0.8em;
}
.options-list button.delete:hover {
    background-color: #d32f2f;
}


button {
  margin-top: 10px;
  padding: 6px 12px;
  cursor: pointer;
  margin-right: 10px;
}

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