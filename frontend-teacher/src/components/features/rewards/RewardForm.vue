<template>
  <form @submit.prevent="submitForm" class="space-y-6">
    <!-- Name -->
    <div>
      <label for="reward-name" class="block text-sm font-medium text-gray-700 mb-1">Nome Ricompensa</label>
      <input type="text" id="reward-name" v-model="formData.name" required
             class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
    </div>

    <!-- Description -->
    <div>
      <label for="reward-description" class="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
      <textarea id="reward-description" v-model="formData.description" rows="3"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"></textarea>
    </div>

    <!-- Cost Points -->
    <div>
      <label for="reward-cost_points" class="block text-sm font-medium text-gray-700 mb-1">Costo (Punti)</label>
      <input type="number" id="reward-cost_points" v-model.number="formData.cost_points" required min="0"
             class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
    </div>

    <!-- Type -->
    <div>
      <label for="reward-type" class="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
      <select id="reward-type" v-model="formData.type" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
        <option disabled value="">Seleziona un tipo</option>
        <option value="DIGITAL">Digitale (es. badge, item virtuale)</option>
        <option value="REAL_WORLD">Reale (consegna tracciata)</option>
      </select>
    </div>

    <!-- Availability Type -->
    <div>
      <label for="reward-availability_type" class="block text-sm font-medium text-gray-700 mb-1">Disponibilità</label>
      <select id="reward-availability_type" v-model="formData.availability_type" required @change="resetSpecificAvailability"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
        <option value="ALL">Tutti gli studenti</option>
        <option value="SPECIFIC">Disponibilità Specifica (Studenti o Gruppi)</option>
      </select>
    </div>

    <!-- Specific Availability Section -->
    <div v-if="formData.availability_type === 'SPECIFIC'" class="space-y-4 border border-gray-200 p-4 rounded-md">
       <label class="block text-sm font-medium text-gray-700 mb-2">Rendi disponibile specificamente per:</label>
       <div class="flex items-center space-x-4 mb-4">
          <label class="flex items-center">
              <input type="radio" v-model="specificTargetType" value="students" name="specificTargetType" @change="resetSpecificSelection" class="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300">
              <span class="ml-2 text-sm text-gray-700">Studenti Singoli</span>
          </label>
          <label class="flex items-center">
              <input type="radio" v-model="specificTargetType" value="groups" name="specificTargetType" @change="resetSpecificSelection" class="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300">
              <span class="ml-2 text-sm text-gray-700">Gruppi</span>
          </label>
      </div>

      <!-- Student Selection (Conditional) -->
      <div v-if="specificTargetType === 'students'">
          <h3 class="text-md font-medium text-gray-800 mb-2">Seleziona Studenti</h3>
          <div v-if="isLoadingStudents" class="text-gray-500 italic">Caricamento studenti...</div>
          <div v-else-if="studentsError" class="text-red-600">{{ studentsError }}</div>
          <div v-else-if="allStudents.length > 0">
             <BaseButton type="button" variant="secondary" @click="isStudentModalOpen = true" class="mb-3">
               Seleziona Studenti Specifici
             </BaseButton>
             <div class="text-sm text-neutral-dark">
               <span v-if="selectedStudentIds.length === 0">Nessuno studente selezionato.</span>
               <span v-else-if="selectedStudentIds.length === 1">1 studente selezionato.</span>
               <span v-else>{{ selectedStudentIds.length }} studenti selezionati.</span>
             </div>
          </div>
          <div v-else class="text-center py-4 text-neutral-dark">Nessuno studente disponibile da selezionare.</div>
      </div>

      <!-- Group Selection (Conditional) -->
      <div v-if="specificTargetType === 'groups'">
          <h3 class="text-md font-medium text-gray-800 mb-2">Seleziona Gruppi</h3>
          <div v-if="isLoadingGroups" class="text-gray-500 italic">Caricamento gruppi...</div>
          <div v-else-if="groupsError" class="text-red-600">{{ groupsError }}</div>
          <div v-else-if="availableGroups.length > 0">
              <label for="group-select" class="block text-sm font-medium text-gray-700 mb-1">Gruppi disponibili:</label>
              <select
                 id="group-select"
                 v-model="selectedGroupIds"
                 multiple
                 class="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 h-32 bg-white"
              >
                 <option v-for="group in availableGroups" :key="group.id" :value="group.id">
                     {{ group.name }} ({{ group.student_count ?? '?' }} membri)
                 </option>
              </select>
              <div class="text-sm text-neutral-dark mt-2">
                 <span v-if="selectedGroupIds.length === 0">Nessun gruppo selezionato.</span>
                 <span v-else-if="selectedGroupIds.length === 1">1 gruppo selezionato.</span>
                 <span v-else>{{ selectedGroupIds.length }} gruppi selezionati.</span>
              </div>
          </div>
          <div v-else class="text-center py-4 text-neutral-dark">Nessun gruppo trovato. <router-link :to="{ name: 'GroupsList' }" class="text-indigo-600 hover:underline">Gestisci Gruppi</router-link></div>
      </div>
    </div>

    <!-- Is Active Checkbox -->
    <div class="flex items-center mt-4">
      <input id="reward-is_active" type="checkbox" v-model="formData.is_active"
             class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
      <label for="reward-is_active" class="ml-2 block text-sm text-gray-900">
        Attiva (visibile nello shop studente)
      </label>
    </div>

    <!-- Form Actions -->
    <div class="flex justify-end space-x-3 border-t border-gray-200 pt-6">
      <button type="button" @click="cancelForm"
              class="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
        Annulla
      </button>
      <button type="submit" :disabled="isSaving"
              :class="['py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
                       isSaving ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700']">
        {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche' : 'Crea Ricompensa') }}
      </button>
    </div>

    <!-- Modale Selezione Studenti (necessita di essere gestita dal componente padre o passata via slot/props) -->
     <StudentSelectionModal
       :show="isStudentModalOpen"
       :students="allStudents"
       :initial-selected-ids="selectedStudentIds"
       @close="isStudentModalOpen = false"
       @update:selectedIds="updateSelectedStudents"
     />
  </form>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted } from 'vue';
