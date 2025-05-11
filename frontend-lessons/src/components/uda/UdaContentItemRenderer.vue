<template>
  <div class="uda-content-item-renderer card mb-3">
    <div class="card-body">
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <h6 class="card-title mb-1">{{ contentTitle }}</h6>
          <small class="text-muted">Tipo: {{ मानविकीकरणContentType(content.content_type) }} | Ordine: {{ content.order }}</small>
        </div>
        <div class="form-check form-switch" v-if="isUDAContext && content.content_type !== 'ACTIVITY_TEMPLATE' && content.content_type !== 'NOTE_TEMPLATE'">
          <input 
            class="form-check-input" 
            type="checkbox" 
            role="switch"
            :id="`teacherMarkedCompleted-${content.id || content.temp_id}`"
            :checked="isTeacherMarkedCompleted"
            @change="toggleTeacherMarkedCompleted"
            :disabled="isLoadingCompletion"
          >
          <label class="form-check-label" :for="`teacherMarkedCompleted-${content.id || content.temp_id}`">
            Completato dal Docente
          </label>
        </div>
      </div>
      <hr />

      <!-- Visualizzazione specifica per tipo di contenuto -->
      <div v-if="content.content_type === UDAContentType.LESSON || content.content_type === UDATemplateContentType.LESSON">
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
      <div class="mt-3 pt-2 border-top">
        <button class="btn btn-sm btn-outline-primary me-2" @click="$emit('edit', content)" :disabled="isLoadingCompletion || isLoadingActivityCompletion">
          <i class="bi bi-pencil"></i> Modifica
        </button>
        <button class="btn btn-sm btn-outline-danger me-2" @click="$emit('delete', content.temp_id || content.id)" :disabled="isLoadingCompletion || isLoadingActivityCompletion">
          <i class="bi bi-trash"></i> Elimina
        </button>
        <button class="btn btn-sm btn-outline-secondary me-1" @click="$emit('move', content, -1)" :disabled="isFirst || isLoadingCompletion || isLoadingActivityCompletion">
          <i class="bi bi-arrow-up"></i>
        </button>
        <button class="btn btn-sm btn-outline-secondary" @click="$emit('move', content, 1)" :disabled="isLast || isLoadingCompletion || isLoadingActivityCompletion">
          <i class="bi bi-arrow-down"></i>
        </button>
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
.uda-content-item-renderer {
  border: 1px solid #dee2e6;
  border-radius: .375rem;
}
.card-title {
  font-size: 1.1rem;
}
.form-check-input {
  cursor: pointer;
}
</style>