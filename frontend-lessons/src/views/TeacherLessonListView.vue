<template>
  <div class="lesson-list-container p-6">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-semibold text-gray-700">Le Mie Lezioni</h2>
      <button @click="openAddModalDirectly" class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-md shadow-sm transition duration-150 ease-in-out">
        Crea Nuova Lezione
      </button>
    </div>

    <div v-if="lessonStore.isLoading" class="text-center text-gray-500 py-10">
      Caricamento lezioni...
    </div>

    <div v-if="lessonStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore:</strong>
      <span class="block sm:inline"> {{ lessonStore.error }}</span>
    </div>

    <div v-if="!lessonStore.isLoading && lessons.length > 0" class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titolo</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Argomento</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Materia</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stato</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Creazione</th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="lesson in lessons" :key="lesson.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ lesson.title }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getTopicName(lesson.topic) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getSubjectNameFromTopic(lesson.topic) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
                <span :class="lesson.is_published ? 'text-green-600' : 'text-yellow-600'">
                    {{ lesson.is_published ? 'Pubblicata' : 'Bozza' }}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(lesson.created_at) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <button @click="editLesson(lesson as Lesson)" class="text-yellow-600 hover:text-yellow-900">Modifica</button>
              <button @click="gotoContents(lesson.id)" class="text-purple-600 hover:text-purple-900">Contenuti</button>
              <button @click="gotoAssign(lesson.id)" class="text-cyan-600 hover:text-cyan-900">Assegna</button>
              <button @click="confirmDelete(lesson as Lesson)" class="text-red-600 hover:text-red-900">Elimina</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!lessonStore.isLoading && lessons.length === 0 && !lessonStore.error" class="text-center text-gray-500 py-10">
      Non hai ancora creato nessuna lezione.
    </div>

     <LessonEditModal
      v-if="showAddModal || lessonToEdit"
      :lesson="lessonToEdit"
      :topics="topicStore.topics"
      @close="closeModal"
      @save="handleSave"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'; // Aggiunto onUnmounted
import { useRouter } from 'vue-router';
import { useLessonStore } from '@/stores/lessons';
import { useTopicStore } from '@/stores/topics';
import { useSubjectStore } from '@/stores/subjects';
import emitter from '@/eventBus'; // Importa l'event bus
import LessonEditModal from '../components/features/lezioni/LessonEditModal.vue';
import type { Lesson } from '@/types/lezioni'; // Rimossi Topic e Subject non usati qui


const lessonStore = useLessonStore();
const topicStore = useTopicStore();
const subjectStore = useSubjectStore();
const router = useRouter();

const lessons = computed(() => lessonStore.lessons);

const showAddModal = ref(false);
const lessonToEdit = ref<Lesson | null>(null);

// Funzione chiamata dall'event bus per aprire il modale
const handleOpenAddModalEvent = () => {
  console.log("TeacherLessonListView: Received open-add-lesson-modal event.");
  lessonToEdit.value = null; // Assicura che non siamo in modalità modifica
  showAddModal.value = true;
};

// Funzione chiamata dal pulsante "Crea Nuova Lezione" locale
const openAddModalDirectly = () => {
    lessonToEdit.value = null;
    showAddModal.value = true;
}

onMounted(async () => {
  await subjectStore.fetchSubjects();
  await topicStore.fetchTopics();
  await lessonStore.fetchLessons();
  // Registra il listener per l'evento
  emitter.on('open-add-lesson-modal', handleOpenAddModalEvent);
});

onUnmounted(() => {
  // Rimuovi il listener quando il componente viene smontato
  emitter.off('open-add-lesson-modal', handleOpenAddModalEvent);
});

const getTopicName = (topicId: number): string => {
    const topic = topicStore.topics.find(t => t.id === topicId);
    return topic ? topic.name : 'N/D';
};
const getSubjectNameFromTopic = (topicId: number): string => {
    const topic = topicStore.topics.find(t => t.id === topicId);
    if (!topic) return 'N/D';
    const subject = subjectStore.subjects.find(s => s.id === topic.subject);
    return subject ? subject.name : 'N/D';
};

const formatDate = (dateString: string): string => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'short', day: 'numeric' });
};

const editLesson = (lesson: Lesson) => {
  lessonToEdit.value = { ...lesson };
  showAddModal.value = false; // Chiudi modale aggiunta se aperto
};

const confirmDelete = async (lesson: Lesson) => {
  if (confirm(`Sei sicuro di voler eliminare la lezione "${lesson.title}"?`)) {
    await lessonStore.deleteLesson(lesson.id);
    if (lessonStore.error) {
        alert(`Errore durante l'eliminazione: ${lessonStore.error}`);
        lessonStore.error = null;
    }
  }
};

const closeModal = () => {
  showAddModal.value = false;
  lessonToEdit.value = null;
};

const handleSave = async (lessonData: { id?: number; title: string; topic: number; description?: string; is_published?: boolean }) => {
    let success = false;
    let savedLesson: Lesson | null = null;

    if (lessonData.id) {
        success = await lessonStore.updateLesson(lessonData.id, lessonData);
    } else {
        savedLesson = await lessonStore.addLesson(lessonData);
        success = !!savedLesson;
    }

    if (success) {
        closeModal();
        await lessonStore.fetchLessons(); // Ricarica per vedere le modifiche
    } else {
         alert(`Errore durante il salvataggio: ${lessonStore.error}`);
         lessonStore.error = null;
    }
};

const gotoAssign = (lessonId: number) => {
    router.push({ name: 'lesson-assign', params: { lessonId: lessonId.toString() } });
};

const gotoContents = (lessonId: number) => {
     // Usa il nome della rotta definito nel router
    router.push({ name: 'lesson-contents', params: { lessonId: lessonId.toString() } });
};

</script>
