<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-content select-existing-content-modal-content">
      <div class="modal-header-custom">
        <h5 class="modal-title-custom">Aggiungi Contenuto Esistente</h5>
        <button type="button" class="button-close-custom" @click="closeModal" aria-label="Close">&times;</button>
      </div>
      <div class="modal-body-custom">
        <ul class="nav nav-tabs mb-3">
          <li class="nav-item">
            <a class="nav-link" :class="{ active: activeTab === 'lessons' }" href="#" @click.prevent="activeTab = 'lessons'">Lezioni</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" :class="{ active: activeTab === 'quizzes' }" href="#" @click.prevent="activeTab = 'quizzes'">Quiz</a>
          </li>
        </ul>

        <div v-if="loading" class="text-center">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">Caricamento...</span>
          </div>
        </div>

        <div v-else-if="errorLoadingContent" class="alert alert-danger">
          {{ errorLoadingContent }}
        </div>
        <div v-else>
          <!-- Tab Lezioni -->
          <div v-show="activeTab === 'lessons'">
            <h6>Seleziona Lezioni</h6>
            <div v-if="!lessons.length" class="alert alert-info">Nessuna lezione disponibile.</div>
            <ul v-else class="list-group content-selection-list">
              <li v-for="lesson in lessons" :key="lesson.id" class="list-group-item">
                <input
                  type="checkbox"
                  :value="{ type: UDAContentType.LESSON, id: lesson.id, title: lesson.title }"
                  v-model="selectedItems"
                  class="form-check-input me-2"
                />
                {{ lesson.title }}
                <small v-if="lesson.subject_name" class="text-muted ms-2">({{ lesson.subject_name }})</small>
              </li>
            </ul>
          </div>

          <!-- Tab Quiz -->
          <div v-show="activeTab === 'quizzes'">
            <h6>Seleziona Template Quiz</h6>
            <div v-if="!quizTemplates.length" class="alert alert-info">Nessun template di quiz disponibile.</div>
            <ul v-else class="list-group content-selection-list">
              <li v-for="template in quizTemplates" :key="template.id" class="list-group-item">
                <!-- Log dell'oggetto template completo -->
                <!-- {{ console.log('[SelectExistingContentModal] Template Quiz in loop:', JSON.parse(JSON.stringify(template))) }} -->
                <input
                  type="checkbox"
                  :value="{ type: 'QUIZ_TEMPLATE', id: template.id, title: template.title }"
                  v-model="selectedItems"
                  class="form-check-input me-2"
                />
                {{ template.title }}
                <small v-if="template.subject_name" class="text-muted ms-2">({{ template.subject_name }})</small>
                 <small v-if="template.questions_count !== undefined" class="text-muted ms-1">[{{ template.questions_count }}q]</small>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="modal-footer-custom">
        <button type="button" class="button-cancel" @click="closeModal" :disabled="isConfirming">Annulla</button>
        <button
          type="button"
          class="button-save"
          @click="confirmSelection"
          :disabled="selectedItems.length === 0 || isConfirming"
        >
          <span v-if="isConfirming" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
          {{ isConfirming ? 'Aggiungendo...' : `Aggiungi Selezionati (${selectedItems.length})` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useLessonStore } from '@/stores/lessons';
import { useQuizStore } from '@/stores/quizStore';
import { useUiStore } from '@/stores/ui';
import type { Lesson } from '@/types/lezioni';
// import type { Quiz } from '@/types/quiz'; // Non più usato direttamente per la lista
import type { QuizTemplate } from '@/types/quizTemplate';
import { UDAContentType } from '@/types/uda'; // Importa l'enum
import type { SelectedContentItem, RawSelectedContentItem } from '@/types/uda';

const emit = defineEmits(['close', 'select']);

const activeTab = ref<'lessons' | 'quizzes'>('lessons');
const loading = ref(false);
const lessons = ref<Lesson[]>([]);
const quizTemplates = ref<QuizTemplate[]>([]); // Modificato da quizzes a quizTemplates
const selectedItems = ref<RawSelectedContentItem[]>([]); // Tipo per la selezione grezza
const errorLoadingContent = ref<string | null>(null);
const isConfirming = ref(false);

const lessonStore = useLessonStore();
const quizStore = useQuizStore();
const uiStore = useUiStore();

const loadLessons = async () => {
  await lessonStore.fetchLessons();
  lessons.value = lessonStore.lessons;
};

const loadQuizTemplates = async () => {
  await quizStore.fetchQuizTemplates();
  quizTemplates.value = quizStore.quizTemplates;
  console.log('[SelectExistingContentModal] Loaded quizTemplates:', JSON.parse(JSON.stringify(quizTemplates.value)));
};

onMounted(async () => {
  loading.value = true;
  errorLoadingContent.value = null;
  try {
    // Carica inizialmente le lezioni (o il tab attivo)
    if (activeTab.value === 'lessons') {
      await loadLessons();
    } else {
      await loadQuizTemplates();
    }
  } catch (error) {
    const errorMessage = (error instanceof Error) ? error.message : "Errore sconosciuto nel caricamento dei contenuti.";
    console.error("Errore nel caricamento dei contenuti esistenti:", error);
    errorLoadingContent.value = `Impossibile caricare i contenuti: ${errorMessage}`;
    uiStore.addNotification({ message: errorLoadingContent.value, type: 'error' });
  } finally {
    loading.value = false;
  }
});

watch(activeTab, async (newTab, oldTab) => {
  if (newTab === oldTab) return;
  loading.value = true;
  errorLoadingContent.value = null;
  selectedItems.value = []; // Resetta la selezione quando si cambia tab
  try {
    if (newTab === 'lessons') {
      if (!lessons.value.length) { // Carica solo se non già caricato
        await loadLessons();
      }
    } else if (newTab === 'quizzes') {
      if (!quizTemplates.value.length) { // Carica solo se non già caricato
        await loadQuizTemplates();
      }
    }
  } catch (error) {
    const errorMessage = (error instanceof Error) ? error.message : `Errore caricando ${newTab}.`;
    console.error(`Errore caricando ${newTab}:`, error);
    errorLoadingContent.value = `Impossibile caricare ${newTab}: ${errorMessage}`;
    uiStore.addNotification({ message: errorLoadingContent.value, type: 'error' });
  } finally {
    loading.value = false;
  }
});

const closeModal = () => {
  if (isConfirming.value) return;
  emit('close');
};

const confirmSelection = async () => {
  if (isConfirming.value || selectedItems.value.length === 0) return;

  console.log('[SelectExistingContentModal] Confirming selection. Selected items:', JSON.parse(JSON.stringify(selectedItems.value)));
  isConfirming.value = true;
  const finalSelectedItems: SelectedContentItem[] = [];
  let hasError = false;

  for (const item of selectedItems.value) {
    if (item.type === 'QUIZ_TEMPLATE') {
      try {
        // Non creiamo più il quiz qui. Passiamo il riferimento al template.
        // Sarà compito del componente ricevente (es. UdaContentEditor tramite udaStore)
        // gestire l'eventuale creazione dell'istanza Quiz se necessario prima del salvataggio dell'UDA.
        finalSelectedItems.push({
          type: UDAContentType.QUIZ_TEMPLATE, // Modificato per usare il tipo corretto
          id: item.id, // id qui è l'ID del QuizTemplate
          title: item.title || `Quiz da template ${item.id}`,
        });
      } catch (error) { // Questo blocco catch potrebbe non essere più necessario se non ci sono operazioni asincrone rischiose qui
        hasError = true; // Manteniamo hasError nel caso in cui altre operazioni nel loop falliscano
        const errorMessage = (error instanceof Error) ? error.message : `Errore processando il template quiz ${item.title || item.id}.`;
        console.error(errorMessage, error);
        uiStore.addNotification({ message: `Errore: ${errorMessage}`, type: 'error' });
      }
    } else if (item.type === UDAContentType.LESSON) { // Usa l'enum anche qui per coerenza
      finalSelectedItems.push(item as SelectedContentItem);
    }
  }

  isConfirming.value = false;

  if (finalSelectedItems.length > 0) {
     emit('select', finalSelectedItems);
  }
  
  if (!hasError || finalSelectedItems.length > 0) { // Chiudi se non ci sono stati errori o se almeno un item è stato processato
    closeModal();
  }
};

</script>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.6); display: flex;
  justify-content: center; align-items: center; z-index: 1000;
}
.select-existing-content-modal-content { /* Classe specifica per evitare conflitti */
  background-color: white; padding: 1.5rem; border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  min-width: 500px; max-width: 800px; /* Adattato per contenuto più ampio */
  display: flex; flex-direction: column;
  max-height: 90vh; /* Limita altezza massima */
}

