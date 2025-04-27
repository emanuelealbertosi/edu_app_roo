<template>
  <div class="container mx-auto p-4">
    <!-- Loading Indicator for initial detail fetch -->
    <GlobalLoadingIndicator :is-loading="isLoadingInitial" />

    <div v-if="!isLoadingInitial && currentGroup">
      <h1 class="text-3xl font-bold mb-2">{{ currentGroup.name }}</h1>
      <p v-if="currentGroup.description" class="text-gray-600 mb-6">{{ currentGroup.description }}</p>
      <p v-else class="text-gray-500 italic mb-6">Nessuna descrizione fornita.</p>

      <!-- Error Display -->
       <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
        <strong class="font-bold">Errore!</strong>
        <span class="block sm:inline"> {{ error }}</span>
        <span class="absolute top-0 bottom-0 right-0 px-4 py-3" @click="groupStore.clearError()">
            <svg class="fill-current h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><title>Close</title><path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/></svg>
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Colonna Sinistra: Info e Token -->
        <div class="md:col-span-1 space-y-6">
           <!-- Group Info Card -->
           <div class="bg-white shadow-md rounded-lg p-6">
             <h2 class="text-xl font-semibold mb-4">Informazioni Gruppo</h2>
             <dl>
               <dt class="font-medium text-gray-500">ID Gruppo</dt>
               <dd class="mb-2">{{ currentGroup.id }}</dd>
               <dt class="font-medium text-gray-500">Creato il</dt>
               <dd class="mb-2">{{ formatDate(currentGroup.created_at) }}</dd>
               <dt class="font-medium text-gray-500">Stato</dt>
               <dd class="mb-2">
                 <span :class="currentGroup.is_active ? 'text-green-600' : 'text-red-600'">
                   {{ currentGroup.is_active ? 'Attivo' : 'Non Attivo' }}
                 </span>
               </dd>
             </dl>
              <BaseButton @click="goToEditGroup" variant="secondary" size="sm" class="mt-4">
                Modifica Info Gruppo
              </BaseButton>
           </div>

           <!-- Registration Token Card -->
           <div class="bg-white shadow-md rounded-lg p-6">
             <h2 class="text-xl font-semibold mb-4">Token Registrazione</h2>
             <!-- Modificato per usare registration_link -->
             <div v-if="currentGroup.registration_link" class="mb-4">
               <p class="text-sm text-gray-500 mb-1">Link di registrazione attuale:</p>
               <div class="flex items-center justify-between bg-gray-100 p-2 rounded">
                 <!-- Mostra il link, magari troncato o con overflow gestito -->
                 <input type="text" :value="currentGroup.registration_link" readonly class="text-sm break-all bg-transparent border-none p-0 flex-grow focus:ring-0">
                 <button @click="copyTokenToClipboard(currentGroup.registration_link!)" title="Copia link negli appunti" class="ml-2 p-1 text-gray-500 hover:text-gray-700">
                    <ClipboardDocumentIcon class="h-5 w-5"/>
                 </button>
               </div>
               <BaseButton @click="handleDeleteToken" :is-loading="isLoadingAction" :disabled="isLoadingAction" variant="danger" size="sm" class="mt-4">
                 Elimina Link/Token
               </BaseButton>
             </div>
             <div v-else class="text-gray-500 mb-4">
               Nessun link di registrazione attivo.
             </div>
             <BaseButton v-if="!currentGroup.registration_link" @click="handleGenerateToken" :is-loading="isLoadingAction" :disabled="isLoadingAction" variant="primary" size="sm">
               Genera Nuovo Link/Token
             </BaseButton>
              <p v-if="copySuccess" class="text-green-600 text-xs mt-2">Token copiato!</p>
              <p v-if="copyError" class="text-red-600 text-xs mt-2">Errore nella copia.</p>
           </div>
        </div>

        <!-- Colonna Destra: Membri -->
        <div class="md:col-span-2">
          <div class="bg-white shadow-md rounded-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Membri del Gruppo ({{ currentGroupMembers.length }})</h2>

            <!-- Pulsante per aprire la modale di aggiunta studenti -->
            <div class="mb-6 text-right">
                 <BaseButton @click="isStudentModalOpen = true" variant="primary" :disabled="isLoadingAction">
                    Aggiungi Membro/i
                 </BaseButton>
            </div>

            <!-- Loading Indicator for Members -->
            <GlobalLoadingIndicator :is-loading="isLoadingMembers" />

            <!-- Members Table -->
            <div v-if="!isLoadingMembers && currentGroupMembers.length > 0" class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cognome</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Aggiunto il</th>
                    <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="member in currentGroupMembers" :key="member.id"> <!-- Usa member.id come chiave -->
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ member.id }}</td> <!-- Mostra member.id -->
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ member.first_name }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ member.last_name }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(member.joined_at) }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <BaseButton @click="handleRemoveStudent(member.id)" :is-loading="isLoadingAction && studentIdBeingRemoved === member.id" :disabled="isLoadingAction" variant="danger" size="sm"> <!-- Passa member.id e confronta con member.id -->
                        Rimuovi
                      </BaseButton>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
             <!-- No Members Message -->
            <div v-if="!isLoadingMembers && currentGroupMembers.length === 0" class="text-center text-gray-500 mt-6">
              Nessun membro in questo gruppo.
            </div>
          </div>
        </div>
      </div>
    </div>
     <!-- Group Not Found Message -->
    <div v-if="!isLoadingInitial && !currentGroup && !error" class="text-center text-gray-500 mt-6">
      Gruppo non trovato.
      <router-link :to="{ name: 'GroupsList' }" class="text-primary hover:underline">Torna alla lista</router-link>
    </div>
     <!-- Error loading initial details -->
     <div v-if="!isLoadingInitial && !currentGroup && error" class="text-center text-red-500 mt-6">
       Errore nel caricamento del gruppo: {{ error }}
       <br>
       <router-link :to="{ name: 'GroupsList' }" class="text-primary hover:underline">Torna alla lista</router-link>
    </div>

    <!-- Modale Selezione Studenti -->
    <StudentSelectionModal
        v-model="isStudentModalOpen"
        :existing-member-ids="existingMemberIds"
        @confirm-selection="handleAddStudentsFromModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useGroupStore } from '@/stores/groups';
