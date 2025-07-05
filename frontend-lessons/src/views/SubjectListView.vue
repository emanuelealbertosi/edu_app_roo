<template>
  <div class="subject-list-container p-6">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex justify-between items-center">
      <h2 class="text-2xl font-semibold">Gestione Materie</h2>
      <!-- Pulsante stile adattato per contrasto -->
      <button @click="openAddModalDirectly" class="flex items-center px-3 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-100 transition duration-150 ease-in-out font-medium">
        <PlusCircleIcon class="h-5 w-5 sm:mr-2" />
        <span class="hidden sm:inline">Aggiungi Materia</span>
      </button>
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca materie per nome o descrizione..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      />
    </div>

    <div v-if="subjectStore.isLoading" class="text-center text-gray-500 py-10">
      Caricamento materie...
    </div>

    <div v-if="subjectStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore:</strong>
      <span class="block sm:inline"> {{ subjectStore.error }}</span>
    </div>

    <div v-if="!subjectStore.isLoading && filteredAndSortedSubjects.length > 0" class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('name')">
              Nome
              <span v-if="sortKey === 'name'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer transition-colors duration-200 hover:text-blue-600" @click="sortBy('description')">
              Descrizione
              <span v-if="sortKey === 'description'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="subject in filteredAndSortedSubjects" :key="subject.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <a href="#" @click.prevent="editSubject(subject as Subject)" class="text-indigo-600 hover:text-indigo-900 hover:underline" title="Modifica Materia">
                {{ subject.name }}
              </a>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ subject.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <button @click="editSubject(subject as Subject)" class="text-yellow-600 hover:text-yellow-900 transition duration-150 ease-in-out" title="Modifica Materia">
                <PencilIcon class="h-5 w-5 inline-block" />
              </button>
              <button @click="confirmDelete(subject as Subject)" class="text-red-600 hover:text-red-900 transition duration-150 ease-in-out" title="Elimina Materia">
                <TrashIcon class="h-5 w-5 inline-block" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!subjectStore.isLoading && filteredAndSortedSubjects.length === 0 && !subjectStore.error" class="text-center text-gray-500 py-10">
        <span v-if="searchQuery">Nessuna materia trovata per "{{ searchQuery }}".</span>
        <span v-else>Nessuna materia trovata. Inizia aggiungendone una!</span>
    </div>

    <!-- Modale gestito da showAddModal e subjectToEdit -->
    <SubjectEditModal
      v-if="showAddModal || subjectToEdit"
      :subject="subjectToEdit"
      @close="closeModal"
      @save="handleSave"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'; // Aggiunto onUnmounted
import { useSubjectStore } from '@/stores/subjects';
import emitter from '@/eventBus'; // Importa l'event bus
import SubjectEditModal from '../components/features/lezioni/SubjectEditModal.vue';
import type { Subject } from '@/types/lezioni';
import { PlusCircleIcon, PencilIcon, TrashIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';

const subjectStore = useSubjectStore();
const subjectToEdit = ref<Subject | null>(null);
const showAddModal = ref(false);
const searchQuery = ref('');
const sortKey = ref<'name' | 'description'>('name');
const sortOrder = ref('asc');

const filteredAndSortedSubjects = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  
  const filtered = query
    ? subjectStore.subjects.filter(subject =>
        (subject.name?.toLowerCase() || '').includes(query) ||
        (subject.description?.toLowerCase() || '').includes(query)
      )
    : subjectStore.subjects;

  return filtered.slice().sort((a, b) => {
    let valA = a[sortKey.value];
    let valB = b[sortKey.value];

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
  console.log("SubjectListView: Received open-add-subject-modal event.");
  subjectToEdit.value = null; // Assicura che non siamo in modalità modifica
  showAddModal.value = true;
};

// Funzione chiamata dal pulsante "Aggiungi Materia" locale
const openAddModalDirectly = () => {
    subjectToEdit.value = null;
    showAddModal.value = true;
}

onMounted(async () => {
  await subjectStore.fetchSubjects();
  // Registra il listener per l'evento
  emitter.on('open-add-subject-modal', handleOpenAddModalEvent);
});

onUnmounted(() => {
  // Rimuovi il listener quando il componente viene smontato
  emitter.off('open-add-subject-modal', handleOpenAddModalEvent);
});

const sortBy = (key: 'name' | 'description') => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

const editSubject = (subject: Subject) => {
  subjectToEdit.value = { ...subject };
  showAddModal.value = false; // Chiudi modale aggiunta se aperto
};

const confirmDelete = async (subject: Subject) => {
  if (confirm(`Sei sicuro di voler eliminare la materia "${subject.name}"? Questa azione potrebbe influire su argomenti e lezioni associate.`)) {
    await subjectStore.deleteSubject(subject.id);
    if (subjectStore.error) {
        alert(`Errore durante l'eliminazione: ${subjectStore.error}`);
        subjectStore.error = null;
    }
  }
};

const closeModal = () => {
  showAddModal.value = false;
  subjectToEdit.value = null;
};

const handleSave = async (subjectData: { id?: number; name: string; description?: string }) => {
    let success = false;
    if (subjectData.id) {
        success = await subjectStore.updateSubject(subjectData.id, subjectData);
    } else {
        const result = await subjectStore.addSubject({ name: subjectData.name, description: subjectData.description });
        success = !!result;
    }

    if (success) {
        closeModal();
    } else {
         alert(`Errore durante il salvataggio: ${subjectStore.error}`);
         subjectStore.error = null;
    }
};

</script>
