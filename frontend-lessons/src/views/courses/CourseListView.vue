<template>
  <div class="course-list-container p-6">
    <!-- Intestazione con sfondo blu -->
    <div class="bg-blue-600 text-white p-4 rounded-md mb-6 flex justify-between items-center">
      <h2 class="text-2xl font-semibold">I Miei Corsi</h2>
      <!-- Pulsante stile adattato per contrasto -->
      <RouterLink
        :to="{ name: 'course-new' }"
        class="flex items-center px-3 py-2 bg-white text-blue-600 rounded-md shadow-sm hover:bg-blue-100 transition duration-150 ease-in-out font-medium"
      >
        <PlusCircleIcon class="h-5 w-5 sm:mr-2" />
        <span class="hidden sm:inline">Crea Nuovo Corso</span>
      </RouterLink>
    </div>

    <!-- Campo di Ricerca -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca corsi per nome, descrizione..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      />
    </div>

    <!-- Azioni di gruppo -->
    <div v-if="selectedCourses.size > 0" class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md flex items-center justify-between">
      <span class="text-sm font-medium text-blue-700">{{ selectedCourses.size }} {{ selectedCourses.size === 1 ? 'corso selezionato' : 'corsi selezionati' }}</span>
      <div class="flex items-center space-x-2">
        <button
          @click="confirmRemoveSelectedFromGroup"
          class="px-4 py-2 bg-red-100 border border-red-300 text-red-700 rounded-md shadow-sm hover:bg-red-200 transition duration-150 ease-in-out font-medium"
          :disabled="!atLeastOneSelectedCourseInGroup"
          title="Rimuovi i corsi selezionati dai loro gruppi"
        >
          Rimuovi dal Gruppo
        </button>
        <button
          @click="openAssignToGroupModal"
          class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md shadow-sm hover:bg-gray-50 transition duration-150 ease-in-out font-medium"
          :disabled="courseGroups.length === 0"
          title="Aggiungi i corsi selezionati a un gruppo esistente"
        >
          Aggiungi a Gruppo...
        </button>
        <button @click="openCreateGroupModal" class="px-4 py-2 bg-blue-600 text-white rounded-md shadow-sm hover:bg-blue-700 transition duration-150 ease-in-out font-medium">
          Crea Nuovo Gruppo...
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center text-gray-500 py-10">
      Caricamento corsi...
    </div>

    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore:</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <!-- Tabella Corsi con Gruppi -->
    <div v-if="!loading && (groupedCourses.grouped.length > 0 || groupedCourses.ungrouped.length > 0)" class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="relative px-4 py-3">
              <input type="checkbox" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" @change="toggleSelectAll" :checked="areAllCoursesSelected" :disabled="allVisibleCourseIds.length === 0" />
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('name')">
              Nome
              <span v-if="sortKey === 'name'">
                <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
                <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
              </span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" @click="sortBy('description')">
             Descrizione
             <span v-if="sortKey === 'description'">
               <ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" />
               <ChevronDownIcon v-else class="h-4 w-4 inline-block" />
             </span>
           </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <!-- Itera sui gruppi -->
          <template v-for="item in groupedCourses.grouped" :key="item.group.id">
            <tr
              class="bg-blue-50 hover:bg-blue-100 cursor-pointer"
              @click="toggleGroup(item.group.id)"
              :class="{ 'group-header-expanded': expandedGroups.has(item.group.id) }"
            >
              <td colspan="4" class="px-6 py-3 text-sm font-semibold text-blue-800">
                <div class="flex items-center">
                  <FolderMinusIcon v-if="expandedGroups.has(item.group.id)" class="h-5 w-5 mr-2 text-blue-700" />
                  <FolderPlusIcon v-else class="h-5 w-5 mr-2 text-blue-600" />
                  <span>{{ item.group.name }} ({{ item.courses.length }})</span>
                  <div class="ml-auto flex items-center space-x-2">
                    <button @click.stop="handleRenameGroup(item.group)" class="text-gray-500 hover:text-blue-600"><PencilIcon class="h-4 w-4"/></button>
                    <button @click.stop="handleDeleteGroup(item.group)" class="text-gray-500 hover:text-red-600"><TrashIcon class="h-4 w-4"/></button>
                    <ChevronDownIcon v-if="expandedGroups.has(item.group.id)" class="h-5 w-5" />
                    <ChevronRightIcon v-else class="h-5 w-5" />
                  </div>
                </div>
              </td>
            </tr>
            <!-- Itera sui corsi del gruppo se espanso -->
            <template v-if="expandedGroups.has(item.group.id)">
              <tr v-for="(course, index) in item.courses" :key="course.id"
                class="hover:bg-gray-50"
                :class="{
                  'bg-blue-50': selectedCourses.has(course.id),
                  'course-in-expanded-group': true,
                  'last-course-in-group': index === item.courses.length - 1
                }">
                <td class="px-4 py-4 whitespace-nowrap">
                  <input type="checkbox" :checked="selectedCourses.has(course.id)" @change="toggleCourseSelection(course.id)" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                </td>
                <td class="pl-12 pr-6 py-4 whitespace-nowrap text-sm font-medium">
                  <RouterLink :to="{ name: 'course-detail', params: { id: course.id } }" class="text-blue-600 hover:text-blue-800 hover:underline">
                    {{ course.name }}
                  </RouterLink>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ course.description }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  <RouterLink :to="{ name: 'course-edit', params: { id: course.id } }" class="text-yellow-600 hover:text-yellow-900"><PencilIcon class="h-5 w-5 inline-block"/></RouterLink>
                  <button @click="handleCopyCourse(course)" class="text-purple-600 hover:text-purple-900"><DocumentDuplicateIcon class="h-5 w-5 inline-block"/></button>
                  <button @click="handleDeleteCourse(course.id)" class="text-red-600 hover:text-red-900"><TrashIcon class="h-5 w-5 inline-block"/></button>
                  <button @click.stop="handleRemoveFromGroup(course.id)" class="text-gray-500 hover:text-gray-700" title="Rimuovi dal gruppo">
                    <XCircleIcon class="h-5 w-5" />
                  </button>
                </td>
              </tr>
            </template>
          </template>
          <!-- Corsi non Raggruppati -->
          <tr v-for="course in groupedCourses.ungrouped" :key="course.id" class="hover:bg-gray-50" :class="{'bg-blue-50': selectedCourses.has(course.id)}">
            <td class="px-4 py-4 whitespace-nowrap">
              <input type="checkbox" :checked="selectedCourses.has(course.id)" @change="toggleCourseSelection(course.id)" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500">
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <RouterLink :to="{ name: 'course-detail', params: { id: course.id } }" class="text-gray-900 hover:text-blue-600 hover:underline">
                {{ course.name }}
              </RouterLink>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ course.description }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <RouterLink :to="{ name: 'course-edit', params: { id: course.id } }" class="text-yellow-600 hover:text-yellow-900"><PencilIcon class="h-5 w-5 inline-block"/></RouterLink>
              <button @click="handleCopyCourse(course)" class="text-purple-600 hover:text-purple-900"><DocumentDuplicateIcon class="h-5 w-5 inline-block"/></button>
              <button @click="handleDeleteCourse(course.id)" class="text-red-600 hover:text-red-900"><TrashIcon class="h-5 w-5 inline-block"/></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="!loading && groupedCourses.grouped.length === 0 && groupedCourses.ungrouped.length === 0 && !error" class="text-center text-gray-500 py-10">
      <span v-if="searchQuery">Nessun corso trovato per "{{ searchQuery }}".</span>
      <span v-else>Non hai ancora creato nessun corso.</span>
    </div>

    <CourseGroupModal
      :show="showGroupModal"
      @close="showGroupModal = false"
      @save="handleGroupSave"
    />

    <AssignToGroupModal
      :show="showAssignToGroupModal"
      :groups="courseGroups"
      @close="showAssignToGroupModal = false"
      @assign="handleAssignToGroup"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { RouterLink } from 'vue-router';
