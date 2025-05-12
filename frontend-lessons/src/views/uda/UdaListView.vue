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

    <!-- Tabella UDA -->
    <div v-else class="shadow-lg overflow-hidden border-b border-gray-200 sm:rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Titolo
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Descrizione
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Stato
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Corso
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Creato da (Corso)
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Argomenti
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Materie
            </th>
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              Contenuti
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Date (Inizio/Fine)
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Azioni
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="uda in filteredUdas" :key="uda.id" class="hover:bg-gray-50 transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap">
              <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }" class="text-sm font-medium text-indigo-700 hover:text-indigo-900">
                {{ uda.title }}
              </RouterLink>
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
              <span :title="uda.description" v-if="uda.description && uda.description.length > 20">
                {{ uda.description.substring(0, 20) + '...' }}
              </span>
              <span v-else>{{ uda.description || 'Nessuna descrizione.' }}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full" :class="getStatusClass(uda.status)">
                {{ uda.status }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
              <!-- Mostra il nome del corso pulito -->
              {{ uda.course_name || '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              <!-- Mostra l'autore del corso -->
              {{ uda.course_teacher_username || '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
              <!-- Mostra i nomi degli argomenti -->
              {{ uda.topics_display?.join(', ') || '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
              <!-- Mostra il nome della prima materia, o '-' -->
              {{ uda.subjects_display?.[0] || '-' }}
              <!-- Potremmo aggiungere un tooltip o indicatore se ci sono più materie -->
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-center">
              {{ uda.contents?.length || 0 }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDate(uda.start_date) }} / {{ formatDate(uda.end_date) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <RouterLink
                :to="{ name: 'uda-detail', params: { id: uda.id } }"
                class="text-blue-600 hover:text-blue-900 transition duration-150 ease-in-out"
                title="Vedi Dettagli"
              >
                <EyeIcon class="h-5 w-5 inline-block" />
              </RouterLink>
              <RouterLink
                :to="{ name: 'uda-edit', params: { id: uda.id } }"
                class="text-yellow-600 hover:text-yellow-900 transition duration-150 ease-in-out"
                title="Modifica UDA"
              >
                <PencilIcon class="h-5 w-5 inline-block" />
              </RouterLink>
              <button
                @click="confirmDeleteSingleUda(uda.id, uda.title)"
                class="text-red-600 hover:text-red-900 transition duration-150 ease-in-out"
                title="Elimina UDA"
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
    // Accedi direttamente a courseStore.courses per migliorare il tracciamento della reattività
    const course = uda.course ? courseStore.courses.find(c => c.id === uda.course) : null;
    // Prendi la prima materia dall'array subjects, se esiste
    const firstSubjectId = uda.subjects && uda.subjects.length > 0 ? uda.subjects[0] : null;
    const subject = firstSubjectId ? subjectStore.getSubjectById(firstSubjectId) : null;
    return {
      ...uda, // Copia tutte le proprietà esistenti di uda
      ...uda,
      subject_details: subject,
    };
  });
});

// Filtra le UDA in base ai filtri selezionati
const filteredUdas = computed(() => {
  // Aggiungi dipendenza esplicita e log per debug
  const courses = courseStore.courses;
  console.log(`[UdaListView] Ricalcolo filteredUdas. Numero corsi nello store: ${courses.length}`);

  return enrichedUdas.value.filter(uda => {
    const statusMatch = selectedStatus.value ? uda.status === selectedStatus.value : true;
    // Confronto tra ID numerici (selectedCourseId.value e uda.course)
    const courseIdFilter = selectedCourseId.value;
    const udaCourseId = uda.course;
    const courseMatch = courseIdFilter !== null ? udaCourseId === courseIdFilter : true;
    // Log per debug
    console.log(`Filtering UDA ${uda.id}: courseIdFilter=${courseIdFilter}(${typeof courseIdFilter}), udaCourseId=${udaCourseId}(${typeof udaCourseId}), match=${courseMatch}`);
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