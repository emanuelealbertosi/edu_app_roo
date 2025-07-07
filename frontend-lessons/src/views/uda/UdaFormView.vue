<template>
  <div class="uda-form-view p-4 md:p-8">
    <h1 class="text-3xl font-bold bg-blue-600 text-white p-4 rounded-t-lg mb-6 shadow-md">{{ pageTitle }}</h1>

    <div v-if="loadingInitialData" class="text-center py-10">
      <p class="text-gray-600">Caricamento dati UDA...</p>
    </div>
    <div v-else-if="initialError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ initialError }}</span>
      <div class="mt-4">
        <RouterLink :to="{ name: 'uda-list' }" class="text-indigo-600 hover:text-indigo-800">
          Torna alla lista UDA
        </RouterLink>
      </div>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="space-y-6 bg-white shadow-lg rounded-lg p-6">
      <div class="bg-gray-50 border border-gray-300 rounded-lg p-6 space-y-6 shadow-sm">
        <h2 class="text-xl font-semibold text-neutral-darkest bg-primary-light p-3 rounded-t-md mb-4 shadow-sm">Dati Principali UDA</h2>

        <!-- Riga 1: Titolo, Descrizione, Data Inizio, Data Fine -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 mb-4">
          <div class="md:col-span-1">
            <label for="udaTitle" class="block text-sm font-medium text-gray-700 mb-1">Titolo UDA</label>
            <input type="text" id="udaTitle" v-model="formData.title" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
          </div>
          <div class="md:col-span-1">
            <label for="udaDescription" class="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
            <textarea id="udaDescription" v-model="formData.description" rows="3" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2"></textarea>
          </div>
          <div>
            <label for="startDate" class="block text-sm font-medium text-gray-700 mb-1">Data Inizio (Opzionale)</label>
            <input type="date" id="startDate" v-model="formData.start_date" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
          </div>
          <div>
            <label for="endDate" class="block text-sm font-medium text-gray-700 mb-1">Data Fine (Opzionale)</label>
            <input type="date" id="endDate" v-model="formData.end_date" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
          </div>
        </div>

        <!-- Riga 2: Stato, Corso, Materie, Argomenti -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-4">
          <div>
            <label for="status" class="block text-sm font-medium text-gray-700 mb-1">Stato</label>
            <select id="status" v-model="formData.status" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
              <option value="TODO">Da Fare</option>
              <option value="IN_PROGRESS">In Corso</option>
              <option value="COMPLETED">Completata</option>
            </select>
          </div>
          
          <div>
            <label for="course" class="block text-sm font-medium text-gray-700 mb-1">Corso di Appartenenza (Opzionale)</label>
            <select id="course" v-model="formData.course" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
              <option :value="null">Nessun corso</option>
              <option v-for="course_item in availableCourses" :key="course_item.id" :value="course_item.id">
                {{ course_item.name }}
              </option>
            </select>
            <div v-if="courseStore.loading" class="text-xs text-gray-500 mt-1">Caricamento corsi...</div>
          </div>
          
          <div class="lg:col-span-1" id="subjects-section">
            <label class="block text-sm font-medium text-gray-700 mb-1">Materie (Opzionale)</label>
            <div v-if="subjectStore.loading" class="text-sm text-gray-500">Caricamento materie...</div>
            <div v-else-if="availableSubjects.length === 0" class="text-sm text-gray-500">Nessuna materia disponibile.</div>
            <div v-else class="max-h-40 overflow-y-auto border border-gray-300 rounded-md p-2 space-y-1 bg-white">
              <div v-for="subject_item in availableSubjects" :key="subject_item.id" class="flex items-center cursor-pointer px-1 py-0.5">
                <input
                  type="checkbox"
                  :id="`subject-uda-${subject_item.id}`"
                  :value="subject_item.id"
                  v-model="formData.subjects"
                  class="h-4 w-4 text-indigo-600 border-gray-400 rounded focus:ring-indigo-500 focus:ring-1 focus:ring-offset-0 cursor-pointer"
                >
                <label :for="`subject-uda-${subject_item.id}`" class="ml-2 block text-sm text-gray-800 select-none cursor-pointer">{{ subject_item.name }}</label>
              </div>
            </div>
          </div>

          <div v-if="formData.subjects.length > 0" class="lg:col-span-1" id="topics-section">
            <label for="topics" class="block text-sm font-medium text-gray-700 mb-1">Argomenti (Opzionale)</label>
            <div v-if="topicStore.loading" class="text-sm text-gray-500">Caricamento argomenti...</div>
            <div v-else-if="availableTopicsForSelectedSubject.length === 0" class="text-sm text-gray-500">
              Nessun argomento per la materia.
            </div>
            <div v-else class="max-h-40 overflow-y-auto border border-gray-300 rounded-md p-2 space-y-1 bg-white">
              <div v-for="topic_item in availableTopicsForSelectedSubject" :key="topic_item.id" class="flex items-center cursor-pointer px-1 py-0.5">
                <input type="checkbox" :id="`topic-uda-${topic_item.id}`" :value="topic_item.id" v-model="formData.topics" class="h-4 w-4 text-indigo-600 border-gray-400 rounded focus:ring-indigo-500 focus:ring-1 focus:ring-offset-0 cursor-pointer">
                <label :for="`topic-uda-${topic_item.id}`" class="ml-2 block text-sm text-gray-800 select-none cursor-pointer">{{ topic_item.name }}</label>
              </div>
            </div>
          </div>
        </div>

        <!-- Sezioni Conoscenze, Abilità, Competenze -->
        <div class="space-y-6">
          <div class="border-blue-500 border-2 rounded-md p-4">
            <label for="knowledgeHtml" class="block text-sm font-medium text-gray-700 mb-2">Conoscenze</label>
            <WysiwygEditor
              id="knowledgeHtml"
              v-model="knowledgeHtmlForEditor"
              :editable="true"
            />
          </div>
          <div class="border-green-500 border-2 rounded-md p-4">
            <label for="skillsHtml" class="block text-sm font-medium text-gray-700 mb-2">Abilità</label>
            <WysiwygEditor
              id="skillsHtml"
              v-model="skillsHtmlForEditor"
              :editable="true"
            />
          </div>
          <div class="border-purple-500 border-2 rounded-md p-4">
            <label for="competencesHtml" class="block text-sm font-medium text-gray-700 mb-2">Competenze</label>
            <WysiwygEditor
              id="competencesHtml"
              v-model="competencesHtmlForEditor"
              :editable="true"
            />
          </div>
        </div>

        <!-- Campi per Export DOCX -->
        <div class="bg-yellow-50 border border-yellow-300 rounded-lg p-6 space-y-6 shadow-sm mt-6">
          <h2 class="text-xl font-semibold text-neutral-darkest bg-yellow-200 p-3 rounded-t-md mb-4 shadow-sm">Dati per Esportazione Documento Ministeriale</h2>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div class="flex items-center">
              <input type="checkbox" id="isCivicEducation" v-model="formData.is_civic_education" class="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500">
              <label for="isCivicEducation" class="ml-2 block text-sm font-medium text-gray-700">Parte del percorso di Educazione Civica</label>
            </div>
          </div>

          <div class="space-y-4">
            <div>
              <label for="didacticStrategiesHtml" class="block text-sm font-medium text-gray-700 mb-1">Strategie Didattiche</label>
              <WysiwygEditor id="didacticStrategiesHtml" v-model="didacticStrategiesHtmlForEditor" :editable="true" />
            </div>
            <div>
              <label for="materialsToolsHtml" class="block text-sm font-medium text-gray-700 mb-1">Materiali e Strumenti</label>
              <WysiwygEditor id="materialsToolsHtml" v-model="materialsToolsHtmlForEditor" :editable="true" />
            </div>
            <div>
              <label for="assessmentTypeHtml" class="block text-sm font-medium text-gray-700 mb-1">Tipo di Verifiche</label>
              <WysiwygEditor id="assessmentTypeHtml" v-model="assessmentTypeHtmlForEditor" :editable="true" />
            </div>
            <div>
              <label for="evaluationHtml" class="block text-sm font-medium text-gray-700 mb-1">Valutazione</label>
              <WysiwygEditor id="evaluationHtml" v-model="evaluationHtmlForEditor" :editable="true" />
            </div>
            <div>
              <label for="otherInvolvedSubjectsText" class="block text-sm font-medium text-gray-700 mb-1">Altre Discipline Coinvolte (Testo Libero)</label>
              <textarea id="otherInvolvedSubjectsText" v-model="formData.other_involved_subjects_text" rows="3" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2"></textarea>
            </div>
            <div>
              <label for="exportSpecificAnnotationsHtml" class="block text-sm font-medium text-gray-700 mb-1">Annotazioni Specifiche per Export</label>
              <WysiwygEditor id="exportSpecificAnnotationsHtml" v-model="exportSpecificAnnotationsHtmlForEditor" :editable="true" />
            </div>
          </div>
        </div>
      </div>
      
      <div class="bg-gray-50 border border-gray-300 rounded-lg p-6 shadow-sm">
        <h2 class="text-2xl font-semibold text-neutral-darkest bg-primary-light p-3 rounded-t-md mb-4 shadow-sm">Contenuti dell'UDA</h2>
        <UdaContentEditor
          v-model="formData.contents"
          context="uda"
          :uda-id="isEditMode && udaId ? udaId : undefined"
          :is-editing="true"
          @edit-lesson="handleEditLesson"
          @edit-lesson-contents="handleEditLessonContents"
        /> <!-- Aggiunto is-editing per mostrare i controlli di modifica/eliminazione -->
      </div>

      <div class="flex justify-end items-center space-x-4 pt-4">
        <SaveStatusIndicator :status="saveStatus" />
        <RouterLink :to="{ name: 'uda-list' }" class="flex items-center border border-gray-300 hover:bg-gray-100 text-gray-700 font-medium py-2 px-4 rounded-md shadow-sm">
          <XMarkIcon class="h-5 w-5 sm:mr-2" />
          <span class="hidden sm:inline">Annulla</span>
        </RouterLink>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="flex items-center bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <CheckCircleIcon class="h-5 w-5 sm:mr-2" v-if="!isSubmitting" />
          <span v-if="isSubmitting">Salvataggio...</span>
          <span v-else class="hidden sm:inline">{{ submitButtonText }}</span>
          <span v-else class="sm:hidden inline">{{ isEditMode ? 'Salva' : 'Crea' }}</span>
        </button>
      </div>
      <div v-if="submitError" class="text-red-600 mt-2 text-sm">{{ submitError }}</div>
    </form>

    <LessonEditModal
      v-if="showLessonEditModal"
      :lesson="lessonToEdit"
      :topics="topicStore.topics"
      :is-saving="isSubmitting"
      @close="handleCloseLessonEditModal"
      @save="handleSaveLesson"
    />

    <IFrameModal
      v-if="showIframeModal"
      :src="iframeSrc"
      title="Modifica Contenuti Lezione"
      @close="handleCloseIframeModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import { useUdaStore } from '@/stores/udaStore';
