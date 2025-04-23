<template>
  <div class="lesson-detail-container">
    <!-- Loading State -->
    <div v-if="lessonStore.isLoading">Caricamento lezione...</div>

    <!-- Error State -->
    <div v-else-if="lessonStore.error" class="error-message">
      Errore nel caricamento della lezione: {{ lessonStore.error }}
    </div>

    <!-- Lesson Content -->
    <div v-else-if="lesson">
      <button @click="goBack" class="back-button">&larr; Torna alla lista</button>
      <h1>{{ lesson.title }}</h1>
      <p class="lesson-meta">
        Argomento: {{ lesson.topic_name || 'N/D' }} (Materia: {{ lesson.subject_name || 'N/D' }})
      </p>
      <p v-if="lesson.description" class="lesson-description">{{ lesson.description }}</p>

      <hr class="content-separator">

      <h2>Contenuti della Lezione</h2>
      <div v-if="!lesson.contents || lesson.contents.length === 0" class="no-content">
        Questa lezione non ha ancora contenuti.
      </div>
      <div v-else class="lesson-contents-wrapper">
        <!-- Itera sui contenuti e usa un componente per visualizzarli -->
        <LessonContentDisplay
          v-for="content in sortedContents"
          :key="content.id"
          :content="content"
          @open-html-modal="handleOpenHtmlModal"
        />
      </div>

       <!-- Sezione Azioni (es. per Docente) -->
       <!-- <div v-if="authStore.userRole === 'Docente'" class="teacher-actions">
            <button @click="editLessonDetails">Modifica Dettagli Lezione</button>
            <button @click="manageContents">Gestisci Contenuti</button>
       </div> -->

    </div>

    <!-- Not Found State -->
    <div v-else>
      Lezione non trovata.
    </div>

    <!-- Modale per visualizzare contenuto HTML -->
    <div v-if="showHtmlModal" class="fixed inset-0 bg-black bg-opacity-75 z-40 flex justify-center items-center p-4 transition-opacity duration-300" @click.self="closeHtmlModal">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden">
        <!-- Header Modale -->
        <div class="flex justify-between items-center p-4 border-b bg-gray-50 flex-shrink-0">
          <div class="flex items-center space-x-3">
             <h3 class="text-lg font-semibold text-gray-800">Visualizzatore Contenuto</h3>
             <button @click="downloadHtmlContent" title="Scarica contenuto HTML" class="text-gray-500 hover:text-indigo-600 transition-colors duration-150">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
             </button>
          </div>
          <button @click="closeHtmlModal" class="text-gray-500 hover:text-gray-800 text-2xl font-bold leading-none">&times;</button>
        </div>
        <!-- Contenuto Modale (Iframe) -->
        <div class="flex-grow overflow-auto">
          <iframe
            :srcdoc="htmlModalContent"
            class="w-full h-full border-0"
            title="Contenuto HTML Modale"
            ></iframe>
        </div>
      </div>
    </div>
    <!-- Fine Modale -->

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useLessonStore } from '@/stores/lessons';
import { useAuthStore } from '@/stores/auth'; // Per eventuali azioni specifiche ruolo
// Importa il componente per visualizzare i contenuti usando percorso relativo
import LessonContentDisplay from '../components/features/lezioni/LessonContentDisplay.vue';
// Importa i tipi corretti
import type { Lesson, LessonContent } from '@/types/lezioni';

// Stato per la modale HTML
const showHtmlModal = ref(false);
const htmlModalContent = ref('');


const route = useRoute();
const router = useRouter();
const lessonStore = useLessonStore();
const authStore = useAuthStore(); // Per controlli ruolo

const lessonId = ref<number | null>(null);

// Estrae l'ID dalla route e carica i dati
const loadLesson = async () => {
    const idParam = route.params.id;
    if (typeof idParam === 'string') {
        const id = parseInt(idParam, 10);
        if (!isNaN(id)) {
            lessonId.value = id;
            await lessonStore.fetchLesson(id); // Usa l'azione rinominata
        } else {
            lessonStore.error = "ID lezione non valido.";
            lessonId.value = null;
        }
    } else {
         lessonStore.error = "ID lezione mancante.";
         lessonId.value = null;
    }
};

// Carica la lezione quando il componente viene montato o l'ID nella route cambia
onMounted(loadLesson);
watch(() => route.params.id, loadLesson); // Ricarica se l'ID cambia

const lesson = computed(() => lessonStore.currentLesson);

// Ordina i contenuti per il campo 'order'
const sortedContents = computed(() => {
    if (!lesson.value || !lesson.value.contents) {
        return [];
    }
    // Clona l'array prima di ordinarlo per non mutare lo state dello store direttamente
    return [...lesson.value.contents].sort((a, b) => a.order - b.order);
});

const goBack = () => {
    // Torna indietro nella history o a una lista specifica
    if (window.history.length > 1) {
        router.go(-1);
    } else {
        // Fallback se non c'è history (es. accesso diretto all'URL)
        if (authStore.userRole === 'Studente') {
            router.push({ name: 'assigned-lessons' });
        } else if (authStore.userRole === 'Docente') {
             router.push({ name: 'teacher-lessons' });
        } else {
            router.push({ name: 'dashboard' }); // Default
        }
    }
};

// Funzioni placeholder per azioni docente (da implementare)
// const editLessonDetails = () => { ... }
// const manageContents = () => { ... }

// Gestori per la modale HTML
const handleOpenHtmlModal = (htmlContent: string) => {
  htmlModalContent.value = htmlContent;
  showHtmlModal.value = true;
};

const closeHtmlModal = () => {
  showHtmlModal.value = false;
  htmlModalContent.value = ''; // Pulisce il contenuto
};

// Funzione per scaricare il contenuto HTML
const downloadHtmlContent = () => {
  if (!htmlModalContent.value) return;

  const blob = new Blob([htmlModalContent.value], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  // Suggerisce un nome file (l'utente può cambiarlo)
  const lessonTitleSlug = lesson.value?.title.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '') || 'lezione';
  link.download = `${lessonTitleSlug}_contenuto.html`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url); // Libera memoria
};

</script>

<style scoped>
.lesson-detail-container {
  padding: 2rem;
  max-width: 900px; /* Limita larghezza per leggibilità */
  margin: 0 auto;
}
.back-button {
    margin-bottom: 1rem;
    background: none;
    border: none;
    color: #007bff;
    cursor: pointer;
    font-size: 0.9rem;
}
.back-button:hover {
    text-decoration: underline;
}

h1 {
  margin-top: 0;
  margin-bottom: 0.5rem;
}
.lesson-meta {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 1rem;
}
.lesson-description {
    margin-bottom: 1.5rem;
    line-height: 1.6;
}
.content-separator {
    margin: 2rem 0;
    border: 0;
    border-top: 1px solid #eee;
}
h2 {
    margin-bottom: 1.5rem;
}
.no-content {
    color: #888;
    font-style: italic;
}
.lesson-contents-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1.5rem; /* Spazio tra i blocchi di contenuto */
}
.error-message {
  color: red;
  margin: 1rem 0;
}
.teacher-actions {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #eee;
    display: flex;
    gap: 1rem;
}
</style>