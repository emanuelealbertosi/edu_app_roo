<template>
  <div class="pathway-template-form-view">
    <h1>{{ isEditing ? 'Modifica Template Percorso' : 'Crea Nuovo Template Percorso' }}</h1>
    <div v-if="isLoading" class="loading">Caricamento dati template...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>

    <form v-else @submit.prevent="savePathwayTemplate">
      <div class="form-group">
        <label for="title">Titolo Template:</label>
        <input type="text" id="title" v-model="templateData.title" required />
      </div>
      <div class="form-group">
        <label for="description">Descrizione Template:</label>
        <textarea id="description" v-model="templateData.description"></textarea>
      </div>
      <div class="form-group">
        <label for="points_on_completion">Punti al Completamento (Default):</label>
        <input type="number" id="points_on_completion" v-model.number="pointsOnCompletion" min="0" placeholder="Es: 50" />
        <small>Punti che verranno assegnati di default alle istanze create da questo template.</small>
      </div>

      <!-- TODO: Aggiungere gestione altri metadata se necessario -->

      <div class="form-actions">
        <button type="submit" :disabled="isSaving" class="btn btn-success">
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche Template' : 'Crea Template') }}
        </button>
        <button type="button" @click="cancel" class="btn btn-secondary">Annulla</button>
      </div>
    </form>

    <!-- Sezione Quiz Template del Percorso Template (in modalità modifica) -->
    <div v-if="isEditing && templateId" class="quizzes-section">
        <h2>Quiz Template nel Percorso</h2>
        <div v-if="isLoadingQuizTemplates" class="loading small">Caricamento quiz template disponibili...</div>
        <div v-else-if="quizTemplatesError" class="error-message small">{{ quizTemplatesError }}</div>

        <!-- Lista Quiz Template nel Percorso Template -->
        <ul v-if="templateData.quiz_template_details.length > 0">
            <li v-for="quizDetail in sortedQuizTemplateDetails" :key="quizDetail.id">
               <span>({{ quizDetail.order }}) {{ quizDetail.quiz_template_title }}</span>
               <button @click="removeQuizTemplate(quizDetail.id)" type="button" class="btn btn-danger text-sm">Rimuovi</button>
               <!-- TODO: Aggiungere UI per modificare ordine -->
            </li>
        </ul>
        <p v-else>Nessun quiz template aggiunto a questo percorso template.</p>

        <!-- Aggiunta Quiz Template -->
        <div class="add-quiz-section form-group">
            <label for="quiz-template-to-add">Aggiungi Quiz Template al Percorso:</label>
            <div class="add-quiz-controls">
                <select id="quiz-template-to-add" v-model="selectedQuizTemplateToAdd" :disabled="isLoadingQuizTemplates">
                    <option value="">Seleziona un quiz template...</option>
                    <option v-for="quizTpl in availableQuizTemplates" :key="quizTpl.id" :value="quizTpl.id">
                        {{ quizTpl.title }} (ID: {{ quizTpl.id }})
                    </option>
                </select>
                <button @click="addSelectedQuizTemplate" type="button" :disabled="!selectedQuizTemplateToAdd || isAddingQuizTemplate" class="btn btn-primary">
                    {{ isAddingQuizTemplate ? 'Aggiungo...' : 'Aggiungi Template' }}
                </button>
            </div>
             <div v-if="addQuizTemplateError" class="error-message small">{{ addQuizTemplateError }}</div>
        </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
// Importa API per Pathway Templates e Quiz Templates
import {
    createPathwayTemplate, fetchPathwayTemplateDetails, updatePathwayTemplate,
    addQuizTemplateToPathwayTemplate, removeQuizTemplateFromPathwayTemplate, fetchQuizTemplatesForPathwayTemplate,
    type PathwayTemplatePayload, type PathwayTemplate, type PathwayQuizTemplateDetail, type AddQuizTemplatePayload
} from '@/api/pathways';
import { fetchTeacherQuizTemplates, type QuizTemplate } from '@/api/quizzes'; // Usa fetchTeacherQuizTemplates

