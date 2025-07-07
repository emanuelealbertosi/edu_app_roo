<template>
  <div class="uda-detail-view p-4 md:p-8 bg-neutral-lightest min-h-screen">
    <div v-if="pageLoading" class="loading-message">Caricamento dati UDA...</div>
    <div v-if="pageError" class="error-message">
      Errore nel caricamento dell'UDA: {{ pageError }}
    </div>

    <div v-if="uda && !pageLoading && !pageError" class="uda-details-container bg-white shadow-lg rounded-lg p-6">
      <!-- Intestazione con sfondo blu -->
      <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex justify-between items-center">
        <h2 class="text-2xl font-semibold">{{ uda.title }}</h2>
        <!-- Pulsante stile adattato per contrasto -->
        <router-link :to="`/udas/${uda.id}/edit`" class="flex items-center px-3 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-100 transition duration-150 ease-in-out font-medium">
          <PencilIcon class="h-5 w-5 sm:mr-2" />
          <span class="hidden sm:inline">Modifica UDA</span>
        </router-link>
      </div>

      <!-- Blocco Descrizione -->
      <div v-if="uda.description" class="mb-6 p-4 border border-gray-200 rounded-md bg-gray-50">
        <h3 class="text-lg font-semibold text-gray-700 mb-2">Descrizione</h3>
        <p class="text-gray-600 whitespace-pre-wrap">{{ uda.description }}</p>
      </div>

      <!-- Sezioni Conoscenze, Abilità, Competenze -->
      <div class="extended-description-sections my-6 flex flex-wrap gap-4 items-start">
        <CollapsibleEditableSection
          title="Conoscenze"
          :initial-content-html="uda.knowledge_html"
          border-style-class="border-blue-500 border-2 rounded-md"
          @save="handleSaveKnowledge"
          class="flex-1 min-w-[300px]"
        />
        <CollapsibleEditableSection
          title="Abilità"
          :initial-content-html="uda.skills_html"
          border-style-class="border-green-500 border-2 rounded-md"
          @save="handleSaveSkills"
          class="flex-1 min-w-[300px]"
        />
        <CollapsibleEditableSection
          title="Competenze"
          :initial-content-html="uda.competences_html"
          border-style-class="border-purple-500 border-2 rounded-md"
          @save="handleSaveCompetences"
          class="flex-1 min-w-[300px]"
        />
      </div>

      <!-- Sezioni per i campi di esportazione DOCX -->
      <div class="export-specific-sections my-6 flex flex-wrap gap-4 items-start">
        <CollapsibleEditableSection
          title="Strategie Didattiche"
          :initial-content-html="uda.didactic_strategies_html"
          border-style-class="border-yellow-500 border-2 rounded-md"
          @save="handleSaveDidacticStrategies"
          class="flex-1 min-w-[300px]"
        />
        <CollapsibleEditableSection
          title="Materiali e Strumenti"
          :initial-content-html="uda.materials_tools_html"
          border-style-class="border-yellow-500 border-2 rounded-md"
          @save="handleSaveMaterialsTools"
          class="flex-1 min-w-[300px]"
        />
        <CollapsibleEditableSection
          title="Tipo di Verifiche"
          :initial-content-html="uda.assessment_type_html"
          border-style-class="border-yellow-500 border-2 rounded-md"
          @save="handleSaveAssessmentType"
          class="flex-1 min-w-[300px]"
        />
      </div>
      <div class="export-specific-sections my-6 flex flex-wrap gap-4 items-start">
        <CollapsibleEditableSection
          title="Valutazione"
          :initial-content-html="uda.evaluation_html"
          border-style-class="border-orange-500 border-2 rounded-md"
          @save="handleSaveEvaluation"
          class="flex-1 min_w-[300px]"
        />
        <CollapsibleEditableSection
          title="Annotazioni Specifiche"
          :initial-content-html="uda.export_specific_annotations_html"
          border-style-class="border-orange-500 border-2 rounded-md"
          @save="handleSaveExportAnnotations"
          class="flex-1 min-w-[300px]"
        />
        <!-- Sezione per campi non HTML -->
        <div class="flex-1 min-w-[300px] p-4 border border-gray-300 rounded-md bg-gray-50 space-y-2">
          <h3 class="text-md font-semibold text-gray-700">Dati Aggiuntivi UDA</h3>
          <div>
            <strong class="text-gray-800">Educazione Civica:</strong>
            <span class="ml-1">{{ uda.is_civic_education ? 'Sì' : 'No' }}</span>
            <!-- Potrebbe avere un piccolo toggle/bottone per modificarlo rapidamente se necessario -->
          </div>
          <div>
            <strong class="text-gray-800">Altre Discipline Coinvolte:</strong>
            <p class="text-gray-600 whitespace-pre-wrap mt-1">{{ uda.other_involved_subjects_text || 'N/D' }}</p>
            <!-- Anche questo potrebbe avere un modo per modificarlo rapidamente -->
          </div>
        </div>
      </div>


      <!-- Riga Metadati Compatti -->
      <div class="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-gray-600 mb-6 border-t border-b py-4">
        <div>
          <strong class="text-gray-800">Stato:</strong>
          <!-- Modificato per usare un select -->
          <select
            :value="uda.status"
            @change="handleStatusChange"
            :disabled="isStatusUpdating"
            class="ml-1 px-2 py-0.5 rounded-md border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm font-medium shadow-sm"
            :class="getStatusSelectClass(uda.status)"
          >
            <option value="TODO">TODO</option>
            <option value="IN_PROGRESS">IN PROGRESS</option>
            <option value="COMPLETED">COMPLETED</option>
          </select>
          <span v-if="isStatusUpdating" class="ml-2 text-xs text-gray-500">Aggiornamento...</span>
        </div>
        <div v-if="uda.start_date">
          <strong class="text-gray-800">Inizio:</strong>
          <span class="ml-1">{{ formatDate(uda.start_date) }}</span>
        </div>
        <div v-if="uda.end_date">
          <strong class="text-gray-800">Fine:</strong>
          <span class="ml-1">{{ formatDate(uda.end_date) }}</span>
        </div>
        <div v-if="uda.course">
          <strong class="text-gray-800">Corso:</strong>
          <router-link :to="`/courses/${uda.course}`" class="text-indigo-600 hover:text-indigo-800 ml-1">
            {{ courseName || `ID: ${uda.course}` }}
          </router-link>
        </div>
         <div v-if="subjectNames">
          <strong class="text-gray-800">Materie:</strong>
          <router-link :to="{ name: 'uda-edit', params: { id: udaId }, hash: '#subjects-section' }" class="ml-1 text-indigo-600 hover:text-indigo-800 hover:underline" title="Modifica Materie">
            {{ subjectNames }}
          </router-link>
        </div>
         <div v-if="topicNames">
          <strong class="text-gray-800">Argomenti:</strong>
          <router-link :to="{ name: 'uda-edit', params: { id: udaId }, hash: '#topics-section' }" class="ml-1 text-indigo-600 hover:text-indigo-800 hover:underline" title="Modifica Argomenti">
            {{ topicNames }}
          </router-link>
        </div>
      </div>

       <!-- Rimosso blocco metadata separato per Materie/Argomenti -->


      <div class="contents-section mt-8"> <!-- Aggiunto mt-8 per separare dalla riga metadati -->
        <!-- Intestazione Sezione Contenuti con sfondo azzurro -->
        <div class="bg-sky-100 p-4 rounded-md mb-6 flex justify-between items-center border border-sky-200">
          <h2 class="text-xl font-semibold text-sky-800">Contenuti dell'UDA</h2>
          <!-- Eventuali pulsanti azione per contenuti potrebbero andare qui -->
        </div>
        <div v-if="uda.contents && uda.contents.length > 0" class="contents-list space-y-4">
          <!-- Modificato per usare i contenuti arricchiti -->
          <UdaContentItemRenderer
            v-for="(content, index) in enrichedUdaContents"
            :key="content.id || content.temp_id"
            :content="content"
            :uda-id="uda.id"
            context="uda"
            :is-first="index === 0"
            :is-last="index === uda.contents.length - 1"
            @edit="handleEditContent"
            @delete="handleDeleteContent"
            @update:teacher-marked-completed="handleTeacherMarkedCompletedUpdate"
            @update:activity-completed="handleActivityCompletedUpdate"
            @move="handleMoveContent"
            @assign-lesson="handleAssignLesson"
            @edit-lesson="handleEditLesson"
            @assign-quiz="handleAssignQuiz"
            @edit-lesson-contents="handleEditLessonContents"
          ></UdaContentItemRenderer> <!-- Modificato in tag di chiusura esplicito -->
          <!--
            Event handlers (handleEditContent, etc.) and their logic need to be implemented
            if direct manipulation from detail view is desired.
            For now, they are placeholders.
          -->
        </div>
        <p v-else>Nessun contenuto definito per questa UDA.</p>
      </div>
    </div>
    <div v-if="!uda && !pageLoading && pageError" class="no-data-message"> <!-- Mostra se c'è errore e non ci sono dati UDA -->
      <!-- Il messaggio di errore è già mostrato sopra -->
    </div>
     <div v-if="!uda && !pageLoading && !pageError" class="no-data-message"> <!-- Mostra se non c'è loading, non c'è errore, ma non ci sono dati UDA -->
      Nessun dato UDA da visualizzare o UDA non trovata.
    </div>
  </div>

  <!-- Modale Modifica Lezione -->
  <LessonEditModal
    v-if="lessonToEdit"
    :lesson="lessonToEdit"
    :topics="topicStore.topics"
    @close="closeEditModal"
    @save="handleEditSave"
  ></LessonEditModal> <!-- CORRETTO: Tag di chiusura esplicito -->

  <!-- Modale Assegna Lezione -->
  <AssignLessonModal
    :show="isAssignModalOpen"
    :lesson-id="currentLessonIdToAssign"
    @close="closeAssignModal"
    @assignment-complete="handleAssignmentCompleted"
  />

  <!-- Modale Assegna Quiz (Placeholder) -->
  <AssignQuizModal
    v-if="isAssignQuizModalOpen"
    :show="isAssignQuizModalOpen"
    :quiz-template-id="currentQuizTemplateIdToAssign"
    @close="closeAssignQuizModal"
    @assignment-complete="handleQuizAssignmentCompleted"
  />

  <!-- Modale IFrame per modifica contenuti lezione -->
  <IFrameModal
    v-if="showIframeModal"
    :src="iframeSrc"
    title="Modifica Contenuti Lezione"
    @close="handleCloseIframeModal"
  />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import { onMounted, computed, ref } from 'vue';