import type { RewardPayload } from '@/api/rewards'; // Usiamo il tipo Payload per coerenza
import { getMyStudents } from '@/api/students';
import type { Student } from '@/types/users';
import { useGroupStore } from '@/stores/groups';
import { storeToRefs } from 'pinia';
import type { StudentGroup } from '@/types/groups';
import BaseButton from '@/components/common/BaseButton.vue';
import StudentSelectionModal from '@/components/features/assignment/StudentSelectionModal.vue';

// Interfaccia per i dati del form interno
interface RewardFormData {
  name: string;
  description: string | null;
  cost_points: number;
  type: string;
  availability_type: string;
  is_active: boolean;
  metadata: Record<string, any> | null; // Manteniamo metadata se serve
}

// Props
const props = defineProps<{
  initialData?: Partial<RewardFormData> & { available_to_specific_students?: number[], available_to_specific_groups?: number[] }; // Dati iniziali per la modifica, inclusi ID specifici
  isSaving: boolean; // Stato di salvataggio gestito dal padre
  isEditing: boolean; // Indica se siamo in modalità modifica
}>();

// Emits
const emit = defineEmits<{
  (e: 'save', payload: { data: RewardPayload, specificStudents: number[], specificGroups: number[] }): void;
  (e: 'cancel'): void;
}>();

// Stato interno del form
const formData = reactive<RewardFormData>({
  name: '',
  description: null,
  cost_points: 0,
  type: '',
  availability_type: 'ALL',
  is_active: true,
  metadata: {},
  ...props.initialData // Sovrascrive i default con i dati iniziali se forniti
});

// Stato per la selezione specifica
const specificTargetType = ref<'students' | 'groups'>('students');
const selectedStudentIds = ref<number[]>([]);
const selectedGroupIds = ref<number[]>([]);

// Stato per caricamento studenti e gruppi (gestito internamente per ora)
const isLoadingStudents = ref(false);
const studentsError = ref<string | null>(null);
const allStudents = ref<Student[]>([]);
const isStudentModalOpen = ref(false);

const groupStore = useGroupStore();
const { groups: availableGroups, isLoadingList: isLoadingGroups, error: groupsError } = storeToRefs(groupStore);