import { useCourseStore } from '@/stores/courseStore';
import { useSubjectStore } from '@/stores/subjectStore';
import { useTopicStore } from '@/stores/topicStore';
import { useLessonStore } from '@/stores/lessons';
import { useQuizStore } from '@/stores/quizStore';
import { useUiStore } from '@/stores/ui';
import UdaContentEditor from '@/components/uda/UdaContentEditor.vue';
import WysiwygEditor from '@/components/WysiwygEditor.vue';
import SaveStatusIndicator from '@/components/common/SaveStatusIndicator.vue';
import LessonEditModal from '@/components/features/lezioni/LessonEditModal.vue';
import IFrameModal from '@/components/common/IFrameModal.vue';
import { type UDA, type UDAContent } from '@/types/uda';
import type { Course as CourseType } from '@/types/uda'; // Course è in uda.ts, rinominato per evitare conflitto
import type { Subject as SubjectType } from '@/types/subject'; // Rinominato
import type { Topic as TopicType } from '@/types/topic'; // Rinominato
import { XMarkIcon, CheckCircleIcon } from '@heroicons/vue/24/outline';

type SaveStatus = 'IDLE' | 'DIRTY' | 'SAVING' | 'SAVED' | 'ERROR';

interface UdaFormData {
  title: string;
  description: string | null;
  knowledge_html: string | null; // Aggiunto
  skills_html: string | null;    // Aggiunto
  competences_html: string | null; // Aggiunto
  // Campi per Export DOCX
  is_civic_education: boolean;
  didactic_strategies_html: string | null;
  materials_tools_html: string | null;
  assessment_type_html: string | null;
  evaluation_html: string | null;
  other_involved_subjects_text: string | null;
  export_specific_annotations_html: string | null;
  start_date: string | null;
  end_date: string | null;
  status: UDA['status'];
  subjects: number[]; 
  topics: number[];
  course: number | null;
  order_in_course: number | null;
  contents: UDAContent[];
}

