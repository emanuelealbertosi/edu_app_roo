<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <!-- Intestazione Modale con sfondo blu -->
      <div class="bg-blue-600 text-white p-4 rounded-t-md -m-8 mb-6">
        <h3 class="text-xl font-semibold text-center">{{ isEditing ? 'Modifica Lezione' : 'Crea Nuova Lezione' }}</h3>
      </div>
      <form @submit.prevent="submitForm">

        <div class="form-group">
          <label for="lesson-title">Titolo Lezione:</label>
          <input
            id="lesson-title"
            v-model="editableLesson.title"
            type="text"
            required
            placeholder="Titolo della lezione"
          />
        </div>

         <div class="form-group">
          <label for="lesson-topic">Argomento:</label>
          <select
            id="lesson-topic"
            v-model="editableLesson.topic"
            required >
             <option disabled value="">Seleziona un argomento</option>
             <optgroup v-for="group in groupedTopics" :key="group.subjectName" :label="group.subjectName">
                 <option v-for="topic in group.topics" :key="topic.id" :value="topic.id">
                    {{ topic.name }}
                 </option>
             </optgroup>
          </select>
        </div>

        <div class="form-group">
          <label for="lesson-description">Descrizione (opzionale):</label>
          <textarea
            id="lesson-description"
            v-model="editableLesson.description"
            rows="4"
            placeholder="Descrizione o introduzione alla lezione"
          ></textarea>
        </div>

        <div class="form-group">
          <label for="lesson-estimated-hours">Ore Stimate (opzionale):</label>
          <input
            id="lesson-estimated-hours"
            v-model.number="editableLesson.estimated_hours"
            type="number"
            step="0.1"
            min="0"
            placeholder="Es. 2.5"
          />
        </div>

         <div class="form-group form-group-checkbox">
          <input
            id="lesson-published"
            v-model="editableLesson.is_published"
            type="checkbox"
          />
          <label for="lesson-published">Pubblicata (visibile agli studenti assegnati)</label>
        </div>

        <div v-if="formError" class="error-message">{{ formError }}</div>

        <div class="modal-actions">
          <button type="button" @click="close" class="button-cancel">Annulla</button>
          <button type="submit" class="button-save" :disabled="isSaving || !editableLesson.topic">
            {{ isSaving ? 'Salvataggio...' : 'Salva Lezione' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, PropType } from 'vue';
import { useSubjectStore } from '@/stores/subjectStore';
import { useTopicStore } from '@/stores/topicStore';
import { useLessonStore } from '@/stores/lessons';
import type { Topic, Lesson } from '@/types/lezioni';


const props = defineProps({
  lesson: {
    type: Object as PropType<Lesson | null>,
    default: null
  },
  topics: {
    type: Array as PropType<Topic[]>,
    required: true
  },
  isSaving: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', lessonData: { id?: number; title: string; topic: number; description?: string; is_published?: boolean; estimated_hours?: number | null }): void;
}>();

const editableLesson = ref({
    id: undefined as number | undefined,
    title: '',
    description: '',
    topic: '' as number | '',
    is_published: false,
    estimated_hours: undefined as number | undefined | null, // Aggiunto
});
const formError = ref<string | null>(null);
const subjectStore = useSubjectStore();
const topicStore = useTopicStore();
const lessonStore = useLessonStore();

const isEditing = computed(() => !!(props.lesson && props.lesson.id));

watch(() => props.lesson, (newLesson) => {
  if (newLesson) {
    // Modal in modalità "Modifica"
    editableLesson.value = {
      id: newLesson.id,
      title: newLesson.title,
      description: newLesson.description || '',
      topic: newLesson.topic || '',
      is_published: newLesson.is_published,
      estimated_hours: newLesson.estimated_hours
    };
  } else {
    // Modal in modalità "Crea"
    editableLesson.value = {
      id: undefined,
      title: '',
      description: '',
      topic: '',
      is_published: false,
      estimated_hours: undefined
    };
  }
}, { immediate: true });


onMounted(async () => {
  // Le materie sono necessarie per raggruppare gli argomenti nel menu a discesa.
  if (subjectStore.subjects.length === 0) {
    await subjectStore.fetchSubjects();
  }
});

const groupedTopics = computed(() => {
    if (!props.topics || props.topics.length === 0) {
        return [];
    }
    const groups: { [key: string]: { subjectName: string; topics: Topic[] } } = {};
    
    props.topics.forEach(topic => {
        const subject = subjectStore.subjects.find(s => s.id === topic.subject);
        const subjectName = subject ? subject.name : 'Senza Materia';
        if (!groups[subjectName]) {
            groups[subjectName] = { subjectName: subjectName, topics: [] };
        }
        groups[subjectName].topics.push(topic);
    });
    return Object.values(groups).sort((a, b) => a.subjectName.localeCompare(b.subjectName))
           .map(group => {
               group.topics.sort((a, b) => a.name.localeCompare(b.name));
               return group;
           });
});


const close = () => {
  emit('close');
};

const submitForm = () => {
  formError.value = null;
   if (!editableLesson.value.topic) {
      formError.value = "Seleziona un argomento.";
      return;
  }
  if (!editableLesson.value.title.trim()) {
    formError.value = "Il titolo della lezione è obbligatorio.";
    return;
  }

  const dataToSave: { id?: number; title: string; topic: number; description?: string; is_published?: boolean; estimated_hours?: number | null } = {
      title: editableLesson.value.title,
      topic: editableLesson.value.topic as number,
      description: editableLesson.value.description || undefined,
      is_published: editableLesson.value.is_published,
      estimated_hours: (typeof editableLesson.value.estimated_hours === 'number' && editableLesson.value.estimated_hours > 0)
                         ? editableLesson.value.estimated_hours
                         : null, // Invia null se non specificato o zero
  };
  if (isEditing.value && editableLesson.value.id) {
      dataToSave.id = editableLesson.value.id;
  }

  emit('save', dataToSave);
};

</script>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.6); display: flex;
  justify-content: center; align-items: center; z-index: 1000;
}
.modal-content {
  background-color: white; padding: 2rem; border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3); min-width: 400px; max-width: 600px;
}
h3 { margin-top: 0; margin-bottom: 1.5rem; text-align: center; }
.form-group { margin-bottom: 1rem; }
label { display: block; margin-bottom: 0.5rem; }
input[type="text"], textarea, select {
  width: 100%; padding: 0.75rem; border: 1px solid #ccc;
  border-radius: 4px; box-sizing: border-box;
}
textarea { resize: vertical; }
.form-group-checkbox { display: flex; align-items: center; }
.form-group-checkbox input[type="checkbox"] { width: auto; margin-right: 0.5rem; }
.form-group-checkbox label { margin-bottom: 0; }
.modal-actions { display: flex; justify-content: flex-end; margin-top: 1.5rem; }
.modal-actions button {
  padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer;
  font-size: 0.9rem; margin-left: 0.5rem; border: none;
}
.button-cancel { background-color: #6c757d; color: white; }
.button-cancel:hover { background-color: #5a6268; }
.button-save { background-color: #007bff; color: white; }
.button-save:hover:not(:disabled) { background-color: #0056b3; }
.button-save:disabled { background-color: #ccc; cursor: not-allowed; }
.error-message { color: red; margin-top: 0.5rem; font-size: 0.9rem; }
</style>