// Interfaccia estesa per i dati locali del form
interface PathwayTemplateFormData extends PathwayTemplatePayload {
    quiz_template_details: PathwayQuizTemplateDetail[]; // Dettagli dei quiz template associati
}

const route = useRoute();
const router = useRouter();

const templateId = ref<number | null>(null); // ID del PathwayTemplate
const isEditing = computed(() => !!templateId.value);
const isLoading = ref(false); // Caricamento dati template principale
const isSaving = ref(false); // Salvataggio dati template principale
const error = ref<string | null>(null); // Errore caricamento/salvataggio template principale

// Stato per gestione quiz template nel percorso template
const availableQuizTemplates = ref<QuizTemplate[]>([]); // Lista dei QuizTemplate disponibili per l'aggiunta
const isLoadingQuizTemplates = ref(false); // Caricamento QuizTemplate disponibili e associati
const quizTemplatesError = ref<string | null>(null); // Errore caricamento QuizTemplate
const selectedQuizTemplateToAdd = ref<number | ''>(''); // ID del QuizTemplate selezionato per l'aggiunta
const isAddingQuizTemplate = ref(false); // Stato durante l'aggiunta di un QuizTemplate
const addQuizTemplateError = ref<string | null>(null); // Errore durante l'aggiunta/rimozione

// Usiamo reactive per l'oggetto del form
const templateData = reactive<PathwayTemplateFormData>({
  title: '',
  description: null,
  metadata: {},
  quiz_template_details: [], // Inizializza vuoto
});

// Calcola i quiz template ordinati per visualizzazione
const sortedQuizTemplateDetails = computed(() => {
    return [...templateData.quiz_template_details].sort((a, b) => a.order - b.order);
});

// Computed property per gestire points_on_completion nei metadata
const pointsOnCompletion = computed({
  get: () => templateData.metadata?.points_on_completion ?? null,
  set: (value) => {
    if (!templateData.metadata) {
      templateData.metadata = {};
    }
    if (value === null || value === '' || isNaN(Number(value))) {
      templateData.metadata.points_on_completion = null;
    } else {
      templateData.metadata.points_on_completion = Number(value);
    }
  }
});

onMounted(async () => {
  const idParam = route.params.id;
  if (idParam) {
    templateId.value = Number(idParam);
    if (!isNaN(templateId.value)) {
      await loadPathwayTemplateData(templateId.value);
      // Carica anche i quiz template associati e disponibili se in modifica
      await loadAssociatedQuizTemplates(templateId.value);
      await loadAvailableQuizTemplates();
    } else {
      console.error("ID Template Percorso non valido:", idParam);
      error.value = "ID Template Percorso non valido.";
      templateId.value = null;
    }
  }
});

