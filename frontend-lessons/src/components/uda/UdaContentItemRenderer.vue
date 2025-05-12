<template>
  <div class="bg-white shadow rounded-lg mb-4 border border-gray-200">
    <div class="p-4">
      <div class="flex justify-between items-start mb-3">
        <div>
          <h6 class="text-lg font-semibold text-neutral-darkest bg-neutral-light p-2 rounded-md mb-1">{{ contentTitle }}</h6>
          <small class="text-gray-500 text-xs">Tipo: {{ मानविकीकरणContentType(content.content_type) }} | Ordine: {{ content.order }}</small>
        </div>
        <!-- Switch Personalizzato con Tailwind -->
        <div v-if="isUDAContext && content.content_type !== 'ACTIVITY_TEMPLATE' && content.content_type !== 'NOTE_TEMPLATE'" class="flex items-center space-x-2">
           <label :for="`teacherMarkedCompleted-${content.id || content.temp_id}`" class="text-sm text-gray-600 select-none">Completato Docente:</label>
          <button
            type="button"
            @click="toggleTeacherMarkedCompleted"
            :disabled="isLoadingCompletion"
            :class="[
              isTeacherMarkedCompleted ? 'bg-indigo-600' : 'bg-gray-200',
              'relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed'
            ]"
            role="switch"
            :aria-checked="isTeacherMarkedCompleted"
          >
            <span class="sr-only">Completato dal Docente</span>
            <span
              aria-hidden="true"
              :class="[
                isTeacherMarkedCompleted ? 'translate-x-5' : 'translate-x-0',
                'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200'
              ]"
            ></span>
          </button>
        </div>
      </div>
      <hr class="my-3 border-gray-200" />

      <!-- Visualizzazione specifica per tipo di contenuto -->
      <div class="mt-3" v-if="content.content_type === UDAContentType.LESSON || content.content_type === UDATemplateContentType.LESSON">
        <LessonContentDisplay :content="content as LessonUDAContent" />
      </div>
      <div v-else-if="content.content_type === UDAContentType.QUIZ || content.content_type === UDATemplateContentType.QUIZ_TEMPLATE">
        <QuizContentDisplay :content="content as QuizUDAContent" />
      </div>
      <div v-else-if="content.content_type === UDAContentType.NOTE">
        <NoteContentDisplay :content="content as NoteUDAContent" />
      </div>
      <div v-else-if="content.content_type === UDATemplateContentType.NOTE_TEMPLATE">
        <NoteTemplateContentDisplay :content="content as NoteTemplateUDAContent" />
      </div>
      <div v-else-if="content.content_type === UDAContentType.ACTIVITY">
        <ActivityContentDisplay :content="content as ActivityUDAContent" @update:activity-completed="handleActivityCompletedUpdate" :is-loading-activity-completion="isLoadingActivityCompletion"/>
      </div>
      <div v-else-if="content.content_type === UDATemplateContentType.ACTIVITY_TEMPLATE">
        <ActivityTemplateContentDisplay :content="content as ActivityTemplateUDAContent" />
      </div>
      <div v-else>
        <p class="text-danger">Tipo di contenuto non riconosciuto: {{ content.content_type }}</p>
        <pre>{{ content }}</pre>
      </div>

      <!-- Azioni sull'item (Modifica, Elimina, Sposta) -->
      <div class="mt-4 pt-3 border-t border-gray-200 flex space-x-2">
        <!-- TODO: Sostituire con icone Heroicons -->
        <button type="button"
                class="text-sm border border-indigo-500 text-indigo-500 hover:bg-indigo-50 font-medium py-1 px-3 rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                @click="$emit('edit', content)"
                :disabled="isLoadingCompletion || isLoadingActivityCompletion">
          Modifica
        </button>
        <button type="button"
                class="text-sm border border-red-500 text-red-500 hover:bg-red-50 font-medium py-1 px-3 rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                @click="$emit('delete', content.temp_id || content.id)"
                :disabled="isLoadingCompletion || isLoadingActivityCompletion">
          Elimina
        </button>
        <!-- Mostra i bottoni di spostamento solo se siamo nel contesto 'uda' -->
        <template v-if="context === 'uda'">
          <button type="button"
                  class="text-sm border border-gray-300 text-gray-600 hover:bg-gray-100 font-medium py-1 px-3 rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  @click="$emit('move', content, -1)"
                  :disabled="isFirst || isLoadingCompletion || isLoadingActivityCompletion">
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fill-rule="evenodd" d="M3.293 9.707a1 1 0 011.414 0L10 5.414l5.293 4.293a1 1 0 011.414-1.414l-6-4.879a1 1 0 01-1.414 0l-6 4.879a1 1 0 010 1.414z" clip-rule="evenodd" />
            </svg>
          </button>
          <button type="button"
                  class="text-sm border border-gray-300 text-gray-600 hover:bg-gray-100 font-medium py-1 px-3 rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  @click="$emit('move', content, 1)"
                  :disabled="isLast || isLoadingCompletion || isLoadingActivityCompletion">
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fill-rule="evenodd" d="M16.707 10.293a1 1 0 01-1.414 0L10 14.586l-5.293-4.293a1 1 0 01-1.414 1.414l6 4.879a1 1 0 011.414 0l6-4.879a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType, ref } from 'vue';
import type {
  UDAContent, UDATemplateContent,
  LessonUDAContent, QuizUDAContent, NoteUDAContent, ActivityUDAContent, // MODIFICATO QuizTemplateUDAContent a QuizUDAContent
  NoteTemplateUDAContent, ActivityTemplateUDAContent
} from '@/types/uda';
import { UDAContentType, UDATemplateContentType } from '@/types/uda'; // Importa gli enum
import { useUdaStore } from '@/stores/udaStore'; // Per aggiornare teacher_marked_completed e activity_completed

