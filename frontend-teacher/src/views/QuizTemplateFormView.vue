<template>
  <div class="quiz-template-form-view"> <!-- Rinominato -->
    <h1>{{ isEditing ? 'Modifica Template Quiz' : 'Crea Nuovo Template Quiz' }}</h1> <!-- Aggiornato -->
    <!-- Messaggio di successo -->
    <div v-if="successMessage" class="success-message bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4 rounded">
        {{ successMessage }}
    </div>
    <form @submit.prevent="saveQuizTemplate"> <!-- Aggiornato handler -->
      <div class="form-group">
        <label for="title">Titolo:</label>
        <input type="text" id="title" v-model="templateData.title" required /> <!-- Usa templateData -->
      </div>
      <div class="form-group">
        <label for="description">Descrizione (Opzionale):</label>
        <textarea id="description" v-model="templateData.description"></textarea> <!-- Usa templateData -->
      </div>
      <!-- Rimossi available_from / available_until -->
      <div class="form-group">
        <label for="points_on_completion">Punti al Completamento (Default):</label> <!-- Aggiornato label -->
        <input type="number" id="points_on_completion" v-model.number="templateData.metadata.points_on_completion" min="0" class="form-input" /> <!-- Usa templateData -->
      </div>
      <div class="form-group">
        <label for="completion_threshold_percent">Soglia Completamento (%) (Default):</label> <!-- Aggiornato label -->
        <input type="number" id="completion_threshold_percent" v-model.number="templateData.metadata.completion_threshold_percent" min="0" max="100" step="0.1" class="form-input" />
        <p class="form-help-text">Percentuale minima (0-100) per considerare superato un quiz creato da questo template. Default: 100%.</p>
      </div>

      <!-- Aggiungere gestione errori -->
      <div v-if="error" class="error-message">{{ error }}</div>

      <div class="form-actions">
         <!-- Applicato stile Tailwind -->
        <button type="submit" :disabled="isSaving" class="btn btn-success mr-2">
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Template' : 'Crea Template') }} <!-- Aggiornato testo -->
        </button>
         <!-- Applicato stile Tailwind -->
        <button type="button" @click="cancel" class="btn btn-secondary">Annulla</button>
      </div>
    </form>

    <!-- Sezione Domande Template (Richiede modifiche API e gestione stato) -->
    <div v-if="isEditing && templateId" class="questions-section"> <!-- Usa templateId -->
        <h2>Domande del Template</h2> <!-- Aggiornato testo -->
        <div v-if="isLoadingQuestions" class="loading">Caricamento domande template...</div> <!-- Aggiornato testo -->
        <div v-else-if="questionsError" class="error-message">
            Errore nel caricamento delle domande template: {{ questionsError }} <!-- Aggiornato testo -->
        </div>
        <div v-else-if="questions.length > 0">
            <ul class="question-list">
                <TemplateQuestionEditor
                    v-for="question in questions"
                    :key="question.id"
                    :question="question"
                    @edit="handleEditQuestion"
                    @delete="handleDeleteQuestion"
                />
            </ul>
        </div>
        <div v-else>
            <p>Nessuna domanda ancora aggiunta a questo template.</p> <!-- Aggiornato testo -->
        </div>
        <!-- Pulsante Aggiungi Domanda -->
         <!-- Applicato stile Tailwind -->
        <button type="button" @click="addQuestion" class="btn btn-primary mt-4">Aggiungi Domanda Template</button> <!-- Aggiornato testo -->
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
// Importa API per Teacher Quiz Templates
import {
    createTeacherQuizTemplate, fetchTeacherQuizTemplateDetails, updateTeacherQuizTemplate,
    type QuizTemplatePayload, type QuizTemplate
} from '@/api/quizzes'; // Rimosse le righe duplicate
// Importa API per domande/opzioni template
import {
    fetchTeacherQuestionTemplates, deleteTeacherQuestionTemplate,
    type QuestionTemplate // Importa anche il tipo QuestionTemplate
    // TODO: Importare API per opzioni e gestione completa domande
} from '@/api/templateQuestions';
import TemplateQuestionEditor from '@/components/TemplateQuestionEditor.vue'; // Importa il nuovo componente

