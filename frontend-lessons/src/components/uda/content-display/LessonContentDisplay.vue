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
      <div v-if="props.content.estimated_hours" class="flex">
        <strong class="w-24 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
      </div>
    </div>
    <p v-else-if="!props.content.lesson" class="text-sm text-yellow-600">
      Nessun ID lezione specificato per questo contenuto.
    </p>
    <p v-else class="text-sm text-red-600">
      Impossibile caricare i dettagli della lezione (ID: {{ props.content.lesson }}).
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, type PropType, watch } from 'vue';
import type { LessonUDAContent } from '@/types/uda';
import type { Lesson } from '@/types/lezioni'; // Assumendo che il tipo Lesson sia definito qui
import { useLessonStore } from '@/stores/lessons';

const props = defineProps({
  content: {
    type: Object as PropType<LessonUDAContent>,
    required: true
  }
});

// Definisci l'evento da emettere
const emit = defineEmits(['details-loaded']);

const lessonStore = useLessonStore();
const lesson = ref<Lesson | null>(null);
const isLoading = ref(false);

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
  if (props.content.lesson) {
    fetchLessonDetails(props.content.lesson);
  }
});

watch(() => props.content.lesson, (newLessonId) => {
  if (newLessonId) {
    fetchLessonDetails(newLessonId);
  } else {
    lesson.value = null;
  }
});
</script>

<style scoped>
.lesson-content-display {
  font-size: 0.9rem;
}
</style>