// Importa i componenti di display specifici
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
  isFirst: { // Per disabilitare il pulsante "Sposta Su"
    type: Boolean,
    default: false
  },
  isLast: { // Per disabilitare il pulsante "Sposta Giù"
    type: Boolean,
    default: false
  },
  udaId: { // Necessario per aggiornare lo stato di completamento nel backend
    type: Number,
    required: false // Non richiesto se il contesto è UDATemplate
  },
  context: { // 'uda' o 'template'
    type: String as PropType<'uda' | 'template'>,
    required: true
  }
});

const emit = defineEmits(['edit', 'delete', 'move', 'update:teacher-marked-completed', 'update:activity-completed']);

const udaStore = useUdaStore();
const isLoadingCompletion = ref(false);
const isLoadingActivityCompletion = ref(false);

const isUDAContext = computed(() => props.context === 'uda');

const isTeacherMarkedCompleted = computed(() => {
  if (isUDAContext.value && 'teacher_marked_completed' in props.content) {
    return (props.content as UDAContent).teacher_marked_completed || false;
  }
  return false;
});

const contentTitle = computed(() => {
  switch (props.content.content_type) {
    case UDAContentType.LESSON:
    case UDATemplateContentType.LESSON:
      return (props.content as LessonUDAContent).lesson_title || `Lezione ID: ${(props.content as LessonUDAContent).lesson}`;
    case UDAContentType.QUIZ: // MODIFICATO UDAContentType.QUIZ_TEMPLATE a UDAContentType.QUIZ
    case UDATemplateContentType.QUIZ_TEMPLATE:
      // Assumendo che QuizTemplateUDAContent abbia quiz_title e quiz_template
      // Per UDAContentType.QUIZ, il titolo potrebbe dover essere recuperato diversamente se non direttamente sull'oggetto content.
      // Per ora, manteniamo la stessa logica, ma potrebbe necessitare di aggiustamenti futuri se quiz_title non è presente.
      return (props.content as QuizUDAContent).quiz_title || `Quiz (da Template ID: ${(props.content as QuizUDAContent).quiz_template})`; // MODIFICATO cast del tipo
    case UDAContentType.NOTE:
      return (props.content as NoteUDAContent).note_title || 'Nota senza titolo';
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
    // Usiamo i valori stringa diretti degli enum come chiavi,
    // dato che UDAContentType.LESSON e UDATemplateContentType.LESSON sono entrambi 'LESSON',
    // e UDAContentType.QUIZ e UDATemplateContentType.QUIZ_TEMPLATE sono ora gestiti.
    'LESSON': 'Lezione',
    'QUIZ': 'Quiz', // AGGIUNTO per UDAContentType.QUIZ
    'QUIZ_TEMPLATE': 'Quiz (da Template)', // Mantenuto per UDATemplateContentType.QUIZ_TEMPLATE
    'NOTE': 'Nota', // Specifico per UDAContentType
    'ACTIVITY': 'Attività', // Specifico per UDAContentType
    'NOTE_TEMPLATE': 'Template Nota', // Specifico per UDATemplateContentType
    'ACTIVITY_TEMPLATE': 'Template Attività', // Specifico per UDATemplateContentType
  };
  // Se un tipo non è in mappa (improbabile con gli enum), restituisce il tipo stesso.
  return map[type as string] || type;
  return map[type] || type;
};

const toggleTeacherMarkedCompleted = async () => {
  if (!isUDAContext.value || !props.udaId || !props.content.id) return;
  
  isLoadingCompletion.value = true;
  try {
    const currentStatus = (props.content as UDAContent).teacher_marked_completed || false;
    const newStatus = !currentStatus;
    await udaStore.updateUdaContentTeacherCompletion(props.udaId, props.content.id, newStatus);
    // L'evento viene emesso per notificare il genitore, che potrebbe voler aggiornare la sua copia dei dati
    // Lo store dovrebbe già aver aggiornato i dati al suo interno, che verranno riflessi se il genitore li usa.
    emit('update:teacher-marked-completed', { contentId: props.content.id, completed: newStatus });
  } catch (error) {
    console.error("Errore nell'aggiornare lo stato teacher_marked_completed:", error);
    // Potrebbe essere utile ripristinare lo stato della checkbox o mostrare un errore
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

</script>

<style scoped>
/* Gli stili principali sono ora gestiti da classi Tailwind. */
/* Eventuali stili specifici aggiuntivi possono rimanere qui. */
.form-check-input { /* Mantenuto per lo switch se necessario, ma lo switch Tailwind è self-contained */
  /* cursor: pointer; */ /* Già gestito da Tailwind sullo switch button */
}
</style>