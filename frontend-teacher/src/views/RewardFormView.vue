<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-2xl font-semibold mb-6 bg-primary text-white px-4 py-2 rounded-md">
      Modifica Ricompensa <!-- Titolo fisso per la modifica -->
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

    <!-- Form Container -->
    <div v-else-if="rewardDataForForm" class="bg-white p-8 rounded-lg shadow-md max-w-3xl mx-auto"> <!-- Aggiunto v-else-if per assicurarsi che i dati siano caricati -->
        <!-- Sempre true qui -->
        <RewardForm
            :initial-data="rewardDataForForm"
            :is-saving="isSaving"
            :is-editing="true"
            @save="handleSave"
            @cancel="handleCancel"
        ></RewardForm>
    </div>
     <!-- Stato alternativo se non c'è errore ma i dati non sono pronti (improbabile con la logica attuale ma per sicurezza) -->
     <div v-else class="text-center py-10 text-gray-500">
        Dati ricompensa non disponibili.
     </div>

  </div> <!-- Chiusura del div principale del template -->
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'; // Rimosso reactive
import { useRoute, useRouter } from 'vue-router';
import { fetchRewardDetails, updateReward, makeRewardAvailable, revokeRewardAvailability, type RewardPayload } from '@/api/rewards';
// Importa solo ciò che serve alla vista
import RewardForm from '@/components/features/rewards/RewardForm.vue'; // Importa il componente form

// Interfaccia per i dati passati al form (può includere dati extra non nel payload base)
interface RewardDataForForm {
  name: string;
  description: string | null;
  cost_points: number;
  type: string;
  availability_type: string;
  is_active: boolean;
  metadata: Record<string, any> | null;
  available_to_specific_students?: number[]; // Campo letto dall'API
  available_to_specific_groups?: number[]; // Campo letto dall'API (ipotetico)
}


const route = useRoute();
const router = useRouter();

const rewardId = ref<number | null>(null);
// const isEditing = computed(() => !!rewardId.value); // Non più necessario, è sempre true
const isLoading = ref(false);
const isSaving = ref(false);
const error = ref<string | null>(null);

// Stato per i dati da passare al componente RewardForm
const rewardDataForForm = ref<RewardDataForForm | undefined>(undefined);


onMounted(async () => {
  const idParam = route.params.id;
  if (idParam && typeof idParam === 'string') {
    const id = Number(idParam);
    if (!isNaN(id)) {
      rewardId.value = id;
      await loadRewardData(id);
    } else {
      console.error("ID Ricompensa non valido:", idParam);
      error.value = "ID Ricompensa non valido.";
      // Potresti reindirizzare o mostrare un errore più permanente
      // router.push({ name: 'rewards' });
    }
  } else {
      console.error("Accesso a RewardFormView senza ID.");
      error.value = "Questa pagina è accessibile solo per la modifica di una ricompensa esistente.";
      // Reindirizza alla lista o mostra errore
      // router.push({ name: 'rewards' });
  }
});