.modal-header-custom {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 1rem; border-bottom: 1px solid #eee; margin-bottom: 1rem;
}
.modal-title-custom {
  font-size: 1.25rem; font-weight: 600; margin: 0;
}
.button-close-custom {
  background: none; border: none; font-size: 1.5rem; cursor: pointer;
  padding: 0.5rem; line-height: 1;
}

.modal-body-custom {
  overflow-y: auto; /* Abilita scroll per il corpo se necessario */
  padding-right: 0.5rem; /* Spazio per la scrollbar se appare */
  flex-grow: 1;
}

.content-selection-list {
  max-height: 40vh; /* Limita altezza delle liste */
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem;
}

.list-group-item {
  padding: 0.5rem 0.75rem;
}
.list-group-item:hover {
  background-color: #f8f9fa;
}
.form-check-input {
  margin-top: 0.1em; /* Allineamento verticale migliore */
}

.modal-footer-custom {
  display: flex; justify-content: flex-end;
  padding-top: 1rem; border-top: 1px solid #eee; margin-top: 1rem;
}
.modal-footer-custom button {
  padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer;
  font-size: 0.9rem; margin-left: 0.5rem; border: none;
}
.button-cancel { background-color: #6c757d; color: white; }
.button-cancel:hover { background-color: #5a6268; }
.button-save { background-color: #007bff; color: white; }
.button-save:hover:not(:disabled) { background-color: #0056b3; }
.button-save:disabled { background-color: #ccc; cursor: not-allowed; }

/* Stili per nav-tabs (Bootstrap-like ma custom) */
.nav-tabs {
  display: flex;
  flex-wrap: wrap;
  padding-left: 0;
  margin-bottom: 1rem;
  list-style: none;
  border-bottom: 1px solid #dee2e6;
}
.nav-item {
  margin-bottom: -1px; /* Per allineare con il border-bottom */
}
.nav-link {
  display: block;
  padding: 0.5rem 1rem;
  color: #007bff;
  text-decoration: none;
  background: 0 0;
  border: 1px solid transparent;
  border-top-left-radius: .25rem;
  border-top-right-radius: .25rem;
}
.nav-link:hover, .nav-link:focus {
  border-color: #e9ecef #e9ecef #dee2e6;
  isolation: isolate;
}
.nav-link.active {
  color: #495057;
  background-color: #fff;
  border-color: #dee2e6 #dee2e6 #fff;
}
.alert { /* Stili base per alert */
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
  border-radius: .25rem;
}
.alert-danger {
  color: #721c24;
  background-color: #f8d7da;
  border-color: #f5c6cb;
}
.alert-info {
  color: #0c5460;
  background-color: #d1ecf1;
  border-color: #bee5eb;
}
.text-center { text-align: center; }
.visually-hidden {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0,0,0,0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}
.spinner-border { /* Stile base per spinner */
    display: inline-block;
    width: 2rem;
    height: 2rem;
    vertical-align: text-bottom;
    border: .25em solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    -webkit-animation: spinner-border .75s linear infinite;
    animation: spinner-border .75s linear infinite;
}
@keyframes spinner-border {
  to { transform: rotate(360deg); }
}
</style>