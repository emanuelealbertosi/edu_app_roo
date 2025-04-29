<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-4">Sfoglia Gruppi Pubblici</h1>

    <!-- Search Input -->
    <div class="mb-4">
      <label for="search-term" class="block text-sm font-medium text-gray-700">Cerca per nome o descrizione</label>
      <div class="mt-1 flex rounded-md shadow-sm">
        <input
          type="text"
          name="search-term"
          id="search-term"
          class="focus:ring-indigo-500 focus:border-indigo-500 flex-1 block w-full rounded-none rounded-l-md sm:text-sm border-gray-300 px-3 py-2"
          placeholder="Es. Fisica Avanzata"
          v-model="searchTerm"
          @keyup.enter="performSearch"
        />
        <button
          type="button"
          @click="performSearch"
          :disabled="isLoadingSearch"
          class="-ml-px relative inline-flex items-center space-x-2 px-4 py-2 border border-gray-300 text-sm font-medium rounded-r-md text-gray-700 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
          </svg>
          <span>Cerca</span>
        </button>
      </div>
    </div>

    <!-- Loading Indicator -->
    <div v-if="isLoadingSearch" class="text-center py-4">
      <p>Ricerca in corso...</p>
      <!-- Add a spinner or animation here -->
    </div>

    <!-- Search Error Message -->
    <div v-if="searchError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ searchError }}</span>
    </div>

     <!-- Request Access Success/Error Message -->
    <div v-if="requestAccessSuccess" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
      Richiesta di accesso inviata con successo!
       <span class="absolute top-0 bottom-0 right-0 px-4 py-3" @click="groupStore.requestAccessSuccess = false">
         <svg class="fill-current h-6 w-6 text-green-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><title>Close</title><path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/></svg>
       </span>
    </div>
     <div v-if="requestAccessError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      <strong class="font-bold">Errore Richiesta!</strong>
      <span class="block sm:inline"> {{ requestAccessError }}</span>
       <span class="absolute top-0 bottom-0 right-0 px-4 py-3" @click="groupStore.requestAccessError = null">
         <svg class="fill-current h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><title>Close</title><path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/></svg>
       </span>
    </div>

    <!-- Search Results -->
    <div v-if="!isLoadingSearch && searchPerformed && searchResults.length === 0" class="text-center text-gray-500 py-4">
      Nessun gruppo pubblico trovato per "{{ previousSearchTerm }}".
    </div>

    <div v-if="searchResults.length > 0" class="mt-6">
      <h2 class="text-xl font-semibold mb-3">Risultati Ricerca</h2>
      <ul class="divide-y divide-gray-200">
        <li v-for="group in searchResults" :key="group.id" class="py-4 flex justify-between items-center">
          <div>
            <p class="text-lg font-medium text-indigo-600">{{ group.name }}</p>
            <p class="text-sm text-gray-600">{{ group.description || 'Nessuna descrizione' }}</p>
            <p class="text-xs text-gray-500 mt-1">Proprietario: {{ group.owner_name || 'N/D' }}</p> <!-- Assumendo che l'API restituisca owner_name -->
          </div>
          <BaseButton
            @click="requestAccess(group.id)"
            :is-loading="isLoadingDetail && requestingGroupId === group.id"
            :disabled="isLoadingDetail && requestingGroupId === group.id"
            variant="secondary"
            size="sm"
          >
            Richiedi Accesso
          </BaseButton>
        </li>
      </ul>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'; // Importa onMounted
import { storeToRefs } from 'pinia';
import { useGroupStore } from '@/stores/groups';
import BaseButton from '@/components/common/BaseButton.vue';

const groupStore = useGroupStore();
const {
  publicGroupsSearchResult: searchResults,
  isLoadingSearch,
  isLoadingDetail, // Used for request access loading state
  searchError,
  requestAccessError,
  requestAccessSuccess
} = storeToRefs(groupStore);

const searchTerm = ref('');
const previousSearchTerm = ref(''); // To display the term for which no results were found
const searchPerformed = ref(false); // To track if a search has been performed
const requestingGroupId = ref<number | null>(null); // Track which group's access is being requested

const performSearch = () => {
  // Usa sempre il valore corrente di searchTerm.value
  const currentSearchTerm = searchTerm.value;
  searchPerformed.value = true;
  previousSearchTerm.value = currentSearchTerm; // Salva il termine usato
  // Clear previous request errors/success messages on new search
  groupStore.requestAccessError = null;
  groupStore.requestAccessSuccess = false;
  // Passa il termine corrente (può essere vuoto) allo store
  groupStore.searchPublicGroups(currentSearchTerm);
};

const requestAccess = async (groupId: number) => {
  requestingGroupId.value = groupId; // Set loading state for the specific button
  await groupStore.requestAccess(groupId);
  requestingGroupId.value = null; // Reset loading state after completion
  // Success/error messages are handled via store refs in the template
};

// Esegui una ricerca iniziale al caricamento del componente per mostrare tutti i gruppi
onMounted(() => {
  // searchTerm.value è inizialmente vuoto, quindi questo caricherà tutti i gruppi
  performSearch();
});

// Clear search results and errors when component is unmounted? Optional.
// import { onUnmounted } from 'vue';
// onUnmounted(() => {
//   groupStore.publicGroupsSearchResult = [];
//   groupStore.searchError = null;
//   groupStore.requestAccessError = null;
//   groupStore.requestAccessSuccess = false;
// });
</script>

<style scoped>
/* Add component-specific styles if needed */
</style>