import { useUdaStore } from '@/stores/udaStore';
import { useCourseStore } from '@/stores/courseStore';
import { useSubjectStore } from '@/stores/subjectStore';
import { useTopicStore } from '@/stores/topicStore';
import { useLessonStore } from '@/stores/lessons'; // Importa lesson store (CORRETTO PATH)
import { useQuizStore } from '@/stores/quizStore';   // Importa quiz store
// Importa tipi separatamente con 'import type'
import type { UDA, UDAContent, LessonUDAContent, QuizUDAContent, UDAStatus } from '@/types/uda'; // Spostato UDAStatus qui
// Importa enum come valori
import { UDAContentType, UDATemplateContentType } from '@/types/uda'; // Rimosso UDAStatus da qui
import UdaContentItemRenderer from '@/components/uda/UdaContentItemRenderer.vue';
import CollapsibleEditableSection from '@/components/uda/CollapsibleEditableSection.vue'; // IMPORTATO NUOVO COMPONENTE
import LessonEditModal from '@/components/features/lezioni/LessonEditModal.vue'; // IMPORTATO MODALE
import AssignLessonModal from '@/components/features/lezioni/AssignLessonModal.vue'; // IMPORTATO MODALE ASSEGNAZIONE
import AssignQuizModal from '@/components/features/quiz/AssignQuizModal.vue'; // IMPORTATO MODALE ASSEGNAZIONE QUIZ
import IFrameModal from '@/components/common/IFrameModal.vue'; // IMPORTATO MODALE IFrame
import type { Lesson } from '@/types/lezioni'; // IMPORTATO TIPO Lesson
import { useUiStore } from '@/stores/ui'; // CORRETTO: Importa da ui.ts
import { PencilIcon } from '@heroicons/vue/24/outline';