// Interfaccia per i dati del form (basata su QuizTemplatePayload + struttura metadata)
interface QuizTemplateFormData {
  title: string;
  description: string | null;
  metadata: {
    points_on_completion: number | null;
    completion_threshold_percent: number | null; // Mantenuto per ora
    // Aggiungere altri metadati specifici del template se necessario
  };
}

const route = useRoute();
const router = useRouter();

const templateId = ref<number | null>(null); // Usa templateId
const isEditing = computed(() => !!templateId.value);
const isSaving = ref(false);
const error = ref<string | null>(null);
const isLoading = ref(false);
const successMessage = ref<string | null>(null);

// Stato per le domande
const questions = ref<QuestionTemplate[]>([]); // Usa il tipo importato QuestionTemplate
const isLoadingQuestions = ref(false);
const questionsError = ref<string | null>(null);

// Oggetto reattivo per i dati del form
const templateData = reactive<QuizTemplateFormData>({ // Rinominato
  title: '',
  description: null,
  metadata: {
    points_on_completion: null,
    completion_threshold_percent: 100.0 // Default
  }
});

onMounted(async () => {
  const idParam = route.params.id;
  if (idParam && idParam !== 'new') {
    templateId.value = Number(idParam); // Usa templateId
    if (!isNaN(templateId.value)) {
      await loadQuizTemplateData(templateId.value);
      await loadTemplateQuestions(templateId.value); // Carica domande template
    } else {
      console.error("ID Template Quiz non valido:", idParam);
      error.value = "ID Template Quiz fornito non valido.";
      templateId.value = null;
    }
  } else {
      templateId.value = null;
  }
});

