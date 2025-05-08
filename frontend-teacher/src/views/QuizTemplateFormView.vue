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
        <input type="text" id="title" v-model="templateData.title" required class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2" /> <!-- Stili input aggiornati -->
      </div>
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="description" class="block text-sm font-medium text-neutral-darker mb-1">Descrizione (Obbligatorio):</label> <!-- Stile label aggiornato -->
        <textarea id="description" v-model="templateData.description" class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2 min-h-[80px]"></textarea> <!-- Stili textarea aggiornati -->
      </div>

      <!-- Campo Materia -->
      <div class="form-group mb-4">
        <label for="subject" class="block text-sm font-medium text-neutral-darker mb-1">Materia (Opzionale):</label>
        <select id="subject" v-model="templateData.subject_id" @change="handleSubjectChange" class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2">
          <option :value="null">Nessuna materia selezionata</option>
          <option v-for="subject_item in teacherSubjects" :key="subject_item.id" :value="subject_item.id">
            {{ subject_item.name }}
          </option>
        </select>
      </div>

      <!-- Campo Argomento -->
      <div class="form-group mb-4">
        <label for="topic" class="block text-sm font-medium text-neutral-darker mb-1">Argomento (Opzionale, richiede una materia):</label>
        <select id="topic" v-model="templateData.topic_id" :disabled="!templateData.subject_id || isLoadingTopics" class="shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2">
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
        <input type="number" id="points_on_completion" v-model.number="templateData.metadata.points_on_completion" min="0" class="form-input shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2" /> <!-- Stili input aggiornati -->
      </div>
      <div class="form-group mb-4"> <!-- Margin bottom -->
        <label for="completion_threshold_percent" class="block text-sm font-medium text-neutral-darker mb-1">Soglia Completamento (%) (Default):</label> <!-- Stile label aggiornato -->
        <input type="number" id="completion_threshold_percent" v-model.number="templateData.metadata.completion_threshold_percent" min="0" max="100" step="0.1" class="form-input shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-neutral-DEFAULT rounded-md p-2" /> <!-- Stili input aggiornati -->
        <p class="form-help-text text-xs text-neutral-dark mt-1">Percentuale minima (0-100) per considerare superato un quiz creato da questo template. Default: 100%.</p> <!-- Stile help text aggiornato -->
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
    <div v-if="isAddQuestionModalOpen" class="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
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
            @question-created="handleQuestionCreatedInModal" />
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

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import QuestionTemplateFormView from './QuestionTemplateFormView.vue'; // Importa il form
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
const questionToEditId = ref<number | null>(null); // ID domanda da modificare nella modale

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
  }
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
    // Non naviga più, apre la modale
    // router.push({
    //     name: 'quiz-template-question-new', // Usa il nome della rotta definita
    //     params: { templateId: templateId.value.toString() },
    // });
};

const closeAddQuestionModal = () => {
    isAddQuestionModalOpen.value = false;
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
    if (!templateId.value) return;
    questionToEditId.value = qId; // Imposta l'ID della domanda da modificare
    isEditQuestionModalOpen.value = true; // Apri la modale di modifica
    // Non naviga più
    // router.push({
    //     name: 'quiz-template-question-edit',
    //     params: { templateId: templateId.value.toString(), questionId: qId.toString() }
    // });
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