import BaseButton from '@/components/common/BaseButton.vue';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import StudentSelectionModal from '@/components/groups/StudentSelectionModal.vue'; // Importa la modale
import { ClipboardDocumentIcon } from '@heroicons/vue/24/outline'; // Import copy icon

const route = useRoute();
const router = useRouter();
const groupStore = useGroupStore();

// Use storeToRefs for reactive access to state and getters
const { currentGroup, currentGroupMembers, error, isLoadingDetail } = storeToRefs(groupStore);

const groupId = computed(() => Number(route.params.id));

// Separate loading states
const isLoadingInitial = ref(false); // For the initial load of group details + members
const isLoadingMembers = ref(false); // Specifically for member list refresh (if needed separately)
const isLoadingAction = ref(false); // For actions like add/remove student, token generation/deletion

// Rimosso: const studentIdToAdd = ref<number | null>(null);
// Rimosso: const addStudentError = ref<string | null>(null);
const studentIdBeingRemoved = ref<number | null>(null); // Track which student is being removed
const isStudentModalOpen = ref(false); // Stato per la visibilità della modale

const copySuccess = ref(false);
const copyError = ref(false);

// Fetch group details and members when component mounts or groupId changes
const loadGroupData = async () => {
  if (!groupId.value) return;
  isLoadingInitial.value = true;
  groupStore.clearError();
  try {
    await groupStore.fetchGroupDetails(groupId.value);
    // Ora carichiamo i membri subito dopo i dettagli, se il gruppo è stato trovato
    if (currentGroup.value) {
        isLoadingMembers.value = true; // Usiamo un loading specifico per i membri
        await groupStore.fetchGroupMembers(groupId.value);
        isLoadingMembers.value = false;
    }
  } catch (err) {
    // Error is handled by the store, displayed via the 'error' ref
    console.error("Error loading group data:", err);
  } finally {
    isLoadingInitial.value = false;
  }
};

onMounted(() => {
  loadGroupData();
});

// Watch for route changes if navigating between group details
watch(groupId, (newId, oldId) => {
  if (newId !== oldId) {
    loadGroupData();
  }
});

// --- Computed ---
const existingMemberIds = computed(() => {
    return currentGroupMembers.value.map(member => member.id); // Usa member.id
});


// --- Methods ---

const goToEditGroup = () => {
  router.push({ name: 'GroupEdit', params: { id: groupId.value } });
};

const handleGenerateToken = async () => {
  if (!currentGroup.value) return;
  isLoadingAction.value = true;
  await groupStore.generateRegistrationToken(groupId.value);
  isLoadingAction.value = false;
  // Token in currentGroup should update reactively
};

