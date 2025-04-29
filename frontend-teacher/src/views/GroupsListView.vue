<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-4">Gestione Gruppi Studenti</h1>

    <div class="mb-4 flex justify-end">
      <BaseButton @click="goToCreateGroup" variant="primary">
        Crea Nuovo Gruppo
      </BaseButton>
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
    <div v-if="!isLoadingList && groups.length > 0" class="overflow-x-auto bg-white shadow-md rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Nome Gruppo
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Descrizione
            </th>
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              Studenti
            </th>
            <!-- Nuova Intestazione Colonna -->
            <th scope="col" class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              Richieste
            </th>
             <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Creato il
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Azioni
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="group in groups" :key="group.id">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
              {{ group.name }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 truncate max-w-xs">
              {{ group.description || '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">
              {{ group.student_count ?? 'N/A' }}
            </td>
            <!-- Nuova Cella Dati -->
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
              <BaseButton @click="goToGroupDetail(group.id)" variant="secondary" size="sm" class="mr-2">
                Dettagli
              </BaseButton>
              <BaseButton @click="handleDeleteGroup(group.id)" variant="danger" size="sm">
                Elimina
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Groups Message -->
    <div v-if="!isLoadingList && groups.length === 0 && !error" class="text-center text-gray-500 mt-6">
      Nessun gruppo trovato. Creane uno nuovo!
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useGroupStore } from '@/stores/groups';
import BaseButton from '@/components/common/BaseButton.vue';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';

const router = useRouter();
const groupStore = useGroupStore();

// Use storeToRefs to keep reactivity
const { groups, isLoadingList, error } = storeToRefs(groupStore);

// Fetch groups when the component is mounted
onMounted(() => {
  groupStore.fetchGroups();
});

// --- Methods ---

const goToCreateGroup = () => {
  // TODO: Define the route '/groups/create' later
  router.push({ name: 'GroupCreate' }); // Assuming named route
};

const goToGroupDetail = (groupId: number) => {
  // TODO: Define the route '/groups/:id' later
  router.push({ name: 'GroupDetail', params: { id: groupId } }); // Assuming named route
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
    return dateString; // Fallback to original string
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