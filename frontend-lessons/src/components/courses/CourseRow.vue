<template>
  <div class="grid grid-cols-12 gap-4 px-4 py-3 items-center border-b last:border-b-0 hover:bg-gray-50">
    <div class="col-span-1 flex items-center">
      <input 
        type="checkbox" 
        :value="course.id" 
        :checked="isSelected"
        @change="toggleSelection"
        class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
      />
    </div>
    <div class="col-span-5">
      <RouterLink :to="{ name: 'course-detail', params: { id: course.id } }" class="text-sm font-medium text-indigo-700 hover:text-indigo-900">
        {{ course.name }}
      </RouterLink>
    </div>
    <div class="col-span-4 text-sm text-gray-500">
      <span :title="course.description ?? undefined">
        {{ truncate(course.description, 50) }}
      </span>
    </div>
    <td class="col-span-2 text-right text-sm font-medium space-x-2">
      <button v-if="course.group" @click="$emit('removeFromGroup', course.id)" class="text-yellow-600 hover:text-yellow-900" title="Rimuovi dal gruppo">
        <ArrowUturnLeftIcon class="h-5 w-5 inline-block" />
      </button>
      <RouterLink :to="{ name: 'course-detail', params: { id: course.id } }" class="text-blue-600 hover:text-blue-900" title="Vedi Dettagli">
        <EyeIcon class="h-5 w-5 inline-block" />
      </RouterLink>
      <button @click="$emit('copy', course)" class="text-green-600 hover:text-green-900" title="Copia Corso">
        <DocumentDuplicateIcon class="h-5 w-5 inline-block" />
      </button>
      <button @click="$emit('delete', course.id)" class="text-red-600 hover:text-red-900" title="Elimina Corso">
        <TrashIcon class="h-5 w-5 inline-block" />
      </button>
    </td>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';
import type { Course } from '@/types/uda';
import { EyeIcon, TrashIcon, DocumentDuplicateIcon, ArrowUturnLeftIcon } from '@heroicons/vue/24/outline';

const props = defineProps<{
  course: Course;
  selectedIds: number[];
}>();

const emit = defineEmits(['update:selectedIds', 'copy', 'delete', 'removeFromGroup']);

const isSelected = computed(() => props.selectedIds.includes(props.course.id));

const toggleSelection = () => {
  const newSelectedIds = [...props.selectedIds];
  if (isSelected.value) {
    const index = newSelectedIds.indexOf(props.course.id);
    newSelectedIds.splice(index, 1);
  } else {
    newSelectedIds.push(props.course.id);
  }
  emit('update:selectedIds', newSelectedIds);
};

const truncate = (text: string | null | undefined, length: number) => {
  if (!text) return 'Nessuna descrizione.';
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
};
</script>