<template>
  <div class="uda-list-view p-4 md:p-8">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex justify-between items-center">
      <h2 class="text-2xl font-semibold">Elenco Unità Didattiche (UDA)</h2>
      <!-- Pulsante stile adattato per contrasto -->
      <RouterLink
        :to="{ name: 'uda-new' }"
        class="flex items-center px-3 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-100 transition duration-150 ease-in-out font-medium"
      >
        <PlusCircleIcon class="h-5 w-5 sm:mr-2" />
        <span class="hidden sm:inline">Nuova UDA</span>
      </RouterLink>
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-6">
        <label for="udaSearch" class="sr-only">Cerca UDA</label>
        <input
            id="udaSearch"
            type="text"
            v-model="searchQuery"
            placeholder="Cerca UDA per titolo, descrizione, stato, corso, materia, argomenti..."
            class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        />
    </div>

    <div v-if="udaStore.loading" class="text-center py-10">
      <p class="text-gray-600">Caricamento UDA...</p>
    </div>
    <div v-else-if="udaStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline">{{ udaStore.error }}</span>
    </div>
    <div v-else-if="filteredUdas.length === 0" class="text-center py-10 bg-gray-50 rounded-md">
       <p class="text-gray-600 text-lg" v-if="searchQuery">Nessuna UDA trovata per "{{ searchQuery }}".</p>
       <p class="text-gray-600 text-lg" v-else>Nessuna UDA trovata.</p>
       <p class="text-gray-500 mt-2" v-if="!searchQuery">Crea la tua prima UDA per iniziare.</p>
    </div>

    <!-- Tabella UDA Filtrate -->
    <div v-else class="shadow-lg overflow-x-auto border-b border-gray-200 sm:rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('title')">
              Titolo
              <span v-if="sortKey === 'title'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('description')">
              Descrizione
              <span v-if="sortKey === 'description'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('status')">
              Stato
              <span v-if="sortKey === 'status'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('course_name')">
              Corso
              <span v-if="sortKey === 'course_name'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('course_teacher_username')">
              Creato da (Corso)
              <span v-if="sortKey === 'course_teacher_username'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('topics_display')">
              Argomenti
              <span v-if="sortKey === 'topics_display'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('subjects_display')">
              Materie
              <span v-if="sortKey === 'subjects_display'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('contents')">
              Contenuti
              <span v-if="sortKey === 'contents'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('lesson_count')">
              N. Lez.
              <span v-if="sortKey === 'lesson_count'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('total_lesson_estimated_hours')">
              Ore Lez.
              <span v-if="sortKey === 'total_lesson_estimated_hours'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('total_estimated_hours')">
              Ore Stimate Tot.
              <span v-if="sortKey === 'total_estimated_hours'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('start_date')">
              Date (Inizio/Fine)
              <span v-if="sortKey === 'start_date'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
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
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-center">
              {{ uda.lesson_count || 0 }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-center">
              {{ uda.total_lesson_estimated_hours || '0.0' }}h
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-center">
              {{ uda.total_estimated_hours || '0.0' }}h
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
              <button
                @click="handleCopyUda(uda.id, uda.title)"
                class="text-green-600 hover:text-green-900 transition duration-150 ease-in-out"
                title="Copia UDA"
              >
                <DocumentDuplicateIcon class="h-5 w-5 inline-block" />
              </button>
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
import { ref, computed, onMounted } from 'vue'; // Rimosso watch
import { RouterLink, useRouter } from 'vue-router'; // Aggiunto useRouter
import { useUdaStore } from '@/stores/udaStore';
import { useCourseStore } from '@/stores/courseStore';
import { useSubjectStore } from '@/stores/subjectStore';
import { useTopicStore } from '@/stores/topicStore'; // Importa topicStore
import { useUiStore } from '@/stores/ui';
import { TrashIcon, EyeIcon, DocumentDuplicateIcon, PlusCircleIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'; // Aggiunto icone ordinamento
import type { UDA } from '@/types/uda'; // Rimosso Course
// import type { Subject } from '@/types/subject'; // Rimosso Subject
// import type { Topic } from '@/types/topic'; // Importa Topic type - Non più utilizzato dopo aver commentato la riga 175

const udaStore = useUdaStore();
const courseStore = useCourseStore();
const subjectStore = useSubjectStore();
const topicStore = useTopicStore(); // Istanzia topicStore
const uiStore = useUiStore();
const router = useRouter(); // Istanza del router
const searchQuery = ref('');
const sortKey = ref('start_date'); // Ordinamento di default
const sortOrder = ref('desc');

// Arricchisce le UDA con dettagli (es. nome corso, nome materia, nomi argomenti)
const enrichedUdas = computed(() => {
  return udaStore.udas.map(uda => {
    const course = uda.course ? courseStore.getCourseById(uda.course) : null;
    // Gestisce uda.subjects come array di ID, prendendo il primo per la materia principale
    // const firstSubjectId = uda.subjects && uda.subjects.length > 0 ? uda.subjects[0] : null; // Non usato
    // const subject = firstSubjectId ? subjectStore.getSubjectById(firstSubjectId) : null; // Non usato
    // const topics = uda.topics?.map(id => topicStore.getTopicById(id)).filter(Boolean) as Topic[] | undefined; // Non usato

    // Cerca il nome utente del docente. Assumiamo che courseStore.getCourseById restituisca dettagli del docente
    // o che ci sia un modo per ottenerli (es. uno store utenti). Adattare se necessario.
    // const teacherUsername = course?.teacher_details?.username || 'N/D'; // Esempio, potrebbe essere diverso
    // Se il backend fornisce direttamente teacher_username nel corso, usarlo:
    // Usa direttamente il campo fornito dal backend per l'UDA
    const teacherUsername = uda.course_teacher_username || '-';

    return {
      ...uda,
      course_name: course?.name,
      course_teacher_username: teacherUsername,
      // subjects_display e topics_display sono già forniti dal backend
      // e sono presenti in '...uda'. Non è necessario ricalcolarli qui
      // se l'obiettivo è solo visualizzare ciò che il backend invia.
      // Se si volesse una logica di fallback o di arricchimento diversa,
      // andrebbe gestita con più attenzione. Per ora, usiamo quelli del backend.
    };
  });
});


// Filtra e ordina le UDA
const filteredUdas = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  
  // 1. Filtra
  const filtered = query
    ? enrichedUdas.value.filter(uda => {
        const title = uda.title?.toLowerCase() || '';
        const description = uda.description?.toLowerCase() || '';
        const status = uda.status?.toLowerCase() || '';
        const courseName = uda.course_name?.toLowerCase() || '';
        const teacherUsername = uda.course_teacher_username?.toLowerCase() || '';
        const subjects = uda.subjects_display?.join(' ').toLowerCase() || '';
        const topics = uda.topics_display?.join(' ').toLowerCase() || '';

        return title.includes(query) ||
               description.includes(query) ||
               status.includes(query) ||
               courseName.includes(query) ||
               teacherUsername.includes(query) ||
               subjects.includes(query) ||
               topics.includes(query);
      })
    : enrichedUdas.value;

  // 2. Ordina
  return filtered.slice().sort((a, b) => {
    let valA: any;
    let valB: any;

    const key = sortKey.value;

    // Gestione chiavi speciali
    if (key === 'contents') {
      valA = a.contents?.length || 0;
      valB = b.contents?.length || 0;
    } else if (key === 'topics_display' || key === 'subjects_display') {
      valA = a[key]?.join(', ') || '';
      valB = b[key]?.join(', ') || '';
    } else {
      valA = a[key as keyof typeof a];
      valB = b[key as keyof typeof b];
    }

    // Normalizzazione per confronto
    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();
    if (valA === null || valA === undefined) valA = '';
    if (valB === null || valB === undefined) valB = '';

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});


onMounted(async () => {
  try {
    await Promise.all([
      udaStore.fetchUdas(),
      courseStore.fetchCourses(),
      subjectStore.fetchSubjects(),
      topicStore.fetchTopics() // Assicura caricamento argomenti
    ]);
  } catch (error) {
    console.error("Errore caricamento dati per UdaListView:", error);
    uiStore.addNotification({ message: `Errore caricamento dati: ${(error as Error).message}`, type: 'error'});
  }
});

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

const confirmDeleteSingleUda = async (udaId: number, udaTitle: string) => {
  const confirmed = window.confirm(`Sei sicuro di voler eliminare l'UDA "${udaTitle}" (ID: ${udaId})? L'azione non è reversibile.`);
  if (confirmed) {
    uiStore.addNotification({ message: `Eliminazione UDA "${udaTitle}" in corso...`, type: 'info' });
    try {
      await udaStore.deleteUda(udaId);
      uiStore.addNotification({ message: `UDA "${udaTitle}" eliminata con successo.`, type: 'success', duration: 3000 });
    } catch (error) {
      console.error(`Errore durante l'eliminazione dell'UDA ID ${udaId}:`, error);
      uiStore.addNotification({ message: `Errore eliminazione: ${(error as Error).message}`, type: 'error' });
    }
  } else {
    uiStore.addNotification({ message: 'Eliminazione UDA annullata.', type: 'info', duration: 2000 });
  }
};

const handleCopyUda = async (udaId: number, udaTitle: string) => {
  uiStore.addNotification({ message: `Copia dell'UDA "${udaTitle}" in corso...`, type: 'info' });
  try {
    const newUda = await udaStore.copyUda(udaId);
    if (newUda && newUda.id) {
      uiStore.addNotification({ message: `UDA "${udaTitle}" copiata con successo come "${newUda.title}".`, type: 'success', duration: 4000 });
      router.push({ name: 'uda-edit', params: { id: newUda.id } });
    } else {
      throw new Error('ID della nuova UDA non ricevuto.');
    }
  } catch (error) {
    console.error(`Errore durante la copia dell'UDA ID ${udaId}:`, error);
    uiStore.addNotification({ message: `Errore durante la copia dell'UDA: ${(error as Error).message}`, type: 'error' });
  }
};

const getStatusClass = (status?: UDA['status']) => {
  if (!status) return 'text-gray-600 bg-gray-100';
  if (status === 'COMPLETED') return 'text-green-700 bg-green-100';
  if (status === 'IN_PROGRESS') return 'text-blue-700 bg-blue-100';
  if (status === 'TODO') return 'text-yellow-700 bg-yellow-100';
  return 'text-gray-600 bg-gray-100';
};

// Rimosso getCourseName perché non utilizzato (il nome del corso è in enrichedUdas)

const formatDate = (dateString?: string | null) => {
  if (!dateString) return 'N/D';
  try {
    const date = new Date(dateString);
    // Verifica se la data è valida prima di formattare
    if (isNaN(date.getTime())) {
        return dateString; // Ritorna la stringa originale se non valida
    }
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch (e) {
    return dateString; // Ritorna la stringa originale in caso di errore
  }
};

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