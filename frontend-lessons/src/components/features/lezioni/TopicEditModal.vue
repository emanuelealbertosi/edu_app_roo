<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <!-- Intestazione Modale con sfondo blu -->
      <div class="bg-blue-600 text-white p-4 rounded-t-md -m-8 mb-6"> <!-- -m-8 mb-6 per sovrapporre padding e aggiungere margine sotto -->
        <h3 class="text-xl font-semibold text-center">{{ isEditing ? 'Modifica Argomento' : 'Aggiungi Nuovo Argomento' }}</h3>
      </div>
      <form @submit.prevent="submitForm">
        <div class="form-group">
          <label for="topic-subject">Seleziona materia:</label>
          <select
            id="topic-subject"
            v-model="editableTopic.subject"
            required
            :disabled="isEditing" >
             <option disabled value="">Seleziona una materia</option>
             <option v-for="subject in props.subjects" :key="subject.id" :value="subject.id">
                {{ subject.name }}
             </option>
          </select>
           <small v-if="isEditing">(La materia non può essere cambiata dopo la creazione)</small>
        </div>

        <div class="form-group">
          <label for="topic-name">Nome Argomento:</label>
          <input
            id="topic-name"
            v-model="editableTopic.name"
            type="text"
            required
            placeholder="Nome dell'argomento"
          />
        </div>
        <div class="form-group">
          <label for="topic-description">Descrizione (opzionale):</label>
          <textarea
            id="topic-description"
            v-model="editableTopic.description"
            rows="3"
            placeholder="Breve descrizione dell'argomento"
          ></textarea>
        </div>

        <div v-if="formError" class="error-message">{{ formError }}</div>

        <div class="modal-actions">
          <button type="button" @click="close" class="button-cancel">Annulla</button>
          <button type="submit" class="button-save" :disabled="isSaving || !editableTopic.subject">
            {{ isSaving ? 'Salvataggio...' : 'Salva' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';

interface Subject {
    id: number;
    name: string;
    description: string;
}
interface Topic {
    id: number;
    name: string;
    description: string;
    subject: number; // ID
    subject_name?: string;
}

const props = defineProps<{
  topic: Topic | null;
  subjects: Subject[]; // Lista materie per il dropdown
  defaultSubjectId?: number | null; // Per preselezionare la materia in aggiunta
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', topicData: { id?: number; name: string; subject: number; description?: string }): void;
}>();

const editableTopic = ref({ id: undefined as number | undefined, name: '', description: '', subject: props.defaultSubjectId ?? '' as number | '' });
const formError = ref<string | null>(null);
const isSaving = ref(false);

const isEditing = computed(() => !!props.topic);

watch(() => props.topic, (newTopic) => {
  if (newTopic) {
    editableTopic.value = { ...newTopic };
  } else {
    editableTopic.value = { id: undefined, name: '', description: '', subject: props.defaultSubjectId ?? '' };
  }
  formError.value = null;
}, { immediate: true });

watch(() => props.defaultSubjectId, (newDefaultSubjectId) => {
    if (!isEditing.value) {
        editableTopic.value.subject = newDefaultSubjectId ?? '';
    }
});


const close = () => {
  emit('close');
};

const submitForm = () => {
  formError.value = null;
  if (!editableTopic.value.subject) {
      formError.value = "Seleziona una materia.";
      return;
  }
  if (!editableTopic.value.name.trim()) {
    formError.value = "Il nome dell'argomento è obbligatorio.";
    return;
  }

  isSaving.value = true;

  const dataToSave: { id?: number; name: string; subject: number; description?: string } = {
      name: editableTopic.value.name,
      subject: editableTopic.value.subject as number,
      description: editableTopic.value.description || undefined,
  };
  if (isEditing.value && editableTopic.value.id) {
      dataToSave.id = editableTopic.value.id;
  }

  emit('save', dataToSave);
  isSaving.value = false; // Resetta (semplificazione)
};

</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  min-width: 350px; /* Leggermente più largo per il select */
  max-width: 550px;
}

h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  text-align: center;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
}

input[type="text"],
textarea,
select { /* Aggiunto select */
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

textarea {
    resize: vertical;
}

select:disabled {
    background-color: #e9ecef; /* Grigio chiaro per indicare disabilitato */
    cursor: not-allowed;
}

small {
    font-size: 0.8rem;
    color: #6c757d;
    display: block;
    margin-top: 0.25rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.modal-actions button {
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  margin-left: 0.5rem;
}

.button-cancel {
  background-color: #6c757d;
  color: white;
  border: none;
}
.button-cancel:hover {
  background-color: #5a6268;
}

.button-save {
  background-color: #007bff;
  color: white;
  border: none;
}
.button-save:hover:not(:disabled) {
  background-color: #0056b3;
}
.button-save:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.error-message {
  color: red;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}
</style>