interface UdaApiPayload {
  title: string;
  description?: string | null;
  knowledge_html?: string | null; // Aggiunto
  skills_html?: string | null;    // Aggiunto
  competences_html?: string | null; // Aggiunto
  // Campi per Export DOCX
  is_civic_education?: boolean;
  didactic_strategies_html?: string | null;
  materials_tools_html?: string | null;
  assessment_type_html?: string | null;
  evaluation_html?: string | null;
  other_involved_subjects_text?: string | null;
  export_specific_annotations_html?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  status: UDA['status'];
  subject_ids?: number[]; 
  topic_ids?: number[];
  course_id?: number | null;
  order_in_course?: number | null;
  contents: Omit<UDAContent, 'temp_id' | 'lesson_title' | 'quiz_title'>[];
}


const route = useRoute();
const router = useRouter();
const udaStore = useUdaStore();
const courseStore = useCourseStore();
const subjectStore = useSubjectStore();
const topicStore = useTopicStore();
const lessonStore = useLessonStore();
const quizStore = useQuizStore();
const uiStore = useUiStore();

const udaId = computed(() => route.params.id ? Number(route.params.id) : null);


const isEditMode = computed(() => udaId.value !== null);
const pageTitle = computed(() => isEditMode.value ? 'Modifica UDA' : 'Crea Nuova UDA');
const submitButtonText = computed(() => isEditMode.value ? 'Salva Modifiche' : 'Crea UDA');

