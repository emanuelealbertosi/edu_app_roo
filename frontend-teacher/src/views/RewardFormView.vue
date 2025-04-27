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
          <option value="SPECIFIC">Disponibilità Specifica (Studenti o Gruppi)</option> <!-- Testo aggiornato -->
        </select>
      </div>

      <!-- Specific Availability Section -->
      <div v-if="rewardData.availability_type === 'SPECIFIC'" class="space-y-4 border border-gray-200 p-4 rounded-md">
         <label class="block text-sm font-medium text-gray-700 mb-2">Rendi disponibile specificamente per:</label>
         <div class="flex items-center space-x-4 mb-4">
            <label class="flex items-center">
                <input type="radio" v-model="specificTargetType" value="students" name="specificTargetType" class="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300">
                <span class="ml-2 text-sm text-gray-700">Studenti Singoli</span>
            </label>
            <label class="flex items-center">
                <input type="radio" v-model="specificTargetType" value="groups" name="specificTargetType" class="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300">
                <span class="ml-2 text-sm text-gray-700">Gruppi</span>
            </label>
        </div>

        <!-- Student Selection (Conditional) -->
        <div v-if="specificTargetType === 'students'">
            <h3 class="text-md font-medium text-gray-800 mb-2">Seleziona Studenti</h3>
            <div v-if="isLoadingStudents" class="text-gray-500 italic">Caricamento studenti...</div>
            <div v-else-if="studentsError" class="text-red-600">{{ studentsError }}</div>
            <!-- Blocco v-else-if / v-else per studenti - Struttura corretta -->
            <div v-else-if="allStudents.length > 0"> <!-- Questo div contiene il caso in cui ci sono studenti -->
               <BaseButton type="button" variant="outline" @click="isStudentModalOpen = true" class="mb-3">
                 Seleziona Studenti Specifici
               </BaseButton>
           <div class="text-sm text-neutral-dark">
             <span v-if="selectedStudentIds.length === 0">Nessuno studente selezionato.</span>
             <span v-else-if="selectedStudentIds.length === 1">1 studente selezionato.</span>
             <span v-else>{{ selectedStudentIds.length }} studenti selezionati.</span>
           </div> <!-- Chiusura del div per il testo degli studenti selezionati -->
           </div> <!-- Chiusura del div v-else-if="allStudents.length > 0" -->
           <div v-else class="text-center py-4 text-neutral-dark">Nessuno studente disponibile da selezionare.</div> <!-- Questo v-else segue direttamente il v-else-if -->
        </div> <!-- Chiusura del div v-if="specificTargetType === 'students'" -->

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
        </div> <!-- Chiusura del div v-if="specificTargetType === 'groups'" -->
     </div> <!-- Questo è il div di chiusura per Specific Availability Section -->

      <!-- Is Active Checkbox -->
      <div class="flex items-center mt-4"> <!-- Aggiunto margine sopra -->
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
    </form> <!-- Chiusura corretta del form -->

    <!-- Modale Selezione Studenti (fuori dal form) -->
    <StudentSelectionModal
      :show="isStudentModalOpen"
      :students="allStudents"
      :initial-selected-ids="selectedStudentIds"
      @close="isStudentModalOpen = false"
      @update:selectedIds="updateSelectedStudents"
    />
  </div> <!-- Chiusura del div principale del template -->
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive, watch } from 'vue'; // Aggiunto watch
import { useRoute, useRouter } from 'vue-router';
import { createReward, fetchRewardDetails, updateReward, makeRewardAvailable, revokeRewardAvailability, type RewardPayload } from '@/api/rewards'; // Corretto revokeAvailability -> revokeRewardAvailability
import { getMyStudents } from '@/api/students'; // Importa API studenti
import type { Student } from '@/types/users'; // Importa il tipo Student dalla sua fonte originale
import { useGroupStore } from '@/stores/groups'; // NUOVO: Importa store gruppi
import { storeToRefs } from 'pinia'; // NUOVO: Per usare storeToRefs
import type { StudentGroup } from '@/types/groups'; // NUOVO: Tipo gruppo
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

