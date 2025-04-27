<template>
  <BaseModal :show="show" @close="closeModal" title="Gestisci Disponibilità Ricompensa">
    <div v-if="!reward" class="p-4 text-center text-gray-500">
      Nessuna ricompensa selezionata.
    </div>
    <div v-else class="p-4 space-y-4">
      <h3 class="text-lg font-medium text-gray-900">
        Ricompensa: <span class="font-normal">{{ reward.name }}</span>
      </h3>

      <p class="text-sm text-gray-600">
        Qui puoi specificare quali studenti singoli o gruppi possono vedere e acquistare questa ricompensa.
      </p>

      <!-- Selettore Target (Studenti/Gruppi) -->
      <div class="flex items-center space-x-4 mb-4 border-b pb-4">
         <label class="flex items-center">
             <input type="radio" v-model="targetType" value="students" name="availabilityTargetType" class="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300">
             <span class="ml-2 text-sm text-gray-700">Studenti Singoli</span>
         </label>
         <label class="flex items-center">
             <input type="radio" v-model="targetType" value="groups" name="availabilityTargetType" class="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300">
             <span class="ml-2 text-sm text-gray-700">Gruppi</span>
         </label>
     </div>

      <!-- Sezione Studenti -->
      <div v-if="targetType === 'students'">
        <h4 class="text-md font-semibold text-gray-800 mb-2">Studenti Disponibili</h4>
        <!-- TODO: Implementare caricamento e selezione studenti -->
        <div v-if="isLoadingStudents" class="text-gray-500">Caricamento studenti...</div>
        <div v-else-if="studentsError" class="text-red-500">{{ studentsError }}</div>
        <div v-else>
          <!-- Lista Studenti con Checkbox -->
          <div v-for="student in allStudents" :key="student.id" class="flex items-center justify-between mb-2 p-2 border rounded hover:bg-gray-50">
             <span>{{ student.first_name }} {{ student.last_name }} ({{ student.student_code }})</span> <!-- CORRETTO: usa student_code -->
             <input
                type="checkbox"
                :checked="isStudentSelected(student.id)"
                @change="toggleStudentAvailability(student.id, $event)"
                :disabled="isUpdatingAvailability"
                class="form-checkbox h-5 w-5 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500 disabled:opacity-50"
             />
          </div>
           <div v-if="!allStudents.length" class="text-gray-500 italic">Nessuno studente trovato.</div>
        </div>
      </div>

      <!-- Sezione Gruppi -->
      <div v-if="targetType === 'groups'">
        <h4 class="text-md font-semibold text-gray-800 mb-2">Gruppi Disponibili</h4>
        <!-- TODO: Implementare caricamento e selezione gruppi -->
         <div v-if="isLoadingGroups" class="text-gray-500">Caricamento gruppi...</div>
         <div v-else-if="groupsError" class="text-red-500">{{ groupsError }}</div>
         <div v-else>
           <!-- Lista Gruppi con Checkbox -->
           <div v-for="group in availableGroups" :key="group.id" class="flex items-center justify-between mb-2 p-2 border rounded hover:bg-gray-50">
              <span>{{ group.name }} ({{ group.student_count ?? '?' }} membri)</span>
              <input
                 type="checkbox"
                 :checked="isGroupSelected(group.id)"
                 @change="toggleGroupAvailability(group.id, $event)"
                 :disabled="isUpdatingAvailability"
                 class="form-checkbox h-5 w-5 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500 disabled:opacity-50"
              />
           </div>
            <div v-if="!availableGroups.length" class="text-gray-500 italic">Nessun gruppo trovato.</div>
         </div>
      </div>

       <!-- Messaggi di Errore/Successo -->
       <div v-if="updateError" class="text-red-600 text-sm mt-2">{{ updateError }}</div>
       <div v-if="updateSuccess" class="text-green-600 text-sm mt-2">{{ updateSuccess }}</div>

    </div>
    <template #footer>
      <BaseButton variant="secondary" @click="closeModal">Chiudi</BaseButton>
      <!-- Non serve un pulsante Salva, le modifiche sono applicate on-the-fly -->
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import BaseModal from '@/components/common/BaseModal.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import type { Reward } from '@/api/rewards';
import { fetchStudents, type Student } from '@/api/students';
import { useGroupStore } from '@/stores/groups';
import { storeToRefs } from 'pinia';
import type { StudentGroup } from '@/types/groups';
import { makeRewardAvailable, revokeRewardAvailability, type MakeRewardAvailablePayload, type RevokeRewardAvailabilityPayload } from '@/api/rewards';

const props = defineProps<{
  show: boolean;
  reward: Reward | null;
}>();

const emit = defineEmits(['close', 'updated']);

const targetType = ref<'students' | 'groups'>('students');

// Stato Studenti
const allStudents = ref<Student[]>([]);
const isLoadingStudents = ref(false);
const studentsError = ref<string | null>(null);
const selectedStudentIds = ref<Set<number>>(new Set()); // Usiamo un Set per efficienza