const loadingInitialData = ref(false);
const initialError = ref<string | null>(null);
const isSubmitting = ref(false);
const initialLoadComplete = ref(false);
const submitError = ref<string | null>(null);
const saveStatus = ref<SaveStatus>('IDLE');

const showLessonEditModal = ref(false);
const editingLessonId = ref<number | null>(null);

const lessonToEdit = computed(() => {
  if (!editingLessonId.value) return null;
  return lessonStore.lessons.find(l => l.id === editingLessonId.value) || null;
});

const showIframeModal = ref(false);
const iframeSrc = ref('');

watch(initialError, (newValue, oldValue) => {
  console.log(`[UdaFormView] initialError cambiato da '${oldValue}' a '${newValue}'`);
  if (newValue !== null) {
    console.trace("[UdaFormView] Traccia per initialError impostato");
  }
});

const formData = ref<UdaFormData>({
  title: '',
  description: null,
  knowledge_html: null,
  skills_html: null,
  competences_html: null,
  // Campi per Export DOCX
  is_civic_education: false,
  didactic_strategies_html: null,
  materials_tools_html: null,
  assessment_type_html: null,
  evaluation_html: null,
  other_involved_subjects_text: null,
  export_specific_annotations_html: null,
  start_date: null,
  end_date: null,
  status: 'TODO',
  subjects: [],
  topics: [],
  course: null,
  order_in_course: null,
  contents: []
});

// Rimossi selectedTopicIds e selectedSubjectIds, useremo formData.topics e formData.subjects direttamente
// const selectedTopicIds = ref<number[]>([]);
// const selectedSubjectIds = ref<number[]>([]);

const availableCourses = computed(() => courseStore.courses as CourseType[]);
const availableSubjects = computed(() => subjectStore.subjects as SubjectType[]); 
const availableTopicsForSelectedSubject = computed(() => {
  if (formData.value.subjects.length > 0) {
    const firstSelectedSubjectId = formData.value.subjects[0];
    return topicStore.getTopicsForSubject(firstSelectedSubjectId) as TopicType[]; 
  }
  return [];
});

// Watchers per selectedSubjectIds e selectedTopicIds rimossi.
// La logica per caricare i topic in base alla materia selezionata
// ora osserverà formData.subjects.
watch(() => formData.value.subjects, (newSubjects, oldSubjects) => {
  if (JSON.stringify(newSubjects) !== JSON.stringify(oldSubjects)) {
    // Questo reset è intenzionale quando l'utente cambia le materie.
    // Durante onMounted, questo verrà eseguito, ma formData.topics sarà ripopolato correttamente dopo.
    formData.value.topics = [];
    if (newSubjects && newSubjects.length > 0) {
      topicStore.fetchTopicsBySubject(newSubjects[0]);
    }
  }
}, { deep: true });

