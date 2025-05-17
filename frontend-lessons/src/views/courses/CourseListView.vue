<template>
  <div class="course-list-view p-4 md:p-8">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex justify-between items-center">
      <h2 class="text-2xl font-semibold">Lista Corsi</h2>
      <!-- Pulsante stile adattato per contrasto -->
      <RouterLink
        :to="{ name: 'course-new' }"
        class="flex items-center px-3 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-100 transition duration-150 ease-in-out font-medium"
      >
        <PlusCircleIcon class="h-5 w-5 sm:mr-2" />
        <span class="hidden sm:inline">Nuovo Corso</span>
      </RouterLink>
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca corsi per nome o descrizione..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      />
    </div>

    <div v-if="loading" class="text-center py-10">
      <p class="text-gray-600">Caricamento corsi...</p>
      <!-- Potresti aggiungere uno spinner qui -->
    </div>

    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ error }}</span>
    </div>

    <div v-else-if="filteredCourses.length === 0" class="text-center py-10">
      <p class="text-gray-600" v-if="searchQuery">Nessun corso trovato per "{{ searchQuery }}".</p>
      <p class="text-gray-600" v-else>Nessun corso trovato.</p>
      <p class="mt-2 text-sm text-gray-500" v-if="!searchQuery">
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
          <tr v-for="course in filteredCourses" :key="course.id" class="hover:bg-gray-50 transition-colors duration-150">
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
                title="Vedi Dettagli Corso"
              >
                <EyeIcon class="h-5 w-5 inline-block" />
              </RouterLink>
              <RouterLink
                :to="{ name: 'course-edit', params: { id: course.id } }"
                class="text-yellow-600 hover:text-yellow-900 transition duration-150 ease-in-out"
                title="Modifica Corso"
              >
                <PencilIcon class="h-5 w-5 inline-block" />
              </RouterLink>
              <button
                @click="handleDeleteCourse(course.id)"
                class="text-red-600 hover:text-red-900 transition duration-150 ease-in-out"
                title="Elimina Corso"
              >
                <TrashIcon class="h-5 w-5 inline-block" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { RouterLink } from 'vue-router';
import { useCourseStore } from '@/stores/courseStore';
import { useUiStore } from '@/stores/ui'; // Importa uiStore
import { PlusCircleIcon, EyeIcon, PencilIcon, TrashIcon } from '@heroicons/vue/24/outline';

const courseStore = useCourseStore();
const uiStore = useUiStore(); // Istanzia uiStore
const searchQuery = ref('');

const courses = computed(() => courseStore.courses);
const loading = computed(() => courseStore.loading);
const error = computed(() => courseStore.error);

const filteredCourses = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  if (!query) {
    return courses.value;
  }
  return courses.value.filter(course => {
    const name = course.name.toLowerCase();
    const description = course.description?.toLowerCase() || '';
    return name.includes(query) || description.includes(query);
  });
});

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