// Stato Gruppi
const groupStore = useGroupStore();
const { groups: availableGroups, isLoadingList: isLoadingGroups, error: groupsError } = storeToRefs(groupStore);
const selectedGroupIds = ref<Set<number>>(new Set()); // Usiamo un Set

// Stato Aggiornamento Disponibilità
const isUpdatingAvailability = ref(false);
const updateError = ref<string | null>(null);
const updateSuccess = ref<string | null>(null);


// Carica studenti e gruppi quando la modale diventa visibile e c'è una ricompensa
watch(() => props.show, async (newShow) => {
  if (newShow && props.reward) {
    await loadInitialData();
  } else {
    // Reset state when modal closes
    resetState();
  }
});

const loadInitialData = async () => {
    if (!props.reward) return;

    isLoadingStudents.value = true;
    studentsError.value = null;
    // Non serve caricare i gruppi qui perché usiamo lo store che potrebbe essere già popolato
    // Ma assicuriamoci che sia stato chiamato fetchGroups almeno una volta
    // TODO: Aggiungere una prop 'loaded' allo store o controllare la lunghezza/stato
    // if (!groupStore.loaded) {
        await groupStore.fetchGroups(); // Chiamiamo comunque per sicurezza o aggiornamento
    // }

    try {
        allStudents.value = await fetchStudents();
        // Inizializza i Set con gli ID correnti dalla prop reward
        selectedStudentIds.value = new Set(props.reward.available_to_specific_students || []);
        selectedGroupIds.value = new Set(props.reward.available_to_specific_groups || []);
    } catch (err: any) {
        console.error("Errore caricamento studenti:", err);
        studentsError.value = "Impossibile caricare gli studenti.";
    } finally {
        isLoadingStudents.value = false;
    }
};


const resetState = () => {
    // allStudents.value = []; // Non resettare la lista studenti/gruppi, potrebbero servire subito dopo
    // availableGroups.value = []; // Lo store gestisce i gruppi
    selectedStudentIds.value.clear();
    selectedGroupIds.value.clear();
    targetType.value = 'students';
    updateError.value = null;
    updateSuccess.value = null;
    isUpdatingAvailability.value = false;
};

const closeModal = () => {
  emit('close');
};

// --- Logica Selezione ---
const isStudentSelected = (studentId: number): boolean => {
    return selectedStudentIds.value.has(studentId);
};

const isGroupSelected = (groupId: number): boolean => {
    return selectedGroupIds.value.has(groupId);
};

// --- Logica Aggiornamento Disponibilità ---
const toggleStudentAvailability = async (studentId: number, event: Event) => {
    if (!props.reward) return;
    const isChecked = (event.target as HTMLInputElement).checked;
    await updateAvailability({ student: studentId }, isChecked);
    if (!updateError.value) { // Aggiorna il Set solo se l'API ha successo
         isChecked ? selectedStudentIds.value.add(studentId) : selectedStudentIds.value.delete(studentId);
         selectedStudentIds.value = new Set(selectedStudentIds.value); // Forza reattività
    }
};

const toggleGroupAvailability = async (groupId: number, event: Event) => {
    if (!props.reward) return;
    const isChecked = (event.target as HTMLInputElement).checked;
    await updateAvailability({ group: groupId }, isChecked);
     if (!updateError.value) { // Aggiorna il Set solo se l'API ha successo
        isChecked ? selectedGroupIds.value.add(groupId) : selectedGroupIds.value.delete(groupId);
        selectedGroupIds.value = new Set(selectedGroupIds.value); // Forza reattività
     }
};

const updateAvailability = async (payload: MakeRewardAvailablePayload | RevokeRewardAvailabilityPayload, makeAvailable: boolean) => {
    if (!props.reward) return;

    isUpdatingAvailability.value = true;
    updateError.value = null;
    updateSuccess.value = null;
    const action = makeAvailable ? makeRewardAvailable : revokeRewardAvailability;
    const actionText = makeAvailable ? 'rendere disponibile' : 'revocare la disponibilità';
    const targetText = payload.student ? `studente ${payload.student}` : `gruppo ${payload.group}`;

    try {
        await action(props.reward.id, payload);
        updateSuccess.value = `Disponibilità ${makeAvailable ? 'impostata' : 'revocata'} per ${targetText}.`;
        emit('updated'); // Notifica il parent che qualcosa è cambiato
        // Pulisci messaggio successo dopo un po'
        setTimeout(() => updateSuccess.value = null, 3000);
    } catch (error: any) {
        console.error(`Errore nel ${actionText} la ricompensa per ${targetText}:`, error);
        updateError.value = `Errore: ${error.response?.data?.detail || error.message || 'Errore sconosciuto'}`;
         // Pulisci messaggio errore dopo un po'
        setTimeout(() => updateError.value = null, 5000);
    } finally {
        isUpdatingAvailability.value = false;
    }
};

</script>

<style scoped>
/* Stili aggiuntivi se necessari */
</style>