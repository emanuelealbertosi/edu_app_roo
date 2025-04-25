<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-2xl font-semibold mb-6 bg-primary text-white px-4 py-2 rounded-md">
      {{ isEditing ? 'Modifica Ricompensa' : 'Crea Nuova Ricompensa' }}
    </h1>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-10">
      <p class="text-gray-500">Caricamento dati ricompensa...</p>
      <!-- Optional: Add a spinner here -->
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <!-- Form -->
    <form v-else @submit.prevent="saveReward" class="space-y-6 bg-white p-8 rounded-lg shadow-md max-w-3xl mx-auto">
      <!-- Name -->
      <div>
        <label for="name" class="block text-sm font-medium text-gray-700 mb-1">Nome Ricompensa</label>
        <input type="text" id="name" v-model="rewardData.name" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
      </div>

      <!-- Description -->
      <div>
        <label for="description" class="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
        <textarea id="description" v-model="rewardData.description" rows="3"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"></textarea>
      </div>

      <!-- Cost Points -->
      <div>
        <label for="cost_points" class="block text-sm font-medium text-gray-700 mb-1">Costo (Punti)</label>
        <input type="number" id="cost_points" v-model.number="rewardData.cost_points" required min="0"
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
      </div>

      <!-- Type -->
      <div>
        <label for="type" class="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
        <select id="type" v-model="rewardData.type" required
                class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
          <option disabled value="">Seleziona un tipo</option>
          <option value="DIGITAL">Digitale (es. badge, item virtuale)</option>
          <option value="REAL_WORLD">Reale (consegna tracciata)</option>
        </select>
      </div>

      <!-- Availability Type -->
      <div>
        <label for="availability_type" class="block text-sm font-medium text-gray-700 mb-1">Disponibilità</label>
        <select id="availability_type" v-model="rewardData.availability_type" required
                class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
          <option value="ALL">Tutti gli studenti</option>
          <option value="SPECIFIC">Studenti Specifici</option>
        </select>
      </div>

      <!-- Specific Students Section (con Modale) -->
      <div v-if="rewardData.availability_type === 'SPECIFIC'">
        <label class="block text-sm font-medium text-gray-700 mb-2">Studenti Specifici</label>
        <div v-if="isLoadingStudents" class="text-gray-500 italic">Caricamento studenti...</div>
        <div v-else-if="studentsError" class="text-red-600">{{ studentsError }}</div>
        <div v-else-if="allStudents.length > 0">
           <BaseButton type="button" variant="outline" @click="isStudentModalOpen = true" class="mb-3"> <!-- Aggiunto type="button" -->
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

      <!-- Is Active Checkbox -->
      <div class="flex items-center">
        <input id="is_active" type="checkbox" v-model="rewardData.is_active"
               class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
        <label for="is_active" class="ml-2 block text-sm text-gray-900">
          Attiva (visibile nello shop studente)
        </label>
      </div>

      <!-- TODO: Aggiungere gestione metadata (potrebbe richiedere un componente dedicato) -->
      <!-- <div class="border-t border-gray-200 pt-6">
        <h3 class="text-lg font-medium text-gray-900">Metadati (Opzionale)</h3>
         Qui si potrebbe inserire un editor JSON o campi specifici
      </div> -->

      <!-- Form Actions -->
      <div class="flex justify-end space-x-3 border-t border-gray-200 pt-6">
        <button type="button" @click="cancel"
                class="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
          Annulla
        </button>
        <button type="submit" :disabled="isSaving"
                :class="['py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
                         isSaving ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700']">
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche' : 'Crea Ricompensa') }}
        </button>
      </div>
    </form>

    <!-- Modale Selezione Studenti -->
    <StudentSelectionModal
      :show="isStudentModalOpen"
      :students="allStudents"
      :initial-selected-ids="selectedStudentIds"
      @close="isStudentModalOpen = false"
      @update:selectedIds="updateSelectedStudents"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createReward, fetchRewardDetails, updateReward, type RewardPayload } from '@/api/rewards';
import { fetchStudents, type Student } from '@/api/students'; // Importa API studenti
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton
import StudentSelectionModal from '@/components/features/assignment/StudentSelectionModal.vue'; // Importa la modale

// Interfaccia per i dati del form
interface RewardFormData {
  name: string;
  description: string | null;
  cost_points: number;
  type: string;
  availability_type: string;
  is_active: boolean;
  metadata: Record<string, any> | null;
  available_to_specific_students?: number[]; // Campo atteso dall'API in lettura
}

const route = useRoute();
const router = useRouter();

const rewardId = ref<number | null>(null);
const isEditing = computed(() => !!rewardId.value);
const isLoading = ref(false);
const isSaving = ref(false);
const error = ref<string | null>(null);
const studentsError = ref<string | null>(null); // Errore caricamento studenti
const isLoadingStudents = ref(false); // Loading studenti
const allStudents = ref<Student[]>([]); // Lista di tutti gli studenti del docente
const selectedStudentIds = ref<number[]>([]); // ID studenti selezionati nel form

const isStudentModalOpen = ref(false); // Stato per la modale