const handleDeleteToken = async () => {
  // Modificato per controllare registration_link
  if (!currentGroup.value || !currentGroup.value.registration_link) return;
   if (window.confirm(`Sei sicuro di voler eliminare il token di registrazione per il gruppo "${currentGroup.value.name}"?`)) {
        isLoadingAction.value = true;
        await groupStore.deleteRegistrationToken(groupId.value);
        isLoadingAction.value = false;
        // Token in currentGroup should update reactively
   }
};

// Rimuoviamo handleAddStudent, sostituito da handleAddStudentsFromModal

/**
 * Gestisce l'aggiunta degli studenti selezionati dalla modale.
 * @param selectedIds Array degli ID degli studenti selezionati.
 */
const handleAddStudentsFromModal = async (selectedIds: number[]) => {
  if (!currentGroup.value || selectedIds.length === 0) return;

  isLoadingAction.value = true;
  groupStore.clearError(); // Pulisce errori precedenti generali
  let successCount = 0;
  let errorMessages: string[] = [];

  for (const studentId of selectedIds) {
    try {
      // Chiamiamo l'azione dello store per ogni studente
      // L'azione dello store dovrebbe idealmente ricaricare i membri alla fine
      // o possiamo farlo noi qui dopo il loop se necessario.
      await groupStore.addStudentToGroup(groupId.value, { student_id: studentId });
      successCount++;
    } catch (err: any) {
      console.error(`Errore aggiungendo studente ID ${studentId}:`, err);
      const detail = err.response?.data?.detail || `Errore per ID ${studentId}`;
      if (!errorMessages.includes(detail)) { // Evita duplicati dello stesso errore generico
        errorMessages.push(detail);
      }
      // Non interrompiamo il loop, proviamo ad aggiungere gli altri
    }
  }

  isLoadingAction.value = false;

  // Se ci sono stati errori, mostrali (potremmo usare un sistema di notifiche migliore)
  if (errorMessages.length > 0) {
      // L'errore viene già impostato nello store da addStudentToGroup in caso di fallimento.
      // Potremmo mostrare un riepilogo qui se necessario.
      // groupStore.setError(`Aggiunti ${successCount}/${selectedIds.length} studenti. Errori: ${errorMessages.join(', ')}`);
      console.warn(`Aggiunti ${successCount}/${selectedIds.length} studenti. Errori: ${errorMessages.join(', ')}`);
  }

  // Assicurati che la lista membri sia aggiornata (se l'azione dello store non lo fa già)
  // await groupStore.fetchGroupMembers(groupId.value); // Decommenta se necessario
};


const handleRemoveStudent = async (studentId: number) => {
  console.log('[DEBUG] Entered handleRemoveStudent with studentId:', studentId, 'Type:', typeof studentId); // Ensure this log is at the very start
  if (!currentGroup.value) return;
   if (window.confirm(`Sei sicuro di voler rimuovere lo studente ID ${studentId} dal gruppo "${currentGroup.value.name}"?`)) {
        isLoadingAction.value = true;
        studentIdBeingRemoved.value = studentId; // Indicate which student is being processed
        // console.log('[DEBUG] handleRemoveStudent - Received studentId:', studentId, 'Type:', typeof studentId); // REMOVE this redundant/misplaced log
        await groupStore.removeStudentFromGroup(groupId.value, studentId);
        isLoadingAction.value = false;
        studentIdBeingRemoved.value = null;
        // Member list updates reactively
   }
};

// Modificato per copiare il link invece del token
const copyTokenToClipboard = async (link: string) => {
    copySuccess.value = false;
    copyError.value = false;
    try {
        await navigator.clipboard.writeText(link);
        copySuccess.value = true;
        setTimeout(() => copySuccess.value = false, 2000); // Hide message after 2s
    } catch (err) {
        console.error('Failed to copy link: ', err);
        copyError.value = true;
         setTimeout(() => copyError.value = false, 3000); // Hide message after 3s
    }
};

const formatDate = (dateString: string | null) => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  } catch (e) {
    console.error("Error formatting date:", e);
    return dateString; // Fallback
  }
};

// Clear group details when leaving the view
import { onBeforeUnmount } from 'vue';
onBeforeUnmount(() => {
    groupStore.clearCurrentGroup();
});

</script>

<style scoped>
/* Add component-specific styles if needed */
</style>