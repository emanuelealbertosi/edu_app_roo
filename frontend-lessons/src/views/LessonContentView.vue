<template>
  <div class="lesson-content-manager">
    <button @click="goBack" class="back-button">&larr; Torna alla Lezione</button>

    <div v-if="lessonStore.isLoading">Caricamento dati lezione...</div>
    <div v-else-if="lessonStore.error && !lesson" class="error-message">
      Errore nel caricamento della lezione: {{ lessonStore.error }}
    </div>
    <div v-else-if="lesson">
      <!-- Intestazione con sfondo blu -->
      <div class="bg-blue-600 text-white p-4 rounded-md mb-6">
        <h2 class="text-2xl font-semibold">Gestisci Contenuti per: {{ lesson.title }}</h2>
      </div>

      <!-- Area Contenuti Evidenziata -->
      <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">

        <!-- Lista Contenuti Esistenti (con opzioni modifica/elimina/riordino) -->
        <div class="content-list">
          <h3 class="text-xl font-semibold text-gray-700 mb-4">Contenuti Attuali</h3> <!-- Stile titolo sezione -->
        <div v-if="lessonStore.isLoadingContents">Caricamento contenuti...</div>
         <div v-else-if="!sortedContents || sortedContents.length === 0" class="no-content">
            Nessun contenuto aggiunto a questa lezione.
        </div>
        <ul v-else class="content-items">
           <!-- Usare Draggable se si vuole riordino drag-and-drop -->
           <li v-for="(content, index) in sortedContents" :key="content.id" class="content-item">
               <span class="content-order">#{{ index + 1 }}</span>
               <span class="content-type-badge">{{ content.content_type.toUpperCase() }}</span>
               <span class="content-item-title">{{ content.title || getContentTypeTitle(content) }}</span>
               <div class="content-actions">
                   <!-- <button @click="moveContentUp(index)" :disabled="index === 0">Su</button>
                   <button @click="moveContentDown(index)" :disabled="index === sortedContents.length - 1">Giù</button> -->
                   <button @click="editContent(content)" class="action-button edit">Modifica</button>
                   <button @click="confirmDeleteContent(content)" class="action-button delete">Elimina</button>
               </div>
           </li>
        </ul>
      </div>

      <hr class="separator">

      <!-- Form per Aggiungere Nuovo Contenuto -->
      <div class="add-content-form">
        <h3>Aggiungi Nuovo Contenuto</h3>
        <form @submit.prevent="handleAddContent">
           <div class="form-group">
             <label for="content-type">Tipo di Contenuto:</label>
             <select id="content-type" v-model="newContent.content_type" required>
                <option value="html">Contenuto HTML</option>
                <option value="pdf">Documento PDF</option>
                <option value="ppt">Presentazione PPT/PPTX</option>
                <option value="url">Link Esterno</option>
             </select>
           </div>

           <div class="form-group">
             <label for="content-title">Titolo (opzionale):</label>
             <input type="text" id="content-title" v-model="newContent.title" placeholder="Es: Introduzione al Capitolo">
           </div>

           <!-- Campi specifici per tipo -->
           <div v-if="newContent.content_type === 'html'" class="form-group">
              <label for="content-html">Contenuto HTML:</label>
              <!-- Sostituito WysiwygEditor con textarea per permettere HTML grezzo -->
              <textarea
                id="content-html"
                v-model="newContent.html_content"
                rows="10"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
                placeholder="Inserisci qui il tuo codice HTML..."
                required
              ></textarea>
              <small class="text-xs text-gray-500 mt-1">Attenzione: Il codice inserito verrà visualizzato senza sanitizzazione.</small>
           </div>
           <div v-if="newContent.content_type === 'pdf' || newContent.content_type === 'ppt'" class="form-group">
               <label for="content-file">Seleziona File ({{ newContent.content_type.toUpperCase() }}):</label>
               <input type="file" id="content-file" @change="handleFileChange" :accept="fileAcceptType" required>
               <div v-if="newContent.file" class="file-preview">Selezionato: {{ newContent.file.name }}</div>
           </div>
            <div v-if="newContent.content_type === 'url'" class="form-group">
               <label for="content-url">URL Esterno:</label>
               <input type="url" id="content-url" v-model="newContent.url" placeholder="https://esempio.com/risorsa" required>
           </div>

           <div v-if="addError" class="error-message">{{ addError }}</div>

           <button type="submit" class="button-save" :disabled="lessonStore.isLoadingContents">
               {{ lessonStore.isLoadingContents ? 'Aggiunta in corso...' : 'Aggiungi Contenuto' }}
           </button>
        </form>
      </div> <!-- Fine add-content-form -->

    </div> <!-- Fine Area Contenuti Evidenziata -->

       <!-- Modale per Modificare Contenuto Esistente -->
       <LessonContentEditModal
            v-if="contentToEdit"
            :content="contentToEdit"
            :lessonId="lessonId"
            @close="closeEditModal"
            @save="handleUpdateContent"
       />

    </div>
    <div v-else>Lezione non trovata o non autorizzato.</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useLessonStore } from '@/stores/lessons';
