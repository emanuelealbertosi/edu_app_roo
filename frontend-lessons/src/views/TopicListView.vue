<template>
  <div class="topic-list-container p-6">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <h2 class="text-2xl font-semibold">Gestione Argomenti</h2>
      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3 w-full sm:w-auto"> <!-- Aggiunto w-full per mobile -->
         <div class="flex items-center gap-2 w-full sm:w-auto"> <!-- Aggiunto w-full per mobile -->
            <label for="subject-filter" class="text-sm font-medium text-blue-100 whitespace-nowrap">Filtra per materia:</label> <!-- Colore label -->
            <!-- Stile select adattato -->
            <select id="subject-filter" v-model="selectedSubjectId" @change="loadTopicsForSubject" class="block w-full sm:w-auto pl-3 pr-10 py-2 text-base border-blue-400 bg-blue-500 text-white focus:outline-none focus:ring-white focus:border-white rounded-md shadow-sm">
              <option :value="null" class="bg-white text-black">Tutte le Materie</option>
              <option v-for="subject in subjectStore.subjects" :key="subject.id" :value="subject.id" class="bg-white text-black">
                {{ subject.name }}
              </option>
            </select>
         </div>
         <!-- Pulsante stile adattato per contrasto -->
         <button @click="openAddModalDirectly" class="flex items-center px-3 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-50 transition duration-150 ease-in-out font-medium disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap" :disabled="!selectedSubjectId">
           <PlusCircleIcon class="h-5 w-5 sm:mr-2" />
           <span class="hidden sm:inline">Aggiungi Argomento</span>
         </button>
         <span v-if="!selectedSubjectId" class="text-xs text-blue-200 mt-1 sm:mt-0">(Seleziona una materia)</span> <!-- Colore testo -->
      </div>
    </div>


    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca argomenti per nome o descrizione..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      />
    </div>

    <div v-if="topicStore.isLoading" class="text-center text-gray-500 py-10">
      Caricamento argomenti...
    </div>

    <div v-if="topicStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore:</strong>
      <span class="block sm:inline"> {{ topicStore.error }}</span>
    </div>

    <div v-if="!topicStore.isLoading && filteredAndSortedTopics.length > 0" class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('name')">
              Nome Argomento
              <span v-if="sortKey === 'name'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('subject')">
              Materia
              <span v-if="sortKey === 'subject'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('description')">
              Descrizione
              <span v-if="sortKey === 'description'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="topic in filteredAndSortedTopics" :key="topic.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <a href="#" @click.prevent="editTopic(topic as Topic)" class="text-indigo-600 hover:text-indigo-900 hover:underline" title="Modifica Argomento">
                {{ topic.name }}
              </a>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ getSubjectName(topic.subject) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ topic.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <button @click="editTopic(topic as Topic)" class="text-yellow-600 hover:text-yellow-900 transition duration-150 ease-in-out" title="Modifica Argomento">
                <PencilIcon class="h-5 w-5 inline-block" />
              </button>
              <button @click="confirmDelete(topic as Topic)" class="text-red-600 hover:text-red-900 transition duration-150 ease-in-out" title="Elimina Argomento">
                <TrashIcon class="h-5 w-5 inline-block" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

     <div v-if="!topicStore.isLoading && filteredAndSortedTopics.length === 0 && !topicStore.error" class="text-center text-gray-500 py-10">
        <span v-if="searchQuery || selectedSubjectId">Nessun argomento trovato per i filtri applicati.</span>
        <span v-else>Nessun argomento trovato.</span>
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
import type { Topic } from '@/types/lezioni'; // Rimosso Subject non usato qui
import { PlusCircleIcon, PencilIcon, TrashIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';

const topicStore = useTopicStore();
const subjectStore = useSubjectStore();

const selectedSubjectId = ref<number | null>(null);
const showAddModal = ref(false);
const topicToEdit = ref<Topic | null>(null);
const searchQuery = ref('');
const sortKey = ref('name');
const sortOrder = ref('asc');

const filteredAndSortedTopics = computed(() => {
  // 1. Filtro per materia
  const bySubject = selectedSubjectId.value
    ? topicStore.topics.filter(t => t.subject === selectedSubjectId.value)
    : topicStore.topics;

  // 2. Filtro per query di ricerca
  const query = searchQuery.value.toLowerCase().trim();
  const bySearch = query
    ? bySubject.filter(topic =>
        (topic.name?.toLowerCase() || '').includes(query) ||
        (topic.description?.toLowerCase() || '').includes(query)
      )
    : bySubject;

  // 3. Ordinamento
  return bySearch.slice().sort((a, b) => {
    let valA: any;
    let valB: any;

    if (sortKey.value === 'subject') {
      valA = getSubjectName(a.subject);
      valB = getSubjectName(b.subject);
    } else {
      valA = a[sortKey.value as keyof Topic];
      valB = b[sortKey.value as keyof Topic];
    }

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();
    if (valA === null || valA === undefined) valA = '';
    if (valB === null || valB === undefined) valB = '';

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

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
  // La logica è ora gestita dalla computed property, non è necessario ricaricare
};

const sortBy = (key: 'name' | 'subject' | 'description') => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

// Rimosso selectedSubjectName non utilizzato
// const selectedSubjectName = computed(() => {
//     if (!selectedSubjectId.value) return '';
//     const subj = subjectStore.subjects.find(s => s.id === selectedSubjectId.value);
//     return subj ? subj.name : '';
// });

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
    // Non è più necessario ricaricare qui, la computed property gestirà il filtro
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
        // Non è più necessario ricaricare, la computed property si aggiornerà
    } else {
         alert(`Errore durante il salvataggio: ${topicStore.error}`);
         topicStore.error = null;
    }
};

</script>
