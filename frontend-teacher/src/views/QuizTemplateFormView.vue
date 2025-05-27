<template>
  <div class="quiz-template-form-view p-4 md:p-6"> <!-- Padding ok -->
    <h1 class="text-2xl font-semibold mb-4 bg-primary text-white px-4 py-2 rounded-md">{{ isEditing ? 'Modifica Template Quiz' : 'Crea Nuovo Template Quiz' }}</h1> <!-- Stile titolo aggiornato -->
    <!-- Messaggio di successo -->
    <div v-if="successMessage" class="success-message bg-success/10 border-l-4 border-success text-success-dark p-4 mb-4 rounded"> <!-- Stile successo aggiornato -->
        {{ successMessage }}
    </div>
    <form @submit.prevent="saveQuizTemplate"> <!-- Handler ok -->
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="title" class="block text-sm font-medium text-neutral-darker mb-1">Titolo (Obbligatorio):</label> <!-- Stile label aggiornato -->
        <input type="text" id="title" v-model="templateData.title" required class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border border-gray-400 rounded-md p-2" /> <!-- Stili input aggiornati -->
      </div>
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="description" class="block text-sm font-medium text-neutral-darker mb-1">Descrizione (Obbligatorio):</label> <!-- Stile label aggiornato -->
        <textarea id="description" v-model="templateData.description" class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border border-gray-400 rounded-md p-2 min-h-[80px]"></textarea> <!-- Stili textarea aggiornati -->
      </div>

      <!-- Campo Materia -->
      <div class="form-group mb-4">
        <label for="subject" class="block text-sm font-medium text-neutral-darker mb-1">Materia (Opzionale):</label>
        <select id="subject" v-model="templateData.subject_id" @change="handleSubjectChange" class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border border-gray-400 rounded-md p-2">
          <option :value="null">Nessuna materia selezionata</option>
          <option v-for="subject_item in teacherSubjects" :key="subject_item.id" :value="subject_item.id">
            {{ subject_item.name }}
          </option>
        </select>
      </div>

      <!-- Campo Argomento -->
      <div class="form-group mb-4">
        <label for="topic" class="block text-sm font-medium text-neutral-darker mb-1">Argomento (Opzionale, richiede una materia):</label>
        <select id="topic" v-model="templateData.topic_id" :disabled="!templateData.subject_id || isLoadingTopics" class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border border-gray-400 rounded-md p-2">
          <option :value="null">Nessun argomento selezionato</option>
          <option v-if="isLoadingTopics" :value="null" disabled>Caricamento argomenti...</option>
          <option v-for="topic_item in filteredTopics" :key="topic_item.id" :value="topic_item.id">
            {{ topic_item.name }}
          </option>
        </select>
        <p v-if="templateData.subject_id && !isLoadingTopics && filteredTopics.length === 0" class="form-help-text text-xs text-neutral-dark mt-1">
            Nessun argomento disponibile per la materia selezionata. Puoi crearne di nuovi in 'Gestione Lezioni'.
        </p>
      </div>
      <!-- Rimossi available_from / available_until -->
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="points_on_completion" class="block text-sm font-medium text-neutral-darker mb-1">Punti al Completamento (Default):</label> <!-- Stile label aggiornato -->
        <input type="number" id="points_on_completion" v-model.number="templateData.metadata.points_on_completion" min="0" class="form-input shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border border-gray-400 rounded-md p-2" /> <!-- Stili input aggiornati -->
      </div>
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="completion_threshold_percent" class="block text-sm font-medium text-neutral-darker mb-1">Soglia Completamento (%) (Default):</label> <!-- Stile label aggiornato -->
        <input type="number" id="completion_threshold_percent" v-model.number="templateData.metadata.completion_threshold_percent" min="0" max="100" step="0.1" class="form-input shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border border-gray-400 rounded-md p-2" /> <!-- Stili input aggiornati -->
        <p class="form-help-text text-xs text-neutral-dark mt-1">Percentuale minima (0-100) per considerare superato un quiz creato da questo template. Default: 100%.</p> <!-- Stile help text aggiornato -->
      </div>

      <!-- Campo Colore Sfondo Card -->
      <div class="form-group mb-4">
        <label for="card_background_color" class="block text-sm font-medium text-neutral-darker mb-1">Colore Sfondo Card (Studente):</label>
        <div class="flex flex-wrap gap-2 mt-1">
          <button
            type="button"
            v-for="color in predefinedColors"
            :key="color.value"
            @click="templateData.card_background_color = color.value"
            class="w-8 h-8 rounded-full border-2 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            :class="[
              templateData.card_background_color === color.value ? 'ring-2 ring-offset-2 ring-primary' : 'border-neutral-light',
              color.value === '#FFFFFF' || color.value === '#FFF' ? 'border-neutral-dark' : '' // Bordo più visibile per il bianco
            ]"
            :style="{ backgroundColor: color.value }"
            :title="color.name"
          >
            <span class="sr-only">{{ color.name }}</span>
          </button>
        </div>
        <p class="form-help-text text-xs text-neutral-dark mt-2">Scegli un colore per lo sfondo della card del quiz come apparirà allo studente. Selezionato: {{ templateData.card_background_color }}</p>
      </div>

      <!-- Aggiungere gestione errori -->
      <div v-if="error" class="error-message text-error text-sm mb-4">{{ error }}</div> <!-- Stile errore aggiornato -->

      <div class="form-actions mt-6 flex space-x-3"> <!-- Margin top e flex -->
        <BaseButton type="submit" variant="success" :disabled="isSaving"> <!-- Usa BaseButton -->
          <span v-if="isSaving">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
               <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
               <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
             </svg>
            Salvataggio...
          </span>
          <span v-else>{{ isEditing ? 'Salva Template' : 'Crea Template' }}</span> <!-- Testo aggiornato -->
        </BaseButton>
        <BaseButton type="button" variant="secondary" @click="cancel">Annulla</BaseButton> <!-- Usa BaseButton -->
      </div>
    </form>

    <!-- Sezione Domande Template -->
    <div v-if="isEditing && templateId" class="questions-section mt-10 pt-6 border-t border-neutral-DEFAULT"> <!-- Stili sezione aggiornati -->
        <h2 class="text-xl font-semibold mb-4 text-neutral-darkest">Domande del Template</h2> <!-- Stile titolo aggiornato -->
        <div v-if="isLoadingQuestions" class="loading text-center py-6 text-neutral-dark">Caricamento domande template...</div> <!-- Stile loading aggiornato -->
        <div v-else-if="questionsError" class="error-message bg-error/10 border border-error text-error p-3 rounded mb-4"> <!-- Stile errore aggiornato -->
            Errore nel caricamento delle domande template: {{ questionsError }}
        </div>
        <div v-else-if="questions.length > 0">
            <ul class="question-list space-y-4"> <!-- Stile lista aggiornato -->
                <TemplateQuestionEditor
                    v-for="question in questions"
                    :key="question.id"
                    :question="question"
                    @edit="handleEditQuestion"
                    @delete="handleDeleteQuestion"
                    @configure-fill-blank="handleConfigureFillBlank"
                    class="bg-white p-4 rounded-lg shadow border border-neutral-DEFAULT" /> <!-- Stile item aggiornato -->
            </ul>
        </div>
        <div v-else class="text-center py-6 text-neutral-dark"> <!-- Stile messaggio vuoto aggiornato -->
            <p>Nessuna domanda ancora aggiunta a questo template.</p>
        </div>
        <!-- Pulsante Aggiungi Domanda -->
        <BaseButton type="button" variant="primary" @click="addQuestion" class="mt-6">Aggiungi Domanda Template</BaseButton> <!-- Usa BaseButton, stile aggiornato -->
    </div>

    <!-- Modale per Aggiungere Domanda -->
    <div v-if="isAddQuestionModalOpen" class="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4" @click="handleClickOutsideAddQuestionModal">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto" @click.stop>
        <!-- Header Modale -->
        <div class="flex justify-between items-center p-4 border-b">
          <h2 class="text-xl font-semibold">Aggiungi Nuova Domanda al Template</h2>
          <button @click="closeAddQuestionModal" class="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
        </div>
        <!-- Contenuto Modale (Form) -->
        <div class="p-6">
          <!-- Passiamo templateId e gestiamo l'evento 'created' -->
          <!-- NOTA: QuestionTemplateFormView potrebbe non funzionare perfettamente qui senza adattamenti
               perché è pensato come vista completa con routing interno.
               Un componente dedicato sarebbe meglio. -->
          <!-- Converti null in undefined per la prop template-id-prop -->
          <QuestionTemplateFormView
            :template-id-prop="templateId ?? undefined"
            :is-in-modal="true"
            @close-modal="closeAddQuestionModal"
            @question-created="handleQuestionCreatedInModal"
            @wysiwyg-prompt-start="isWysiwygPromptActive = true"
            @wysiwyg-prompt-end="handleWysiwygPromptEnd" />
        </div>
      </div>
    </div>

    <!-- Modale per Modificare Domanda -->
    <div v-if="isEditQuestionModalOpen && questionToEditId" class="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <!-- Header Modale -->
        <div class="flex justify-between items-center p-4 border-b">
          <h2 class="text-xl font-semibold">Modifica Domanda Template (ID: {{ questionToEditId }})</h2>
          <button @click="closeEditQuestionModal" class="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
        </div>
        <!-- Contenuto Modale (Form) -->
        <div class="p-6">
          <!-- Commento per question-id-prop -->
          <QuestionTemplateFormView
            :template-id-prop="templateId ?? undefined"
            :question-id-prop="questionToEditId"
            :is-in-modal="true"
            @close-modal="closeEditQuestionModal"
            @question-updated="handleQuestionUpdatedInModal" /> <!-- Auto-chiuso -->
        </div>
      </div>
    </div>

    <!-- Modale per Configurare Fill Blank -->
    <div v-if="isConfigureBlankModalOpen && currentQuestionForBlankConfig" class="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto"> <!-- Aumentata larghezza a max-w-4xl -->
        <div class="flex justify-between items-center p-4 border-b">
          <h2 class="text-xl font-semibold">Configura Spazi Vuoti per: "{{ currentQuestionForBlankConfig.text.length > 50 ? currentQuestionForBlankConfig.text.substring(0, 50) + '...' : currentQuestionForBlankConfig.text }}"</h2>
          <button @click="closeConfigureBlankModal" class="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
        </div>
        <div class="p-6">
          <FillBlankQuestionEditor
            :initial-question-text="currentQuestionForBlankConfig.text"
            :initial-metadata="currentQuestionForBlankConfig.metadata as FillBlankMetadata | null"
            @update:question-details="handleFillBlankDetailsSaved"
          />
          <!-- Aggiungere un pulsante Salva qui se FillBlankQuestionEditor non lo ha,
               o se l'evento @update:metadata deve essere scatenato da un'azione esplicita in questa modale.
               Per ora, assumiamo che @update:metadata sia sufficiente e venga emesso al salvataggio interno
               di FillBlankQuestionEditor. Se FillBlankQuestionEditor emette solo al cambio,
               allora avremo bisogno di un pulsante Salva qui che chiami una funzione
               che prende i metadati da un ref esposto da FillBlankQuestionEditor e poi chiama handleFillBlankMetadataSaved.

               Per semplicità, modifichiamo FillBlankQuestionEditor per avere un pulsante Salva interno
               che emette 'update:metadata'. Se questo è già il caso, allora la struttura attuale va bene.
               Altrimenti, questa modale dovrebbe avere i suoi pulsanti Salva/Annulla.
               L'attuale FillBlankQuestionEditor ha un pulsante "Salva Configurazione Spazi Vuoti"
               che emette 'update:metadata', quindi dovrebbe funzionare.
          -->
        </div>
         <div class="p-4 border-t flex justify-end">
            <BaseButton @click="closeConfigureBlankModal" variant="secondary">Chiudi</BaseButton>
            <!-- Se FillBlankQuestionEditor non avesse un suo "salva" che emette update:metadata,
                 un pulsante di salvataggio andrebbe qui. Ma dato che lo ha, questo "Chiudi" è sufficiente.
                 L'utente salva DENTRO FillBlankQuestionEditor, che emette l'evento,
                 e poi può chiudere questa modale. -->
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import QuestionTemplateFormView from './QuestionTemplateFormView.vue';
import FillBlankQuestionEditor, { type FillBlankMetadata } from '@/components/questions/FillBlankQuestionEditor.vue';
// Importa API per Teacher Quiz Templates
import {
    createTeacherQuizTemplate, fetchTeacherQuizTemplateDetails, updateTeacherQuizTemplate,
    type QuizTemplatePayload, type QuizTemplate
} from '@/api/quizzes'; // Rimosse le righe duplicate
// Importa API per domande/opzioni template
import {
    fetchTeacherQuestionTemplates, deleteTeacherQuestionTemplate,
    type QuestionTemplate, type QuestionTemplatePayload, // Aggiunto QuestionTemplatePayload
    updateTeacherQuestionTemplate // Usiamo questa per aggiornare l'intera domanda template
    // TODO: Importare API per opzioni e gestione completa domande
} from '@/api/templateQuestions';
import TemplateQuestionEditor from '@/components/TemplateQuestionEditor.vue'; // Importa il nuovo componente
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton
// Importa le API reali e i tipi per materie e argomenti
import {
    fetchTeacherSubjects,
    fetchTeacherTopicsForSubject,
    type Subject,
    type Topic
} from '@/api/subjects'; // Percorso aggiornato