// Importa il modale di modifica e l'editor WYSIWYG usando percorsi relativi
import LessonContentEditModal from '../components/features/lezioni/LessonContentEditModal.vue';
// Rimosso import WysiwygEditor non più utilizzato

// Importa i tipi corretti
import type { LessonContent } from '@/types/lezioni'; // Rimosso 'Lesson' non utilizzato

const route = useRoute();
const router = useRouter();
const lessonStore = useLessonStore();

const lessonId = ref<number>(0); // Inizializza a 0 o gestisci null
const addError = ref<string | null>(null); // Dichiarato una sola volta
const contentToEdit = ref<LessonContent | null>(null);

// Stato per il nuovo contenuto
const newContent = ref({
    content_type: 'html' as 'html' | 'pdf' | 'ppt' | 'url',
    title: '',
    html_content: '',
    file: null as File | null,
    url: ''
});

// Carica la lezione (che include i contenuti)
const loadLessonData = async () => {
    const idParam = route.params.lessonId; // Assumendo che l'URL sia /lezioni/:lessonId/manage-contents
    if (typeof idParam === 'string') {
        const id = parseInt(idParam, 10);
        if (!isNaN(id)) {
            lessonId.value = id;
            // Usiamo fetchLesson perché carica anche i contenuti associati (azione rinominata nello store)
            await lessonStore.fetchLesson(id);
        } else {
            lessonStore.error = "ID lezione non valido.";
            lessonId.value = 0; // Resetta a valore non valido
        }
    } else {
         lessonStore.error = "ID lezione mancante.";
         lessonId.value = 0; // Resetta a valore non valido
    }
};

onMounted(loadLessonData);
// Ricarica se l'ID cambia (improbabile in questa vista ma per sicurezza)
watch(() => route.params.lessonId, loadLessonData);

const lesson = computed(() => lessonStore.currentLesson);

const sortedContents = computed(() => {
    if (!lesson.value || !lesson.value.contents) return [];
    return [...lesson.value.contents].sort((a, b) => a.order - b.order);
});

// Determina l'attributo accept per l'input file
const fileAcceptType = computed(() => {
    if (newContent.value.content_type === 'pdf') return '.pdf,application/pdf';
    if (newContent.value.content_type === 'ppt') return '.ppt,.pptx,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation';
    return '*/*'; // Default
});

