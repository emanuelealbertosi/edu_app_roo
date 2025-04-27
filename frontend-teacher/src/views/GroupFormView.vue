<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-4">{{ isEditing ? 'Modifica Gruppo' : 'Crea Nuovo Gruppo' }}</h1>

    <form @submit.prevent="handleSubmit" class="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
      <!-- Error Message -->
      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
        <strong class="font-bold">Errore!</strong>
        <span class="block sm:inline"> {{ error }}</span>
         <span class="absolute top-0 bottom-0 right-0 px-4 py-3" @click="groupStore.clearError()">
            <svg class="fill-current h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><title>Close</title><path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/></svg>
        </span>
      </div>

      <!-- Group Name -->
      <div class="mb-4">
        <label class="block text-gray-700 text-sm font-bold mb-2" for="group-name">
          Nome Gruppo <span class="text-red-500">*</span>
        </label>
        <input
          v-model="groupData.name"
          class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          :class="{ 'border-red-500': validationErrors.name }"
          id="group-name"
          type="text"
          placeholder="Es. Classe 5A - Informatica"
          required
        />
         <p v-if="validationErrors.name" class="text-red-500 text-xs italic">{{ validationErrors.name }}</p>
      </div>

      <!-- Group Description -->
      <div class="mb-6">
        <label class="block text-gray-700 text-sm font-bold mb-2" for="group-description">
          Descrizione (Opzionale)
        </label>
        <textarea
          v-model="groupData.description"
          class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
           :class="{ 'border-red-500': validationErrors.description }"
          id="group-description"
          placeholder="Breve descrizione del gruppo"
          rows="3"
        ></textarea>
         <p v-if="validationErrors.description" class="text-red-500 text-xs italic">{{ validationErrors.description }}</p>
      </div>

      <!-- Submit Button -->
      <div class="flex items-center justify-between">
        <BaseButton type="submit" :is-loading="isLoading" :disabled="isLoading" variant="primary">
          {{ isEditing ? 'Salva Modifiche' : 'Crea Gruppo' }}
        </BaseButton>
        <BaseButton type="button" @click="goBack" variant="secondary" :disabled="isLoading">
          Annulla
        </BaseButton>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useGroupStore } from '@/stores/groups';
import type { StudentGroupData } from '@/types/groups';
import BaseButton from '@/components/common/BaseButton.vue';
// Import GlobalLoadingIndicator if needed for the whole view, or rely on button's loading state
// import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';

const router = useRouter();
const route = useRoute();
const groupStore = useGroupStore();

const { error, isLoadingDetail: isLoadingStore } = storeToRefs(groupStore); // Use isLoadingDetail for fetching/updating

const groupId = computed(() => route.params.id ? Number(route.params.id) : null);
const isEditing = computed(() => !!groupId.value);
const isLoading = ref(false); // Local loading state for form submission

const groupData = reactive<StudentGroupData>({
  name: '',
  description: null,
});

const validationErrors = reactive<{ name?: string; description?: string }>({});

// Fetch group data if editing
onMounted(async () => {
  groupStore.clearError(); // Clear previous errors
  if (isEditing.value && groupId.value) {
    isLoading.value = true; // Use local loading state
    await groupStore.fetchGroupDetails(groupId.value);
    if (groupStore.currentGroup) {
      groupData.name = groupStore.currentGroup.name;
      groupData.description = groupStore.currentGroup.description;
    }
    isLoading.value = false;
  } else {
      // Reset form for creation mode
      groupData.name = '';
      groupData.description = null;
  }
});

const validateForm = (): boolean => {
    validationErrors.name = '';
    validationErrors.description = '';
    let isValid = true;
    if (!groupData.name || groupData.name.trim() === '') {
        validationErrors.name = 'Il nome del gruppo è obbligatorio.';
        isValid = false;
    }
    // Add other validation rules if needed (e.g., description length)
    return isValid;
}

const handleSubmit = async () => {
  if (!validateForm()) {
      return;
  }

  isLoading.value = true;
  groupStore.clearError(); // Clear previous errors before submitting

  try {
    if (isEditing.value && groupId.value) {
      // Update existing group
      await groupStore.updateGroup(groupId.value, {
          name: groupData.name,
          description: groupData.description // Pass only fields being edited
      });
      // Optionally show success message
      router.push({ name: 'GroupsList' }); // Redirect back to list after update
    } else {
      // Create new group
      await groupStore.createGroup({
          name: groupData.name,
          description: groupData.description
      });
      // Optionally show success message
      router.push({ name: 'GroupsList' }); // Redirect back to list after creation
    }
  } catch (err: any) {
    // Error is already set in the store, but we might handle specific validation errors here
     console.error("Form submission error:", err);
     // Potentially map backend validation errors to validationErrors object
     if (err.response?.data) {
         const backendErrors = err.response.data;
         if (backendErrors.name) validationErrors.name = backendErrors.name.join(', ');
         if (backendErrors.description) validationErrors.description = backendErrors.description.join(', ');
         // Handle non_field_errors or detail if present
         if (backendErrors.detail && !validationErrors.name && !validationErrors.description) {
             groupStore.error = backendErrors.detail; // Use store error for general messages
         }
     }
  } finally {
    isLoading.value = false;
  }
};

const goBack = () => {
  router.back(); // Or router.push({ name: 'GroupsList' });
};
</script>

<style scoped>
/* Add component-specific styles if needed */
</style>