// Carica studenti e gruppi al montaggio del componente form
onMounted(async () => {
  await Promise.all([loadAllStudents(), loadGroups()]);
  // Se siamo in modifica, popola le selezioni iniziali dai props
  if (props.isEditing && props.initialData) {
      if (props.initialData.availability_type === 'SPECIFIC') {
          selectedStudentIds.value = props.initialData.available_to_specific_students || [];
          selectedGroupIds.value = props.initialData.available_to_specific_groups || []; // Assumendo che initialData possa contenerlo

          // Determina il tipo di target iniziale basandosi su cosa è popolato
          if (selectedGroupIds.value.length > 0) {
              specificTargetType.value = 'groups';
          } else if (selectedStudentIds.value.length > 0) {
              specificTargetType.value = 'students';
          } else {
              specificTargetType.value = 'students'; // Default se entrambi vuoti
          }
      } else {
          // Se availability è ALL, assicurati che le selezioni siano vuote
          resetSpecificAvailability();
      }
  }
});


const loadAllStudents = async () => {
    isLoadingStudents.value = true;
    studentsError.value = null;
    try {
        const response = await getMyStudents();
        allStudents.value = response.data;
    } catch (err: any) {
        console.error("Errore caricamento studenti nel form:", err);
        studentsError.value = err.response?.data?.detail || err.message || 'Errore caricamento studenti.';
    } finally {
        isLoadingStudents.value = false;
    }
};

const loadGroups = async () => {
   // Usa l'azione dello store, isLoadingGroups e groupsError sono già gestiti da storeToRefs
   await groupStore.fetchGroups();
};


const updateSelectedStudents = (newSelectedIds: number[]) => {
    selectedStudentIds.value = newSelectedIds;
};

// Watchers per resettare le selezioni
watch(() => formData.availability_type, (newType) => {
  if (newType !== 'SPECIFIC') {
    resetSpecificAvailability();
  }
});

watch(specificTargetType, () => {
    resetSpecificSelection();
});

function resetSpecificAvailability() {
    selectedStudentIds.value = [];
    selectedGroupIds.value = [];
    specificTargetType.value = 'students';
}

function resetSpecificSelection() {
    if (specificTargetType.value === 'students') {
        selectedGroupIds.value = [];
    } else {
        selectedStudentIds.value = [];
    }
}

// Gestione submit
const submitForm = () => {
  // Prepara il payload base
  const payloadData: RewardPayload = {
    name: formData.name,
    description: formData.description,
    cost_points: Number(formData.cost_points) || 0,
    type: formData.type,
    availability_type: formData.availability_type,
    is_active: formData.is_active,
    ...(formData.metadata && Object.keys(formData.metadata).length > 0 && { metadata: formData.metadata }),
    // Non includere specific_student_ids o group_ids qui
  };

  // Emetti l'evento save con i dati del form e le selezioni specifiche
  emit('save', {
      data: payloadData,
      specificStudents: formData.availability_type === 'SPECIFIC' && specificTargetType.value === 'students' ? selectedStudentIds.value : [],
      specificGroups: formData.availability_type === 'SPECIFIC' && specificTargetType.value === 'groups' ? selectedGroupIds.value : []
  });
};

// Gestione annulla
const cancelForm = () => {
  emit('cancel');
};

// Watch per aggiornare formData quando initialData cambia (utile se il padre ricarica i dati)
watch(() => props.initialData, (newData) => {
    if (newData) {
        Object.assign(formData, newData);
        // Aggiorna anche le selezioni specifiche se siamo in modifica
        if (props.isEditing) {
            if (newData.availability_type === 'SPECIFIC') {
                selectedStudentIds.value = newData.available_to_specific_students || [];
                selectedGroupIds.value = newData.available_to_specific_groups || [];
                 if (selectedGroupIds.value.length > 0) {
                    specificTargetType.value = 'groups';
                } else if (selectedStudentIds.value.length > 0) {
                    specificTargetType.value = 'students';
                } else {
                    specificTargetType.value = 'students';
                }
            } else {
                resetSpecificAvailability();
            }
        }
    }
}, { deep: true }); // Usa deep watch per oggetti

</script>

<style scoped>
/* Stili specifici se necessari */
select[multiple] {
  /* appearance: none; */
}
select[multiple] option {
  padding: 0.5rem;
}
</style>