<template>
  <div class="course-form-view p-4 md:p-8">
    <h1 class="text-3xl font-bold text-gray-800 mb-6">
      {{ isEditing ? 'Modifica Corso' : 'Crea Nuovo Corso' }}
    </h1>

    <div v-if="pageLoading" class="text-center py-10">
      <p class="text-gray-600">Caricamento dati corso...</p>
    </div>

    <div v-else-if="pageError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ pageError }}</span>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="bg-white shadow-md rounded-lg px-8 pt-6 pb-8 mb-4">
      <div class="mb-4">
        <label for="courseName" class="block text-gray-700 text-sm font-bold mb-2">
          Nome Corso:
        </label>
        <input
          id="courseName"
          v-model="courseData.name"
          type="text"
          required
          class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          :class="{ 'border-red-500': formErrors.name }"
        />
        <p v-if="formErrors.name" class="text-red-500 text-xs italic">{{ formErrors.name }}</p>
      </div>

      <div class="mb-6">
        <label for="courseDescription" class="block text-gray-700 text-sm font-bold mb-2">
          Descrizione (opzionale):
        </label>
        <textarea
          id="courseDescription"
          v-model="courseData.description"
          rows="4"
          class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          :class="{ 'border-red-500': formErrors.description }"
        ></textarea>
        <p v-if="formErrors.description" class="text-red-500 text-xs italic">{{ formErrors.description }}</p>
      </div>

      <div class="flex items-center justify-between">
        <button
          type="submit"
          :disabled="isSubmitting"
          class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
        >
          {{ isSubmitting ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche' : 'Crea Corso') }}
        </button>
        <RouterLink
          :to="{ name: 'course-list' }"
          class="inline-block align-baseline font-bold text-sm text-indigo-600 hover:text-indigo-800"
        >
          Annulla
        </RouterLink>
      </div>
      <p v-if="submitError" class="text-red-500 text-xs italic mt-4">{{ submitError }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import { useCourseStore } from '@/stores/courseStore';
import { useUiStore } from '@/stores/ui'; // Importa uiStore
import type { Course } from '@/types/uda';

const courseStore = useCourseStore();
const uiStore = useUiStore(); // Istanzia uiStore
const router = useRouter();
const route = useRoute();

const courseId = computed(() => route.params.id ? Number(route.params.id) : null);
const isEditing = computed(() => !!courseId.value);

const courseData = reactive<Pick<Course, 'name' | 'description'>>({
  name: '',
  description: '',
});

const formErrors = reactive({
  name: '',
  description: ''
});

const pageLoading = ref(false);
const pageError = ref<string | null>(null);
const isSubmitting = ref(false);
const submitError = ref<string | null>(null);

onMounted(async () => {
  if (isEditing.value && courseId.value) {
    pageLoading.value = true;
    pageError.value = null;
    try {
      // Controlla se il corso è già nello store per evitare fetch non necessarie
      let course: Course | null | undefined = courseStore.getCourseById(courseId.value);
      if (!course) {
        await courseStore.fetchCourse(courseId.value);
        course = courseStore.currentCourse;
      } else {
        courseStore.currentCourse = course; // Assicura che currentCourse sia settato
      }
      
      if (course) {
        courseData.name = course.name;
        courseData.description = course.description || '';
      } else {
        pageError.value = 'Corso non trovato.';
      }
    } catch (err) {
      pageError.value = (err as Error).message || 'Errore nel caricamento del corso.';
    } finally {
      pageLoading.value = false;
    }
  }
});

const validateForm = (): boolean => {
  formErrors.name = '';
  formErrors.description = '';
  let isValid = true;
  if (!courseData.name.trim()) {
    formErrors.name = 'Il nome del corso è obbligatorio.';
    isValid = false;
  }
  // Aggiungere altre validazioni se necessario (es. lunghezza massima)
  return isValid;
};

const handleSubmit = async () => {
  if (!validateForm()) {
    return;
  }

  isSubmitting.value = true;
  submitError.value = null;

  try {
    if (isEditing.value && courseId.value) {
      const updatedCourse = await courseStore.updateCourse(courseId.value, courseData);
      if (updatedCourse) {
        uiStore.addNotification({ message: 'Corso aggiornato con successo!', type: 'success', duration: 3000 });
        router.push({ name: 'course-detail', params: { id: updatedCourse.id } });
      }
    } else {
      const newCourse = await courseStore.createCourse(courseData);
      if (newCourse) {
        uiStore.addNotification({ message: 'Corso creato con successo!', type: 'success', duration: 3000 });
        router.push({ name: 'course-detail', params: { id: newCourse.id } });
      }
    }
  } catch (err) {
    submitError.value = (err as Error).message || 'Si è verificato un errore durante il salvataggio.';
    uiStore.addNotification({ message: submitError.value, type: 'error', duration: 5000 });
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
/* Stili aggiuntivi se necessari */
</style>