const knowledgeHtmlForEditor = computed({
  get: () => formData.value.knowledge_html || undefined,
  set: (val) => { formData.value.knowledge_html = val || null; }
});

const skillsHtmlForEditor = computed({
  get: () => formData.value.skills_html || undefined,
  set: (val) => { formData.value.skills_html = val || null; }
});

const competencesHtmlForEditor = computed({
  get: () => formData.value.competences_html || undefined,
  set: (val) => { formData.value.competences_html = val || null; }
});

const didacticStrategiesHtmlForEditor = computed({
  get: () => formData.value.didactic_strategies_html || undefined,
  set: (val) => { formData.value.didactic_strategies_html = val || null; }
});

const materialsToolsHtmlForEditor = computed({
  get: () => formData.value.materials_tools_html || undefined,
  set: (val) => { formData.value.materials_tools_html = val || null; }
});

const assessmentTypeHtmlForEditor = computed({
  get: () => formData.value.assessment_type_html || undefined,
  set: (val) => { formData.value.assessment_type_html = val || null; }
});

const evaluationHtmlForEditor = computed({
  get: () => formData.value.evaluation_html || undefined,
  set: (val) => { formData.value.evaluation_html = val || null; }
});

const exportSpecificAnnotationsHtmlForEditor = computed({
  get: () => formData.value.export_specific_annotations_html || undefined,
  set: (val) => { formData.value.export_specific_annotations_html = val || null; }
});


// Non sono più necessari i watch per sincronizzare formData.topics/subjects con selectedTopicIds/selectedSubjectIds
// perché usiamo formData.topics/subjects direttamente come v-model.

// Rimosso watch su udaStore.currentUda?.contents per prevenire il reset del form.
// I dati vengono caricati solo in onMounted e poi il formData vive di vita propria.

// Debounce function
const debounce = (fn: Function, delay: number) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  return function(...args: any[]) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  }
}

const handleAutoSave = async () => {
  if (!isEditMode.value || !udaId.value || saveStatus.value === 'SAVING') return;

  saveStatus.value = 'SAVING';

  const payload: UdaApiPayload = {
    title: formData.value.title,
    description: formData.value.description || undefined,
    knowledge_html: formData.value.knowledge_html || undefined,
    skills_html: formData.value.skills_html || undefined,
    competences_html: formData.value.competences_html || undefined,
    is_civic_education: formData.value.is_civic_education,
    didactic_strategies_html: formData.value.didactic_strategies_html || undefined,
    materials_tools_html: formData.value.materials_tools_html || undefined,
    assessment_type_html: formData.value.assessment_type_html || undefined,
    evaluation_html: formData.value.evaluation_html || undefined,
    other_involved_subjects_text: formData.value.other_involved_subjects_text || undefined,
    export_specific_annotations_html: formData.value.export_specific_annotations_html || undefined,
    start_date: formData.value.start_date || undefined,
    end_date: formData.value.end_date || undefined,
    status: formData.value.status,
    subject_ids: formData.value.subjects,
    topic_ids: formData.value.topics,
    course_id: formData.value.course || undefined,
    order_in_course: formData.value.order_in_course || undefined,
    contents: formData.value.contents.map(c => {
      const { temp_id, lesson_title, quiz_title, ...contentToSave } = c as any;
      return contentToSave;
    })
  };

  Object.keys(payload).forEach(keyStr => {
    const key = keyStr as keyof UdaApiPayload;
    if (payload[key] === undefined) {
      delete payload[key];
    }
  });

  try {
    await udaStore.updateUda(udaId.value, payload, { silent: true });
    saveStatus.value = 'SAVED';
  } catch (error) {
    console.error("Errore durante il salvataggio automatico dell'UDA:", error);
    saveStatus.value = 'ERROR';
  }
};

const debouncedAutoSave = debounce(handleAutoSave, 3000);

watch(saveStatus, (newStatus) => {
  if (newStatus === 'DIRTY') {
    debouncedAutoSave();
  }
});

const setDirty = () => {
  if (initialLoadComplete.value && saveStatus.value !== 'DIRTY') {
    saveStatus.value = 'DIRTY';
  }
}

