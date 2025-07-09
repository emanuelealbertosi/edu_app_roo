<template>
  <table class="min-w-full divide-y divide-gray-200">
    <thead class="bg-gray-50">
      <tr>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titolo</th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stato</th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Corso</th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contenuti</th>
        <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
      </tr>
    </thead>
    <tbody class="bg-white divide-y divide-gray-200">
      <tr v-for="uda in udas" :key="uda.id" class="hover:bg-gray-50">
        <td class="px-6 py-4 whitespace-nowrap">
          <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }" class="text-sm font-medium text-indigo-700 hover:text-indigo-900">
            {{ uda.title }}
          </RouterLink>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full" :class="getStatusClass(uda.status)">
            {{ uda.status }}
          </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
          {{ uda.course_name || '-' }}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-center">
          {{ uda.contents?.length || 0 }}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
          <RouterLink :to="{ name: 'uda-detail', params: { id: uda.id } }" class="text-blue-600 hover:text-blue-900" title="Vedi Dettagli">
            <EyeIcon class="h-5 w-5 inline-block" />
          </RouterLink>
          <button @click="$emit('copy-uda', { id: uda.id, title: uda.title })" class="text-green-600 hover:text-green-900" title="Copia UDA">
            <DocumentDuplicateIcon class="h-5 w-5 inline-block" />
          </button>
          <button @click="$emit('delete-uda', { id: uda.id, title: uda.title })" class="text-red-600 hover:text-red-900" title="Elimina UDA">
            <TrashIcon class="h-5 w-5 inline-block" />
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';
import { RouterLink } from 'vue-router';
import { EyeIcon, DocumentDuplicateIcon, TrashIcon } from '@heroicons/vue/24/outline';
import type { UDA } from '@/types/uda';

defineProps<{
  udas: UDA[];
}>();

defineEmits<{
  (e: 'delete-uda', payload: { id: number; title: string }): void;
  (e: 'copy-uda', payload: { id: number; title: string }): void;
}>();

const getStatusClass = (status?: UDA['status']) => {
  if (!status) return 'text-gray-600 bg-gray-100';
  if (status === 'COMPLETED') return 'text-green-700 bg-green-100';
  if (status === 'IN_PROGRESS') return 'text-blue-700 bg-blue-100';
  if (status === 'TODO') return 'text-yellow-700 bg-yellow-100';
  return 'text-gray-600 bg-gray-100';
};
</script>