const route = useRoute();
// const router = useRouter(); // Rimosso perché non utilizzato
const udaStore = useUdaStore();
const courseStore = useCourseStore(); // Istanzia course store
const subjectStore = useSubjectStore();
const topicStore = useTopicStore();
const lessonStore = useLessonStore(); // Istanzia lesson store (CORRETTO PATH)
const quizStore = useQuizStore();   // Istanzia quiz store
const uiStore = useUiStore();       // Istanzia uiStore

const udaId = computed(() => route.params.id as string);

const uda = computed<UDA | null>(() => udaStore.currentUda);
// Definisci ref locali per lo stato di caricamento e errore della pagina
const pageLoading = ref(true);
const pageError = ref<string | null>(null);
const isStatusUpdating = ref(false); // Ref per lo stato di aggiornamento dello status
const lessonToEdit = ref<Lesson | null>(null); // Ref per la modale di modifica

// Stato per la modale di assegnazione lezione
const isAssignModalOpen = ref(false);
const currentLessonIdToAssign = ref<number | null>(null);

// Stato per la modale di assegnazione quiz
const isAssignQuizModalOpen = ref(false);
const currentQuizTemplateIdToAssign = ref<number | null>(null);

// Stato per la modale IFrame
const showIframeModal = ref(false);
const iframeSrc = ref('');


