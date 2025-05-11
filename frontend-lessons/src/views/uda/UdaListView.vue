<template>
  <div class="uda-list-view p-4 md:p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-gray-800">Elenco Unità Didattiche (UDA)</h1>
      <RouterLink
        :to="{ name: 'uda-new' }"
        class="bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center"
      >
        <PlusCircleIcon class="h-5 w-5 mr-2" />
        Nuova UDA
      </RouterLink>
    </div>

    <!-- Filtri -->
    <div class="mb-6 p-4 bg-gray-50 rounded-lg shadow">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label for="statusFilter" class="block text-sm font-medium text-gray-700 mb-1">Filtra per Stato:</label>
          <select id="statusFilter" v-model="selectedStatus" @change="applyFilters" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
            <option value="">Tutti gli stati</option>
            <option value="TODO">Da Fare</option>
            <option value="IN_PROGRESS">In Corso</option>
            <option value="COMPLETED">Completata</option>
          </select>
        </div>
        <div>
          <label for="courseFilter" class="block text-sm font-medium text-gray-700 mb-1">Filtra per Corso:</label>
          <select id="courseFilter" v-model="selectedCourseId" @change="applyFilters" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2">
            <option :value="null">Tutti i corsi</option>
            <option v-for="course in availableCourses" :key="course.id" :value="course.id">
              {{ course.name }}
            </option>
          </select>
          <div v-if="courseStore.loading" class="text-xs text-gray-500 mt-1">Caricamento corsi...</div>
        </div>
      </div>
    </div>

    <div v-if="udaStore.loading" class="text-center py-10">
      <p class="text-gray-600">Caricamento UDA...</p>
    </div>
    <div v-else-if="udaStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ udaStore.error }}</span>
    </div>
    <div v-else-if="filteredUdas.length === 0" class="text-center py-10 bg-gray-50 rounded-md">
      <p class="text-gray-600 text-lg">Nessuna UDA trovata con i filtri selezionati.</p>
      <p class="text-gray-500 mt-2" v-if="selectedStatus === '' && selectedCourseId === null">Crea la tua prima UDA per iniziare.</p>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="uda in filteredUdas"
        :key="uda.id"
        class="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-lg transition-shadow duration-200 p-5"
      >
        <div class="flex justify-between items-start">
          <div>
            <h2 class="text-xl font-semibold text-indigo-700 mb-1">
              <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }" class="hover:underline">
                {{ uda.title }}
              </RouterLink>
            </h2>
            <p class="text-gray-600 text-sm mb-2 h-16 overflow-y-auto custom-scrollbar">{{ uda.description || 'Nessuna descrizione.' }}</p>
            <div class="text-xs text-gray-500 space-y-0.5">
              <p>Stato: <span class="font-medium px-1.5 py-0.5 rounded-full" :class="getStatusClass(uda.status)">{{ uda.status }}</span></p>
              <p v-if="getCourseName(uda.course)">Corso: <span class="font-medium text-gray-700">{{ getCourseName(uda.course) }}</span></p>
              <p v-if="uda.subject_details">Materia: <span class="font-medium text-gray-700">{{ uda.subject_details.name }}</span></p>
              <p>Contenuti: {{ uda.contents?.length || 0 }}</p>
              <p>Dal: {{ formatDate(uda.start_date) }} Al: {{ formatDate(uda.end_date) }}</p>
            </div>
          </div>
          <div class="flex flex-col space-y-2 flex-shrink-0 ml-4">
            <RouterLink
              :to="{ name: 'uda-detail', params: { id: uda.id } }"
              class="text-sm bg-blue-500 hover:bg-blue-600 text-white font-medium py-1.5 px-3 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center justify-center"
              title="Vedi Dettagli"
            >
              <EyeIcon class="h-4 w-4 mr-1" /> Vedi
            </RouterLink>
            <RouterLink
              :to="{ name: 'uda-edit', params: { id: uda.id } }"
              class="text-sm bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-1.5 px-3 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center justify-center"
              title="Modifica UDA"
            >
              <PencilIcon class="h-4 w-4 mr-1" /> Modifica
            </RouterLink>
            <button
              @click="confirmDeleteSingleUda(uda.id, uda.title)"
              class="text-sm bg-red-500 hover:bg-red-600 text-white font-medium py-1.5 px-3 rounded-md shadow-sm transition duration-150 ease-in-out flex items-center justify-center"
              title="Elimina UDA"
            >
              <TrashIcon class="h-4 w-4 mr-1" /> Elimina
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { RouterLink } from 'vue-router';
import { useUdaStore } from '@/stores/udaStore';
import { useCourseStore } from '@/stores/courseStore';
import { useSubjectStore } from '@/stores/subjectStore'; // Per arricchire con nome materia
import { useUiStore } from '@/stores/ui';
import { PlusCircleIcon, PencilIcon, TrashIcon, EyeIcon } from '@heroicons/vue/24/outline';
import type { UDA, Course } from '@/types/uda'; // Importa Course da uda.ts
import type { Subject } from '@/types/subject';

