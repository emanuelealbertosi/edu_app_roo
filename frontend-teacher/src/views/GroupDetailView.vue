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
               <!-- Visualizza QR Code se presente -->
               <div v-if="currentGroup.qr_code_base64" class="mt-4">
                   <p class="text-sm text-gray-500 mb-1">QR Code per registrazione:</p>
                   <img :src="currentGroup.qr_code_base64" alt="QR Code Registrazione Gruppo" class="border border-gray-300 rounded-md p-1 bg-white max-w-[150px] h-auto">
               </div>
               <BaseButton @click="handleDeleteToken" :is-loading="isLoadingAction" :disabled="isLoadingAction" variant="danger" size="sm" class="mt-4">
                 Elimina Link/Token e QR Code
               </BaseButton>
             </div>
             <div v-else class="text-gray-500 mb-4">
               Nessun link di registrazione attivo.
             </div>
             <BaseButton v-if="!currentGroup.registration_link" @click="handleGenerateToken" :is-loading="isLoadingAction" :disabled="isLoadingAction" variant="primary" size="sm">
               Genera Nuovo Link e QR Code
             </BaseButton>
              <p v-if="copySuccess" class="text-green-600 text-xs mt-2">Link copiato!</p> <!-- Messaggio aggiornato -->
              <p v-if="copyError" class="text-red-600 text-xs mt-2">Errore nella copia.</p>
            </div>
 
            <!-- Access Requests Card (Owner Only) -->
            <div v-if="isOwner" class="bg-white shadow-md rounded-lg p-6 mt-6">
              <h2 class="text-xl font-semibold mb-4">Richieste di Accesso Pendenti</h2>
 
              <!-- Loading Indicator for Requests -->
              <GlobalLoadingIndicator :is-loading="isLoadingRequests" />
 
              <!-- Requests Error Message -->
              <div v-if="requestsError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                <strong class="font-bold">Errore Richieste!</strong>
                <span class="block sm:inline"> {{ requestsError }}</span>
                 <span class="absolute top-0 bottom-0 right-0 px-4 py-3" @click="groupStore.requestsError = null">
                  <svg class="fill-current h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><title>Close</title><path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/></svg>
                </span>
              </div>
 
              <!-- No Pending Requests Message -->
              <div v-if="!isLoadingRequests && accessRequests.length === 0 && !requestsError" class="text-center text-gray-500 py-4">
                Nessuna richiesta di accesso pendente.
              </div>
 
              <!-- List of Requests -->
              <ul v-if="!isLoadingRequests && accessRequests.length > 0" class="divide-y divide-gray-200">
                <li v-for="request in accessRequests" :key="request.id" class="py-3 flex flex-col sm:flex-row justify-between items-start sm:items-center">
                  <div>
                    <p class="text-sm font-medium text-gray-900">
                      {{ request.requesting_teacher_name || `Docente ID: ${request.requesting_teacher}` }}
                    </p>
                    <p class="text-xs text-gray-500">
                      Richiesto il: {{ formatDate(request.requested_at) }} <!-- Corretto: usa requested_at -->
                    </p>
                  </div>
                  <div class="mt-2 sm:mt-0 flex space-x-2 flex-shrink-0">
                    <BaseButton
                      @click="handleRespondToRequest(request.id, true)"
                      :is-loading="isRespondingToRequest === request.id"
                      :disabled="!!isRespondingToRequest"
                      variant="success"
                      size="sm"
                    >
                      <CheckCircleIcon class="h-4 w-4 mr-1" />
                      Approva
                    </BaseButton>
                    <BaseButton
                      @click="handleRespondToRequest(request.id, false)"
                      :is-loading="isRespondingToRequest === request.id"
                      :disabled="!!isRespondingToRequest"
                      variant="danger"
                      size="sm"
                    >
                       <XCircleIcon class="h-4 w-4 mr-1" />
                      Rifiuta
                    </BaseButton>
                  </div>
                </li>
              </ul>
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
import { useAuthStore } from '@/stores/auth'; // Import auth store
import type { GroupAccessRequest } from '@/types/groups'; // Import type
import BaseButton from '@/components/common/BaseButton.vue';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import StudentSelectionModal from '@/components/groups/StudentSelectionModal.vue'; // Importa la modale
import { ClipboardDocumentIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/vue/24/outline'; // Import copy icon + check/x icons

const route = useRoute();
const router = useRouter();
const groupStore = useGroupStore();
const authStore = useAuthStore(); // Initialize auth store

// Use storeToRefs for reactive access to state and getters
const {
    currentGroup,
    currentGroupMembers,
    accessRequests, // Get access requests
    error,
    requestsError, // Get requests error
    isLoadingDetail,
    isLoadingRequests // Get requests loading state
} = storeToRefs(groupStore);
const { user } = storeToRefs(authStore); // Get user from auth store

const groupId = computed(() => Number(route.params.id));

// Separate loading states
const isLoadingInitial = ref(false); // For the initial load of group details + members
const isLoadingMembers = ref(false); // Specifically for member list refresh (if needed separately)
const isLoadingAction = ref(false); // For actions like add/remove student, token generation/deletion
const isRespondingToRequest = ref<number | null>(null); // Track which request is being responded to

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

        // Fetch access requests ONLY if the current user is the owner
        if (isOwner.value && currentGroup.value) {
             await groupStore.fetchAccessRequests(groupId.value);
        }
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

// Computed property to check if the logged-in user is the owner of the current group
const isOwner = computed(() => {
  // Make sure user and currentGroup are loaded and owner_id exists
  // Corretto: Usa 'owner' (che contiene l'ID) invece di 'owner_id' come restituito dal serializer
  return !!user.value && !!currentGroup.value && typeof currentGroup.value.owner === 'number' && user.value.id === currentGroup.value.owner;
});


// --- Methods ---

const goToEditGroup = () => {
  router.push({ name: 'GroupEdit', params: { id: groupId.value } });
};

const handleGenerateToken = async () => {
  if (!currentGroup.value) return;
  isLoadingAction.value = true;
  groupStore.clearError(); // Pulisce errori precedenti
  try {
    await groupStore.generateRegistrationToken(groupId.value);
    // Lo stato currentGroup viene aggiornato reattivamente dallo store,
    // ma per sicurezza e per forzare il refresh completo, ricarichiamo i dettagli.
    await groupStore.fetchGroupDetails(groupId.value); // Ripristinato fetch per forzare refresh
    // Rimosso console.log di debug
  } catch (err) {
      // L'errore dovrebbe essere gestito dallo store e mostrato nel template
      console.error("Errore durante la generazione del token:", err);
  } finally {
      isLoadingAction.value = false;
  }
};

const handleDeleteToken = async () => {
  // Modificato per controllare registration_link
  if (!currentGroup.value || !currentGroup.value.registration_link) return;
   if (window.confirm(`Sei sicuro di voler eliminare il token di registrazione per il gruppo "${currentGroup.value.name}"?`)) {
        isLoadingAction.value = true;
        await groupStore.deleteRegistrationToken(groupId.value);
        isLoadingAction.value = false;
        // Link e QR code in currentGroup si aggiornano reattivamente dallo store
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

const handleRespondToRequest = async (requestId: number, approve: boolean) => {
    if (!groupId.value) {
        console.error("Group ID is missing, cannot respond to request.");
        // Potresti voler mostrare un errore all'utente qui
        return;
    }
    isRespondingToRequest.value = requestId; // Set loading state for this specific request
    // Passa groupId.value come primo argomento all'azione dello store aggiornata
    await groupStore.respondToRequest(groupId.value, requestId, approve);
    isRespondingToRequest.value = null; // Reset loading state
    // The request list should update reactively via the store
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