import { useCourseStore } from '@/stores/courseStore';
import { useUiStore } from '@/stores/ui';
import type { Course, CourseGroup } from '@/types/uda';
import {
  PlusCircleIcon, TrashIcon, DocumentDuplicateIcon, ChevronUpIcon, ChevronDownIcon,
  FolderIcon, PencilIcon, FolderPlusIcon, FolderMinusIcon, ChevronRightIcon, XCircleIcon
} from '@heroicons/vue/24/outline';
import CourseGroupModal from '@/components/features/courses/CourseGroupModal.vue';
import AssignToGroupModal from '@/components/features/courses/AssignToGroupModal.vue';

const courseStore = useCourseStore();
const uiStore = useUiStore();

const searchQuery = ref('');
const sortKey = ref('name');
const sortOrder = ref('asc');
const selectedCourses = ref<Set<number>>(new Set());
const expandedGroups = ref<Set<number>>(new Set());
const showGroupModal = ref(false);
const showAssignToGroupModal = ref(false);

const courses = computed(() => courseStore.courses);
const courseGroups = computed(() => courseStore.courseGroups);
const loading = computed(() => courseStore.loading || courseStore.isLoadingCourseGroups);
const error = computed(() => courseStore.error);

const filteredAndSortedCourses = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  const filtered = query
    ? courses.value.filter(c => c.name.toLowerCase().includes(query) || (c.description && c.description.toLowerCase().includes(query)))
    : courses.value;

  return [...filtered].sort((a, b) => {
    let valA = a[sortKey.value as keyof typeof a] as any;
    let valB = b[sortKey.value as keyof typeof b] as any;
    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();
    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

const groupedCourses = computed(() => {
  const grouped: { group: CourseGroup; courses: Course[] }[] = [];
  const ungrouped: Course[] = [];
  const groupMap = new Map<number, { group: CourseGroup; courses: Course[] }>();

  courseGroups.value.forEach(group => {
    groupMap.set(group.id, { group, courses: [] });
  });

  filteredAndSortedCourses.value.forEach(course => {
    if (course.group && groupMap.has(course.group.id)) {
      groupMap.get(course.group.id)!.courses.push(course);
    } else {
      ungrouped.push(course);
    }
  });

  groupMap.forEach(value => {
    if (value.courses.length > 0 || !searchQuery.value) { // Mostra gruppo se ha corsi o se non si sta cercando
        grouped.push(value);
    }
  });
  
  grouped.sort((a, b) => a.group.name.localeCompare(b.group.name));

  return { grouped, ungrouped };
});

const allVisibleCourseIds = computed(() => filteredAndSortedCourses.value.map(c => c.id));
const areAllCoursesSelected = computed(() => {
    const visibleIds = new Set(allVisibleCourseIds.value);
    return visibleIds.size > 0 && [...visibleIds].every(id => selectedCourses.value.has(id));
});

const atLeastOneSelectedCourseInGroup = computed(() => {
  for (const courseId of selectedCourses.value) {
    const course = courseStore.courses.find(c => c.id === courseId);
    if (course && course.group) {
      return true;
    }
  }
  return false;
});

const toggleCourseSelection = (courseId: number) => {
  if (selectedCourses.value.has(courseId)) {
    selectedCourses.value.delete(courseId);
  } else {
    selectedCourses.value.add(courseId);
  }
};

const toggleSelectAll = () => {
    const visibleIds = allVisibleCourseIds.value;
    if (areAllCoursesSelected.value) {
        visibleIds.forEach(id => selectedCourses.value.delete(id));
    } else {
        visibleIds.forEach(id => selectedCourses.value.add(id));
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
  courseStore.fetchCourses();
  courseStore.fetchCourseGroups();
});

const sortBy = (key: 'name' | 'description') => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

const handleRenameGroup = (group: CourseGroup) => {
  // TODO: Implementare la logica per rinominare un gruppo, magari con una modale
  const newName = prompt(`Rinomina il gruppo "${group.name}":`, group.name);
  if (newName && newName.trim() !== '') {
    courseStore.updateCourseGroup(group.id, newName)
      .then(() => uiStore.addNotification({ message: 'Gruppo rinominato con successo.', type: 'success' }))
      .catch(err => uiStore.addNotification({ message: `Errore: ${err.message}`, type: 'error' }));
  }
};

const handleDeleteGroup = async (group: CourseGroup) => {
    if (confirm(`Sei sicuro di voler eliminare il gruppo "${group.name}"? I corsi in questo gruppo non verranno eliminati, ma solo sganciati.`)) {
        try {
            await courseStore.deleteCourseGroup(group.id);
            uiStore.addNotification({ message: 'Gruppo eliminato!', type: 'success' });
        } catch (err) {
            uiStore.addNotification({ message: (err as Error).message, type: 'error' });
        }
    }
};

const handleRemoveFromGroup = async (courseId: number) => {
    if (confirm("Sei sicuro di voler rimuovere questo corso dal gruppo?")) {
        try {
            await courseStore.removeCourseFromGroup(courseId);
            uiStore.addNotification({ message: 'Corso rimosso dal gruppo!', type: 'success' });
        } catch (err) {
            uiStore.addNotification({ message: (err as Error).message, type: 'error' });
        }
    }
};

const openCreateGroupModal = () => {
  showGroupModal.value = true;
};

const handleGroupSave = async (groupName: string) => {
  try {
    const group = await courseStore.createCourseGroup(groupName);
    if (group) {
      const courseIds = Array.from(selectedCourses.value);
      if (courseIds.length > 0) {
        await courseStore.assignCoursesToGroup(courseIds, group.id);
        uiStore.addNotification({ message: `Gruppo "${groupName}" creato e ${courseIds.length} corsi assegnati.`, type: 'success' });
      } else {
        uiStore.addNotification({ message: `Gruppo "${groupName}" creato con successo.`, type: 'success' });
      }
      selectedCourses.value.clear();
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
  const courseIds = Array.from(selectedCourses.value);
  await courseStore.assignCoursesToGroup(courseIds, groupId);
  uiStore.addNotification({ message: `${courseIds.length} corsi assegnati al gruppo.`, type: 'success' });
  selectedCourses.value.clear();
  showAssignToGroupModal.value = false;
};

const confirmRemoveSelectedFromGroup = async () => {
  if (confirm(`Sei sicuro di voler rimuovere i corsi selezionati dai loro gruppi?`)) {
    const courseIds = Array.from(selectedCourses.value);
    await courseStore.removeCoursesFromGroup(courseIds);
     if (courseStore.error) {
      uiStore.addNotification({ message: `Errore durante la rimozione: ${courseStore.error}`, type: 'error' });
      courseStore.error = null;
    } else {
      uiStore.addNotification({ message: `Corsi rimossi dai gruppi con successo.`, type: 'success' });
      selectedCourses.value.clear();
    }
  }
};

const handleDeleteCourse = async (courseId: number) => {
  if (confirm('Sei sicuro di voler eliminare questo corso?')) {
    try {
      await courseStore.deleteCourse(courseId);
      uiStore.addNotification({ message: 'Corso eliminato!', type: 'success' });
    } catch (err) {
      uiStore.addNotification({ message: (err as Error).message, type: 'error' });
    }
  }
};

const handleCopyCourse = async (course: { id: number; name: string }) => {
 if (confirm(`Sei sicuro di voler copiare il corso "${course.name}"?`)) {
   try {
     await courseStore.copyCourse(course.id);
     uiStore.addNotification({ message: 'Corso copiato!', type: 'success' });
   } catch (err) {
     uiStore.addNotification({ message: (err as Error).message, type: 'error' });
   }
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

.course-in-expanded-group td:first-child {
  border-left: 2px solid #BFDBFE;
}
.course-in-expanded-group td:last-child {
  border-right: 2px solid #BFDBFE;
}

.last-course-in-group td {
  border-bottom: 2px solid #BFDBFE;
}

.last-course-in-group td:first-child {
  border-bottom-left-radius: 8px;
}

.last-course-in-group td:last-child {
  border-bottom-right-radius: 8px;
}

.pl-12 {
  padding-left: 3rem;
}
</style>