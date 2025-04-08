<template>
  <div class="reward-form-view">
    <h1>{{ isEditing ? 'Modifica Ricompensa' : 'Crea Nuova Ricompensa' }}</h1>
    <div v-if="isLoading" class="loading">Caricamento dati ricompensa...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>

    <form v-else @submit.prevent="saveReward">
      <div class="form-group">
        <label for="name">Nome:</label>
        <input type="text" id="name" v-model="rewardData.name" required />
      </div>
      <div class="form-group">
        <label for="description">Descrizione:</label>
        <textarea id="description" v-model="rewardData.description"></textarea>
      </div>
      <div class="form-group">
        <label for="cost_points">Costo (Punti):</label>
        <input type="number" id="cost_points" v-model.number="rewardData.cost_points" required min="0" />
      </div>
       <div class="form-group">
        <label for="type">Tipo:</label>
        <select id="type" v-model="rewardData.type" required>
            <option disabled value="">Seleziona un tipo</option>
            <!-- Valori aggiornati per corrispondere a RewardTemplate.RewardType -->
            <option value="DIGITAL">Digitale (es. badge, item virtuale)</option>
            <option value="REAL_WORLD">Reale (consegna tracciata)</option>
        </select>
      </div>
       <div class="form-group">
        <label for="availability_type">Disponibilità:</label>
        <select id="availability_type" v-model="rewardData.availability_type" required>
            <option value="ALL">Tutti gli studenti</option> <!-- Corretto valore -->
            <option value="SPECIFIC">Studenti Specifici</option> <!-- Corretto valore -->
        </select>
        <!-- TODO: Aggiungere UI per selezionare studenti specifici se availability_type === 'SPECIFIC_STUDENTS' -->
      </div>
       <div class="form-group">
        <label for="is_active">
            <input type="checkbox" id="is_active" v-model="rewardData.is_active" />
            Attiva (visibile nello shop)
        </label>
      </div>

      <!-- TODO: Aggiungere gestione metadata -->

      <div class="form-actions">
        <button type="submit" :disabled="isSaving" class="btn btn-success">
          {{ isSaving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche' : 'Crea Ricompensa') }}
        </button>
        <button type="button" @click="cancel" class="btn btn-secondary">Annulla</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createReward, fetchRewardDetails, updateReward, type RewardPayload } from '@/api/rewards';

// Interfaccia per i dati del form
interface RewardFormData {
  name: string;
  description: string | null;
  cost_points: number;
  type: string;
  availability_type: string;
  is_active: boolean;
  metadata: Record<string, any> | null;
  // specific_student_ids: number[]; // Da aggiungere
}

const route = useRoute();
const router = useRouter();

const rewardId = ref<number | null>(null);
const isEditing = computed(() => !!rewardId.value);
const isLoading = ref(false);
const isSaving = ref(false);
const error = ref<string | null>(null);

// Usiamo reactive per l'oggetto del form
const rewardData = reactive<RewardFormData>({
  name: '',
  description: null,
  cost_points: 0,
  type: '',
  availability_type: 'ALL_STUDENTS', // Default
  is_active: true,
  metadata: {},
  // specific_student_ids: [],
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
    // TODO: Caricare specific_student_ids se availability_type è SPECIFIC
  } catch (err: any) {
    console.error("Errore nel caricamento della ricompensa:", err);
    error.value = err.response?.data?.detail || err.message || 'Errore nel caricamento dei dati della ricompensa.';
  } finally {
    isLoading.value = false;
  }
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
    // TODO: Includere specific_student_ids se availability_type è SPECIFIC
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
    error.value = err.response?.data?.detail || err.message || 'Errore durante il salvataggio della ricompensa.';
     if (err.response?.data && typeof err.response.data === 'object') {
         console.log("Dettagli errore API:", err.response.data);
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
/* Stili simili a QuizFormView/PathwayFormView */
.reward-form-view {
  padding: 20px;
  max-width: 700px;
  margin: auto;
}
.form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
.form-group input[type="text"],
.form-group input[type="number"],
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.form-group input[type="checkbox"] {
    width: auto;
    margin-right: 5px;
}
.form-group textarea {
  min-height: 100px;
  resize: vertical;
}
.form-actions {
  margin-top: 20px;
}
.form-actions button {
  padding: 10px 15px;
  margin-right: 10px;
  cursor: pointer;
  border-radius: 4px;
  border: none;
}
.form-actions button[type="submit"] {
  background-color: #4CAF50;
  color: white;
}
.form-actions button[type="submit"]:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}
.form-actions button[type="button"] {
  background-color: #f44336;
  color: white;
}
.error-message {
  color: red;
  margin-top: 10px;
  font-weight: bold;
}
.loading {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
</style>