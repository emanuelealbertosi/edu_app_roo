<template>
  <div class="quiz-content-display">
    <div v-if="isLoading" class="text-muted">
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      Caricamento dettagli template quiz...
    </div>
    <div v-else-if="quizTemplate">
      <p>
        <strong>Template Quiz: </strong>
        <span>{{ quizTemplate.title || `ID Template: ${quizTemplate.id}` }}</span>
      </p>
      <p v-if="quizTemplate.description" class="text-muted small">
        <em>{{ quizTemplate.description }}</em>
      </p>
      <p v-if="quizTemplate.subject_name">
        <strong>Materia: </strong> {{ quizTemplate.subject_name }}
      </p>
      <p v-if="quizTemplate.topic_name">
        <strong>Argomento: </strong> {{ quizTemplate.topic_name }}
      </p>
    </div>
    <!-- Messaggio rimosso: "Nessun ID template quiz specificato per questo contenuto." -->
    <!-- La condizione !quizTemplate (riga 7) e il successivo v-else gestiscono i casi di errore caricamento -->
    <p v-else-if="!isLoading && !quizTemplate && props.content.quiz_template" class="text-danger">
      Impossibile caricare i dettagli del template quiz (ID: {{ props.content.quiz_template }}).
    </p>
    <p v-else-if="!isLoading && !props.content.quiz_template" class="text-warning">
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