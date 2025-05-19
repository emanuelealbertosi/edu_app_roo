<template>
  <div class="collapsible-editable-section" :class="props.borderStyleClass">
    <div class="section-header" @click="toggleExpand">
      <h3>{{ title }}</h3>
    </div>
    <div v-if="isExpanded" class="section-content" :class="{'with-border-top': props.borderStyleClass === 'default-border-style'}">
      <div v-if="!isEditing" @click="startEditing" class="editable-content-area">
        <div v-if="currentHtml" v-html="currentHtml" class="content-display"></div>
        <div v-else class="content-placeholder">Nessun contenuto. Clicca qui per aggiungerne.</div>
        <!-- L'icona PencilIcon per avviare la modifica è stata rimossa, ora si clicca direttamente sul testo -->
      </div>
      <div v-else class="editor-container">
        <WysiwygEditor
          v-model="editableHtml"
          :editable="true"
        />
        <div class="editor-actions">
          <button @click="saveChanges" :disabled="isLoading" class="action-icon-button" title="Salva modifiche">
            <CheckIcon class="h-5 w-5" />
          </button>
          <button @click="cancelEditing" :disabled="isLoading" class="action-icon-button" title="Annulla modifiche">
            <XMarkIcon class="h-5 w-5" />
          </button>
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { PencilIcon, CheckIcon, XMarkIcon } from '@heroicons/vue/24/outline';
import WysiwygEditor from '@/components/WysiwygEditor.vue'; // Importato l'editor effettivo

interface Props {
  title: string;
  initialContentHtml?: string | null;
  isInitiallyExpanded?: boolean;
  borderStyleClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  initialContentHtml: '',
  isInitiallyExpanded: false,
  borderStyleClass: 'default-border-style', // Classe di fallback se non specificata
});

const emit = defineEmits<{
  (e: 'save', newHtml: string): Promise<void>;
}>();

const isExpanded = ref(props.isInitiallyExpanded);
const isEditing = ref(false);
const currentHtml = ref(props.initialContentHtml || '');
const editableHtml = ref(''); // Contenuto specifico per l'editor
const isLoading = ref(false);
const error = ref<string | null>(null);

// Sincronizza currentHtml quando initialContentHtml cambia dall'esterno
// (utile se il componente genitore ricarica i dati)
watch(() => props.initialContentHtml, (newValue) => {
  if (!isEditing.value) { // Aggiorna solo se non si sta modificando attivamente
    currentHtml.value = newValue || '';
  }
});

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value;
  // Se si collassa mentre si sta modificando, annulla le modifiche
  if (!isExpanded.value && isEditing.value) {
    cancelEditing();
  }
};

const startEditing = () => {
  editableHtml.value = currentHtml.value; // Inizializza l'editor con il contenuto corrente
  isEditing.value = true;
  error.value = null; // Resetta errori precedenti
};

const saveChanges = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    await emit('save', editableHtml.value);
    currentHtml.value = editableHtml.value; // Aggiorna il contenuto visualizzato
    isEditing.value = false;
  } catch (e) {
    console.error("Errore durante il salvataggio:", e);
    error.value = (e instanceof Error ? e.message : 'Errore sconosciuto durante il salvataggio.');
  } finally {
    isLoading.value = false;
  }
};

const cancelEditing = () => {
  // Non è necessario ripristinare editableHtml perché startEditing lo reinizializza
  isEditing.value = false;
  error.value = null;
};

onMounted(() => {
  // Potrebbe essere utile inizializzare qui se props.initialContentHtml non è reattivo come desiderato
  // currentHtml.value = props.initialContentHtml || '';
});

</script>

<style scoped>
.collapsible-editable-section {
  /* Il bordo è ora controllato da borderStyleClass */
  margin-bottom: 1rem;
  border-radius: 4px;
  /* Per permettere ai figli di occupare larghezza flessibile in un contenitore flex/grid */
  flex-grow: 1;
  flex-basis: 300px; /* Base minima, si espanderà */
  min-width: 280px; /* Per evitare che diventi troppo stretto */
}