const loadRewardData = async (id: number) => {
  isLoading.value = true;
  error.value = null;
  rewardDataForForm.value = undefined; // Resetta prima del caricamento
  try {
    const fetchedReward = await fetchRewardDetails(id);
    // Mappa i dati fetchati nel formato atteso da RewardForm
    rewardDataForForm.value = {
        name: fetchedReward.name,
        description: fetchedReward.description,
        cost_points: fetchedReward.cost_points,
        type: fetchedReward.type,
        availability_type: fetchedReward.availability_type,
        is_active: fetchedReward.is_active,
        metadata: fetchedReward.metadata || {},
        available_to_specific_students: fetchedReward.available_to_specific_students || [],
        // available_to_specific_groups: fetchedReward.available_to_specific_groups || [] // Aggiungere se l'API lo supporta
    };
    console.log("Dati caricati per il form:", rewardDataForForm.value);

  } catch (err: any) {
    console.error("Errore nel caricamento della ricompensa:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore nel caricamento dei dati della ricompensa.';
  } finally {
    isLoading.value = false;
  }
};


// Gestore per l'evento 'save' emesso da RewardForm
const handleSave = async (payload: { data: RewardPayload, specificStudents: number[], specificGroups: number[] }) => {
  if (!rewardId.value) {
      error.value = "ID Ricompensa mancante per l'aggiornamento.";
      return;
  }

  isSaving.value = true;
  error.value = null;

  try {
    // 1. Aggiorna i dati base della ricompensa
    await updateReward(rewardId.value, payload.data);
    console.log(`Ricompensa ${rewardId.value} aggiornata con i dati base.`);

    // 2. Gestisci la disponibilità specifica (logica semplificata - solo aggiunta)
    // ATTENZIONE: Questa logica semplificata potrebbe portare a duplicati o mancate revoche.
    // Una soluzione robusta richiederebbe di ottenere lo stato attuale e fare una diff.
    console.warn("Logica di aggiornamento disponibilità semplificata: verranno solo aggiunte le nuove selezioni.");

    const availabilityPromises: Promise<any>[] = [];

    if (payload.data.availability_type === 'SPECIFIC') {
        // Aggiungi studenti selezionati (solo se non già presenti? L'API potrebbe gestire duplicati)
        payload.specificStudents.forEach(studentId => {
            availabilityPromises.push(
                makeRewardAvailable(rewardId.value!, { student_id: studentId })
                    .catch(err => {
                        console.error(`Errore aggiungendo disponibilità studente ${studentId}:`, err);
                        // Non bloccare tutto, ma segnala l'errore parziale
                        error.value = (error.value ? error.value + '; ' : '') + `Errore assegnando a studente ${studentId}`;
                    })
            );
        });

        // Aggiungi gruppi selezionati
        payload.specificGroups.forEach(groupId => {
            availabilityPromises.push(
                makeRewardAvailable(rewardId.value!, { group_id: groupId })
                     .catch(err => {
                        console.error(`Errore aggiungendo disponibilità gruppo ${groupId}:`, err);
                         error.value = (error.value ? error.value + '; ' : '') + `Errore assegnando a gruppo ${groupId}`;
                    })
            );
        });
        // TODO: Aggiungere logica per REVOCARE studenti/gruppi deselezionati.
        // Questo richiederebbe di sapere quali erano selezionati PRIMA della modifica.
        // Potrebbe essere necessario passare lo stato iniziale a handleSave o ricaricarlo.

    } else if (payload.data.availability_type === 'ALL') {
        // TODO: Idealmente, qui si dovrebbero revocare TUTTE le disponibilità specifiche esistenti.
        console.warn("Passaggio ad 'ALL': non sono state revocate le disponibilità specifiche precedenti.");
        // Esempio (richiede API di revoca bulk o per ID):
        // const currentAvailability = await fetchRewardAvailability(rewardId.value); // API ipotetica
        // currentAvailability.students.forEach(sId => revokeRewardAvailability(rewardId.value, { student_id: sId }));
        // currentAvailability.groups.forEach(gId => revokeRewardAvailability(rewardId.value, { group_id: gId }));
    }

    if (availabilityPromises.length > 0) {
        console.log(`Eseguo ${availabilityPromises.length} chiamate per aggiornare la disponibilità...`);
        await Promise.all(availabilityPromises); // Attende il completamento di tutte le chiamate di aggiunta
        console.log("Chiamate disponibilità completate.");
    }

    // Se non ci sono stati errori *parziali* durante l'aggiornamento della disponibilità, reindirizza
    if (!error.value) {
        router.push({ name: 'rewards' }); // Torna alla lista
    } else {
        // Se ci sono stati errori parziali, l'utente rimane sulla pagina per vederli
        console.error("Errori parziali durante l'aggiornamento della disponibilità:", error.value);
    }

  } catch (err: any) {
    // Errore durante updateReward (errore principale, blocca il reindirizzamento)
    console.error("Errore durante l'aggiornamento della ricompensa (principale):", err);
    if (err.response?.data && typeof err.response.data === 'object') {
        const fieldErrors = Object.values(err.response.data).flat().join(' ');
        error.value = fieldErrors || err.response.data.detail || 'Errore di validazione.';
    } else {
        error.value = err.message || 'Errore sconosciuto durante il salvataggio.';
    }
  } finally {
    isSaving.value = false;
  }
};

// Gestore per l'evento 'cancel' emesso da RewardForm
const handleCancel = () => {
  router.push({ name: 'rewards' }); // Torna alla lista
};

</script>

<style scoped>
/* Stili specifici per la vista contenitore, se necessari */
</style>