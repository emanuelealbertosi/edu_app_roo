<template>
  <div class="pathway-template-form-view p-4 md:p-6"> <!-- Padding ok -->
    <h1 class="text-2xl font-semibold mb-4 bg-primary text-white px-4 py-2 rounded-md">{{ isEditing ? 'Modifica Template Percorso' : 'Crea Nuovo Template Percorso' }}</h1> <!-- Stile titolo aggiornato -->
    <div v-if="isLoading" class="loading text-center py-6 text-neutral-dark">Caricamento dati template...</div> <!-- Stile loading aggiornato -->
    <div v-else-if="error" class="error-message bg-error/10 border border-error text-error p-3 rounded mb-4">{{ error }}</div> <!-- Stile errore aggiornato -->

    <form v-else @submit.prevent="savePathwayTemplate">
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="title" class="block text-sm font-medium text-neutral-darker mb-1">Titolo Template:</label> <!-- Stile label aggiornato -->
        <input type="text" id="title" v-model="templateData.title" required class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2" /> <!-- Stili input aggiornati -->
      </div>
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="description" class="block text-sm font-medium text-neutral-darker mb-1">Descrizione Template:</label> <!-- Stile label aggiornato -->
        <textarea id="description" v-model="templateData.description" class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2 min-h-[80px]"></textarea> <!-- Stili textarea aggiornati -->
      </div>
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="points_on_completion" class="block text-sm font-medium text-neutral-darker mb-1">Punti al Completamento (Default):</label> <!-- Stile label aggiornato -->
        <input type="number" id="points_on_completion" v-model.number="pointsOnCompletion" min="0" placeholder="Es: 50" class="form-input shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2" /> <!-- Stili input aggiornati -->
        <small class="text-xs text-neutral-dark mt-1">Punti che verranno assegnati di default alle istanze create da questo template.</small> <!-- Stile help text aggiornato -->
      </div>

      <!-- TODO: Aggiungere gestione altri metadata se necessario -->

      <div class="form-actions mt-6 flex space-x-3"> <!-- Margin top e flex -->
        <BaseButton type="submit" variant="success" :disabled="isSaving"> <!-- Usa BaseButton -->
          <span v-if="isSaving">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
               <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
               <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
             </svg>
            Salvataggio...
          </span>
          <span v-else>{{ isEditing ? 'Salva Modifiche Template' : 'Crea Template' }}</span>
        </BaseButton>
        <BaseButton type="button" variant="secondary" @click="cancel">Annulla</BaseButton> <!-- Usa BaseButton -->
      </div>
    </form>

    <!-- Sezione Quiz Template del Percorso Template (in modalità modifica) -->
    <div v-if="isEditing && templateId" class="quizzes-section mt-10 pt-6 border-t border-neutral-DEFAULT"> <!-- Stili sezione aggiornati -->
        <h2 class="text-xl font-semibold mb-4 text-neutral-darkest">Quiz Template nel Percorso</h2> <!-- Stile titolo aggiornato -->
        <div v-if="isLoadingQuizTemplates" class="loading small text-center py-4 text-neutral-dark">Caricamento quiz template disponibili...</div> <!-- Stile loading aggiornato -->
        <div v-else-if="quizTemplatesError" class="error-message small bg-error/10 border border-error text-error p-2 rounded text-sm mb-4">{{ quizTemplatesError }}</div> <!-- Stile errore aggiornato -->

        <!-- Lista Quiz Template nel Percorso Template -->
        <ul v-if="templateData.quiz_template_details.length > 0" class="space-y-3"> <!-- Stile lista aggiornato -->
            <li v-for="quizDetail in sortedQuizTemplateDetails" :key="quizDetail.id" class="flex justify-between items-center bg-neutral-lightest p-3 rounded-md border border-neutral-DEFAULT"> <!-- Stile item aggiornato -->
               <span class="text-sm text-neutral-darkest"><strong class="font-medium">({{ quizDetail.order }})</strong> {{ quizDetail.quiz_template_title }}</span> <!-- Stile testo aggiornato -->
               <BaseButton @click="removeQuizTemplate(quizDetail.id)" variant="danger" size="sm">Rimuovi</BaseButton> <!-- Usa BaseButton -->
               <!-- TODO: Aggiungere UI per modificare ordine -->
            </li>
        </ul>
        <p v-else class="text-center py-4 text-neutral-dark">Nessun quiz template aggiunto a questo percorso template.</p> <!-- Stile messaggio vuoto aggiornato -->

        <!-- Aggiunta Quiz Template -->
        <div class="add-quiz-section form-group mt-6 pt-4 border-t border-dashed border-neutral-DEFAULT"> <!-- Stili sezione aggiornati -->
            <label for="quiz-template-to-add" class="block text-sm font-medium text-neutral-darker mb-1">Aggiungi Quiz Template al Percorso:</label> <!-- Stile label aggiornato -->
            <div class="add-quiz-controls flex items-center gap-3"> <!-- Stile controlli aggiornato -->
                <select id="quiz-template-to-add" v-model="selectedQuizTemplateToAdd" :disabled="isLoadingQuizTemplates" class="flex-grow p-2 border border-neutral-DEFAULT rounded-md shadow-sm focus:ring-primary focus:border-primary"> <!-- Stili select aggiornati -->
                    <option value="">Seleziona un quiz template...</option>
                    <option v-for="quizTpl in availableQuizTemplates" :key="quizTpl.id" :value="quizTpl.id">
                        {{ quizTpl.title }} (ID: {{ quizTpl.id }})
                    </option>
                </select>
                <BaseButton @click="addSelectedQuizTemplate" variant="primary" :disabled="!selectedQuizTemplateToAdd || isAddingQuizTemplate"> <!-- Usa BaseButton -->
                    <span v-if="isAddingQuizTemplate">
                      <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                         <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                         <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                       </svg>
                      Aggiungo...
                    </span>
                    <span v-else>Aggiungi Template</span>
                </BaseButton>
            </div>
             <div v-if="addQuizTemplateError" class="error-message small text-error text-xs mt-1">{{ addQuizTemplateError }}</div> <!-- Stile errore aggiornato -->
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
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton

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
/* Rimuovi stili specifici se non necessari, Tailwind dovrebbe gestire la maggior parte */
</style>