.section-header {
  background-color: #f5f5f5;
  padding: 0.75rem; /* Ridotto padding laterale se il testo è centrato */
  cursor: pointer;
  display: flex;
  justify-content: center; /* Centra il titolo */
  align-items: center;
  /* border-bottom è rimosso, gestito dal bordo del wrapper o da classi specifiche */
}

.section-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.section-content {
  padding: 1rem;
  /* border-top è rimosso, gestito dal bordo del wrapper o da classi specifiche */
}

.section-content.with-border-top {
  border-top: 1px solid #ccc; /* Bordo superiore solo per lo stile di default, se necessario */
}

.editable-content-area {
  cursor: pointer;
  min-height: 50px; /* Assicura che ci sia un'area cliccabile anche se vuota */
}

.content-display {
  /* margin-bottom: 0.75rem; Rimosso per non avere doppio spazio se l'icona edit era sotto */
  /* Stili per il contenuto HTML renderizzato (es. da un editor WYSIWYG) */
  /* Potrebbe essere necessario aggiungere stili più specifici per p, ul, li, ecc. */
  line-height: 1.6;
}
.content-display :deep(p:first-child) {
    margin-top: 0;
}
.content-display :deep(p:last-child) {
    margin-bottom: 0;
}

.content-display :deep(ul) {
  list-style-type: disc;
  padding-inline-start: 2em; /* o 40px */
  margin-block-start: 1em;
  margin-block-end: 1em;
}

.content-display :deep(ol) {
  list-style-type: decimal;
  padding-inline-start: 2em; /* o 40px */
  margin-block-start: 1em;
  margin-block-end: 1em;
}

.content-display :deep(li) {
  display: list-item;
}


.content-placeholder {
  color: #777;
  font-style: italic;
  margin-bottom: 0.75rem;
}

.edit-icon-button {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  margin-top: 0.5rem; /* Aggiunge un po' di spazio sopra l'icona */
  display: inline-block; /* Per allineare correttamente con il testo se necessario */
}

.edit-icon-button:hover .h-5.w-5 {
  /* color: #4f46e5; /* Esempio di colore hover (indigo-600) */
}


.editor-container {
  /* Stili per il contenitore dell'editor */
}

.editor-actions {
  margin-top: 0.75rem;
  display: flex;
  gap: 0.5rem;
}

.editor-actions button.action-icon-button {
  background-color: #f0f0f0; /* Sfondo leggero per i pulsanti icona */
  border: 1px solid #ccc;
  border-radius: 50%; /* Cerchio */
  padding: 0.5rem; /* Spaziatura interna per l'icona */
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.editor-actions button.action-icon-button:hover:not([disabled]) {
  background-color: #e0e0e0;
}

.editor-actions button.action-icon-button .h-5.w-5 {
  color: #333; /* Colore icona */
}

.editor-actions button.action-icon-button:first-of-type .h-5.w-5 { /* Salva - CheckIcon */
  color: #28a745; /* Verde */
}
.editor-actions button.action-icon-button:first-of-type:hover:not([disabled]) .h-5.w-5 {
  color: #218838;
}

.editor-actions button.action-icon-button:last-of-type .h-5.w-5 { /* Annulla - XMarkIcon */
  color: #dc3545; /* Rosso */
}
.editor-actions button.action-icon-button:last-of-type:hover:not([disabled]) .h-5.w-5 {
  color: #c82333;
}


.editor-actions button[disabled] {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Rimosse le regole specifiche per :first-of-type e :last-of-type con background-color e color,
   ora gestite direttamente sopra per le icone. */

.error-message {
  color: red;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

/* Stile di fallback per l'intero wrapper se non viene passata una classe specifica */
.default-border-style {
  border: 1px solid #ccc;
}


</style>