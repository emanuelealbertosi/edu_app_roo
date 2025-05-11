<template>
  <div class="course-list-view p-4 md:p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-gray-800">Lista Corsi</h1>
      <RouterLink
        :to="{ name: 'course-new' }"
        class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
      >
        <PlusCircleIcon class="h-5 w-5 mr-2" />
        Nuovo Corso
      </RouterLink>
    </div>

    <div v-if="loading" class="text-center py-10">
      <p class="text-gray-600">Caricamento corsi...</p>
      <!-- Potresti aggiungere uno spinner qui -->
    </div>

    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ error }}</span>
    </div>

    <div v-else-if="courses.length === 0" class="text-center py-10">
      <p class="text-gray-600">Nessun corso trovato.</p>
      <p class="mt-2 text-sm text-gray-500">
        Inizia creando il tuo primo corso!
      </p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="course in courses"
        :key="course.id"
        class="bg-white shadow-lg rounded-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 ease-in-out"
      >
        <div class="p-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-2">{{ course.name }}</h2>
          <p class="text-gray-600 text-sm mb-4 h-20 overflow-y-auto">
            {{ course.description || 'Nessuna descrizione fornita.' }}
          </p>
          <div class="flex justify-end space-x-3">
            <RouterLink
              :to="{ name: 'course-detail', params: { id: course.id } }"
              class="text-sm text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
            >
              Dettagli
            </RouterLink>
            <RouterLink
              :to="{ name: 'course-edit', params: { id: course.id } }"
              class="text-sm text-green-600 hover:text-green-800 font-medium transition-colors"
            >
              Modifica
            </RouterLink>
            <button
              @click="handleDeleteCourse(course.id)"
              class="text-sm text-red-600 hover:text-red-800 font-medium transition-colors"
            >
              Elimina
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { RouterLink } from 'vue-router';
import { useCourseStore } from '@/stores/courseStore';
import { useUiStore } from '@/stores/ui'; // Importa uiStore
import { PlusCircleIcon } from '@heroicons/vue/24/outline';

const courseStore = useCourseStore();
const uiStore = useUiStore(); // Istanzia uiStore

const courses = computed(() => courseStore.courses);
const loading = computed(() => courseStore.loading);
const error = computed(() => courseStore.error);

onMounted(() => {
  courseStore.fetchCourses();
});

const handleDeleteCourse = async (courseId: number) => {
  if (confirm('Sei sicuro di voler eliminare questo corso? Questa azione è irreversibile.')) {
    try {
      await courseStore.deleteCourse(courseId);
      uiStore.addNotification({ message: 'Corso eliminato con successo!', type: 'success', duration: 3000 });
    } catch (err) {
      console.error("Errore durante l'eliminazione del corso:", err);
      uiStore.addNotification({ message: (err as Error).message || 'Errore durante l\'eliminazione del corso.', type: 'error', duration: 5000 });
    }
  }
};
</script>

<style scoped>
/* Stili aggiuntivi se necessari */
.course-list-view {
  /* Esempio: padding: 1rem; */
}
</style>