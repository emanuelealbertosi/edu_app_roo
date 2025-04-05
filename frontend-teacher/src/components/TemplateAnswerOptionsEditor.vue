<template>
  <div class="template-answer-options-editor">
    <h3>Opzioni Risposta Template</h3>

    <div v-if="isLoading" class="loading small">Caricamento opzioni...</div>
    <div v-else-if="error" class="error-message small">{{ error }}</div>

    <ul v-else-if="options.length > 0" class="options-list">
      <li v-for="(option, index) in options" :key="option.id || `new-${index}`"> <!-- Usa index per chiavi temporanee -->
        <input type="text" v-model="option.text" placeholder="Testo opzione" class="option-text-input" @blur="saveOption(option)" /> <!-- Salva su blur -->
        <label class="is-correct-label">
          <input
            type="checkbox"
            v-model="option.is_correct"
            :name="`correct_${questionTemplateId}`"
            v-if="questionType === 'MC_MULTI'"
            @change="saveOption(option)" /> <!-- Spostato /> qui -->
           <!-- Rimossa riga 18 vuota -->
          <input
            type="radio"
            :value="option.id"
            v-model="correctOptionId"
            :name="`correct_radio_${questionTemplateId}`"
            v-if="questionType === 'MC_SINGLE' || questionType === 'TF'" /> <!-- Spostato /> qui -->
          Corretta?
          <!-- Rimossa riga 26 vuota -->
        </label>
        <!-- Rimosso pulsante Salva per opzione singola -->
        <button @click="deleteOption(option.id)" type="button" class="delete-option-btn" :disabled="!option.id">Elimina</button> <!-- Disabilita se nuova -->
      </li>
    </ul>
    <p v-else>Nessuna opzione definita.</p>

    <!-- Form Aggiunta Nuova Opzione -->
    <div class="add-option-form">
      <input type="text" v-model="newOptionText" placeholder="Nuovo testo opzione" />
      <button @click="addOption" type="button" :disabled="!newOptionText.trim() || isAdding">
        {{ isAdding ? 'Aggiungo...' : 'Aggiungi Opzione' }}
      </button>
    </div>
     <div v-if="addError" class="error-message small">{{ addError }}</div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineProps, reactive, watch, computed } from 'vue';
import {
    fetchTeacherAnswerOptionTemplates, createTeacherAnswerOptionTemplate,
    updateTeacherAnswerOptionTemplate, deleteTeacherAnswerOptionTemplate,
    type AnswerOptionTemplate, type AnswerOptionTemplatePayload
} from '@/api/templateQuestions';

const props = defineProps<{
  quizTemplateId: number;
  questionTemplateId: number;
  questionType: string; // Necessario per gestire radio/checkbox
}>();

