<template>
  <div class="lesson-content-display p-3 bg-white rounded-b-md"> <!-- Aggiunto padding e sfondo per coerenza se il titolo ha sfondo -->
    <div v-if="isLoading" class="text-sm text-gray-500">
      Caricamento dettagli lezione...
    </div>
    <div v-else-if="lesson" class="space-y-3 text-sm"> <!-- Aumentato space-y per descrizione -->
      <!-- Titolo Lezione rimosso (già presente nel renderer) -->
      <!-- Etichetta Descrizione rimossa -->
      <div v-if="lesson.description" class="italic text-gray-600">
        {{ lesson.description }}
      </div>
      <!-- Materia e Argomento rimossi da qui, verranno emessi all'evento details-loaded -->
      <div class="flex">
        <strong class="w-24 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">
          {{ typeof props.content.estimated_hours === 'number' && props.content.estimated_hours > 0 ? props.content.estimated_hours + 'h' : (props.content.estimated_hours === 0 ? '0h' : 'N/D') }}
        </span>
      </div>
      <div class="flex items-center">
        <strong class="w-24 flex-shrink-0 text-gray-700">Ore Effettive:</strong>
        <div v-if="!isEditingActualHours" class="flex items-center">
          <span class="text-gray-600 mr-2">{{ props.content.actual_hours !== null && typeof props.content.actual_hours !== 'undefined' ? props.content.actual_hours + 'h' : 'N/D' }}</span>
          <button @click="startEditingActualHours" class="text-xs text-blue-500 hover:text-blue-700">(modifica)</button>
        </div>
        <div v-else class="flex items-center space-x-2">
          <input
            type="number"
            step="0.1"
            min="0"
            v-model.number="editableActualHours"
            class="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
            placeholder="Ore"
          />
          <button @click="saveActualHours" class="px-2 py-1 text-xs bg-green-500 hover:bg-green-600 text-white rounded">Salva</button>
          <button @click="cancelEditingActualHours" class="px-2 py-1 text-xs bg-gray-300 hover:bg-gray-400 rounded">Annulla</button>
        </div>
      </div>
    </div>
    <p v-else-if="!props.content.lesson && !isLoading" class="text-sm text-yellow-600">
      Nessun ID lezione specificato per questo contenuto.
    </p>
    <p v-else class="text-sm text-red-600">
      Impossibile caricare i dettagli della lezione (ID: {{ props.content.lesson }}).
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, type PropType, watch } from 'vue';
import type { LessonUDAContent, UDAContent } from '@/types/uda'; // Aggiunto UDAContent
import type { Lesson } from '@/types/lezioni';
import { useLessonStore } from '@/stores/lessons';
import { useUdaStore } from '@/stores/udaStore'; // Aggiunto useUdaStore

const props = defineProps({
  content: {
    // Assicuriamoci che LessonUDAContent includa uda_id e id (del UDAContent)
    // Se LessonUDAContent è definito come `BaseContent & { lesson: number, ... }` e BaseContent ha id e uda_id, va bene.
    // Altrimenti, potrebbe essere necessario un cast più specifico o un aggiornamento del tipo.
    // Per coerenza con Note/Activity, potremmo aspettarci { ...LessonUDAContent, uda_id: number, id: number }
    // Tuttavia, UDAContent (che dovrebbe essere la base per LessonUDAContent) dovrebbe già avere id e uda_id.
    type: Object as PropType<LessonUDAContent & { uda_id?: number; id?: number }>, // Aggiunto uda_id e id opzionali per sicurezza, ma dovrebbero essere in LessonUDAContent
    required: true
  }
});

// Definisci l'evento da emettere
const emit = defineEmits(['details-loaded']);

const lessonStore = useLessonStore();
const udaStore = useUdaStore(); // Inizializza udaStore
const lesson = ref<Lesson | null>(null);
const isLoading = ref(false); // Per il caricamento dei dettagli della lezione

// State per la modifica delle ore effettive
const isEditingActualHours = ref(false);
const editableActualHours = ref<number | undefined | null>(props.content.actual_hours);
const originalActualHours = ref<number | undefined | null>(props.content.actual_hours);