// Gestisce la selezione del file
const handleFileChange = (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files[0]) {
        const file = target.files[0];
        const invalidCharsRegex = /[ ()]/; // Regex per trovare spazi o parentesi

        if (invalidCharsRegex.test(file.name)) {
            // Nome file non valido
            addError.value = "Il nome del file non può contenere spazi o parentesi.";
            newContent.value.file = null;
            target.value = ''; // Resetta l'input per permettere nuova selezione
        } else {
            // Nome file valido
            newContent.value.file = file;
            addError.value = null; // Pulisce eventuali errori precedenti
        }
    } else {
        newContent.value.file = null;
    }
};

// Resetta il form di aggiunta
const resetNewContentForm = () => {
    newContent.value = {
        content_type: 'html', title: '', html_content: '', file: null, url: ''
    };
    addError.value = null;
    // Resetta anche l'input file nel DOM se necessario
    const fileInput = document.getElementById('content-file') as HTMLInputElement;
    if (fileInput) fileInput.value = '';
};

// Gestisce l'invio del form di aggiunta (Versione Corretta)
const handleAddContent = async () => {
    addError.value = null; // Resetta errore all'inizio
    if (!lessonId.value) return;

    let addedContent: LessonContent | null = null; // Per tracciare il risultato

    try {
        if (newContent.value.content_type === 'html') {
            if (!newContent.value.html_content) { throw new Error("Il contenuto HTML è obbligatorio."); }
            const apiData = {
                content_type: 'html',
                title: newContent.value.title || undefined,
                html_content: newContent.value.html_content,
                // order: ... // Il backend dovrebbe assegnare l'ordine? O lo inviamo?
            };
            addedContent = await lessonStore.addLessonContent(lessonId.value, apiData);

        } else if (newContent.value.content_type === 'url') {
            if (!newContent.value.url) { throw new Error("L'URL è obbligatorio."); }
             const apiData = {
                content_type: 'url',
                title: newContent.value.title || undefined,
                url: newContent.value.url,
                // order: ...
            };
            addedContent = await lessonStore.addLessonContent(lessonId.value, apiData);

        } else if (newContent.value.content_type === 'pdf' || newContent.value.content_type === 'ppt') {
            if (!newContent.value.file) { throw new Error("Selezionare un file è obbligatorio."); }
            if (!(newContent.value.file instanceof File)) { throw new Error("Errore interno: file non valido."); }

            const formData = new FormData();
            formData.append('content_type', newContent.value.content_type);
            if (newContent.value.title) formData.append('title', newContent.value.title);
            formData.append('file', newContent.value.file);
            // formData.append('order', ...);

            addedContent = await lessonStore.addLessonContent(lessonId.value, formData);

        } else {
            throw new Error("Tipo di contenuto non valido.");
        }

        // Se arriviamo qui senza errori, l'aggiunta ha avuto successo (o lo store ha gestito l'errore API)
        if (addedContent) {
            resetNewContentForm();
            // Lo store dovrebbe essersi aggiornato, la lista si aggiornerà reattivamente
        } else {
             // Se addLessonContent ritorna null ma non lancia eccezioni, l'errore è nello store
             addError.value = lessonStore.error || "Errore sconosciuto durante l'aggiunta.";
        }

    } catch (error: any) {
         console.error("Errore in handleAddContent:", error);
         addError.value = error.message || "Si è verificato un errore.";
         // Assicurati che l'errore dello store sia resettato se gestiamo qui
         lessonStore.error = null;
    }
};


// Funzioni per Modifica/Elimina/Riordino
const editContent = (content: LessonContent) => {
    contentToEdit.value = { ...content }; // Passa una copia al modale
};

const closeEditModal = () => {
    contentToEdit.value = null;
};

// Gestisce il salvataggio dal modale di modifica
const handleUpdateContent = async (contentId: number, data: FormData | object) => {
    if (!lessonId.value) return;
    // Chiama l'azione dello store per aggiornare
    const success = await lessonStore.updateLessonContent(lessonId.value, contentId, data);
    if (success) {
        closeEditModal();
        // Lo store dovrebbe aggiornare currentLesson.contents, la lista si aggiorna
    } else {
        // Mostra errore (preso dallo store)
        alert(`Errore durante l'aggiornamento: ${lessonStore.error || 'Errore sconosciuto'}`);
        lessonStore.error = null; // Resetta errore nello store
    }
};