const options = ref<AnswerOptionTemplate[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const newOptionText = ref('');
const isAdding = ref(false);
const addError = ref<string | null>(null);
// Rimosso isSaving per opzione singola, il salvataggio è automatico
// const isSaving = reactive<Record<number, boolean>>({});

// Per radio button (MC_SINGLE, TF)
const correctOptionId = ref<number | null>(null);

// Carica le opzioni quando il componente viene montato o l'ID della domanda cambia
onMounted(loadOptions);
watch(() => props.questionTemplateId, loadOptions);

// Watcher per aggiornare correctOptionId quando le opzioni cambiano (es. dopo caricamento)
watch(options, (newOptions) => {
    if (props.questionType === 'MC_SINGLE' || props.questionType === 'TF') {
        const correctOption = newOptions.find(opt => opt.is_correct);
        correctOptionId.value = correctOption ? correctOption.id : null;
    }
}, { immediate: true }); // Esegui subito dopo il mount

// Watcher per aggiornare is_correct quando correctOptionId cambia (per radio)
watch(correctOptionId, (newCorrectId) => {
    if (props.questionType === 'MC_SINGLE' || props.questionType === 'TF') {
        options.value.forEach(opt => {
            const shouldBeCorrect = opt.id === newCorrectId;
            if (opt.is_correct !== shouldBeCorrect) {
                opt.is_correct = shouldBeCorrect;
                // Salva automaticamente l'opzione modificata (o aggiungi un pulsante "Salva tutte")
                if (opt.id) { // Salva solo se l'opzione esiste già
                   saveOption(opt);
                }
            }
        });
    }
});


async function loadOptions() {
  if (!props.quizTemplateId || !props.questionTemplateId) return;
  isLoading.value = true;
  error.value = null;
  try {
    options.value = await fetchTeacherAnswerOptionTemplates(props.quizTemplateId, props.questionTemplateId);
  } catch (err: any) {
    console.error("Errore caricamento opzioni template:", err);
    error.value = "Errore caricamento opzioni.";
  } finally {
    isLoading.value = false;
  }
}

async function addOption() {
  if (!newOptionText.value.trim() || !props.quizTemplateId || !props.questionTemplateId) return;
  isAdding.value = true;
  addError.value = null;

  const payload: AnswerOptionTemplatePayload = {
    text: newOptionText.value,
    is_correct: false // Default a false
  };

  try {
    const newOption = await createTeacherAnswerOptionTemplate(props.quizTemplateId, props.questionTemplateId, payload);
    options.value.push(newOption); // Aggiungi alla lista locale
    newOptionText.value = ''; // Pulisci input
  } catch (err: any) {
    console.error("Errore aggiunta opzione template:", err);
    addError.value = `Errore aggiunta: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
  } finally {
    isAdding.value = false;
  }
}

async function saveOption(option: AnswerOptionTemplate) {
  if (!option.id || !props.quizTemplateId || !props.questionTemplateId) return; // Salva solo opzioni esistenti

  // isSaving[option.id] = true; // Rimosso
  // error.value = null; // L'errore viene gestito, ma non c'è più uno stato di saving per opzione

  const payload: Partial<AnswerOptionTemplatePayload> = {
    text: option.text,
    is_correct: option.is_correct
  };

  try {
    const updatedOption = await updateTeacherAnswerOptionTemplate(
        props.quizTemplateId,
        props.questionTemplateId,
        option.id,
        payload
    );
    // Aggiorna l'opzione nella lista locale (opzionale, v-model dovrebbe bastare)
    const index = options.value.findIndex(o => o.id === option.id);
    if (index !== -1) {
        options.value[index] = { ...options.value[index], ...updatedOption }; // Aggiorna con dati dal server
    }
     // Aggiorna correctOptionId se necessario (per radio button)
     if ((props.questionType === 'MC_SINGLE' || props.questionType === 'TF') && updatedOption.is_correct) {
         correctOptionId.value = updatedOption.id;
     }

  } catch (err: any) {
    console.error(`Errore salvataggio opzione template ${option.id}:`, err);
    error.value = `Errore salvataggio opzione ${option.id}: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    // Potresti voler ripristinare lo stato precedente dell'opzione qui
    await loadOptions(); // Ricarica per sicurezza
  } finally {
    // isSaving[option.id] = false; // Rimosso
  }
}


async function deleteOption(optionId: number | undefined) {
  if (!optionId || !props.quizTemplateId || !props.questionTemplateId) return; // Non eliminare opzioni non salvate

  if (!confirm(`Sei sicuro di voler eliminare questa opzione template?`)) {
    return;
  }
  addError.value = null; // Pulisce errori precedenti

  try {
    await deleteTeacherAnswerOptionTemplate(props.quizTemplateId, props.questionTemplateId, optionId);
    options.value = options.value.filter(opt => opt.id !== optionId); // Rimuovi dalla lista locale
  } catch (err: any) {
    console.error(`Errore eliminazione opzione template ${optionId}:`, err);
    addError.value = `Errore eliminazione: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
  }
}

</script>

<style scoped>
.template-answer-options-editor {
  margin-top: 15px;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #fafafa;
}
.options-list {
  list-style: none;
  padding: 0;
  margin: 0 0 15px 0;
}
.options-list li {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px; /* Spazio tra elementi */
}
.option-text-input {
  flex-grow: 1;
  padding: 6px 8px;
  border: 1px solid #ccc;
  border-radius: 3px;
}
.is-correct-label {
  display: flex;
  align-items: center;
  white-space: nowrap;
  cursor: pointer;
}
.is-correct-label input {
    margin-right: 4px;
}

.save-option-btn, .delete-option-btn {
    padding: 4px 8px;
    font-size: 0.9em;
    border-radius: 3px;
    cursor: pointer;
    border: none;
    color: white;
}
/* Rimosso stile per .save-option-btn */
.delete-option-btn {
    background-color: #f44336; /* Rosso */
}
.delete-option-btn:hover:not(:disabled) {
    background-color: #d32f2f;
}
.delete-option-btn:disabled {
    background-color: #aaa;
    cursor: not-allowed;
}


.add-option-form {
  display: flex;
  gap: 8px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #ccc;
}
.add-option-form input {
  flex-grow: 1;
   padding: 6px 8px;
  border: 1px solid #ccc;
  border-radius: 3px;
}
.add-option-form button {
   padding: 6px 12px;
   background-color: #2196F3; /* Blu */
   color: white;
   border: none;
   border-radius: 3px;
   cursor: pointer;
   white-space: nowrap;
}
.add-option-form button:disabled {
    background-color: #aaa;
    cursor: not-allowed;
}
.add-option-form button:hover:not(:disabled) {
    background-color: #0b7dda;
}

.loading.small, .error-message.small {
    font-size: 0.9em;
    margin-top: 5px;
    margin-bottom: 10px;
}
</style>