watch(() => formData.value.contents, setDirty, { deep: true });

watch(() => [
  formData.value.title,
  formData.value.description,
  formData.value.knowledge_html,
  formData.value.skills_html,
  formData.value.competences_html,
  formData.value.is_civic_education,
  formData.value.didactic_strategies_html,
  formData.value.materials_tools_html,
  formData.value.assessment_type_html,
  formData.value.evaluation_html,
  formData.value.other_involved_subjects_text,
  formData.value.export_specific_annotations_html,
  formData.value.start_date,
  formData.value.end_date,
  formData.value.status,
  formData.value.subjects,
  formData.value.topics,
  formData.value.course
], setDirty, { deep: true });


onMounted(async () => {
  loadingInitialData.value = true;
  initialError.value = null;
  try {
    const promises = [
      subjectStore.fetchSubjects(),
      courseStore.fetchCourses(),
      lessonStore.fetchLessons(),
      topicStore.fetchTopics()
    ];
    await Promise.all(promises);

    if (isEditMode.value && udaId.value) {
      await udaStore.fetchUda(udaId.value);
      const udaToEdit = udaStore.currentUda;
      if (udaToEdit) {
        const enrichedContents = await enrichContents(udaToEdit.contents);

        // Attendi il prossimo ciclo di aggiornamento DOM prima di popolare il form
        // per dare tempo alle opzioni del select (es. corsi) di essere renderizzate.
        formData.value.title = udaToEdit.title;
        formData.value.description = udaToEdit.description || null;
        formData.value.knowledge_html = udaToEdit.knowledge_html || null;
        formData.value.skills_html = udaToEdit.skills_html || null;
        formData.value.competences_html = udaToEdit.competences_html || null;
        // Campi per Export DOCX
        formData.value.is_civic_education = udaToEdit.is_civic_education || false;
        formData.value.didactic_strategies_html = udaToEdit.didactic_strategies_html || null;
        formData.value.materials_tools_html = udaToEdit.materials_tools_html || null;
        formData.value.assessment_type_html = udaToEdit.assessment_type_html || null;
        formData.value.evaluation_html = udaToEdit.evaluation_html || null;
        formData.value.other_involved_subjects_text = udaToEdit.other_involved_subjects_text || null;
        formData.value.export_specific_annotations_html = udaToEdit.export_specific_annotations_html || null;
        
        formData.value.start_date = udaToEdit.start_date || null;
        formData.value.end_date = udaToEdit.end_date || null;
        formData.value.status = udaToEdit.status;
        formData.value.course = udaToEdit.course || null;
        formData.value.order_in_course = udaToEdit.order_in_course || null;
        
        // Popola materie e argomenti
        formData.value.subjects = udaToEdit.subjects || [];
        if (formData.value.subjects.length > 0) {
          await topicStore.fetchTopicsBySubject(formData.value.subjects[0]);
          formData.value.topics = udaToEdit.topics || [];
        } else {
          formData.value.topics = [];
        }

        formData.value.contents = enrichedContents;
      } else {
        initialError.value = `UDA con ID ${udaId.value} non trovata.`;
        console.error(initialError.value);
      }
    }
  } catch (error) {
    console.error("Errore durante il caricamento iniziale dei dati UDA:", error);
    initialError.value = "Impossibile caricare i dati necessari per la pagina.";
  } finally {
    loadingInitialData.value = false;
    // Imposta il flag a true solo dopo che tutti i dati sono stati caricati e popolati
    nextTick(() => {
      initialLoadComplete.value = true;
    });
  }
});

const enrichContents = async (contents: UDAContent[]): Promise<UDAContent[]> => {
  if (!contents) return [];

  const enriched = await Promise.all(
    contents.map(async (content) => {
      const newContent = { ...content };
      if (newContent.content_type === 'LESSON' && newContent.lesson) {
        await lessonStore.fetchLesson(newContent.lesson);
        newContent.lesson_title = lessonStore.currentLesson?.title || 'Titolo Lezione non trovato';
      } else if (newContent.content_type === 'QUIZ' && newContent.quiz_template) {
        await quizStore.fetchQuizTemplate(newContent.quiz_template);
        newContent.quiz_title = quizStore.currentQuizTemplate?.title || 'Titolo Quiz non trovato';
      }
      return newContent;
    })
  );
  return JSON.parse(JSON.stringify(enriched));
};