const loadQuizTemplateData = async (id: number) => { // Rinominata
  isLoading.value = true;
  error.value = null;
  try {
    const fetchedTemplate = await fetchTeacherQuizTemplateDetails(id); // Usa API template
    templateData.title = fetchedTemplate.title;
    templateData.description = fetchedTemplate.description;
    // Carica metadata con attenzione
    templateData.metadata.points_on_completion = fetchedTemplate.metadata?.points_on_completion ?? null;
    // Assumendo che la soglia sia salvata come 0-1 nel metadata del template
    const threshold_api = fetchedTemplate.metadata?.completion_threshold;
    templateData.metadata.completion_threshold_percent = threshold_api !== undefined && threshold_api !== null ? threshold_api * 100 : 100.0;

  } catch (err: any) {
    console.error("Errore nel caricamento del template quiz:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore caricamento dati template.';
  } finally {
    isLoading.value = false;
  }
};

// Carica le domande associate a questo template
const loadTemplateQuestions = async (id: number) => {
    isLoadingQuestions.value = true;
    questionsError.value = null;
    try {
        // Usa la funzione API importata
        questions.value = await fetchTeacherQuestionTemplates(id);
    } catch (err: any) {
        console.error(`Errore caricamento domande template per ${id}:`, err);
        questionsError.value = `Errore caricamento domande template: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    } finally {
        isLoadingQuestions.value = false;
    }
};

const saveQuizTemplate = async () => { // Rinominata
  isSaving.value = true;
  error.value = null;
  successMessage.value = null;

  // Prepara payload
  const threshold_percent = templateData.metadata.completion_threshold_percent;
  // Salva come decimale 0-1 nel backend
  const completion_threshold = threshold_percent === null || isNaN(Number(threshold_percent)) ? 1.0 : Number(threshold_percent) / 100;

  const payload: QuizTemplatePayload = { // Usa QuizTemplatePayload
      title: templateData.title,
      description: templateData.description,
      metadata: {
          points_on_completion: templateData.metadata.points_on_completion === null || isNaN(Number(templateData.metadata.points_on_completion)) ? 0 : Number(templateData.metadata.points_on_completion),
          completion_threshold: completion_threshold,
      },
  };

  try {
    let savedTemplate: QuizTemplate | null = null; // Usa tipo QuizTemplate
    if (isEditing.value && templateId.value) {
      savedTemplate = await updateTeacherQuizTemplate(templateId.value, payload); // Usa API template
      await loadQuizTemplateData(templateId.value); // Ricarica dati
      successMessage.value = "Template Quiz aggiornato con successo!";
    } else {
      savedTemplate = await createTeacherQuizTemplate(payload); // Usa API template
      successMessage.value = "Template Quiz creato con successo! Ora puoi aggiungere domande.";
      templateId.value = savedTemplate.id; // Imposta ID per modalità modifica
      // Aggiorna URL senza ricaricare pagina
      router.replace({ name: 'quiz-template-edit', params: { id: savedTemplate.id.toString() } });
      await loadTemplateQuestions(savedTemplate.id); // Carica domande (vuote) dopo creazione
    }

    setTimeout(() => {
        successMessage.value = null;
    }, 3000);

  } catch (err: any) {
    console.error("Errore durante il salvataggio del template quiz:", err);
    if (err.response?.data && typeof err.response.data === 'object') {
        const errorDetails = Object.entries(err.response.data)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ');
        error.value = `Errore salvataggio: ${errorDetails}`;
    } else {
        error.value = err.response?.data?.detail || err.message || 'Errore salvataggio template.';
    }
  } finally {
    isSaving.value = false;
  }
};

const cancel = () => {
  router.push({ name: 'quiz-templates' }); // Naviga alla lista template
};

// Naviga alla vista per aggiungere una nuova domanda template
const addQuestion = () => {
    if (!templateId.value) return;
    router.push({
        name: 'quiz-template-question-new', // Usa il nome della rotta definita
        params: { templateId: templateId.value.toString() },
    });
};

const handleEditQuestion = (questionId: number) => {
    if (!templateId.value) return;
    // Naviga alla vista per modificare la domanda template specifica
    router.push({
        name: 'quiz-template-question-edit', // Usa il nome della rotta definita
        params: { templateId: templateId.value.toString(), questionId: questionId.toString() }
    });
};

const handleDeleteQuestion = async (questionId: number) => {
    if (!templateId.value) return;
    if (!confirm(`Sei sicuro di voler eliminare la domanda template con ID ${questionId}? Questa azione è irreversibile.`)) {
        return;
    }
    questionsError.value = null;
    successMessage.value = null; // Pulisci messaggi precedenti
    try {
        // Usa la funzione API importata
        await deleteTeacherQuestionTemplate(templateId.value, questionId);
        await loadTemplateQuestions(templateId.value); // Ricarica la lista delle domande
        successMessage.value = `Domanda template ${questionId} eliminata con successo.`;
         setTimeout(() => { successMessage.value = null; }, 3000); // Messaggio temporaneo
    } catch (err: any) {
        console.error(`Errore eliminazione domanda template ${questionId}:`, err);
        questionsError.value = `Errore eliminazione domanda template: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    }
};

</script>

<style scoped>
/* Stili per lo più identici a QuizFormView, aggiornato selettore classe */
.quiz-template-form-view {
  padding: 20px;
  max-width: 800px;
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
.form-group input[type="datetime-local"], /* Mantenuto per ora, ma non usato */
.form-group input[type="number"].form-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.form-help-text {
    font-size: 0.8rem;
    color: #666;
    margin-top: 4px;
}
.form-group textarea {
  min-height: 100px;
  resize: vertical;
}
.form-actions {
  margin-top: 20px;
}
.error-message {
  color: red;
  margin-top: 10px;
  font-weight: bold;
}
.success-message {
  margin-bottom: 15px;
}
.questions-section {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}
.questions-section .question-list {
    list-style: none;
    padding: 0;
    margin-top: 15px;
}
</style>