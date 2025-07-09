<template>
  <table class="min-w-full divide-y divide-gray-200">
    <thead class="bg-gray-50">
      <tr>
        <th scope="col" class="px-6 py-3 text-left">
          <input type="checkbox" @change="toggleSelectAll" :checked="allSelected" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
        </th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Nome
        </th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Descrizione
        </th>
        <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
          Azioni
        </th>
      </tr>
    </thead>
    <tbody class="bg-white divide-y divide-gray-200">
      <tr v-for="course in courses" :key="course.id" class="hover:bg-gray-50 transition-colors duration-150">
        <td class="px-6 py-4">
          <input type="checkbox" :value="course.id" @change="toggleSelection(course.id)" :checked="selectedCourses.has(course.id)" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm font-medium text-indigo-700 hover:text-indigo-900">
            <RouterLink :to="{ name: 'course-detail', params: { id: course.id } }">
              {{ course.name }}
            </RouterLink>
          </div>
        </td>
        <td class="px-6 py-4 text-sm text-gray-500">
          <span :title="course.description" v-if="course.description && course.description.length > 30">
            {{ course.description.substring(0, 30) + '...' }}
          </span>
          <span v-else>{{ course.description || 'Nessuna descrizione fornita.' }}</span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
          <RouterLink :to="{ name: 'course-detail', params: { id: course.id } }" class="text-blue-600 hover:text-blue-900" title="Vedi Dettagli">
            <EyeIcon class="h-5 w-5 inline-block" />
          </RouterLink>
          <button @click="handleCopyCourse(course)" class="text-green-600 hover:text-green-900" title="Copia Corso">
            <DocumentDuplicateIcon class="h-5 w-5 inline-block" />
          </button>
          <button @click="handleDeleteCourse(course.id)" class="text-red-600 hover:text-red-900" title="Elimina Corso">
            <TrashIcon class="h-5 w-5 inline-block" />
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';
import type { Course } from '@/types/uda';
import { useCourseStore } from '@/stores/courseStore';
import { useUiStore } from '@/stores/ui';
import { EyeIcon, TrashIcon, DocumentDuplicateIcon } from '@heroicons/vue/24/outline';

const props = defineProps<{
  courses: Course[];
  selectedCourses: Set<number>;
}>();

const emit = defineEmits(['update:selectedCourses']);

const courseStore = useCourseStore();
const uiStore = useUiStore();

const allSelected = computed(() => {
  if (props.courses.length === 0) return false;
  return props.courses.every(course => props.selectedCourses.has(course.id));
});

const toggleSelectAll = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const newSelectedCourses = new Set(props.selectedCourses);
  if (target.checked) {
    props.courses.forEach(course => newSelectedCourses.add(course.id));
  } else {
    props.courses.forEach(course => newSelectedCourses.delete(course.id));
  }
  emit('update:selectedCourses', newSelectedCourses);
};

const toggleSelection = (courseId: number) => {
  const newSelectedCourses = new Set(props.selectedCourses);
  if (newSelectedCourses.has(courseId)) {
    newSelectedCourses.delete(courseId);
  } else {
    newSelectedCourses.add(courseId);
  }
  emit('update:selectedCourses', newSelectedCourses);
};

const handleDeleteCourse = async (courseId: number) => {
  if (confirm('Sei sicuro di voler eliminare questo corso?')) {
    try {
      await courseStore.deleteCourse(courseId);
      uiStore.addNotification({ message: 'Corso eliminato con successo', type: 'success' });
    } catch (err) {
      uiStore.addNotification({ message: (err as Error).message || 'Errore', type: 'error' });
    }
  }
};

const handleCopyCourse = async (course: Course) => {
  if (confirm(`Copiare il corso "${course.name}"?`)) {
    try {
      await courseStore.copyCourse(course.id);
      uiStore.addNotification({ message: 'Corso copiato', type: 'success' });
    } catch (err) {
      uiStore.addNotification({ message: (err as Error).message || 'Errore', type: 'error' });
    }
  }
};
</script>