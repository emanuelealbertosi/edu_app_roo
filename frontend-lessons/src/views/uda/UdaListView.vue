<template>
  <div class="uda-list-container p-6">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex justify-between items-center">
      <h2 class="text-2xl font-semibold">Le Mie UDA</h2>
      <RouterLink
        :to="{ name: 'uda-new' }"
        class="flex items-center px-3 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-100 transition duration-150 ease-in-out font-medium"
      >
        <PlusCircleIcon class="h-5 w-5 sm:mr-2" />
        <span class="hidden sm:inline">Crea Nuova UDA</span>
      </RouterLink>
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca UDA per titolo, descrizione, stato..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      />
    </div>

    <!-- Azioni di gruppo -->
    <div v-if="selectedUdas.size > 0" class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md flex items-center justify-between">
      <span class="text-sm font-medium text-blue-700">{{ selectedUdas.size }} {{ selectedUdas.size === 1 ? 'UDA selezionata' : 'UDA selezionate' }}</span>
      <div class="flex items-center space-x-2">
        <button
          @click="confirmRemoveSelectedFromGroup"
          class="px-4 py-2 bg-red-100 border border-red-300 text-red-700 rounded-md shadow-sm hover:bg-red-200 transition duration-150 ease-in-out font-medium"
          :disabled="!atLeastOneSelectedUdaInGroup"
          title="Rimuovi le UDA selezionate dai loro gruppi"
        >
          Rimuovi dal Gruppo
        </button>
        <button
          @click="openAssignToGroupModal"
          class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md shadow-sm hover:bg-gray-50 transition duration-150 ease-in-out font-medium"
          :disabled="udaStore.udaGroups.length === 0"
          title="Aggiungi le UDA selezionate a un gruppo esistente"
        >
          Aggiungi a Gruppo...
        </button>
        <button @click="openCreateGroupModal" class="px-4 py-2 bg-blue-600 text-white rounded-md shadow-sm hover:bg-blue-700 transition duration-150 ease-in-out font-medium">
          Crea Nuovo Gruppo...
        </button>
      </div>
    </div>

    <div v-if="udaStore.loading" class="text-center text-gray-500 py-10">
      Caricamento UDA...
    </div>

    <div v-if="udaStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore:</strong>
      <span class="block sm:inline"> {{ udaStore.error }}</span>
    </div>

    <!-- Tabella UDA con Gruppi -->
    <div v-if="!udaStore.loading && (groupedUdas.grouped.length > 0 || groupedUdas.ungrouped.length > 0)" class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="relative px-4 py-3">
              <input type="checkbox" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" @change="toggleSelectAll" :checked="areAllUdasSelected" :disabled="allVisibleUdaIds.length === 0" />
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('title')">Titolo</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('description')">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('status')">Stato</th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <!-- Itera sui gruppi -->
          <template v-for="item in groupedUdas.grouped" :key="item.group.id">
            <tr
              class="bg-blue-50 hover:bg-blue-100 cursor-pointer"
              @click="toggleGroup(item.group.id)"
              :class="{ 'group-header-expanded': expandedGroups.has(item.group.id) }"
            >
              <td colspan="5" class="px-6 py-3 text-sm font-semibold text-blue-800">
                <div class="flex items-center">
                  <FolderMinusIcon v-if="expandedGroups.has(item.group.id)" class="h-5 w-5 mr-2 text-blue-700" />
                  <FolderPlusIcon v-else class="h-5 w-5 mr-2 text-blue-600" />
                  <span>{{ item.group.name }} ({{ item.udas.length }})</span>
                  <div class="ml-auto flex items-center space-x-2">
                    <button @click.stop="handleRenameGroup(item.group)" class="text-gray-500 hover:text-blue-600"><PencilIcon class="h-4 w-4"/></button>
                    <button @click.stop="handleDeleteGroup(item.group)" class="text-gray-500 hover:text-red-600"><TrashIcon class="h-4 w-4"/></button>
                    <ChevronDownIcon v-if="expandedGroups.has(item.group.id)" class="h-5 w-5" />
                    <ChevronRightIcon v-else class="h-5 w-5" />
                  </div>
                </div>
              </td>
            </tr>
            <!-- Itera sulle UDA del gruppo se espanso -->
            <template v-if="expandedGroups.has(item.group.id)">
              <tr v-for="(uda, index) in item.udas" :key="uda.id"
                class="hover:bg-gray-50"
                :class="{
                  'bg-blue-50': selectedUdas.has(uda.id),
                  'uda-in-expanded-group': true,
                  'last-uda-in-group': index === item.udas.length - 1
                }">
                <td class="px-4 py-4 whitespace-nowrap">
                  <input type="checkbox" :checked="selectedUdas.has(uda.id)" @change="toggleUdaSelection(uda.id)" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                </td>
                <td class="pl-12 pr-6 py-4 whitespace-nowrap text-sm font-medium">
                  <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }" class="text-blue-600 hover:text-blue-800 hover:underline">
                    {{ uda.title }}
                  </RouterLink>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ uda.description }}</td>
                <td class="px-6 py-4 whitespace-nowrap"><span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full" :class="getStatusClass(uda.status)">{{ uda.status }}</span></td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }" class="text-blue-600 hover:text-blue-900"><EyeIcon class="h-5 w-5 inline-block"/></RouterLink>
                  <button @click="handleCopyUda(uda.id, uda.title)" class="text-green-600 hover:text-green-900"><DocumentDuplicateIcon class="h-5 w-5 inline-block"/></button>
                  <button @click="confirmDeleteSingleUda(uda.id, uda.title)" class="text-red-600 hover:text-red-900"><TrashIcon class="h-5 w-5 inline-block"/></button>
                  <button @click.stop="handleRemoveFromGroup(uda.id)" class="text-gray-500 hover:text-gray-700" title="Rimuovi dal gruppo"><XCircleIcon class="h-5 w-5" /></button>
                </td>
              </tr>
            </template>
          </template>
          <!-- UDA non raggruppate -->
          <tr v-for="uda in groupedUdas.ungrouped" :key="uda.id" class="hover:bg-gray-50" :class="{'bg-blue-50': selectedUdas.has(uda.id)}">
            <td class="px-4 py-4 whitespace-nowrap">
              <input type="checkbox" :checked="selectedUdas.has(uda.id)" @change="toggleUdaSelection(uda.id)" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500">
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }" class="text-gray-900 hover:text-blue-600 hover:underline">
                {{ uda.title }}
              </RouterLink>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ uda.description }}</td>
            <td class="px-6 py-4 whitespace-nowrap"><span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full" :class="getStatusClass(uda.status)">{{ uda.status }}</span></td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }" class="text-blue-600 hover:text-blue-900"><EyeIcon class="h-5 w-5 inline-block"/></RouterLink>
              <button @click="handleCopyUda(uda.id, uda.title)" class="text-green-600 hover:text-green-900"><DocumentDuplicateIcon class="h-5 w-5 inline-block"/></button>
              <button @click="confirmDeleteSingleUda(uda.id, uda.title)" class="text-red-600 hover:text-red-900"><TrashIcon class="h-5 w-5 inline-block"/></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!udaStore.loading && groupedUdas.grouped.length === 0 && groupedUdas.ungrouped.length === 0 && !udaStore.error" class="text-center text-gray-500 py-10">
      <span v-if="searchQuery">Nessuna UDA trovata per "{{ searchQuery }}".</span>
      <span v-else>Non hai ancora creato nessuna UDA.</span>
    </div>

    <UdaGroupModal
      :show="showGroupModal"
      @close="showGroupModal = false"
      @save="handleGroupSave"
    />

    <AssignToGroupModal
      :show="showAssignToGroupModal"
      :groups="udaStore.udaGroups"
      @close="showAssignToGroupModal = false"
      @assign="handleAssignToGroup"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import { useUdaStore } from '@/stores/udaStore';