const loadPathwayTemplateData = async (id: number) => {
  isLoading.value = true;
  error.value = null;
  try {
    const fetchedTemplate = await fetchPathwayTemplateDetails(id);
    templateData.title = fetchedTemplate.title;
    templateData.description = fetchedTemplate.description;
    templateData.metadata = fetchedTemplate.metadata || {};
    // quiz_template_details verranno caricati da loadAssociatedQuizTemplates
  } catch (err: any) {
    console.error("Errore nel caricamento del template di percorso:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore nel caricamento dei dati del template.';
  } finally {
    isLoading.value = false;
  }
};

const savePathwayTemplate = async () => {
  isSaving.value = true;
  error.value = null;

  const payload: PathwayTemplatePayload = {
    title: templateData.title,
    description: templateData.description,
    metadata: templateData.metadata && Object.keys(templateData.metadata).length > 0 ? templateData.metadata : {},
  };

  try {
    let savedTemplate: PathwayTemplate;
    if (isEditing.value && templateId.value) {
      savedTemplate = await updatePathwayTemplate(templateId.value, payload);
    } else {
      savedTemplate = await createPathwayTemplate(payload);
      // Dopo la creazione, naviga alla modifica per aggiungere quiz template?
      templateId.value = savedTemplate.id; // Imposta l'ID per entrare in modalità modifica
      router.replace({ name: 'pathway-template-edit', params: { id: savedTemplate.id.toString() } }); // Usa replace per aggiornare l'URL senza aggiungere alla history
      // Carica i dati necessari per la sezione quiz template
      await loadAssociatedQuizTemplates(savedTemplate.id);
      await loadAvailableQuizTemplates();
      // Non tornare alla lista, rimani qui per aggiungere quiz
      // return; // Esce dalla funzione save dopo la creazione e navigazione/caricamento
    }
     // Se era una modifica, potresti voler mostrare un messaggio di successo
     console.log("Template salvato con successo:", savedTemplate);

  } catch (err: any) {
    console.error("Errore durante il salvataggio del template di percorso:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore durante il salvataggio del template.';
  } finally {
    isSaving.value = false;
  }
};

const cancel = () => {
  // Torna alla lista dei template
  router.push({ name: 'pathway-templates' });
};

// --- Logica Gestione Quiz Template nel Percorso Template ---

const loadAssociatedQuizTemplates = async (id: number) => {
    isLoadingQuizTemplates.value = true; // Usa lo stesso indicatore per semplicità
    quizTemplatesError.value = null;
    try {
        templateData.quiz_template_details = await fetchQuizTemplatesForPathwayTemplate(id);
    } catch (err: any) {
        console.error("Errore caricamento quiz template associati:", err);
        quizTemplatesError.value = "Impossibile caricare i quiz template associati.";
    } finally {
        isLoadingQuizTemplates.value = false;
    }
};

const loadAvailableQuizTemplates = async () => {
    isLoadingQuizTemplates.value = true;
    quizTemplatesError.value = null;
    try {
        // Filtra i quiz template già presenti? Forse non necessario, l'API add dovrebbe gestire duplicati.
        availableQuizTemplates.value = await fetchTeacherQuizTemplates(); // Usa la funzione corretta
    } catch (err: any) {
        console.error("Errore caricamento quiz template disponibili:", err);
        quizTemplatesError.value = "Impossibile caricare l'elenco dei quiz template disponibili.";
    } finally {
        isLoadingQuizTemplates.value = false;
    }
};

const addSelectedQuizTemplate = async () => {
    if (!selectedQuizTemplateToAdd.value || !templateId.value) return;

    isAddingQuizTemplate.value = true;
    addQuizTemplateError.value = null;
    const quizTemplateId = selectedQuizTemplateToAdd.value;

    // Calcola il prossimo ordine disponibile
    const nextOrder = templateData.quiz_template_details.length > 0
        ? Math.max(...templateData.quiz_template_details.map(q => q.order)) + 1
        : 0;

    const payload: AddQuizTemplatePayload = {
        quiz_template_id: quizTemplateId,
        order: nextOrder
    };

    try {
        const newPathwayQuizTemplateDetail = await addQuizTemplateToPathwayTemplate(templateId.value, payload);
        // Aggiungi il nuovo dettaglio alla lista locale
        templateData.quiz_template_details.push(newPathwayQuizTemplateDetail);
        selectedQuizTemplateToAdd.value = ''; // Resetta il dropdown
        console.log(`Quiz template ${quizTemplateId} aggiunto al pathway template ${templateId.value}`);
    } catch (err: any) {
        console.error(`Errore aggiunta quiz template ${quizTemplateId} al percorso template:`, err);
        addQuizTemplateError.value = `Errore aggiunta quiz template: ${err.response?.data?.detail || err.response?.data?.order || err.response?.data?.quiz_template_id || err.message || 'Errore sconosciuto'}`;
    } finally {
        isAddingQuizTemplate.value = false;
    }
};

const removeQuizTemplate = async (pathwayQuizTemplateId: number) => {
    // pathwayQuizTemplateId è l'ID della relazione PathwayQuizTemplate
    if (!templateId.value) return;

    const indexToRemove = templateData.quiz_template_details.findIndex(detail => detail.id === pathwayQuizTemplateId);
    if (indexToRemove === -1) return;

    const quizTitle = templateData.quiz_template_details[indexToRemove].quiz_template_title;
    if (!confirm(`Sei sicuro di voler rimuovere il quiz template "${quizTitle}" da questo percorso template?`)) {
        return;
    }

    try {
        await removeQuizTemplateFromPathwayTemplate(templateId.value, pathwayQuizTemplateId);
        // Rimuovi dalla lista locale SOLO dopo successo API
        templateData.quiz_template_details.splice(indexToRemove, 1);
        console.log(`Quiz template (relazione ${pathwayQuizTemplateId}) rimosso dal pathway template ${templateId.value}.`);
        addQuizTemplateError.value = null; // Pulisce errori precedenti
    } catch (err: any) {
        console.error(`Errore rimozione quiz template (relazione ${pathwayQuizTemplateId}) dal pathway template ${templateId.value}:`, err);
        addQuizTemplateError.value = `Errore rimozione quiz template: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    }
};

</script>

<style scoped>
/* Stili simili a PathwayFormView */
.pathway-template-form-view {
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
.form-group input[type="number"], /* Aggiunto stile per number */
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.form-group textarea {
  min-height: 100px;
  resize: vertical;
}
.form-group small { /* Stile per help text */
    display: block;
    margin-top: 4px;
    font-size: 0.85em;
    color: #666;
}
.form-actions {
  margin-top: 20px;
}
.form-actions button {
  padding: 10px 15px;
  margin-right: 10px;
  cursor: pointer;
  border-radius: 4px;
  border: none;
}
.form-actions button[type="submit"] {
  background-color: #4CAF50;
  color: white;
}
.form-actions button[type="submit"]:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}
.form-actions button[type="button"] {
  background-color: #f44336;
  color: white;
}
.error-message {
  color: red;
  margin-top: 10px;
  font-weight: bold;
}
.error-message.small { /* Stile per errori più piccoli */
    font-size: 0.9em;
    margin-top: 5px;
}
.loading {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
.loading.small { /* Stile per loading più piccoli */
    font-size: 0.9em;
    margin-top: 5px;
}
.quizzes-section {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}
.quizzes-section ul {
    list-style: none;
    padding: 0;
    margin-top: 15px;
}
.quizzes-section li {
    margin-bottom: 10px;
    padding: 10px;
    border: 1px solid #eee;
    border-radius: 4px;
    background-color: #f9f9f9;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.quizzes-section li span {
    flex-grow: 1;
    margin-right: 10px;
}
.quizzes-section li button.small {
    padding: 2px 6px;
    font-size: 0.8em;
}
.quizzes-section li button.delete {
    background-color: #f44336;
    color: white;
    border: none;
    border-radius: 3px; /* Aggiunto per coerenza */
}
.quizzes-section li button.delete:hover {
     background-color: #d32f2f;
}

.add-quiz-section {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px dashed #ccc;
}
.add-quiz-controls {
    display: flex;
    gap: 10px;
    align-items: center;
}
.add-quiz-controls select {
    flex-grow: 1;
    padding: 8px; /* Aggiunto padding */
    border: 1px solid #ccc; /* Aggiunto bordo */
    border-radius: 4px; /* Aggiunto radius */
}
.add-quiz-controls button {
    padding: 8px 12px;
    white-space: nowrap;
    background-color: #2196F3; /* Blu */
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
.add-quiz-controls button:disabled {
    background-color: #aaa;
    cursor: not-allowed;
}
.add-quiz-controls button:hover:not(:disabled) {
    background-color: #0b7dda;
}
</style>