// --- NUOVO: Stato per Gruppi ---
const groupStore = useGroupStore();
const { groups: availableGroups, isLoadingList: isLoadingGroups, error: groupsError } = storeToRefs(groupStore);
const selectedGroupIds = ref<number[]>([]); // ID gruppi selezionati
const specificTargetType = ref<'students' | 'groups'>('students'); // Target per disponibilità specifica

// Usiamo reactive per l'oggetto del form
const rewardData = reactive<RewardFormData>({
  name: '',
  description: null,
  cost_points: 0,
  type: '',
  availability_type: 'ALL', // Default aggiornato a 'ALL'
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
  // Carica studenti e gruppi
  await Promise.all([loadAllStudents(), loadGroups()]);
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
      selectedStudentIds.value = [];
    }
    // Nota: Il caricamento iniziale non imposta i gruppi selezionati
    // perché l'API fetchRewardDetails non restituisce (ancora?) gli ID dei gruppi
    // a cui la ricompensa è disponibile. Questa logica andrà aggiunta se/quando
    // l'API verrà aggiornata per restituire anche `available_to_specific_groups`.
    // Per ora, la selezione dei gruppi parte sempre vuota in modifica.
    selectedGroupIds.value = [];
    // Imposta il target type iniziale in base a cosa è selezionato (solo studenti per ora)
    specificTargetType.value = selectedStudentIds.value.length > 0 ? 'students' : 'students'; // Default a students se nessuno è selezionato

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
        // TODO: Verificare se getMyStudents restituisce direttamente Student[] o { data: Student[] }
        // Se restituisce { data: Student[] }, la riga sotto dovrebbe essere:
        // const response = await getMyStudents();
        // allStudents.value = response.data;
        // Per ora assumiamo restituisca direttamente Student[] come suggerito dal nome
        // ma l'implementazione in students.ts restituisce Promise<{ data: Student[] }>
        // Correggo per usare .data
        const response = await getMyStudents();
        allStudents.value = response.data;
    } catch (err: any) {
        console.error("Errore nel caricamento degli studenti:", err);
        studentsError.value = err.response?.data?.detail || err.message || 'Errore nel caricamento della lista studenti.';
    } finally {
        isLoadingStudents.value = false;
    }
};

