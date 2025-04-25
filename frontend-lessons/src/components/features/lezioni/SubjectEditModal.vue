<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <!-- Intestazione Modale con sfondo blu -->
      <div class="bg-blue-600 text-white p-4 rounded-t-md -m-8 mb-6"> <!-- -m-8 mb-6 per sovrapporre padding e aggiungere margine sotto -->
        <h3 class="text-xl font-semibold text-center">{{ isEditing ? 'Modifica Materia' : 'Aggiungi Nuova Materia' }}</h3>
      </div>
      <form @submit.prevent="submitForm">
        <div class="form-group">
          <label for="subject-name">Nome Materia:</label>
          <input
            id="subject-name"
            v-model="editableSubject.name"
            type="text"
            required
            placeholder="Nome della materia"
          />
        </div>
        <div class="form-group">
          <label for="subject-description">Descrizione (opzionale):</label>
          <textarea
            id="subject-description"
            v-model="editableSubject.description"
            rows="3"
            placeholder="Breve descrizione della materia"
          ></textarea>
        </div>

        <div v-if="formError" class="error-message">{{ formError }}</div>
        <div class="modal-actions">
          <button type="button" @click="close" class="button-cancel">Annulla</button>
          <button type="submit" class="button-save" :disabled="isSaving">
            {{ isSaving ? 'Salvataggio...' : 'Salva' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';

// Definisci l'interfaccia Subject qui o importala
interface Subject {
    id: number;
    name: string;
    description: string;
}

const props = defineProps<{
  subject: Subject | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', subjectData: { id?: number; name: string; description?: string }): void; // Evento per salvare
}>();

const editableSubject = ref({ id: undefined as number | undefined, name: '', description: '' });
const formError = ref<string | null>(null);
const isSaving = ref(false); // Per disabilitare il bottone durante il salvataggio

const isEditing = computed(() => !!props.subject);

watch(() => props.subject, (newSubject) => {
  if (newSubject) {
    editableSubject.value = { ...newSubject }; // Copia i dati per la modifica
  } else {
    // Resetta il form se stiamo aggiungendo
    editableSubject.value = { id: undefined, name: '', description: '' };
  }
  formError.value = null;
}, { immediate: true });
const close = () => {
  emit('close');
};

const submitForm = () => {
  formError.value = null; // Resetta errore
  if (!editableSubject.value.name.trim()) {
    formError.value = "Il nome della materia è obbligatorio.";
    return;
  }

  isSaving.value = true;
  const dataToSave: { id?: number; name: string; description?: string } = {
      name: editableSubject.value.name,
      description: editableSubject.value.description || undefined,
  };
  if (isEditing.value && editableSubject.value.id) {
      dataToSave.id = editableSubject.value.id;
  }

  emit('save', dataToSave);

   isSaving.value = false;
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
  min-width: 300px;
  max-width: 500px;
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
textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

textarea {
    resize: vertical;
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
  background-color: #6c757d; /* Grigio */
  color: white;
  border: none;
}
.button-cancel:hover {
  background-color: #5a6268;
}

.button-save {
  background-color: #007bff; /* Blu */
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