import { useUiStore } from '@/stores/ui';
import type { UDA, UdaGroup } from '@/types/uda';
import UdaGroupModal from '@/components/features/uda/UdaGroupModal.vue';
import AssignToGroupModal from '@/components/features/uda/AssignToGroupModal.vue';
import {
  TrashIcon, EyeIcon, DocumentDuplicateIcon, PlusCircleIcon, ChevronUpIcon, ChevronDownIcon,
  FolderPlusIcon, FolderMinusIcon, PencilIcon, ChevronRightIcon, XCircleIcon
} from '@heroicons/vue/24/outline';

const udaStore = useUdaStore();
const uiStore = useUiStore();
const router = useRouter();

const searchQuery = ref('');
const sortKey = ref('title');
const sortOrder = ref('asc');
const selectedUdas = ref<Set<number>>(new Set());
const expandedGroups = ref<Set<number>>(new Set());
const showGroupModal = ref(false);
const showAssignToGroupModal = ref(false);

const filteredUdas = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  return udaStore.udas.filter(uda =>
    uda.title.toLowerCase().includes(query) ||
    (uda.description && uda.description.toLowerCase().includes(query))
  );
});

const groupedUdas = computed(() => {
  const grouped: { group: UdaGroup; udas: UDA[] }[] = [];
  const ungrouped: UDA[] = [];
  const groupMap = new Map<number, { group: UdaGroup; udas: UDA[] }>();

  udaStore.udaGroups.forEach(group => {
    groupMap.set(group.id, { group, udas: [] });
  });

  filteredUdas.value.forEach(uda => {
    if (uda.group && groupMap.has(uda.group.id)) {
      groupMap.get(uda.group.id)!.udas.push(uda);
    } else {
      ungrouped.push(uda);
    }
  });

  groupMap.forEach(value => {
    if (value.udas.length > 0 || !searchQuery.value) {
      grouped.push(value);
    }
  });
  
  grouped.sort((a, b) => a.group.name.localeCompare(b.group.name));

  return { grouped, ungrouped };
});

