<template>
  <div class="topic-list-container p-6">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
      <h2 class="text-2xl font-semibold text-gray-700">Gestione Argomenti</h2>
      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
         <div class="flex items-center gap-2">
            <label for="subject-filter" class="text-sm font-medium text-gray-600 whitespace-nowrap">Seleziona materia:</label>
            <select id="subject-filter" v-model="selectedSubjectId" @change="loadTopicsForSubject" class="block w-full sm:w-auto pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 rounded-md shadow-sm">
              <option :value="null">Tutte le Materie</option>
              <option v-for="subject in subjectStore.subjects" :key="subject.id" :value="subject.id">
                {{ subject.name }}
              </option>
            </select>
         </div>
         <button @click="openAddModalDirectly" class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-md shadow-sm transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap" :disabled="!selectedSubjectId">
           Aggiungi Argomento
         </button>
         <span v-if="!selectedSubjectId" class="text-xs text-gray-500 mt-1 sm:mt-0">(Seleziona una materia)</span>
      </div>
    </div>


    <div v-if="topicStore.isLoading" class="text-center text-gray-500 py-10">
      Caricamento argomenti...
    </div>

    <div v-if="topicStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore:</strong>
      <span class="block sm:inline"> {{ topicStore.error }}</span>
    </div>

    <div v-if="!topicStore.isLoading && topics.length > 0" class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome Argomento</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Materia</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="topic in topics" :key="topic.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ topic.name }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getSubjectName(topic.subject) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ topic.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <button @click="editTopic(topic as Topic)" class="text-yellow-600 hover:text-yellow-900">Modifica</button>
              <button @click="confirmDelete(topic as Topic)" class="text-red-600 hover:text-red-900">Elimina</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

     <div v-if="!topicStore.isLoading && topics.length === 0 && !topicStore.error" class="text-center text-gray-500 py-10">
       Nessun argomento trovato per la materia selezionata.
     </div>

     <TopicEditModal
      v-if="showAddModal || topicToEdit"
      :topic="topicToEdit"
      :subjects="subjectStore.subjects"
      :defaultSubjectId="selectedSubjectId"
      @close="closeModal"
      @save="handleSave"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'; // Aggiunto onUnmounted
import { useTopicStore } from '@/stores/topics';
import { useSubjectStore } from '@/stores/subjects';
import emitter from '@/eventBus'; // Importa l'event bus
import TopicEditModal from '../components/features/lezioni/TopicEditModal.vue';
import type { Topic, Subject } from '@/types/lezioni';

const topicStore = useTopicStore();
const subjectStore = useSubjectStore();

const topics = computed(() => topicStore.topics);
const selectedSubjectId = ref<number | null>(null);

const showAddModal = ref(false);
const topicToEdit = ref<Topic | null>(null);

// Funzione chiamata dall'event bus per aprire il modale
const handleOpenAddModalEvent = () => {
  console.log("TopicListView: Received open-add-topic-modal event.");
  // Apri solo se una materia è selezionata
  if (selectedSubjectId.value !== null) {
      topicToEdit.value = null; // Assicura che non siamo in modalità modifica
      showAddModal.value = true;
  } else {
      console.warn("TopicListView: Cannot open Add Topic modal via event - no subject selected.");
      alert("Seleziona prima una materia per poter aggiungere un argomento.");
  }
};

// Funzione chiamata dal pulsante "Aggiungi Argomento" locale
const openAddModalDirectly = () => {
    if (selectedSubjectId.value !== null) {
        topicToEdit.value = null;
        showAddModal.value = true;
    }
    // Non fare nulla se nessuna materia è selezionata (il pulsante è già disabilitato)
}

onMounted(async () => {
  await subjectStore.fetchSubjects();
  await topicStore.fetchTopics(); // Carica tutti inizialmente
  // Registra il listener per l'evento
  emitter.on('open-add-topic-modal', handleOpenAddModalEvent);
});

onUnmounted(() => {
  // Rimuovi il listener quando il componente viene smontato
  emitter.off('open-add-topic-modal', handleOpenAddModalEvent);
});

const loadTopicsForSubject = () => {
  topicStore.fetchTopics(selectedSubjectId.value);
};

const selectedSubjectName = computed(() => {
    if (!selectedSubjectId.value) return '';
    const subj = subjectStore.subjects.find(s => s.id === selectedSubjectId.value);
    return subj ? subj.name : '';
});

const getSubjectName = (subjectId: number): string => {
    const subj = subjectStore.subjects.find(s => s.id === subjectId);
    return subj ? subj.name : 'N/D';
};

const editTopic = (topic: Topic) => {
  topicToEdit.value = { ...topic };
  showAddModal.value = false; // Chiudi modale aggiunta se aperto
};

const confirmDelete = async (topic: Topic) => {
  if (confirm(`Sei sicuro di voler eliminare l'argomento "${topic.name}"? Questa azione potrebbe influire sulle lezioni associate.`)) {
    await topicStore.deleteTopic(topic.id);
    if (topicStore.error) {
        alert(`Errore durante l'eliminazione: ${topicStore.error}`);
        topicStore.error = null;
    }
    // Ricarica gli argomenti per la materia corrente dopo l'eliminazione
    await loadTopicsForSubject();
  }
};

const closeModal = () => {
  showAddModal.value = false;
  topicToEdit.value = null;
};

const handleSave = async (topicData: { id?: number; name: string; subject: number; description?: string }) => {
    let success = false;
    if (topicData.id) {
        success = await topicStore.updateTopic(topicData.id, topicData);
    } else {
        const result = await topicStore.addTopic(topicData);
        success = !!result;
    }

    if (success) {
        closeModal();
        await loadTopicsForSubject(); // Ricarica per vedere le modifiche
    } else {
         alert(`Errore durante il salvataggio: ${topicStore.error}`);
         topicStore.error = null;
    }
};

</script>