const udaStore = useUdaStore();
const courseStore = useCourseStore();
const subjectStore = useSubjectStore();
const uiStore = useUiStore();

const selectedStatus = ref<UDA['status'] | ''>('');
const selectedCourseId = ref<number | null>(null);

// Arricchisce le UDA con dettagli (es. nome corso, nome materia)
const enrichedUdas = computed(() => {
  return udaStore.udas.map(uda => {
    const course = uda.course ? courseStore.getCourseById(uda.course) : null;
    const subject = uda.subject ? subjectStore.getSubjectById(uda.subject) : null;
    return {
      ...uda,
      course_name: course?.name,
      subject_details: subject,
    };
  });
});

// Filtra le UDA in base ai filtri selezionati
const filteredUdas = computed(() => {
  return enrichedUdas.value.filter(uda => {
    const statusMatch = selectedStatus.value ? uda.status === selectedStatus.value : true;
    const courseMatch = selectedCourseId.value !== null ? uda.course === selectedCourseId.value : true;
    return statusMatch && courseMatch;
  });
});

const availableCourses = computed(() => courseStore.courses);

const applyFilters = () => {
  // La computed property filteredUdas si aggiornerà automaticamente
  // Potremmo voler ricaricare le UDA dal backend se i filtri sono complessi
  // e gestiti dal backend, ma per ora filtriamo lato client.
  // Se si volesse filtrare lato backend:
  // udaStore.fetchUdas({ status: selectedStatus.value || undefined, courseId: selectedCourseId.value || undefined });
  console.log('Filtri applicati:', { status: selectedStatus.value, course: selectedCourseId.value });
};

onMounted(async () => {
  // udaStore.loading, courseStore.loading, subjectStore.loading gestiranno i propri stati.
  // La vista può mostrare un indicatore di caricamento generale basato su udaStore.loading
  // o stati di loading più granulari se necessario.
  try {
    await Promise.all([
      udaStore.fetchUdas(),
      courseStore.fetchCourses(),
      subjectStore.fetchSubjects()
    ]);
  } catch (error) {
    console.error("Errore caricamento dati per UdaListView:", error);
    uiStore.addNotification({ message: `Errore caricamento dati: ${(error as Error).message}`, type: 'error'});
  }
  // Lo stato di loading individuale degli store si resetterà da solo.
});

const confirmDeleteSingleUda = async (udaId: number, udaTitle: string) => {
  const confirmed = window.confirm(`Sei sicuro di voler eliminare l'UDA "${udaTitle}" (ID: ${udaId})? L'azione non è reversibile.`);
  if (confirmed) {
    uiStore.addNotification({ message: `Eliminazione UDA "${udaTitle}" in corso...`, type: 'info' });
    try {
      await udaStore.deleteUda(udaId);
      uiStore.addNotification({ message: `UDA "${udaTitle}" eliminata con successo.`, type: 'success', duration: 3000 });
      // Le UDA si aggiorneranno automaticamente perché filteredUdas dipende da udaStore.udas
    } catch (error) {
      console.error(`Errore durante l'eliminazione dell'UDA ID ${udaId}:`, error);
      uiStore.addNotification({ message: `Errore eliminazione: ${(error as Error).message}`, type: 'error' });
    }
  } else {
    uiStore.addNotification({ message: 'Eliminazione UDA annullata.', type: 'info', duration: 2000 });
  }
};

const getStatusClass = (status?: UDA['status']) => {
  if (!status) return 'text-gray-600 bg-gray-100';
  if (status === 'COMPLETED') return 'text-green-700 bg-green-100';
  if (status === 'IN_PROGRESS') return 'text-blue-700 bg-blue-100';
  if (status === 'TODO') return 'text-yellow-700 bg-yellow-100';
  return 'text-gray-600 bg-gray-100';
};

const getCourseName = (courseId?: number | null): string | undefined => {
  if (!courseId) return undefined;
  const course = courseStore.getCourseById(courseId);
  return course?.name;
};

const formatDate = (dateString?: string | null) => {
  if (!dateString) return 'N/D';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch (e) {
    return dateString; // Ritorna la stringa originale se non è una data valida
  }
};

// Watch per ricaricare le UDA se i filtri cambiano (se si implementa filtro backend)
// watch([selectedStatus, selectedCourseId], () => {
//   applyFilters(); // O chiama direttamente fetchUdas con i nuovi filtri
// });

</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #c5c5c5;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #a5a5a5;
}
</style>