// Mantieni le computed per i dati, ma non per lo stato di caricamento/errore della pagina
// const loading = computed(() => udaStore.loading); // Questo è lo loading dello store, non della pagina
// const error = computed(() => udaStore.error);     // Questo è l'error dello store

const courseName = computed(() => {
  if (uda.value?.course) {
    return courseStore.getCourseById(uda.value.course)?.name;
  }
  return null;
});

const subjectNames = computed(() => {
  if (uda.value?.subjects_display && uda.value.subjects_display.length > 0) {
    return uda.value.subjects_display.join(', ');
  }
  if (!uda.value?.subjects || uda.value.subjects.length === 0) return null;
  return uda.value.subjects
    .map(id => subjectStore.getSubjectById(id)?.name || `ID:${id}`)
    .join(', ');
});

const topicNames = computed(() => {
  if (uda.value?.topics_display && uda.value.topics_display.length > 0) {
    return uda.value.topics_display.join(', ');
  }
  if (!uda.value?.topics || uda.value.topics.length === 0) return null;
  return uda.value.topics
    .map(id => topicStore.getTopicById(id)?.name || `ID:${id}`)
    .join(', ');
});
// Computed property per arricchire i contenuti UDA con i titoli di lezioni/quiz
const enrichedUdaContents = computed(() => {
  if (!uda.value?.contents) return [];

  return uda.value.contents.map(content => {
    const enrichedContent = { ...content }; // Crea una copia per non mutare lo store

    if (content.content_type === UDAContentType.LESSON || content.content_type === UDATemplateContentType.LESSON) {
      const lessonId = (content as LessonUDAContent).lesson;
      const lesson = lessonStore.getLessonById(lessonId);
      // Usa type assertion 'as any' per aggiungere dinamicamente la proprietà
      if (lesson && !(enrichedContent as any).lesson_title) {
        (enrichedContent as any).lesson_title = lesson.title;
      }
    } else if (content.content_type === UDAContentType.QUIZ || content.content_type === UDATemplateContentType.QUIZ_TEMPLATE) {
      const quizTemplateId = (content as QuizUDAContent).quiz_template;
      const quizTemplate = quizStore.getQuizTemplateById(quizTemplateId);
       // Usa type assertion 'as any' per aggiungere dinamicamente la proprietà
      if (quizTemplate && !(enrichedContent as any).quiz_title) {
        (enrichedContent as any).quiz_title = quizTemplate.title;
      }
    }
    return enrichedContent;
  });
});


// Rimosso getStatusClass perché non utilizzata

// Funzione per ottenere classi CSS specifiche per il select dello stato
const getStatusSelectClass = (status?: UDA['status']) => {
  if (!status) return 'text-gray-700 bg-gray-100 border-gray-300';
  if (status === 'COMPLETED') return 'text-green-700 bg-green-50 border-green-300';
  if (status === 'IN_PROGRESS') return 'text-blue-700 bg-blue-50 border-blue-300';
  if (status === 'TODO') return 'text-yellow-700 bg-yellow-50 border-yellow-300';
  return 'text-gray-700 bg-gray-100 border-gray-300';
};