// Interfaccia per i dati del form (basata su QuizTemplatePayload + struttura metadata)
interface QuizTemplateFormData {
  title: string;
  description: string | null;
  subject_id: number | null; // Ripristinato
  topic_id: number | null;   // Ripristinato
  metadata: {
    points_on_completion: number | null;
    completion_threshold_percent: number | null; // Mantenuto per ora
    // Aggiungere altri metadati specifici del template se necessario
  };
  card_background_color: string | null; // Nuovo campo per il colore
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
const isAddQuestionModalOpen = ref(false); // Stato per la modale di aggiunta
const isEditQuestionModalOpen = ref(false); // Stato per la modale di modifica
const questionToEditId = ref<number | null>(null);
const isConfigureBlankModalOpen = ref(false);
const questionToConfigureBlankId = ref<number | null>(null);
const currentQuestionForBlankConfig = ref<QuestionTemplate | null>(null);
const isWysiwygPromptActive = ref(false); // Flag per interazione WYSIWYG

const predefinedColors = ref([
  { name: 'Rosso Brillante', value: '#EF4444' }, // red-500
  { name: 'Arancio Vivo', value: '#F97316' }, // orange-500
  { name: 'Ambra', value: '#F59E0B' }, // amber-500
  { name: 'Verde Smeraldo', value: '#10B981' }, // emerald-500
  { name: 'Ciano', value: '#06B6D4' }, // cyan-500
  { name: 'Blu Intenso', value: '#3B82F6' }, // blue-500
  { name: 'Indaco', value: '#6366F1' }, // indigo-500
  { name: 'Viola Acceso', value: '#8B5CF6' }, // violet-500
  { name: 'Fucsia', value: '#D946EF' }, // fuchsia-500
  { name: 'Rosa Shocking', value: '#EC4899' }, // pink-500
  { name: 'Grigio Medio', value: '#6B7280' }, // gray-500
  { name: 'Bianco', value: '#FFFFFF' },
]);

// Dati per materie e argomenti
const teacherSubjects = ref<Subject[]>([]);
const filteredTopics = ref<Topic[]>([]);
const isLoadingSubjects = ref(false);
const isLoadingTopics = ref(false);

// Oggetto reattivo per i dati del form
const templateData = reactive<QuizTemplateFormData>({ // Rinominato
  title: '',
  description: null,
  subject_id: null, // Ripristinato
  topic_id: null,   // Ripristinato
  metadata: {
    points_on_completion: null,
    completion_threshold_percent: 100.0 // Default
  },
  card_background_color: '#FFFFFF' // Default a bianco
});

onMounted(async () => {
  await loadSubjects(); // Ripristinato caricamento materie
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

const loadSubjects = async () => {
  isLoadingSubjects.value = true;
  try {
    teacherSubjects.value = await fetchTeacherSubjects();
  } catch (err) {
    console.error("Errore caricamento materie:", err);
    error.value = "Impossibile caricare l'elenco delle materie.";
  } finally {
    isLoadingSubjects.value = false;
  }
};

const loadTopicsForSubject = async (subjectId: number | null) => { // Ripristinato
  if (!subjectId) {
    filteredTopics.value = [];
    templateData.topic_id = null;
    return;
  }
  isLoadingTopics.value = true;
  try {
    filteredTopics.value = await fetchTeacherTopicsForSubject(subjectId);
  } catch (err) {
    console.error(`Errore caricamento argomenti per materia ${subjectId}:`, err);
    error.value = `Impossibile caricare gli argomenti per la materia selezionata.`;
    filteredTopics.value = [];
  } finally {
    isLoadingTopics.value = false;
  }
};

const handleSubjectChange = async () => { // Ripristinato
  templateData.topic_id = null;
  await loadTopicsForSubject(templateData.subject_id);
};

const loadQuizTemplateData = async (id: number) => { // Rinominata
  isLoading.value = true;
  error.value = null;
  try {
    const fetchedTemplate: QuizTemplate = await fetchTeacherQuizTemplateDetails(id); // Usa API template
    templateData.title = fetchedTemplate.title;
    templateData.description = fetchedTemplate.description;
    // Carica materia: cerca l'ID corrispondente al nome ricevuto dall'API
    if (fetchedTemplate.subject && teacherSubjects.value.length > 0) {
      const foundSubject = teacherSubjects.value.find(s => s.name === fetchedTemplate.subject);
      if (foundSubject) {
        templateData.subject_id = foundSubject.id;
      } else {
        console.warn(`Materia "${fetchedTemplate.subject}" (template) non trovata nell'elenco locale. L'ID non sarà impostato.`);
        templateData.subject_id = null;
      }
    } else {
      templateData.subject_id = null; // Nessun nome materia dall'API o nessun subject locale caricato
    }

    // Carica argomenti se la materia è stata identificata e popolata
    if (templateData.subject_id) {
      await loadTopicsForSubject(templateData.subject_id);
      // Ora cerca l'ID dell'argomento corrispondente al nome ricevuto
      if (fetchedTemplate.topic && filteredTopics.value.length > 0) {
        const foundTopic = filteredTopics.value.find(t => t.name === fetchedTemplate.topic);
        if (foundTopic) {
          templateData.topic_id = foundTopic.id;
        } else {
          console.warn(`Argomento "${fetchedTemplate.topic}" (template) non trovato per la materia selezionata. L'ID non sarà impostato.`);
          templateData.topic_id = null;
        }
      } else {
        templateData.topic_id = null; // Nessun nome argomento dall'API o nessun topic locale caricato/corrispondente
      }
    } else {
      // Se non c'è materia, non può esserci argomento preselezionato
      templateData.topic_id = null;
      filteredTopics.value = [];
    }

    // Carica metadata con attenzione
    templateData.metadata.points_on_completion = fetchedTemplate.metadata?.points_on_completion ?? null;
    // Assumendo che la soglia sia salvata come 0-1 nel metadata del template
    const threshold_api = fetchedTemplate.metadata?.completion_threshold;
    templateData.metadata.completion_threshold_percent = threshold_api !== undefined && threshold_api !== null ? threshold_api * 100 : 100.0;
    templateData.card_background_color = fetchedTemplate.card_background_color || '#FFFFFF'; // Carica il colore o default


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
        const fetchedQuestions = await fetchTeacherQuestionTemplates(id);
        questions.value = fetchedQuestions.map(q => ({
            ...q,
            question_type: q.question_type ? q.question_type.toLowerCase() : ''
        }));
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

  // Trova i nomi di materia e argomento basati sugli ID selezionati
  const selectedSubject = teacherSubjects.value.find(s => s.id === templateData.subject_id);
  const subjectName = selectedSubject ? selectedSubject.name : null;

  const selectedTopic = filteredTopics.value.find(t => t.id === templateData.topic_id);
  const topicName = selectedTopic ? selectedTopic.name : null;

  const payload: QuizTemplatePayload = { // Usa QuizTemplatePayload
      title: templateData.title,
      description: templateData.description,
      subject: subjectName, // Invia nome
      topic: topicName,     // Invia nome
      metadata: {
          points_on_completion: templateData.metadata.points_on_completion === null || isNaN(Number(templateData.metadata.points_on_completion)) ? 0 : Number(templateData.metadata.points_on_completion),
          completion_threshold: completion_threshold,
      },
      card_background_color: templateData.card_background_color, // Aggiungi al payload
  };

  // Validazione: topic (nome) richiede subject (nome)
  if (payload.topic && !payload.subject) {
      error.value = "Un argomento può essere selezionato solo se è stata selezionata anche una materia.";
      isSaving.value = false;
      return;
  }

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

// Mostra la modale per aggiungere una nuova domanda template
const addQuestion = () => {
    if (!templateId.value) return;
    isAddQuestionModalOpen.value = true;
};

const closeAddQuestionModal = () => {
    isAddQuestionModalOpen.value = false;
};

const handleClickOutsideAddQuestionModal = (event: MouseEvent) => {
    if (isWysiwygPromptActive.value) {
        // Non chiudere la modale se il prompt del WYSIWYG è attivo o è appena stato chiuso,
        // poiché il focus potrebbe tornare in modi imprevisti.
        // isWysiwygPromptActive si resetterà a false sull'evento 'wysiwyg-prompt-end'.
        return;
    }
    if (event.target === event.currentTarget) {
        closeAddQuestionModal();
    }
};

const handleWysiwygPromptEnd = () => {
  setTimeout(() => {
    isWysiwygPromptActive.value = false;
  }, 100); // Ritarda il reset del flag di 100ms
};

// Funzione chiamata quando una domanda viene creata con successo nella modale
const handleQuestionCreatedInModal = async () => {
    closeAddQuestionModal();
    if (templateId.value) {
        await loadTemplateQuestions(templateId.value); // Ricarica la lista
        successMessage.value = "Nuova domanda aggiunta con successo!"; // Mostra messaggio
        setTimeout(() => { successMessage.value = null; }, 3000);
    }
};

// Apre la modale per modificare una domanda esistente
const handleEditQuestion = (qId: number) => {
    questionToEditId.value = qId;
    isEditQuestionModalOpen.value = true;
};

const closeEditQuestionModal = () => {
    isEditQuestionModalOpen.value = false;
    questionToEditId.value = null; // Resetta l'ID
};

// Funzione chiamata quando una domanda viene aggiornata con successo nella modale
const handleQuestionUpdatedInModal = async () => {
    closeEditQuestionModal();
    if (templateId.value) {
        await loadTemplateQuestions(templateId.value); // Ricarica la lista
        successMessage.value = "Domanda aggiornata con successo!"; // Mostra messaggio
        setTimeout(() => { successMessage.value = null; }, 3000);
    }
};

const handleConfigureFillBlank = (questionPayload: QuestionTemplate) => { // Modificato parametro
  // Ora riceviamo l'intero oggetto domanda
  if (questionPayload && (questionPayload.question_type === 'fill_blank' || questionPayload.question_type === 'FILL_BLANK')) {
    currentQuestionForBlankConfig.value = questionPayload;
    questionToConfigureBlankId.value = questionPayload.id; // Assumendo che l'ID sia ancora necessario altrove
    isConfigureBlankModalOpen.value = true;
  } else {
    console.error("Impossibile configurare i blank: payload della domanda non valido, mancante o tipo non corretto.", questionPayload);
    questionsError.value = "Impossibile configurare i blank per questa domanda (payload o tipo errato).";
  }
};

const closeConfigureBlankModal = () => {
  isConfigureBlankModalOpen.value = false;
  questionToConfigureBlankId.value = null;
  currentQuestionForBlankConfig.value = null;
};

// Funzione per gestire il salvataggio dei metadati e del testo da FillBlankQuestionEditor
const handleFillBlankDetailsSaved = async (details: { text: string, metadata: FillBlankMetadata } | null) => {
  if (!questionToConfigureBlankId.value || !currentQuestionForBlankConfig.value || !details) {
    console.error("ID domanda, dati domanda corrente o dettagli mancanti per salvare i dati fill-blank.");
    questionsError.value = "Errore: impossibile salvare la configurazione degli spazi vuoti (dati mancanti).";
    return;
  }

  // Prepara il payload per l'aggiornamento della domanda
  const payload: Partial<QuestionTemplatePayload> = { // Usare QuestionTemplatePayload importato
    text: details.text, // Testo aggiornato
    question_type: currentQuestionForBlankConfig.value.question_type, // Tipo esistente
    metadata: details.metadata, // Nuovi metadati
    order: currentQuestionForBlankConfig.value.order, // Manteniamo l'ordine esistente
  };

  isSaving.value = true; // Aggiunto per feedback visivo
  try {
    if (!templateId.value) {
        throw new Error("ID del template quiz non disponibile.");
    }
    // Chiamata API per aggiornare la domanda template
    await updateTeacherQuestionTemplate(templateId.value, questionToConfigureBlankId.value, payload as QuestionTemplatePayload);
    successMessage.value = "Configurazione 'Fill Blank' e testo domanda salvati con successo.";
    // Ricarica le domande per riflettere l'aggiornamento
    await loadTemplateQuestions(templateId.value);
    // Aggiorna currentQuestionForBlankConfig con il nuovo testo per il titolo della modale, se rimane aperta
    const updatedQuestion = questions.value.find(q => q.id === questionToConfigureBlankId.value);
    if (updatedQuestion) {
        currentQuestionForBlankConfig.value = updatedQuestion;
    }
    // La modale viene chiusa da FillBlankQuestionEditor dopo l'emissione dell'evento.
    // Se si vuole chiudere qui esplicitamente: closeConfigureBlankModal();
    setTimeout(() => { successMessage.value = null; }, 3000);
  } catch (err: any) {
    console.error("Errore durante l'aggiornamento della domanda template con i dettagli fill-blank:", err);
    questionsError.value = `Errore salvataggio configurazione: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
  } finally {
    isSaving.value = false; // Aggiunto per feedback visivo
  }
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
/* Rimuovi stili specifici se non necessari, Tailwind dovrebbe gestire la maggior parte */
/* Esempio: rimuovi .form-group, .form-actions, .error-message, etc. */
</style>