const allVisibleUdaIds = computed(() => filteredUdas.value.map(u => u.id));

const areAllUdasSelected = computed(() => {
  const visibleIds = new Set(allVisibleUdaIds.value);
  return visibleIds.size > 0 && [...visibleIds].every(id => selectedUdas.value.has(id));
});

const atLeastOneSelectedUdaInGroup = computed(() => {
  for (const udaId of selectedUdas.value) {
    const uda = udaStore.udas.find(u => u.id === udaId);
    if (uda && uda.group) {
      return true;
    }
  }
  return false;
});

const toggleUdaSelection = (udaId: number) => {
  if (selectedUdas.value.has(udaId)) {
    selectedUdas.value.delete(udaId);
  } else {
    selectedUdas.value.add(udaId);
  }
};

const toggleSelectAll = () => {
  const visibleIds = allVisibleUdaIds.value;
  if (areAllUdasSelected.value) {
    visibleIds.forEach(id => selectedUdas.value.delete(id));
  } else {
    visibleIds.forEach(id => selectedUdas.value.add(id));
  }
};

const toggleGroup = (groupId: number) => {
  if (expandedGroups.value.has(groupId)) {
    expandedGroups.value.delete(groupId);
  } else {
    expandedGroups.value.add(groupId);
  }
};

onMounted(() => {
  udaStore.fetchUdas();
  udaStore.fetchUdaGroups();
});

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

const confirmDeleteSingleUda = async (udaId: number, udaTitle: string) => {
  if (confirm(`Sei sicuro di voler eliminare l'UDA "${udaTitle}"?`)) {
    await udaStore.deleteUda(udaId);
  }
};

const handleCopyUda = async (udaId: number, udaTitle: string) => {
  if (confirm(`Sei sicuro di voler copiare l'UDA "${udaTitle}"?`)) {
    const newUda = await udaStore.copyUda(udaId);
    if (newUda) {
      router.push({ name: 'uda-edit', params: { id: newUda.id } });
    }
  }
};

const getStatusClass = (status?: UDA['status']) => {
  if (!status) return 'text-gray-600 bg-gray-100';
  if (status === 'COMPLETED') return 'text-green-700 bg-green-100';
  if (status === 'IN_PROGRESS') return 'text-blue-700 bg-blue-100';
  if (status === 'TODO') return 'text-yellow-700 bg-yellow-100';
  return 'text-gray-600 bg-gray-100';
};