const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      year: 'numeric', month: 'long', day: 'numeric'
    });
  } catch (e) {
    return dateString; 
  }
};

onMounted(async () => {
  if (udaId.value) {
    const idAsNumber = parseInt(udaId.value, 10);
    if (!isNaN(idAsNumber)) {
      pageLoading.value = true;
      pageError.value = null;
      try {
        // 1. Carica i dati di supporto (corsi, materie, argomenti) in parallelo
        await Promise.all([
          courseStore.fetchCourses(), // Recupera corsi
          subjectStore.fetchSubjects(), // Recupera materie
          topicStore.fetchTopics(),     // Recupera argomenti
          lessonStore.fetchLessons(),   // Recupera lezioni (CORRETTO PATH)
          quizStore.fetchQuizTemplates() // Recupera template quiz
        ]);

        // 2. Solo dopo che i dati di supporto sono caricati, carica l'UDA specifica
        await udaStore.fetchUda(idAsNumber); // Questo aggiornerà udaStore.currentUda e udaStore.loading/error

        // Verifica se l'UDA è stata effettivamente caricata (potrebbe dare 404 o altro errore gestito dallo store)
        if (udaStore.error) { // Controlla l'errore dello store dopo il fetch
            throw new Error(udaStore.error);
        }
        if (!uda.value) { // Se non c'è errore ma l'uda è ancora null, consideralo un errore
            throw new Error(`UDA con ID ${idAsNumber} non trovata.`);
        }

      } catch (err) {
         console.error("Errore durante il caricamento dei dati UDA per la vista dettaglio:", err);
         pageError.value = (err as Error).message || 'Errore sconosciuto durante il caricamento.';
      } finally {
         pageLoading.value = false;
      }
    } else {
      console.error("ID UDA non valido fornito nella route:", udaId.value);
      pageError.value = "ID UDA non valido.";
      pageLoading.value = false;
    }
  } else {
     pageError.value = "ID UDA non specificato.";
     pageLoading.value = false;
  }
});

// TODO: Gestire la visualizzazione del corso di appartenenza (recuperare nome da ID)
// TODO: Gestire la visualizzazione di materia e argomenti (recuperare nomi da ID)

const handleEditContent = (contentItem: UDAContent) => {
  console.log('Edit content:', contentItem);
  alert(`Modifica contenuto (ID: ${contentItem.id || contentItem.temp_id}) - Implementare navigazione/modale`);
};

const handleDeleteContent = (contentId: number | string) => {
  console.log('Delete content ID:', contentId);
  alert(`Elimina contenuto (ID: ${contentId}) - Implementare logica e conferma`);
};

// Rimossa importazione 'ref' non più necessaria qui
// Rimossa la funzione handleMoveContent dalla vista dettaglio
// L'ordinamento verrà gestito nella vista di modifica (UdaFormView.vue)

const handleTeacherMarkedCompletedUpdate = (payload: { contentId: number, completed: boolean }) => {
  console.log('Teacher marked completed update:', payload);
};

const handleActivityCompletedUpdate = (payload: { contentId: number, completed: boolean }) => {
  console.log('Activity completed update:', payload);
};

const handleAssignLesson = (lessonIdInput: number | string) => {
  console.log(`Assign lesson with ID: ${lessonIdInput} from UdaDetailView`);
  const idAsNumber = typeof lessonIdInput === 'string' ? parseInt(lessonIdInput, 10) : lessonIdInput;

  if (isNaN(idAsNumber)) {
    console.error(`Invalid lessonId: ${lessonIdInput}. Cannot open assign modal.`);
    currentLessonIdToAssign.value = null;
    // Potresti voler mostrare una notifica all'utente qui
    uiStore.addNotification({ message: 'ID lezione non valido per l\'assegnazione.', type: 'error' });
    return;
  }
  currentLessonIdToAssign.value = idAsNumber;
  isAssignModalOpen.value = true;
};

const closeAssignModal = () => {
  isAssignModalOpen.value = false;
  currentLessonIdToAssign.value = null;
};

const handleAssignmentCompleted = () => {
  uiStore.addNotification({ message: 'Lezione assegnata con successo!', type: 'success', duration: 3000 });
  closeAssignModal();
  // Potrebbe essere necessario ricaricare/aggiornare dati se l'assegnazione modifica lo stato visualizzato
};