const handleSubmit = async () => {
  isSubmitting.value = true;
  submitError.value = null;

  const payload: UdaApiPayload = {
    title: formData.value.title,
    description: formData.value.description || undefined,
    knowledge_html: formData.value.knowledge_html || undefined,
    skills_html: formData.value.skills_html || undefined,
    competences_html: formData.value.competences_html || undefined,
    // Campi per Export DOCX
    is_civic_education: formData.value.is_civic_education,
    didactic_strategies_html: formData.value.didactic_strategies_html || undefined,
    materials_tools_html: formData.value.materials_tools_html || undefined,
    assessment_type_html: formData.value.assessment_type_html || undefined,
    evaluation_html: formData.value.evaluation_html || undefined,
    other_involved_subjects_text: formData.value.other_involved_subjects_text || undefined,
    export_specific_annotations_html: formData.value.export_specific_annotations_html || undefined,
    start_date: formData.value.start_date || undefined,
    end_date: formData.value.end_date || undefined,
    status: formData.value.status,
    subject_ids: formData.value.subjects,
    topic_ids: formData.value.topics,
    course_id: formData.value.course || undefined,
    order_in_course: formData.value.order_in_course || undefined,
    contents: formData.value.contents.map(c => {
      const { temp_id, lesson_title, quiz_title, ...contentToSave } = c as any; 
      return contentToSave;
    })
  };
  
  Object.keys(payload).forEach(keyStr => {
    const key = keyStr as keyof UdaApiPayload;
    if (payload[key] === undefined) {
      delete payload[key];
    }
  });

  try {
    if (isEditMode.value && udaId.value) {
      await udaStore.updateUda(udaId.value, payload);
      uiStore.addNotification({ message: 'UDA aggiornata con successo!', type: 'success' });
    } else {
      await udaStore.createUda(payload);
      uiStore.addNotification({ message: 'UDA creata con successo!', type: 'success' });
    }
    if (isEditMode.value) {
      // Non fare nulla, l'utente rimane sulla pagina
    } else {
      // Dopo la creazione, reindirizza alla modalità di modifica della nuova UDA
      const newUdaId = udaStore.currentUda?.id;
      if (newUdaId) {
        router.push({ name: 'uda-edit', params: { id: newUdaId } });
      } else {
        router.push({ name: 'uda-list' });
      }
    }
  } catch (error) {
    console.error("Errore durante il salvataggio dell'UDA:", error);
    submitError.value = (error as Error).message || "Errore sconosciuto durante il salvataggio.";
    uiStore.addNotification({ message: `Errore: ${submitError.value}`, type: 'error' });
  } finally {
    isSubmitting.value = false;
  }
};

const handleEditLesson = (lessonId: number) => {
  editingLessonId.value = lessonId;
  showLessonEditModal.value = true;
};

const handleCloseLessonEditModal = () => {
  showLessonEditModal.value = false;
  editingLessonId.value = null;
};

const handleSaveLesson = async (lessonData: any) => {
  try {
    let savedLesson;
    if (lessonData.id) {
      savedLesson = await lessonStore.updateLesson(lessonData.id, lessonData);
    } else {
      savedLesson = await lessonStore.addLesson(lessonData);
    }

    if (savedLesson) {
      // Aggiorna il titolo nella lista dei contenuti dell'UDA
      formData.value.contents = formData.value.contents.map(content => {
        if (content.content_type === 'LESSON' && content.lesson === savedLesson.id) {
          return { ...content, lesson_title: savedLesson.title };
        }
        return content;
      });
    }

    handleCloseLessonEditModal();
    uiStore.addNotification({ message: 'Lezione salvata con successo.', type: 'success' });

  } catch (error) {
    console.error("Errore durante il salvataggio della lezione:", error);
    uiStore.addNotification({ message: 'Errore durante il salvataggio della lezione.', type: 'error' });
  }
};

const handleEditLessonContents = (lessonId: number) => {
  iframeSrc.value = `/lezioni/${lessonId}/contenuti`;
  showIframeModal.value = true;
};

const handleCloseIframeModal = () => {
  showIframeModal.value = false;
  iframeSrc.value = '';
};
</script>

<style scoped>
/* Stili aggiuntivi se necessari */
</style>