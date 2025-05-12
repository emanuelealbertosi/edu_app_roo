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

    <div v-else class="shadow-lg overflow-hidden border-b border-gray-200 sm:rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Nome
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Descrizione
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Azioni
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="course in courses" :key="course.id" class="hover:bg-gray-50 transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-indigo-700 hover:text-indigo-900">
                <RouterLink :to="{ name: 'course-detail', params: { id: course.id } }">
                  {{ course.name }}
                </RouterLink>
              </div>
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
              <span :title="course.description" v-if="course.description && course.description.length > 30">
                {{ course.description.substring(0, 30) + '...' }}
              </span>
              <span v-else>{{ course.description || 'Nessuna descrizione fornita.' }}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <RouterLink
                :to="{ name: 'course-detail', params: { id: course.id } }"
                class="text-blue-600 hover:text-blue-900 transition duration-150 ease-in-out"
                title="Vedi Dettagli"
              >
                Dettagli
              </RouterLink>
              <RouterLink
                :to="{ name: 'course-edit', params: { id: course.id } }"
                class="text-yellow-600 hover:text-yellow-900 transition duration-150 ease-in-out"
                title="Modifica Corso"
              >
                Modifica
              </RouterLink>
              <button
                @click="handleDeleteCourse(course.id)"
                class="text-red-600 hover:text-red-900 transition duration-150 ease-in-out"
                title="Elimina Corso"
              >
                Elimina
              </button>
            </td>
          </tr>
        </tbody>
      </table>
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