const handleAssignQuiz = (quizTemplateIdInput: number | string) => {
  console.log(`Assign quiz template with ID: ${quizTemplateIdInput} from UdaDetailView`);
  const idAsNumber = typeof quizTemplateIdInput === 'string' ? parseInt(quizTemplateIdInput, 10) : quizTemplateIdInput;

  if (isNaN(idAsNumber)) {
    console.error(`Invalid quizTemplateId: ${quizTemplateIdInput}. Cannot open assign modal.`);
    uiStore.addNotification({ message: 'ID template quiz non valido per l\'assegnazione.', type: 'error' });
    return;
  }
  currentQuizTemplateIdToAssign.value = idAsNumber;
  isAssignQuizModalOpen.value = true;
};

const closeAssignQuizModal = () => {
  isAssignQuizModalOpen.value = false;
  currentQuizTemplateIdToAssign.value = null;
};

const handleQuizAssignmentCompleted = () => {
  uiStore.addNotification({ message: 'Quiz assegnato con successo!', type: 'success', duration: 3000 });
  closeAssignQuizModal();
  // Eventuale logica di refresh dati se necessario
};

const handleEditLessonContents = (lessonId: number) => {
  console.log(`Request to edit contents for lesson ID: ${lessonId}`);
  iframeSrc.value = `/lezioni/${lessonId}/contenuti?modal=true`;
  showIframeModal.value = true;
};

const handleCloseIframeModal = () => {
  showIframeModal.value = false;
  iframeSrc.value = '';
  // Potrebbe essere necessario un refresh dei dati se i contenuti sono cambiati
  // uiStore.addNotification({ message: 'Contenuti aggiornati.', type: 'info' });
  // onMounted(); // Attenzione: ricarica tutto
};


// Funzione per gestire il cambio di stato
const handleStatusChange = async (event: Event) => {
  if (!uda.value || !uda.value.id) return;

  const target = event.target as HTMLSelectElement;
  const newStatus = target.value as UDAStatus; // Assicurati che UDAStatus sia importato

  if (newStatus === uda.value.status) return; // Nessun cambiamento

  isStatusUpdating.value = true;
  try {
    await udaStore.updateUda(uda.value.id, { status: newStatus });
    // Lo store dovrebbe aggiornare automaticamente currentUda, quindi la UI si aggiorna.
    uiStore.addNotification({ message: 'Stato UDA aggiornato con successo!', type: 'success', duration: 3000 }); // Usa addNotification
  } catch (error) {
    console.error("Errore durante l'aggiornamento dello stato UDA:", error);
    uiStore.addNotification({ message: `Errore nell'aggiornamento dello stato: ${(error as Error).message}`, type: 'error', duration: 5000 }); // Usa addNotification
    // Opzionale: ripristina il valore del select allo stato precedente in caso di errore
    target.value = uda.value.status;
  } finally {
    isStatusUpdating.value = false;
  }
};

const handleMoveContent = async (contentToMove: UDAContent, direction: number) => {
  if (!uda.value || !uda.value.contents || !uda.value.id) {
    console.error("UDA o contenuti non disponibili per lo spostamento.");
    return;
  }

  const currentIndex = uda.value.contents.findIndex(c => (c.id || c.temp_id) === (contentToMove.id || contentToMove.temp_id));
  if (currentIndex === -1) {
    console.error("Contenuto da spostare non trovato nell'array.");
    return;
  }

  const newIndex = currentIndex + direction;

  // Verifica se il nuovo indice è valido
  if (newIndex < 0 || newIndex >= uda.value.contents.length) {
    console.warn("Spostamento non valido (fuori dai limiti).");
    return;
  }

  // Crea una copia dell'array dei contenuti
  const newContentsOrder = [...uda.value.contents];

  // Rimuovi l'elemento dalla posizione corrente
  const [movedItem] = newContentsOrder.splice(currentIndex, 1);

  // Inserisci l'elemento nella nuova posizione
  newContentsOrder.splice(newIndex, 0, movedItem);

  // Estrai gli ID nel nuovo ordine (assicurati che tutti abbiano un ID valido)
  const orderedContentIds = newContentsOrder.map(c => c.id).filter((id): id is number => id !== undefined && id !== null);

  // Verifica se tutti i contenuti hanno un ID valido prima di chiamare l'API
  if (orderedContentIds.length !== newContentsOrder.length) {
      console.error("Errore: alcuni contenuti mancano di ID validi. Impossibile riordinare.");
      // Potresti mostrare un messaggio all'utente qui
      return;
  }


  try {
    // Chiama l'azione dello store per aggiornare il backend
    await udaStore.reorderUdaContents(uda.value.id, orderedContentIds);
    // Lo store aggiornerà automaticamente this.currentUda.contents,
    // quindi la UI si aggiornerà reattivamente.
    console.log('Contenuti riordinati con successo.');
  } catch (error) {
    console.error("Errore durante il riordino dei contenuti:", error);
    // Potrebbe essere utile mostrare un messaggio di errore all'utente
    // e potenzialmente ripristinare l'ordine visivo precedente se necessario.
  }
};

