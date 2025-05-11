<template>
  <div class="lesson-content-display">
    <div v-if="isLoading" class="text-muted">
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      Caricamento dettagli lezione...
    </div>
    <div v-else-if="lesson">
      <p>
        <strong>Lezione: </strong>
        <router-link :to="{ name: 'lesson-detail', params: { id: lesson.id } }">
          {{ lesson.title || `ID Lezione: ${lesson.id}` }}
        </router-link>
      </p>
      <p v-if="lesson.subject_name">
        <strong>Materia: </strong> {{ lesson.subject_name }}
      </p>
      <p v-if="lesson.topic_name">
        <strong>Argomento: </strong> {{ lesson.topic_name }}
      </p>
      <!-- Potremmo aggiungere altri dettagli qui, es. descrizione breve -->
    </div>
    <p v-else-if="!props.content.lesson" class="text-warning">
      Nessun ID lezione specificato per questo contenuto.
    </p>
    <p v-else class="text-danger">
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
    return;
  }
  try {
    // Se non è nello store, la recupera (fetchLesson dovrebbe aggiungere/aggiornare lo store)
    await lessonStore.fetchLesson(lessonId);
    lesson.value = lessonStore.currentLesson; // currentLesson dovrebbe essere aggiornato da fetchLesson
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