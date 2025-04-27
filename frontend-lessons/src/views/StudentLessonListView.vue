<template>
  <div class="assigned-lesson-list-container p-6">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6">
        <h2 class="text-2xl font-semibold">Le Mie Lezioni Assegnate</h2>
    </div>

    <div v-if="lessonStore.isLoadingAssignments" class="text-center text-gray-500 py-10">
      Caricamento lezioni assegnate...
    </div>

    <div v-if="lessonStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore:</strong>
      <span class="block sm:inline"> {{ lessonStore.error }}</span>
    </div>

    <div v-if="!lessonStore.isLoadingAssignments && assignedLessons.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
       <div v-for="assignment in assignedLessons" :key="assignment.id" class="lesson-card bg-white rounded-lg shadow-md overflow-hidden flex flex-col">
           <div class="p-5 flex-grow">
               <h3 class="text-lg font-semibold text-gray-800 mb-2">{{ assignment.lesson.title || 'Lezione (ID: ' + assignment.lesson.id + ')' }}</h3>
               <p class="text-xs text-gray-500 mb-3">
                   <!-- Rimosso 'Assegnata da:' perché il campo non è più disponibile -->
                   Assegnata il: {{ formatDate(assignment.assigned_at) }} <br>
                   <span v-if="assignment.viewed_at" class="text-green-600">Vista il: {{ formatDate(assignment.viewed_at) }}</span>
                   <span v-else class="text-yellow-600 italic">Non ancora vista</span>
               </p>
           </div>
           <div class="bg-gray-50 px-5 py-3 mt-auto">
               <button @click="viewLesson(assignment as LessonAssignment)" class="w-full text-center px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-sm font-medium rounded-md shadow-sm transition duration-150 ease-in-out">
                   Visualizza Lezione
               </button>
           </div>
       </div>
    </div>

    <div v-if="!lessonStore.isLoadingAssignments && assignedLessons.length === 0 && !lessonStore.error" class="text-center text-gray-500 py-10">
      Nessuna lezione ti è stata ancora assegnata.
    </div>

  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useLessonStore } from '@/stores/lessons';
// Importa il tipo corretto
import type { LessonAssignment } from '@/types/lezioni';


const lessonStore = useLessonStore();
const router = useRouter();

const assignedLessons = computed(() => lessonStore.assignedLessons);

onMounted(() => {
  lessonStore.fetchAssignedLessons();
});

// Helper per formattare date
const formatDate = (dateString: string | null | undefined): string => {
    if (!dateString) return '';
    const date = new Date(dateString);
    // Controllo più robusto per aggiungere l'ora
    const isViewedAt = assignedLessons.value.some(a => a.viewed_at === dateString);
    const options: Intl.DateTimeFormatOptions = {
        year: 'numeric', month: 'short', day: 'numeric',
        ...(isViewedAt && { hour: '2-digit', minute: '2-digit' }) // Aggiunge ora se è viewed_at
    };
    return date.toLocaleDateString('it-IT', options);
};

// La funzione ora accetta il tipo LessonAssignment importato
const viewLesson = (assignment: LessonAssignment) => {
    if (!assignment.viewed_at) {
        lessonStore.markAssignmentAsViewed(assignment.id);
    }
    // Corretto: passare l'ID numerico della lezione, non l'oggetto intero convertito in stringa
    router.push({ name: 'lesson-detail', params: { id: assignment.lesson.id.toString() } });
};

</script>