// Funzioni per salvare Conoscenze, Abilità, Competenze
const handleSaveKnowledge = async (newHtml: string) => {
  if (uda.value?.id) {
    try {
      await udaStore.updateUda(uda.value.id, { knowledge_html: newHtml });
      uiStore.addNotification({ message: 'Conoscenze aggiornate!', type: 'success' });
    } catch (e) {
      uiStore.addNotification({ message: `Errore aggiornamento Conoscenze: ${(e as Error).message}`, type: 'error' });
      throw e; // Rilancia l'errore per farlo gestire dal componente figlio (mostra messaggio errore)
    }
  }
};

const handleSaveSkills = async (newHtml: string) => {
  if (uda.value?.id) {
    try {
      await udaStore.updateUda(uda.value.id, { skills_html: newHtml });
      uiStore.addNotification({ message: 'Abilità aggiornate!', type: 'success' });
    } catch (e) {
      uiStore.addNotification({ message: `Errore aggiornamento Abilità: ${(e as Error).message}`, type: 'error' });
      throw e;
    }
  }
};

const handleSaveCompetences = async (newHtml: string) => {
  if (uda.value?.id) {
    try {
      await udaStore.updateUda(uda.value.id, { competences_html: newHtml });
      uiStore.addNotification({ message: 'Competenze aggiornate!', type: 'success' });
    } catch (e) {
      uiStore.addNotification({ message: `Errore aggiornamento Competenze: ${(e as Error).message}`, type: 'error' });
      throw e;
    }
  }
};

const handleSaveDidacticStrategies = async (newHtml: string) => {
  if (uda.value?.id) {
    try {
      await udaStore.updateUda(uda.value.id, { didactic_strategies_html: newHtml });
      uiStore.addNotification({ message: 'Strategie Didattiche (Export) aggiornate!', type: 'success' });
    } catch (e) {
      uiStore.addNotification({ message: `Errore aggiornamento Strategie Didattiche: ${(e as Error).message}`, type: 'error' });
      throw e;
    }
  }
};

const handleSaveMaterialsTools = async (newHtml: string) => {
  if (uda.value?.id) {
    try {
      await udaStore.updateUda(uda.value.id, { materials_tools_html: newHtml });
      uiStore.addNotification({ message: 'Materiali e Strumenti (Export) aggiornati!', type: 'success' });
    } catch (e) {
      uiStore.addNotification({ message: `Errore aggiornamento Materiali e Strumenti: ${(e as Error).message}`, type: 'error' });
      throw e;
    }
  }
};

const handleSaveAssessmentType = async (newHtml: string) => {
  if (uda.value?.id) {
    try {
      await udaStore.updateUda(uda.value.id, { assessment_type_html: newHtml });
      uiStore.addNotification({ message: 'Tipo di Verifiche (Export) aggiornato!', type: 'success' });
    } catch (e) {
      uiStore.addNotification({ message: `Errore aggiornamento Tipo di Verifiche: ${(e as Error).message}`, type: 'error' });
      throw e;
    }
  }
};

