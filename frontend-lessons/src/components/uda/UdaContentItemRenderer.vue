<template>
  <div class="bg-white shadow rounded-lg mb-3 border" :class="contentBorderClass">
    <!-- RIGA 1: Intestazioni e Azioni -->
    <div class="p-3 border-b border-gray-200">
      <div class="flex justify-between items-center space-x-3">
        
        <div class="flex-grow flex items-center space-x-2 min-w-0">
          <span :class="contentTypeLabelClass(content.content_type)" class="px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0">
            {{ मानविकीकरणContentType(content.content_type) }}
          </span>
          <div class="flex-grow min-w-0">
            <h6 class="text-base font-semibold text-slate-900 truncate" :title="contentTitle">{{ contentTitle }}</h6>
            <div v-if="(content.content_type === UDAContentType.LESSON || content.content_type === UDATemplateContentType.LESSON) && (lessonSubjectName || lessonTopicName)" class="flex items-center space-x-1.5 mt-0.5 text-xs">
              <span v-if="lessonSubjectName" class="px-1.5 py-0.5 rounded-full bg-teal-100 text-teal-800 whitespace-nowrap">M: {{ lessonSubjectName }}</span>
              <span v-if="lessonTopicName" class="px-1.5 py-0.5 rounded-full bg-cyan-100 text-cyan-800 whitespace-nowrap">A: {{ lessonTopicName }}</span>
            </div>
          </div>
        </div>

        
        <div class="flex items-center space-x-2 flex-shrink-0">
          
          <button
            v-if="isUDAContext && content.content_type === UDAContentType.LESSON && !props.isEditing"
            @click="toggleManualAssignment"
            type="button"
            class="p-1 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            :aria-label="isManuallyMarkedAssigned ? 'Marca come non assegnata' : 'Marca come assegnata'"
            :title="isManuallyMarkedAssigned ? 'Marca come non assegnata' : 'Marca come assegnata'"
          >
            <CheckCircleIcon v-if="isManuallyMarkedAssigned" class="h-5 w-5 text-green-500" />
            <XCircleIcon v-else class="h-5 w-5 text-red-500" />
          </button>

          
          <div v-if="isUDAContext && content.content_type !== 'ACTIVITY_TEMPLATE' && content.content_type !== 'NOTE_TEMPLATE'" class="flex items-center space-x-1">
            <label :for="`teacherMarkedCompleted-${content.id || content.temp_id}`" class="text-xs text-gray-600 select-none whitespace-nowrap">Completata:</label>
            <button
              type="button"
              @click="toggleTeacherMarkedCompleted"
              :disabled="isLoadingCompletion"
              :class="[
                isTeacherMarkedCompleted ? 'bg-indigo-600' : 'bg-gray-200',
                'relative inline-flex flex-shrink-0 h-5 w-9 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed'
              ]"
              role="switch"
              :aria-checked="isTeacherMarkedCompleted"
            >
              <span class="sr-only">Completata</span>
              <span
                aria-hidden="true"
                :class="[
                  isTeacherMarkedCompleted ? 'translate-x-4' : 'translate-x-0',
                  'pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200'
                ]"
              ></span>
            </button>
          </div>

          
          <div class="flex items-center space-x-1.5">
            
            <button
              @click="emit('move', content, -1)"
              :disabled="props.isFirst"
              type="button"
              class="p-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Sposta Su"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
              </svg>
            </button>
            <button
              @click="emit('move', content, 1)"
              :disabled="props.isLast"
              type="button"
              class="p-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Sposta Giù"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            
            <div v-if="isEditing" class="flex items-center space-x-1.5">
              <button
                @click="emit('edit', content)"
                type="button"
                class="p-1.5 border border-gray-300 shadow-sm rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500"
                title="Modifica questo contenuto"
              >
                <PencilIcon class="h-4 w-4 text-gray-500" />
              </button>
              <button
                @click="emit('delete', content)"
                type="button"
                class="p-1.5 border border-transparent shadow-sm rounded text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-500"
                title="Elimina questo contenuto"
              >
                <TrashIcon class="h-4 w-4" />
              </button>
            </div>
          </div>

          
          <div v-if="isUDAContext && content.content_type === UDAContentType.LESSON && content.lesson && !props.isEditing" class="flex items-center space-x-1.5">
             <button
               @click="emitEditLesson"
               type="button"
               class="p-1.5 border border-gray-300 shadow-sm rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500"
               title="Modifica Lezione"
             >
               <PencilSquareIcon class="h-4 w-4 text-gray-500" />
             </button>
              <router-link
               :to="`/lezioni/${content.lesson}/contenuti`"
               class="p-1.5 border border-gray-300 shadow-sm rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500"
               rel="noopener noreferrer"
               title="Vai ai Contenuti della Lezione"
             >
               <DocumentTextIcon class="h-4 w-4 text-gray-500" />
             </router-link>
             <button
               @click="emitAssignLesson"
               type="button"
               class="p-1.5 border border-transparent shadow-sm rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500"
               title="Assegna Lezione"
             >
               <UserPlusIcon class="h-4 w-4" />
             </button>
          </div>
          <!-- Pulsante Assegna Quiz -->
          <div v-if="isUDAContext && (content.content_type === UDAContentType.QUIZ || content.content_type === UDATemplateContentType.QUIZ_TEMPLATE) && (content as QuizUDAContent).quiz_template && !props.isEditing" class="flex items-center space-x-1.5">
            <button
                @click="emitAssignQuiz"
                type="button"
                class="p-1.5 border border-transparent shadow-sm rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-green-500"
                title="Assegna Quiz"
            >
                <UserPlusIcon class="h-4 w-4" />
                <span class="sr-only">Assegna Quiz</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    
    <div class="p-3">
      
      <div class="mt-0" v-if="content.content_type === UDAContentType.LESSON || content.content_type === UDATemplateContentType.LESSON">
        <LessonContentDisplay :content="content as LessonUDAContent" @details-loaded="handleLessonDetailsLoaded" />
      </div>
      <div class="mt-0" v-else-if="content.content_type === UDAContentType.QUIZ || content.content_type === UDATemplateContentType.QUIZ_TEMPLATE">
        <QuizContentDisplay :content="content as QuizUDAContent" />
      </div>
      <div class="mt-0" v-else-if="content.content_type === UDAContentType.NOTE">
        <NoteContentDisplay :content="content as NoteUDAContent" />
      </div>
      <div class="mt-0" v-else-if="content.content_type === UDATemplateContentType.NOTE_TEMPLATE">
        <NoteTemplateContentDisplay :content="content as NoteTemplateUDAContent" />
      </div>
      <div class="mt-0" v-else-if="content.content_type === UDAContentType.ACTIVITY">
        <ActivityContentDisplay :content="content as ActivityUDAContent" @update:activity-completed="handleActivityCompletedUpdate" :is-loading-activity-completion="isLoadingActivityCompletion"/>
      </div>
      <div class="mt-0" v-else-if="content.content_type === UDATemplateContentType.ACTIVITY_TEMPLATE">
        <ActivityTemplateContentDisplay :content="content as ActivityTemplateUDAContent" />
      </div>
      <div class="mt-0" v-else>
        <p class="text-danger">Tipo di contenuto non riconosciuto: {{ content.content_type }}</p>
        <pre>{{ content }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType, ref } from 'vue';