const formatDate = (dateString?: string | null) => {
  if (!dateString) return 'N/D';
  return new Date(dateString).toLocaleDateString('it-IT', { year: 'numeric', month: 'short', day: 'numeric' });
};

const openCreateGroupModal = () => {
  showGroupModal.value = true;
};

const handleGroupSave = async (groupName: string) => {
  try {
    const group = await udaStore.createUdaGroup(groupName);
    if (group) {
      const udaIds = Array.from(selectedUdas.value);
      if (udaIds.length > 0) {
        await udaStore.assignUdasToGroup(udaIds, group.id);
        uiStore.addNotification({ message: `Gruppo "${groupName}" creato e ${udaIds.length} UDA assegnate.`, type: 'success' });
      } else {
        uiStore.addNotification({ message: `Gruppo "${groupName}" creato con successo.`, type: 'success' });
      }
      selectedUdas.value.clear();
      // Lo store si occupa dell'aggiornamento ottimistico, non è necessario un refetch.
    }
  } catch (err) {
    uiStore.addNotification({ message: (err as Error).message, type: 'error' });
  } finally {
    showGroupModal.value = false;
  }
};

const openAssignToGroupModal = () => {
  showAssignToGroupModal.value = true;
};

const handleAssignToGroup = async (groupId: number) => {
  const udaIds = Array.from(selectedUdas.value);
  await udaStore.assignUdasToGroup(udaIds, groupId);
  uiStore.addNotification({ message: `${udaIds.length} UDA assegnate al gruppo.`, type: 'success' });
  selectedUdas.value.clear();
  // Lo store si occupa dell'aggiornamento ottimistico, non è necessario un refetch.
  showAssignToGroupModal.value = false;
};

const confirmRemoveSelectedFromGroup = async () => {
  if (confirm(`Sei sicuro di voler rimuovere le UDA selezionate dai loro gruppi?`)) {
    const udaIds = Array.from(selectedUdas.value);
    await udaStore.removeUdasFromGroup(udaIds);
    if (udaStore.error) {
      uiStore.addNotification({ message: `Errore durante la rimozione: ${udaStore.error}`, type: 'error' });
      udaStore.error = null;
    } else {
      uiStore.addNotification({ message: `UDA rimosse dai gruppi con successo.`, type: 'success' });
      selectedUdas.value.clear();
    }
  }
};

const handleRenameGroup = (group: UdaGroup) => {
  const newName = prompt(`Rinomina il gruppo "${group.name}":`, group.name);
  if (newName && newName.trim() !== '') {
    udaStore.updateUdaGroup(group.id, newName)
      .then(() => uiStore.addNotification({ message: 'Gruppo rinominato con successo.', type: 'success' }))
      .catch(err => uiStore.addNotification({ message: `Errore: ${err.message}`, type: 'error' }));
  }
};

const handleDeleteGroup = async (group: UdaGroup) => {
  if (confirm(`Sei sicuro di voler eliminare il gruppo "${group.name}"? Le UDA contenute non saranno eliminate, ma solo separate dal gruppo.`)) {
    await udaStore.deleteUdaGroup(group.id);
  }
};

const handleRemoveFromGroup = async (udaId: number) => {
  if (confirm("Sei sicuro di voler rimuovere questa UDA dal gruppo?")) {
    await udaStore.removeUdaFromGroup(udaId);
  }
};
</script>

<style scoped>
.group-header-expanded td {
  border-top: 2px solid #BFDBFE; /* blue-200 */
  border-left: 2px solid #BFDBFE;
  border-right: 2px solid #BFDBFE;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.uda-in-expanded-group td:first-child {
  border-left: 2px solid #BFDBFE;
}
.uda-in-expanded-group td:last-child {
  border-right: 2px solid #BFDBFE;
}

.last-uda-in-group td {
  border-bottom: 2px solid #BFDBFE;
}

.last-uda-in-group td:first-child {
  border-bottom-left-radius: 8px;
}

.last-uda-in-group td:last-child {
  border-bottom-right-radius: 8px;
}

.pl-12 {
  padding-left: 3rem;
}
</style>