const handleSaveEvaluation = async (newHtml: string) => {
  if (uda.value?.id) {
    try {
      await udaStore.updateUda(uda.value.id, { evaluation_html: newHtml });
      uiStore.addNotification({ message: 'Valutazione (Export) aggiornata!', type: 'success' });
    } catch (e) {
      uiStore.addNotification({ message: `Errore aggiornamento Valutazione: ${(e as Error).message}`, type: 'error' });
      throw e;
    }
  }
};

const handleSaveExportAnnotations = async (newHtml: string) => {
  if (uda.value?.id) {
    try {
      await udaStore.updateUda(uda.value.id, { export_specific_annotations_html: newHtml });
      uiStore.addNotification({ message: 'Annotazioni Specifiche (Export) aggiornate!', type: 'success' });
    } catch (e) {
      uiStore.addNotification({ message: `Errore aggiornamento Annotazioni Specifiche: ${(e as Error).message}`, type: 'error' });
      throw e;
    }
  }
};

// Funzione per gestire il click sul bottone "Modifica" Lezione -> Apre Modale
const handleEditLesson = (lessonId: number) => {
  if (!lessonId) {
    console.error("ID Lezione non valido per la modifica.");
    uiStore.addNotification({ message: "ID Lezione non valido.", type: 'error' });
    return;
  }
  const lesson = lessonStore.getLessonById(lessonId);
  if (lesson) {
    lessonToEdit.value = { ...lesson }; // Imposta la ref per aprire la modale
  } else {
    console.error(`Lezione con ID ${lessonId} non trovata nello store.`);
    uiStore.addNotification({ message: `Lezione con ID ${lessonId} non trovata.`, type: 'error' });
  }
};

// Funzione per chiudere la modale di modifica
const closeEditModal = () => {
  lessonToEdit.value = null;
};

// Funzione per salvare le modifiche dalla modale
const handleEditSave = async (lessonData: { id?: number; title: string; topic: number; description?: string; is_published?: boolean }) => {
  if (!lessonData.id) {
      console.error("ID lezione mancante per l'aggiornamento.");
      uiStore.addNotification({ message: "Errore: ID lezione mancante.", type: 'error' });
      return;
  }

  const success = await lessonStore.updateLesson(lessonData.id, lessonData);

  if (success) {
      closeEditModal();
      // Non è necessario fetchLessons se lo store è reattivo e aggiorna l'elemento
      // await lessonStore.fetchLessons(); // Ricarica solo se necessario
      uiStore.addNotification({ message: 'Lezione aggiornata con successo!', type: 'success' });
      // Potrebbe essere necessario aggiornare enrichedUdaContents se il titolo è cambiato,
      // ma la reattività di Pinia dovrebbe gestire questo automaticamente se getLessonById restituisce dati aggiornati.
  } else {
       uiStore.addNotification({ message: `Errore durante l'aggiornamento: ${lessonStore.error || 'Errore sconosciuto'}`, type: 'error' });
       lessonStore.error = null; // Resetta l'errore nello store
  }
};

</script>

<style scoped>
.uda-detail-view {
  padding: 20px;
}

.loading-message, .error-message, .no-data-message {
  text-align: center;
  padding: 20px;
  font-size: 1.2em;
}

.error-message {
  color: red;
  background-color: #ffe0e0;
  border: 1px solid red;
  border-radius: 5px;
}

.uda-details-container {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* Rimosse regole CSS scoped che confliggono con Tailwind */
/* .header-actions h1 { ... } */

.btn { /* Mantenuto se usato altrove, ma il bottone Modifica ora usa classi Tailwind */
  padding: 8px 15px;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.9em;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
  border-color: #6c757d;
}
.btn-secondary:hover {
  background-color: #5a6268;
  border-color: #545b62;
}

.description {
  margin-bottom: 20px;
  color: #555;
  line-height: 1.6;
}

.metadata {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border: 1px solid #eee;
  border-radius: 5px;
}

.metadata p, .metadata div {
  margin-bottom: 8px;
}

.metadata strong {
  color: #444;
}

.metadata ul {
  list-style-type: disc;
  padding-left: 20px;
  margin-top: 5px;
}

.contents-section {
  margin-top: 30px;
}

.contents-section h2 {
  border-bottom: 2px solid #eee;
  padding-bottom: 10px;
  margin-bottom: 20px;
  color: #333;
}

.contents-list > div { 
  margin-bottom: 15px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 5px;
}
</style>