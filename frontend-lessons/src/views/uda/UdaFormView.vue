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
          
          <div class="lg:col-span-1">
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

          <div v-if="formData.subjects.length > 0" class="lg:col-span-1">
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
      </div>
      
      <div class="bg-gray-50 border border-gray-300 rounded-lg p-6 shadow-sm">
        <h2 class="text-2xl font-semibold text-neutral-darkest bg-primary-light p-3 rounded-t-md mb-4 shadow-sm">Contenuti dell'UDA</h2>
        <UdaContentEditor
          v-model="formData.contents"
          context="uda"
          :uda-id="isEditMode && udaId ? udaId : undefined"
          :is-editing="true"
        /> <!-- Aggiunto is-editing per mostrare i controlli di modifica/eliminazione -->
      </div>

      <div class="flex justify-end space-x-3 pt-4">
        <RouterLink :to="{ name: 'uda-list' }" class="border border-gray-300 hover:bg-gray-100 text-gray-700 font-medium py-2 px-4 rounded-md shadow-sm">
          Annulla
        </RouterLink>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="isSubmitting">Salvataggio...</span>
          <span v-else>{{ submitButtonText }}</span>
        </button>
      </div>
      <div v-if="submitError" class="text-red-600 mt-2 text-sm">{{ submitError }}</div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import { useUdaStore } from '@/stores/udaStore';
import { useCourseStore } from '@/stores/courseStore';
import { useSubjectStore } from '@/stores/subjectStore';
import { useTopicStore } from '@/stores/topicStore';
import { useUiStore } from '@/stores/ui';
import UdaContentEditor from '@/components/uda/UdaContentEditor.vue';
import { type UDA, type UDAContent } from '@/types/uda';
import type { Course as CourseType } from '@/types/uda'; // Course è in uda.ts, rinominato per evitare conflitto
import type { Subject as SubjectType } from '@/types/subject'; // Rinominato
import type { Topic as TopicType } from '@/types/topic'; // Rinominato

interface UdaFormData {
  title: string;
  description: string | null;
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
const uiStore = useUiStore();

const udaId = computed(() => route.params.id ? Number(route.params.id) : null);


const isEditMode = computed(() => udaId.value !== null);
const pageTitle = computed(() => isEditMode.value ? 'Modifica UDA' : 'Crea Nuova UDA');
const submitButtonText = computed(() => isEditMode.value ? 'Salva Modifiche' : 'Crea UDA');

const loadingInitialData = ref(false);
const initialError = ref<string | null>(null);
const isSubmitting = ref(false);
// const initialLoadComplete = ref(false); // Rimosso completamente
const submitError = ref<string | null>(null);

watch(initialError, (newValue, oldValue) => {
  console.log(`[UdaFormView] initialError cambiato da '${oldValue}' a '${newValue}'`);
  if (newValue !== null) {
    console.trace("[UdaFormView] Traccia per initialError impostato");
  }
});

const formData = ref<UdaFormData>({
  title: '',
  description: null,
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

// Non sono più necessari i watch per sincronizzare formData.topics/subjects con selectedTopicIds/selectedSubjectIds
// perché usiamo formData.topics/subjects direttamente come v-model.

watch(() => udaStore.currentUda?.contents, (newContents) => {
  if (isEditMode.value && udaId.value && udaStore.currentUda && udaStore.currentUda.id === udaId.value) {
    if (newContents && JSON.stringify(newContents) !== JSON.stringify(formData.value.contents)) {
      formData.value.contents = JSON.parse(JSON.stringify(newContents));
    }
  }
}, { deep: true });


onMounted(async () => {
  loadingInitialData.value = true;
  initialError.value = null;
  try {
    const promises = [
      subjectStore.fetchSubjects(),
      courseStore.fetchCourses()
    ];
    await Promise.all(promises);

    if (isEditMode.value && udaId.value) {
      await udaStore.fetchUda(udaId.value);
      const udaToEdit = udaStore.currentUda;
      if (udaToEdit) {
        // Attendi il prossimo ciclo di aggiornamento DOM prima di popolare il form
        // per dare tempo alle opzioni del select (es. corsi) di essere renderizzate.
        formData.value.title = udaToEdit.title;
        formData.value.description = udaToEdit.description || null;
        formData.value.start_date = udaToEdit.start_date || null;
        formData.value.end_date = udaToEdit.end_date || null;
        formData.value.status = udaToEdit.status;
        // Popola prima subjects
        formData.value.subjects = udaToEdit.subjects ? [...udaToEdit.subjects] : [];
        
        formData.value.course = udaToEdit.course || null;
        formData.value.order_in_course = udaToEdit.order_in_course || null;
        formData.value.contents = udaToEdit.contents ? JSON.parse(JSON.stringify(udaToEdit.contents)) : [];
        
        // Se ci sono materie, attendi il caricamento dei relativi argomenti disponibili
        // Il watch su formData.subjects si occuperà di chiamare fetchTopicsBySubject
        // e resetterà formData.topics temporaneamente.
        if (formData.value.subjects && formData.value.subjects.length > 0) {
          await topicStore.fetchTopicsBySubject(formData.value.subjects[0]);
        }
        
        // Attendi che Vue processi gli aggiornamenti DOM e i watch
        await nextTick();
        
        // Ora ripopola formData.topics con i valori corretti dell'UDA.
        // Questo sovrascriverà il reset fatto dal watch se necessario.
        formData.value.topics = udaToEdit.topics ? [...udaToEdit.topics] : [];
      } else {
        initialError.value = `UDA con ID ${udaId.value} non trovata.`;
      }
    }

  } catch (error) {
    console.error("Errore caricamento dati form UDA:", error);
    initialError.value = (error as Error).message || "Errore sconosciuto durante il caricamento.";
  } finally {
    loadingInitialData.value = false;
  }
});

const handleSubmit = async () => {
  isSubmitting.value = true;
  submitError.value = null;

  const payload: UdaApiPayload = {
    title: formData.value.title,
    description: formData.value.description || undefined,
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
    router.push({ name: 'uda-list' });
  } catch (error) {
    console.error("Errore durante il salvataggio dell'UDA:", error);
    submitError.value = (error as Error).message || "Errore sconosciuto durante il salvataggio.";
    uiStore.addNotification({ message: `Errore: ${submitError.value}`, type: 'error' });
  } finally {
    isSubmitting.value = false;
  }
};

</script>

<style scoped>
/* Stili aggiuntivi se necessari */
</style>