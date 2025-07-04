<template>
  <div class="p-4">
    <!-- Stile titolo aggiornato -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Gestione Gruppi Studenti</h1>
      <p class="opacity-90">Elenco dei gruppi di studenti creati e gestione delle relative richieste di accesso.</p>
    </div>

    <div class="mb-4 flex justify-end">
      <BaseButton @click="goToCreateGroup" variant="primary" class="flex items-center">
        <PlusCircleIcon class="h-5 w-5 mr-2" />
        Crea Nuovo Gruppo
      </BaseButton>
    </div>

    <!-- Filtro -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca per nome o descrizione..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-neutral-DEFAULT rounded-md shadow-sm placeholder-neutral-dark focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
      />
    </div>

    <!-- Loading Indicator -->
    <GlobalLoadingIndicator :is-loading="isLoadingList" />

    <!-- Error Message -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
      <span class="absolute top-0 bottom-0 right-0 px-4 py-3" @click="groupStore.clearError()">
        <svg class="fill-current h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><title>Close</title><path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/></svg>
      </span>
    </div>

    <!-- Groups Table -->
    <div v-if="!isLoadingList && filteredAndSortedGroups.length > 0" class="overflow-x-auto bg-white shadow-md rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('name')">
              Nome Gruppo
              <span v-if="sortKey === 'name'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('description')">
              Descrizione
              <span v-if="sortKey === 'description'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('student_count')">
              Studenti
              <span v-if="sortKey === 'student_count'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('pending_requests_count')">
              Richieste
              <span v-if="sortKey === 'pending_requests_count'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
             <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('created_at')">
              Creato il
              <span v-if="sortKey === 'created_at'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Azioni
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="group in filteredAndSortedGroups" :key="group.id">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
              {{ group.name }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 truncate max-w-xs">
              {{ group.description || '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">
              {{ group.student_count ?? 'N/A' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
               <span v-if="group.pending_requests_count && group.pending_requests_count > 0" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800" title="Richieste di accesso pendenti">
                 {{ group.pending_requests_count }}
               </span>
               <span v-else class="text-gray-400">-</span>
             </td>
             <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDate(group.created_at) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <BaseButton @click="goToGroupDetail(group.id)" variant="info" size="sm" class="mr-2 p-2" title="Dettagli Gruppo">
                <EyeIcon class="h-5 w-5" />
              </BaseButton>
              <BaseButton @click="handleDeleteGroup(group.id)" variant="danger" size="sm" class="p-2" title="Elimina Gruppo">
                <TrashIcon class="h-5 w-5" />
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Groups Message -->
    <div v-if="!isLoadingList && filteredAndSortedGroups.length === 0 && !error" class="text-center text-gray-500 mt-6">
      <span v-if="searchQuery">Nessun gruppo trovato per "{{ searchQuery }}".</span>
      <span v-else>Nessun gruppo trovato. Creane uno nuovo!</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useGroupStore } from '@/stores/groups';
import BaseButton from '@/components/common/BaseButton.vue';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import { PlusCircleIcon, EyeIcon, TrashIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';

const router = useRouter();
const groupStore = useGroupStore();

// Use storeToRefs to keep reactivity
const { groups, isLoadingList, error } = storeToRefs(groupStore);

const searchQuery = ref('');
const sortKey = ref('created_at');
const sortOrder = ref('desc');

const filteredAndSortedGroups = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  const filtered = query
    ? groups.value.filter(g => {
        const name = g.name.toLowerCase();
        const description = g.description?.toLowerCase() || '';
        return name.includes(query) || description.includes(query);
      })
    : groups.value;

  return filtered.slice().sort((a, b) => {
    let valA: any = a[sortKey.value as keyof typeof a] ?? 0;
    let valB: any = b[sortKey.value as keyof typeof b] ?? 0;

    if (typeof valA === 'string' && typeof valB === 'string') {
      valA = valA.toLowerCase();
      valB = valB.toLowerCase();
    }
    
    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

// Fetch groups when the component is mounted
onMounted(() => {
  groupStore.fetchGroups();
});

// --- Methods ---

const goToCreateGroup = () => {
  router.push({ name: 'GroupCreate' });
};

const goToGroupDetail = (groupId: number) => {
  router.push({ name: 'GroupDetail', params: { id: groupId } });
};

const goToEditGroup = (groupId: number) => {
  router.push({ name: 'GroupEdit', params: { id: groupId } });
};

const handleDeleteGroup = async (groupId: number) => {
  // Simple confirmation dialog (consider a custom modal component for better UX)
  if (window.confirm(`Sei sicuro di voler eliminare il gruppo ID ${groupId}? Questa azione non può essere annullata.`)) {
    await groupStore.deleteGroup(groupId);
    // Optionally show a success notification
  }
};

const formatDate = (dateString: string) => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      year: 'numeric', month: 'short', day: 'numeric'
    });
  } catch (e) {
    console.error("Error formatting date:", e);
    return dateString;
  }
};

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

</script>

<style scoped>
/* Add any component-specific styles here if needed */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.max-w-xs {
  max-width: 20rem; /* Adjust as needed */
}
</style>