// Usiamo reactive per l'oggetto del form
const rewardData = reactive<RewardFormData>({
  name: '',
  description: null,
  cost_points: 0,
  type: '',
  availability_type: 'ALL_STUDENTS', // Default
  is_active: true,
  metadata: {},
  // available_to_specific_students non serve qui, è solo in lettura
});

// TODO: Caricare tipi da backend o definire costanti
// const rewardTypes = [...]
// const availabilityTypes = [...]

onMounted(async () => {
  const idParam = route.params.id;
  if (idParam) {
    rewardId.value = Number(idParam);
    if (!isNaN(rewardId.value)) {
      await loadRewardData(rewardId.value);
    } else {
      console.error("ID Ricompensa non valido:", idParam);
      error.value = "ID Ricompensa non valido.";
      rewardId.value = null;
    }
  }
  // Carica anche la lista studenti
  await loadAllStudents();
});

const loadRewardData = async (id: number) => {
  isLoading.value = true;
  error.value = null;
  try {
    const fetchedReward = await fetchRewardDetails(id);
    rewardData.name = fetchedReward.name;
    rewardData.description = fetchedReward.description;
    rewardData.cost_points = fetchedReward.cost_points;
    rewardData.type = fetchedReward.type;
    rewardData.availability_type = fetchedReward.availability_type;
    rewardData.is_active = fetchedReward.is_active;
    rewardData.metadata = fetchedReward.metadata || {};
    // Popola gli studenti selezionati se la modalità è SPECIFIC
    if (fetchedReward.availability_type === 'SPECIFIC') {
      // Assumiamo che l'API restituisca gli ID in available_to_specific_students
      selectedStudentIds.value = fetchedReward.available_to_specific_students || [];
    } else {
      selectedStudentIds.value = []; // Resetta se non è SPECIFIC
    }
  } catch (err: any) {
    console.error("Errore nel caricamento della ricompensa:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore nel caricamento dei dati della ricompensa.';
  } finally {
    isLoading.value = false;
  }
};

// Funzione per caricare la lista di tutti gli studenti
const loadAllStudents = async () => {
    isLoadingStudents.value = true;
    studentsError.value = null;
    try {
        allStudents.value = await fetchStudents();
    } catch (err: any) {
        console.error("Errore nel caricamento degli studenti:", err);
        studentsError.value = err.response?.data?.detail || err.message || 'Errore nel caricamento della lista studenti.';
    } finally {
        isLoadingStudents.value = false;
    }
};

// Funzione per aggiornare gli studenti selezionati dalla modale
const updateSelectedStudents = (newSelectedIds: number[]) => {
    selectedStudentIds.value = newSelectedIds;
};

const saveReward = async () => {
  isSaving.value = true;
  error.value = null;

  // Prepara il payload
  const payload: Partial<RewardPayload> = {
    name: rewardData.name,
    description: rewardData.description,
    cost_points: Number(rewardData.cost_points) || 0, // Forza conversione a numero
    type: rewardData.type,
    availability_type: rewardData.availability_type,
    is_active: rewardData.is_active,
    // Ometti metadata se vuoto, altrimenti invialo
    ...(rewardData.metadata && Object.keys(rewardData.metadata).length > 0 && { metadata: rewardData.metadata }),
    // Includi specific_student_ids solo se availability_type è SPECIFIC
    ...(rewardData.availability_type === 'SPECIFIC' && { specific_student_ids: selectedStudentIds.value }),
    // template: null, // Rimuoviamo template, è opzionale
  };

  try {
    if (isEditing.value && rewardId.value) {
      await updateReward(rewardId.value, payload);
    } else {
      // Assicurati che i campi obbligatori per la creazione siano presenti
      if (!payload.type) {
          throw new Error("Il tipo di ricompensa è obbligatorio.");
      }
      await createReward(payload as RewardPayload); // Cast a RewardPayload completo
    }
    router.push({ name: 'rewards' }); // Torna alla lista
  } catch (err: any) {
    console.error("Errore durante il salvataggio della ricompensa:", err);
    // Tenta di estrarre messaggi di errore specifici per campo
    if (err.response?.data && typeof err.response.data === 'object') {
        console.error("Dettagli errore API:", err.response.data);
        // Cerca errori specifici (es. per specific_student_ids)
        const fieldErrors = Object.values(err.response.data).flat().join(' '); // Concatena tutti i messaggi di errore
        error.value = fieldErrors || err.response.data.detail || 'Errore di validazione. Controlla i campi.';
    } else {
        // Errore generico
        error.value = err.message || 'Errore sconosciuto durante il salvataggio della ricompensa.';
    }
  } finally {
    isSaving.value = false;
  }
};

const cancel = () => {
  router.push({ name: 'rewards' }); // Torna alla lista
};

</script>

<style scoped>
/* Stili specifici rimasti o aggiunti se necessario.
   La maggior parte dello stile è ora gestita da Tailwind. */

/* Aggiusta leggermente l'aspetto del select multiplo se necessario */
select[multiple] {
  /* Esempio: rimuovere l'aspetto nativo se non piace */
  /* appearance: none; */
}

select[multiple] option {
  padding: 0.5rem; /* Aumenta padding per leggibilità */
}
</style>