watch(() => props.content.actual_hours, (newVal) => {
  if (!isEditingActualHours.value) {
    editableActualHours.value = newVal;
    originalActualHours.value = newVal;
  }
});


const fetchLessonDetails = async (lessonId: number) => {
  isLoading.value = true;
  // Verifica se la lezione è già nello store per evitare chiamate API duplicate
  const existingLesson = lessonStore.getLessonById(lessonId);
  if (existingLesson) {
    lesson.value = existingLesson;
    isLoading.value = false;
    // Emetti evento anche se preso dalla cache
    emit('details-loaded', {
      subjectName: lesson.value?.subject_name,
      topicName: lesson.value?.topic_name
    });
    return;
  }
  try {
    // Se non è nello store, la recupera (fetchLesson dovrebbe aggiungere/aggiornare lo store)
    await lessonStore.fetchLesson(lessonId);
    lesson.value = lessonStore.currentLesson; // currentLesson dovrebbe essere aggiornato da fetchLesson
    // Emetti evento dopo il fetch
    emit('details-loaded', {
      subjectName: lesson.value?.subject_name,
      topicName: lesson.value?.topic_name
    });
  } catch (error) {
    console.error(`Errore nel caricare i dettagli della lezione ${lessonId}:`, error);
    lesson.value = null;
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  console.log('[LessonContentDisplay] Mounted. props.content:', JSON.parse(JSON.stringify(props.content))); // LOG 5
  if (props.content.lesson) {
    fetchLessonDetails(props.content.lesson);
  }
});

watch(() => props.content, (newContentValue) => {
  console.log('[LessonContentDisplay] Watch props.content updated:', JSON.parse(JSON.stringify(newContentValue))); // LOG 6
  // Se l'ID della lezione cambia, ricarica i dettagli
  const currentLessonId = lesson.value?.id;
  const newLessonIdInContent = newContentValue.lesson;

  if (newLessonIdInContent && newLessonIdInContent !== currentLessonId) {
    fetchLessonDetails(newLessonIdInContent);
  } else if (!newLessonIdInContent && currentLessonId) { // Se la lezione viene rimossa dal contenuto
    lesson.value = null;
    emit('details-loaded', { subjectName: undefined, topicName: undefined });
  }
}, { deep: true, immediate: false }); // immediate: false per evitare doppio log con onMounted se props.content è già lì

// --- Metodi per la modifica delle ore effettive ---
const startEditingActualHours = () => {
  originalActualHours.value = props.content.actual_hours;
  editableActualHours.value = props.content.actual_hours;
  isEditingActualHours.value = true;
};

const saveActualHours = async () => {
  console.log('[LessonContentDisplay] saveActualHours called. editableActualHours:', editableActualHours.value);
  const valueToSave = (typeof editableActualHours.value === 'undefined' || editableActualHours.value === null)
                      ? null
                      : Number(editableActualHours.value);

  if (valueToSave !== originalActualHours.value) {
    if (typeof props.content.id === 'undefined' || typeof props.content.uda_id === 'undefined') {
      console.error('Cannot update actual hours: content ID or UDA ID is undefined. Props.content:', props.content);
      // TODO: Mostrare un messaggio di errore all'utente
      return;
    }
    try {
      const updatedData: Partial<Pick<LessonUDAContent, 'actual_hours'>> = {
        actual_hours: valueToSave,
      };
      // Usiamo UDAContent per il tipo nel payload dello store, dato che actual_hours è un campo base
      await udaStore.updateContentInUda(props.content.uda_id, props.content.id, updatedData as UDAContent);
      originalActualHours.value = valueToSave;
      isEditingActualHours.value = false;
    } catch (error) {
      console.error('Failed to save actual hours for lesson content:', error);
      // TODO: Gestire lo stato di errore per l'UI
    }
  } else {
    isEditingActualHours.value = false;
  }
};

const cancelEditingActualHours = () => {
  editableActualHours.value = originalActualHours.value;
  isEditingActualHours.value = false;
};
</script>

<style scoped>
.lesson-content-display {
  font-size: 0.9rem;
}
</style>