// --- NUOVO: Funzione per caricare i gruppi ---
const loadGroups = async () => {
   // Usa l'azione dello store, isLoadingGroups e groupsError sono già gestiti da storeToRefs
   await groupStore.fetchGroups();
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
    // NON includere specific_student_ids o group_ids nel payload di salvataggio base.
    // La disponibilità specifica verrà gestita separatamente.
    // template: null, // Rimuoviamo template, è opzionale
  };

  // Rimuovi specific_student_ids se presente (per sicurezza)
  delete payload.specific_student_ids;

  try {
    let savedRewardId: number | null = null;

    if (isEditing.value && rewardId.value) {
      await updateReward(rewardId.value, payload);
      savedRewardId = rewardId.value;
      // TODO: Implementare logica di revoca/aggiornamento disponibilità esistenti se necessario
      // Per ora, aggiungiamo solo le nuove selezioni senza rimuovere le vecchie in caso di modifica.
      // Una logica più completa richiederebbe di confrontare le selezioni precedenti e attuali.
      console.warn("Modifica ricompensa: la logica di aggiornamento della disponibilità specifica non rimuove le vecchie assegnazioni.");

    } else {
      // Creazione
      if (!payload.type) {
          throw new Error("Il tipo di ricompensa è obbligatorio.");
      }
      const createdReward = await createReward(payload as RewardPayload); // Ottieni la ricompensa creata
      savedRewardId = createdReward.id; // Salva l'ID della nuova ricompensa
    }

    // --- Gestione Disponibilità Specifica ---
    if (savedRewardId && rewardData.availability_type === 'SPECIFIC') {
        console.log(`Gestione disponibilità specifica per ricompensa ID: ${savedRewardId}, tipo target: ${specificTargetType.value}`);

        // TODO: Aggiungere logica per revocare disponibilità precedenti se necessario (in modifica)

        const availabilityPromises: Promise<any>[] = [];

        if (specificTargetType.value === 'students' && selectedStudentIds.value.length > 0) {
            console.log(`Rendo disponibile per studenti: ${selectedStudentIds.value.join(', ')}`);
            selectedStudentIds.value.forEach(studentId => {
                availabilityPromises.push(
                    makeRewardAvailable(savedRewardId!, { student_id: studentId }) // Ripristinato: student -> student_id
                        .catch(err => {
                            console.error(`Errore rendendo disponibile ricompensa ${savedRewardId} per studente ${studentId}:`, err);
                            // Accumula errore parziale? Per ora logga e continua.
                            error.value = (error.value ? error.value + '; ' : '') + `Errore assegnando a studente ${studentId}`;
                        })
                );
            });
        } else if (specificTargetType.value === 'groups' && selectedGroupIds.value.length > 0) {
            console.log(`Rendo disponibile per gruppi: ${selectedGroupIds.value.join(', ')}`);
            selectedGroupIds.value.forEach(groupId => {
                availabilityPromises.push(
                    makeRewardAvailable(savedRewardId!, { group_id: groupId }) // Ripristinato: group -> group_id
                         .catch(err => {
                            console.error(`Errore rendendo disponibile ricompensa ${savedRewardId} per gruppo ${groupId}:`, err);
                            // Accumula errore parziale? Per ora logga e continua.
                             error.value = (error.value ? error.value + '; ' : '') + `Errore assegnando a gruppo ${groupId}`;
                        })
                );
            });
        }

        if (availabilityPromises.length > 0) {
            console.log(`Eseguo ${availabilityPromises.length} chiamate per la disponibilità...`);
            await Promise.all(availabilityPromises);
            console.log("Chiamate disponibilità completate.");
        }
    } else if (savedRewardId && rewardData.availability_type === 'ALL') {
         // TODO: Se si passa da SPECIFIC a ALL, bisognerebbe revocare tutte le disponibilità specifiche esistenti.
         console.warn("Modifica ricompensa: la logica di aggiornamento non revoca le disponibilità specifiche precedenti quando si passa ad 'ALL'.");
    }
    // --- Fine Gestione Disponibilità Specifica ---


    // Se non ci sono stati errori parziali nella gestione disponibilità, reindirizza
    if (!error.value) {
        router.push({ name: 'rewards' }); // Torna alla lista
    } else {
        // Se ci sono stati errori parziali, non reindirizzare ma mostrali
        console.error("Errori parziali durante il salvataggio della disponibilità:", error.value);
        // L'errore è già impostato nel ref 'error', verrà mostrato nel template
    }

  } catch (err: any) {
    // Errore durante createReward o updateReward (errore principale)
    console.error("Errore durante il salvataggio della ricompensa (principale):", err);
    // Tenta di estrarre messaggi di errore specifici per campo dal payload base
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

// --- Watchers ---
// Resetta selezioni specifiche quando cambia il tipo di disponibilità
watch(() => rewardData.availability_type, (newType) => {
  if (newType !== 'SPECIFIC') {
    selectedStudentIds.value = [];
    selectedGroupIds.value = [];
    specificTargetType.value = 'students'; // Resetta anche il tipo di target
  }
});

// Resetta l'altra selezione quando cambia il tipo di target specifico
watch(specificTargetType, (newTarget) => {
    if (newTarget === 'students') {
        selectedGroupIds.value = [];
    } else if (newTarget === 'groups') {
        selectedStudentIds.value = [];
    }
});

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