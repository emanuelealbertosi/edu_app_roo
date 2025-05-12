<template>
  <div class="quiz-content-display p-3 bg-white rounded-b-md"> <!-- Aggiunto padding e sfondo per coerenza -->
    <div v-if="isLoading" class="text-sm text-gray-500">
      Caricamento dettagli template quiz...
    </div>
    <div v-else-if="quizTemplate" class="space-y-2 text-sm">
      <!-- Titolo Template Quiz rimosso (già presente nel renderer) -->
      <!-- Etichetta Descrizione rimossa -->
      <div v-if="quizTemplate.description" class="italic text-gray-600 truncate">
        {{ quizTemplate.description }}
      </div>
      <div v-if="quizTemplate.subject_name" class="flex">
        <strong class="w-28 flex-shrink-0 text-gray-700">Materia:</strong>
        <span class="text-gray-600">{{ quizTemplate.subject_name }}</span>
      </div>
      <div v-if="quizTemplate.topic_name" class="flex">
        <strong class="w-28 flex-shrink-0 text-gray-700">Argomento:</strong>
        <span class="text-gray-600">{{ quizTemplate.topic_name }}</span>
      </div>
       <div v-if="props.content.estimated_hours" class="flex">
        <strong class="w-28 flex-shrink-0 text-gray-700">Ore Stimate:</strong>
        <span class="text-gray-600">{{ props.content.estimated_hours }}h</span>
      </div>
    </div>
    <p v-else-if="!isLoading && !quizTemplate && props.content.quiz_template" class="text-sm text-red-600">
      Impossibile caricare i dettagli del template quiz (ID: {{ props.content.quiz_template }}).
    </p>
    <p v-else-if="!isLoading && !props.content.quiz_template" class="text-sm text-yellow-600">
      ID del template quiz non fornito nel contenuto.
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, type PropType, watch } from 'vue';
import type { QuizUDAContent } from '@/types/uda'; // MODIFICATO per usare il tipo corretto QuizUDAContent
import type { QuizTemplate } from '@/types/quizTemplate'; // Importa QuizTemplate
import { useQuizStore } from '@/stores/quizStore';

const props = defineProps({
  content: {
    type: Object as PropType<QuizUDAContent>, // MODIFICATO per usare il tipo corretto QuizUDAContent
    required: true
  }
});

const quizStore = useQuizStore();
const quizTemplate = ref<QuizTemplate | null>(null); // Rinominato e tipizzato
const isLoading = ref(false);

// Rinominata e modificata per caricare un template di quiz
const fetchQuizTemplateDetails = async (templateId: number) => {
  isLoading.value = true;
  // Prova prima a prenderlo dallo store se già caricato in una lista
  const existingTemplate = quizStore.getQuizTemplateById(templateId);
  if (existingTemplate) {
    quizTemplate.value = existingTemplate;
    isLoading.value = false;
    return;
  }
  try {
    await quizStore.fetchQuizTemplate(templateId); // Chiama l'azione corretta
    quizTemplate.value = quizStore.currentQuizTemplate; // Assegna il template caricato
     if (!quizTemplate.value) {
        console.warn(`Template Quiz non trovato con ID ${templateId} dopo il fetch.`);
    }
  } catch (error) {
    console.error(`Errore nel caricare i dettagli del template quiz ${templateId}:`, error);
    quizTemplate.value = null;
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  if (props.content.quiz_template) { // props.content.quiz_template ora è l'ID del template
    fetchQuizTemplateDetails(props.content.quiz_template);
  }
});

watch(() => props.content.quiz_template, (newTemplateId) => {
  if (newTemplateId) {
    fetchQuizTemplateDetails(newTemplateId);
  } else {
    quizTemplate.value = null;
  }
});
</script>

<style scoped>
.quiz-content-display {
  font-size: 0.9rem;
}
</style>