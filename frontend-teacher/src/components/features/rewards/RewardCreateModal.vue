<template>
  <!-- Base Modal Structure (esempio semplice, potrebbe essere un componente BaseModal riutilizzabile) -->
  <div v-if="show" class="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"> <!-- Limit height and enable scroll -->
      <!-- Modal Header -->
      <div class="flex justify-between items-center p-4 border-b border-gray-200">
        <h2 class="text-xl font-semibold">Crea Nuova Ricompensa</h2>
        <button @click="closeModal" class="text-gray-500 hover:text-gray-700">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6">
        <!-- Error Display -->
        <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong class="font-bold">Errore!</strong>
          <span class="block sm:inline"> {{ error }}</span>
        </div>

        <!-- Reward Form Component -->
        <!-- Modalità creazione -->
        <RewardForm
          :is-saving="isSaving"
          :is-editing="false"
          @save="handleSave"
          @cancel="closeModal"
        ></RewardForm>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { createReward, makeRewardAvailable, type RewardPayload } from '@/api/rewards';
import RewardForm from './RewardForm.vue'; // Importa il componente form

// Props
const props = defineProps<{
  show: boolean; // Controlla la visibilità della modale
}>();

// Emits
const emit = defineEmits<{
  (e: 'close'): void; // Evento per chiudere la modale
  (e: 'created'): void; // Evento emesso dopo la creazione con successo
}>();

// Stato interno
const isSaving = ref(false);
const error = ref<string | null>(null);

// Gestore salvataggio dal form
const handleSave = async (payload: { data: RewardPayload, specificStudents: number[], specificGroups: number[] }) => {
  isSaving.value = true;
  error.value = null;

  try {
    // 1. Crea la ricompensa base
    if (!payload.data.type) {
        throw new Error("Il tipo di ricompensa è obbligatorio.");
    }
    const createdReward = await createReward(payload.data);
    const savedRewardId = createdReward.id;
    console.log(`Ricompensa creata con ID: ${savedRewardId}`);

    // 2. Gestisci la disponibilità specifica (se necessaria)
    if (savedRewardId && payload.data.availability_type === 'SPECIFIC') {
        console.log(`Gestione disponibilità specifica per nuova ricompensa ID: ${savedRewardId}`);
        const availabilityPromises: Promise<any>[] = [];

        // Aggiungi studenti selezionati
        payload.specificStudents.forEach(studentId => {
            availabilityPromises.push(
                makeRewardAvailable(savedRewardId, { student_id: studentId })
                    .catch(err => {
                        console.error(`Errore aggiungendo disponibilità studente ${studentId} per nuova ricompensa:`, err);
                        error.value = (error.value ? error.value + '; ' : '') + `Errore assegnando a studente ${studentId}`;
                    })
            );
        });

        // Aggiungi gruppi selezionati
        payload.specificGroups.forEach(groupId => {
            availabilityPromises.push(
                makeRewardAvailable(savedRewardId, { group_id: groupId })
                     .catch(err => {
                        console.error(`Errore aggiungendo disponibilità gruppo ${groupId} per nuova ricompensa:`, err);
                         error.value = (error.value ? error.value + '; ' : '') + `Errore assegnando a gruppo ${groupId}`;
                    })
            );
        });

        if (availabilityPromises.length > 0) {
            console.log(`Eseguo ${availabilityPromises.length} chiamate per la disponibilità...`);
            await Promise.all(availabilityPromises);
            console.log("Chiamate disponibilità completate.");
        }
    }

    // Se non ci sono stati errori parziali, chiudi la modale ed emetti evento
    if (!error.value) {
        emit('created'); // Segnala al padre che la creazione è avvenuta
        closeModal();     // Chiudi la modale
    }
    // Se ci sono stati errori parziali, rimani sulla modale per mostrarli

  } catch (err: any) {
    // Errore durante createReward (principale)
    console.error("Errore durante la creazione della ricompensa:", err);
    if (err.response?.data && typeof err.response.data === 'object') {
        const fieldErrors = Object.values(err.response.data).flat().join(' ');
        error.value = fieldErrors || err.response.data.detail || 'Errore di validazione.';
    } else {
        error.value = err.message || 'Errore sconosciuto durante la creazione.';
    }
  } finally {
    isSaving.value = false;
  }
};

// Funzione per chiudere la modale
const closeModal = () => {
  error.value = null; // Resetta l'errore alla chiusura
  emit('close');
};

</script>

<style scoped>
/* Stili aggiuntivi per la modale se necessario */
</style>