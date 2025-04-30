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

      <!-- Is Public Checkbox (Conditional) -->
      <div v-if="userCanCreatePublicGroups" class="mb-6">
        <label class="flex items-center text-gray-700 text-sm font-bold" for="group-is-public">
          <input
            v-model="groupData.is_public"
            class="mr-2 leading-tight"
            id="group-is-public"
            type="checkbox"
          />
          <span class="text-sm">Rendi questo gruppo pubblico</span>
        </label>
        <p class="text-xs text-gray-600 mt-1">Se selezionato, altri docenti potranno trovare questo gruppo e richiedere l'accesso.</p>
        <p v-if="validationErrors.is_public" class="text-red-500 text-xs italic">{{ validationErrors.is_public }}</p>
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
import { useAuthStore } from '@/stores/auth'; // Import auth store
import type { StudentGroup, StudentGroupData } from '@/types/groups'; // Import StudentGroup too
import BaseButton from '@/components/common/BaseButton.vue';
// Import GlobalLoadingIndicator if needed for the whole view, or rely on button's loading state
// import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';

const router = useRouter();
const route = useRoute();
const groupStore = useGroupStore();
const authStore = useAuthStore(); // Initialize auth store

const { error, isLoadingDetail: isLoadingStore, currentGroup } = storeToRefs(groupStore); // Use isLoadingDetail for fetching/updating, get currentGroup
const { user } = storeToRefs(authStore); // Get user data from auth store

// Computed property to check if the user can create public groups
// Assumes the user object from authStore has a 'can_create_public_groups' property
const userCanCreatePublicGroups = computed(() => !!user.value?.can_create_public_groups);

const groupId = computed(() => route.params.id ? Number(route.params.id) : null);
const isEditing = computed(() => !!groupId.value);
const isLoading = ref(false); // Local loading state for form submission

const groupData = reactive<StudentGroupData>({
  name: '',
  description: null,
  is_public: false, // Initialize is_public
});

const validationErrors = reactive<{ name?: string; description?: string; is_public?: string }>({});

// Fetch group data if editing
onMounted(async () => {
  groupStore.clearError(); // Clear previous errors
  // Log user data and permission check on mount
  console.log('[GroupFormView Mounted] User Data:', user.value);
  console.log('[GroupFormView Mounted] Computed userCanCreatePublicGroups:', userCanCreatePublicGroups.value);
  if (isEditing.value && groupId.value) {
    isLoading.value = true; // Use local loading state
    await groupStore.fetchGroupDetails(groupId.value);
    // Use the ref obtained from storeToRefs
    if (currentGroup.value) {
      groupData.name = currentGroup.value.name;
      groupData.description = currentGroup.value.description;
      // Populate is_public only if the user has permission to see/edit it
      if (userCanCreatePublicGroups.value) {
          groupData.is_public = currentGroup.value.is_public ?? false;
      }
    }
    isLoading.value = false;
  } else {
      // Reset form for creation mode
      groupData.name = '';
      groupData.description = null;
      groupData.is_public = false; // Default to false for new groups
  }
});

const validateForm = (): boolean => {
    validationErrors.name = '';
    validationErrors.description = '';
    validationErrors.is_public = ''; // Reset is_public errors
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
      // Prepare data, include is_public only if user has permission
      const updateData: Partial<StudentGroupData> = {
          name: groupData.name,
          description: groupData.description,
      };
      if (userCanCreatePublicGroups.value) {
          updateData.is_public = groupData.is_public;
      }
      await groupStore.updateGroup(groupId.value, updateData);
      // Optionally show success message
      router.push({ name: 'GroupsList' }); // Redirect back to list after update
    } else {
      // Create new group
      // Prepare data, include is_public only if user has permission
      const createData: StudentGroupData = {
          name: groupData.name,
          description: groupData.description,
      };
       if (userCanCreatePublicGroups.value) {
          createData.is_public = groupData.is_public;
      }
      await groupStore.createGroup(createData);
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
         if (backendErrors.is_public) validationErrors.is_public = backendErrors.is_public.join(', '); // Handle is_public errors
         // Handle non_field_errors or detail if present
         if (backendErrors.detail && !validationErrors.name && !validationErrors.description && !validationErrors.is_public) {
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