import type {
  UDAContent, UDATemplateContent,
  LessonUDAContent, QuizUDAContent, NoteUDAContent, ActivityUDAContent,
  NoteTemplateUDAContent, ActivityTemplateUDAContent
} from '@/types/uda';
import { UDAContentType, UDATemplateContentType } from '@/types/uda';
import { useUdaStore } from '@/stores/udaStore';
import { CheckCircleIcon, XCircleIcon, PencilIcon, TrashIcon, PencilSquareIcon, DocumentTextIcon, UserPlusIcon, PaperAirplaneIcon } from '@heroicons/vue/24/outline';

import LessonContentDisplay from '@/components/uda/content-display/LessonContentDisplay.vue';
import QuizContentDisplay from '@/components/uda/content-display/QuizContentDisplay.vue';
import NoteContentDisplay from '@/components/uda/content-display/NoteContentDisplay.vue';
import ActivityContentDisplay from '@/components/uda/content-display/ActivityContentDisplay.vue';
import NoteTemplateContentDisplay from '@/components/uda/content-display/NoteTemplateContentDisplay.vue';
import ActivityTemplateContentDisplay from '@/components/uda/content-display/ActivityTemplateContentDisplay.vue';

const props = defineProps({
  content: {
    type: Object as PropType<UDAContent | UDATemplateContent>,
    required: true
  },
  isFirst: {
    type: Boolean,
    default: false
  },
  isLast: {
    type: Boolean,
    default: false
  },
  udaId: {
    type: Number,
    required: false
  },
  context: {
    type: String as PropType<'uda' | 'template'>,
    required: true
  },
  isEditing: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['edit', 'delete', 'move', 'update:teacher-marked-completed', 'update:activity-completed', 'assign-lesson', 'edit-lesson', 'assign-quiz']);

const udaStore = useUdaStore();
const isLoadingCompletion = ref(false);
const isLoadingActivityCompletion = ref(false);
const lessonSubjectName = ref<string | null | undefined>(null);
const lessonTopicName = ref<string | null | undefined>(null);
const isManuallyMarkedAssigned = ref(false);

const isUDAContext = computed(() => props.context === 'uda');

const isTeacherMarkedCompleted = computed(() => {
  if (isUDAContext.value && 'teacher_marked_completed' in props.content) {
    return (props.content as UDAContent).teacher_marked_completed || false;
  }
  return false;
});

const contentTitle = computed(() => {
  const genericTitle = (props.content as any)?.title;
  switch (props.content.content_type) {
    case UDAContentType.LESSON:
    case UDATemplateContentType.LESSON:
      return (props.content as LessonUDAContent).lesson_title || genericTitle || 'Lezione';
    case UDAContentType.QUIZ:
    case UDATemplateContentType.QUIZ_TEMPLATE:
      return (props.content as QuizUDAContent).quiz_title || genericTitle || 'Quiz';
    case UDAContentType.NOTE:
      return (props.content as NoteUDAContent).note_title || 'Nota';
    case UDATemplateContentType.NOTE_TEMPLATE:
      return (props.content as NoteTemplateUDAContent).note_template_title || 'Template Nota senza titolo';
    case UDAContentType.ACTIVITY:
      return (props.content as ActivityUDAContent).activity_title || 'Attività senza titolo';
    case UDATemplateContentType.ACTIVITY_TEMPLATE:
      return (props.content as ActivityTemplateUDAContent).activity_template_title || 'Template Attività senza titolo';
    default:
      return 'Contenuto Sconosciuto';
  }
});

const मानविकीकरणContentType = (type: UDAContentType | UDATemplateContentType): string => {
  const map: Record<string, string> = {
    'LESSON': 'Lezione',
    'QUIZ': 'Quiz',
    'QUIZ_TEMPLATE': 'Quiz (da Template)',
    'NOTE': 'Nota',
    'ACTIVITY': 'Attività',
    'NOTE_TEMPLATE': 'Template Nota',
    'ACTIVITY_TEMPLATE': 'Template Attività',
  };
  return map[type as string] || type;
};

const contentTypeLabelClass = (type: UDAContentType | UDATemplateContentType): string => {
  const baseClass = "px-2 py-0.5 rounded-full text-xs font-medium";
  switch (type) {
    case UDAContentType.LESSON:
    case UDATemplateContentType.LESSON:
      return `${baseClass} bg-blue-100 text-blue-800`;
    case UDAContentType.QUIZ:
    case UDATemplateContentType.QUIZ_TEMPLATE:
      return `${baseClass} bg-green-100 text-green-800`;
    case UDAContentType.NOTE:
    case UDATemplateContentType.NOTE_TEMPLATE:
      return `${baseClass} bg-yellow-100 text-yellow-800`;
    case UDAContentType.ACTIVITY:
    case UDATemplateContentType.ACTIVITY_TEMPLATE:
      return `${baseClass} bg-purple-100 text-purple-800`;
    default:
      return `${baseClass} bg-gray-100 text-gray-800`;
  }
};

const contentBorderClass = computed(() => {
  switch (props.content.content_type) {
    case UDAContentType.LESSON:
    case UDATemplateContentType.LESSON:
      return 'border-blue-300';
    case UDAContentType.QUIZ:
    case UDATemplateContentType.QUIZ_TEMPLATE:
      return 'border-green-300';
    case UDAContentType.NOTE:
    case UDATemplateContentType.NOTE_TEMPLATE:
      return 'border-yellow-300';
    case UDAContentType.ACTIVITY:
    case UDATemplateContentType.ACTIVITY_TEMPLATE:
      return 'border-purple-300';
    default:
      return 'border-gray-300'; 
  }
});


const toggleTeacherMarkedCompleted = async () => {
  if (!isUDAContext.value || !props.udaId || !props.content.id) return;
  isLoadingCompletion.value = true;
  try {
    const currentStatus = (props.content as UDAContent).teacher_marked_completed || false;
    const newStatus = !currentStatus;
    await udaStore.updateUdaContentTeacherCompletion(props.udaId, props.content.id, newStatus);
    emit('update:teacher-marked-completed', { contentId: props.content.id, completed: newStatus });
  } catch (error) {
    console.error("Errore nell'aggiornare lo stato teacher_marked_completed:", error);
  } finally {
    isLoadingCompletion.value = false;
  }
};

const handleActivityCompletedUpdate = async (completed: boolean) => {
  if (!isUDAContext.value || !props.udaId || !props.content.id || props.content.content_type !== UDAContentType.ACTIVITY) return;
  isLoadingActivityCompletion.value = true;
  try {
    await udaStore.completeActivityInUda(props.udaId, props.content.id, completed);
    emit('update:activity-completed', { contentId: props.content.id, completed });
  } catch (error) {
    console.error("Errore nell'aggiornare lo stato activity_completed:", error);
  } finally {
    isLoadingActivityCompletion.value = false;
  }
};

const handleLessonDetailsLoaded = (details: { subjectName?: string | null, topicName?: string | null }) => {
  lessonSubjectName.value = details.subjectName;
  lessonTopicName.value = details.topicName;
};

const emitAssignLesson = () => {
  if (isUDAContext.value && props.content.content_type === UDAContentType.LESSON && props.content.lesson) {
    emit('assign-lesson', props.content.lesson);
  }
};

const emitEditLesson = () => {
  if (isUDAContext.value && props.content.content_type === UDAContentType.LESSON && props.content.lesson) {
    emit('edit-lesson', props.content.lesson);
  }
};

const emitAssignQuiz = () => {
  if (isUDAContext.value && (props.content.content_type === UDAContentType.QUIZ || props.content.content_type === UDATemplateContentType.QUIZ_TEMPLATE) && (props.content as QuizUDAContent).quiz_template) {
    emit('assign-quiz', (props.content as QuizUDAContent).quiz_template);
  }
};

const toggleManualAssignment = () => {
  isManuallyMarkedAssigned.value = !isManuallyMarkedAssigned.value;
};

</script>

<style scoped>
/* Stili principali gestiti da Tailwind. */
</style>