const confirmDeleteContent = async (content: LessonContent) => {
     if (confirm(`Sei sicuro di voler eliminare questo blocco di contenuto (${content.title || getContentTypeTitle(content)})?`)) {
        if (!lessonId.value) return;
        await lessonStore.deleteLessonContent(lessonId.value, content.id);
         if (lessonStore.error) {
            alert(`Errore durante l'eliminazione: ${lessonStore.error}`);
            lessonStore.error = null;
        }
        // Lo store si aggiorna localmente, non serve ricaricare
     }
};

// const moveContentUp = (index: number) => { /* Logica riordino */ };
// const moveContentDown = (index: number) => { /* Logica riordino */ };

// Helper per titolo default
const getContentTypeTitle = (content: LessonContent): string => {
    switch(content.content_type) {
        case 'html': return 'Blocco HTML';
        case 'pdf': return 'Documento PDF';
        case 'ppt': return 'Presentazione PPT';
        case 'url': return 'Link Esterno';
        default: return 'Contenuto Sconosciuto';
    }
};


const goBack = () => {
    if (lessonId.value) {
        // Torna alla vista dettaglio lezione
        router.push({ name: 'lesson-detail', params: { id: lessonId.value.toString() } });
    } else {
        router.push({ name: 'teacher-lessons' }); // Fallback alla lista lezioni docente
    }
};

</script>

<style scoped>
/* Stili (invariati) */
.lesson-content-manager {
  padding: 2rem;
  max-width: 900px;
  margin: 0 auto;
}
.back-button {
    margin-bottom: 1rem;
    background: none; border: none; color: #007bff; cursor: pointer; font-size: 0.9rem;
}
.back-button:hover { text-decoration: underline; }
h2, h3 { margin-bottom: 1rem; }
.content-list { margin-bottom: 2rem; }
.content-items { list-style: none; padding: 0; }
.content-item {
    display: flex;
    align-items: center;
    padding: 0.8rem 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 0.5rem;
    background-color: #fff;
}
.content-order { font-weight: bold; margin-right: 0.75rem; color: #888; }
.content-type-badge {
    background-color: #e9ecef;
    color: #495057;
    padding: 0.2em 0.6em;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.75rem;
    text-transform: uppercase;
}
.content-item-title { flex-grow: 1; margin-right: 1rem; }
.content-actions { display: flex; gap: 0.5rem; }
.action-button { /* Stili base comuni */
    padding: 4px 8px; font-size: 0.8rem; border: none; border-radius: 3px; cursor: pointer; color: white;
}
.action-button.edit { background-color: #ffc107; color: #333; }
.action-button.delete { background-color: #dc3545; }
.separator { margin: 2rem 0; border: 0; border-top: 1px solid #eee; }
.add-content-form { border: 1px solid #eee; padding: 1.5rem; border-radius: 6px; background-color: #f8f9fa; }
.form-group { margin-bottom: 1rem; }
label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
input[type="text"], input[type="url"], textarea, select {
  width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;
}
textarea { resize: vertical; min-height: 150px; }
input[type="file"] { padding: 0.5rem; } /* Stile diverso per file input */
.file-preview { font-size: 0.9rem; color: #555; margin-top: 0.5rem; }
.button-save { /* Stile bottone salva */
    padding: 0.7rem 1.5rem; background-color: #28a745; color: white; border: none;
    border-radius: 4px; cursor: pointer; font-size: 1rem;
}
.button-save:disabled { background-color: #ccc; cursor: not-allowed; }
.button-save:not(:disabled):hover { background-color: #218838; }
.error-message { color: red; margin: 1rem 0; }
.no-content { color: #888; font-style: italic; margin-top: 1rem; }
</style>