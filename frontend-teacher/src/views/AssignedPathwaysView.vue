<template>
  <div class="assigned-pathways-view">
    <h1>Percorsi Assegnati (Istanze)</h1>
    <p>Qui puoi visualizzare le istanze concrete dei percorsi che hai assegnato.</p>

    <div v-if="isLoading" class="loading">Caricamento percorsi assegnati...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento dei percorsi assegnati: {{ error }}
    </div>
    <div v-else-if="assignedPathways.length > 0" class="pathways-list">
      <table>
        <thead>
          <tr>
            <th>Titolo Istanza</th>
            <th>Descrizione</th>
            <th>Template Sorgente</th>
            <th>Creato il</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <!-- Modificato tbody per usare template e gestire righe multiple per percorso -->
        <template v-for="pathway in assignedPathways" :key="pathway.id">
          <tbody> <!-- Aggiunto tbody per raggruppare le righe di un percorso -->
            <tr> <!-- Riga principale del percorso -->
              <td>{{ pathway.title }}</td>
              <td>{{ pathway.description || '-' }}</td>
              <td>{{ pathway.source_template ? `ID: ${pathway.source_template}` : 'Nessuno (Creato manualmente)' }}</td>
              <td>{{ new Date(pathway.created_at).toLocaleDateString() }}</td>
              <td>
                <button @click="toggleAssignments(pathway.id)" class="btn btn-secondary btn-sm">
                   {{ selectedPathwayId === pathway.id ? 'Nascondi' : 'Visualizza' }} Assegnazioni
                </button>
              </td>
            </tr>
            <!-- Riga per i dettagli (sempre presente ma contenuto condizionale) -->
            <tr>
              <td :colspan="5">
                <!-- Contenuto visibile solo se selezionato -->
                <div v-if="selectedPathwayId === pathway.id"> <!-- v-if spostato qui -->
                  <div v-if="isLoadingAssignments" class="loading small">Caricamento assegnazioni...</div>
                  <div v-else-if="assignmentsError" class="error-message small">Errore: {{ assignmentsError }}</div>
                  <div v-else-if="selectedPathwayAssignments">
                    <!-- Sezione Statistiche -->
                    <div class="stats-section mb-3 p-2 border-b">
                      <span class="mr-4"><strong>Assegnati:</strong> {{ selectedPathwayAssignments.stats.assigned_count }}</span>
                      <span class="mr-4"><strong>Iniziati:</strong> {{ selectedPathwayAssignments.stats.started_count }}</span>
                      <span><strong>Completati:</strong> {{ selectedPathwayAssignments.stats.completed_count }}</span>
                    </div>
                    <!-- Sezione Elenco Studenti -->
                    <h4 class="text-md font-semibold mt-2 mb-1">Studenti Assegnati:</h4>
                    <ul v-if="selectedPathwayAssignments.assignments.length > 0" class="assignment-list">
                      <li v-for="assignment in selectedPathwayAssignments.assignments" :key="assignment.id">
                        <span>
                           <router-link
                            :to="{ name: 'student-detail', params: { id: assignment.student_id } }"
                            class="text-blue-600 hover:underline"
                          >
                            <strong>{{ assignment.student_full_name }}</strong>
                           </router-link>
                            ({{ assignment.student_username }})
                          - Ass: {{ new Date(assignment.assigned_at).toLocaleDateString() }}
                        </span>
                        <button
                          @click="handleUnassignPathway(assignment.id, pathway.id)"
                          class="btn btn-danger btn-xs ml-2"
                          :disabled="isUnassigning === assignment.id"
                        >
                          {{ isUnassigning === assignment.id ? '...' : 'Disassegna' }}
                        </button>
                      </li>
                    </ul>
                    <p v-else class="no-assignments">Nessuno studente assegnato a questo percorso.</p>
                    <div v-if="unassignError" class="error-message small mt-2">Errore disassegnazione: {{ unassignError }}</div>
                  </div>
                  <div v-else>Stato imprevisto.</div>
                </div>
              </td>
            </tr>
          </tbody> <!-- Fine tbody -->
        </template> <!-- Fine template v-for -->
      </table>
    </div>
    <div v-else class="no-pathways">
      Nessun percorso assegnato trovato.
    </div>

    <!-- Rimosso div separato -->
    <!-- Rimosso div extra -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importa API per fetchare le istanze Pathway concrete e le assegnazioni
import {
  fetchPathways, deletePathwayApi, type Pathway,
  fetchPathwayAssignments, type PathwayAssignmentDetail, type PathwayAssignmentsResponse, unassignPathwayFromStudent // Importa anche PathwayAssignmentsResponse
} from '@/api/pathways'; // Assicurati che Pathway includa source_template

const assignedPathways = ref<Pathway[]>([]); // Usa il tipo Pathway
const isLoading = ref(false);
const router = useRouter();
const error = ref<string | null>(null); // Errore caricamento percorsi
const unassignError = ref<string | null>(null); // Errore disassegnazione

// Stato per visualizzare le assegnazioni di un percorso specifico
const selectedPathwayId = ref<number | null>(null);
const selectedPathwayAssignments = ref<PathwayAssignmentsResponse | null>(null); // Aggiornato tipo
const isLoadingAssignments = ref(false);
const assignmentsError = ref<string | null>(null);
const isUnassigning = ref<number | null>(null); // ID dell'assegnazione in corso di disassegnazione

onMounted(async () => {
  isLoading.value = true;
  error.value = null;
  try {
    // Usiamo fetchPathways che dovrebbe restituire le istanze create dal docente
    const fetchedPathways = await fetchPathways();
    console.log('[AssignedPathwaysView] Pathways received from API:', JSON.stringify(fetchedPathways)); // Log data received
    assignedPathways.value = fetchedPathways;
    // TODO: Verificare se PathwaySerializer nel backend include 'source_template'
  } catch (err: any) {
    console.error("Errore nel recupero dei percorsi assegnati:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
  } finally {
    isLoading.value = false;
  }
});

// Funzione per mostrare/nascondere e caricare le assegnazioni di un percorso
const toggleAssignments = async (pathwayId: number) => {
  if (selectedPathwayId.value === pathwayId) {
    selectedPathwayId.value = null;
    selectedPathwayAssignments.value = null;
    assignmentsError.value = null;
    unassignError.value = null;
  } else {
    selectedPathwayId.value = pathwayId;
    selectedPathwayAssignments.value = null;
    isLoadingAssignments.value = true;
    assignmentsError.value = null;
    unassignError.value = null;
    console.log(`Recupero assegnazioni per percorso ${pathwayId}...`);
    try {
      const responseData = await fetchPathwayAssignments(pathwayId);
      selectedPathwayAssignments.value = responseData; // Assegna l'intera risposta
      console.log('Assegnazioni recuperate:', selectedPathwayAssignments.value);
    } catch (err: any) {
      console.error(`Errore nel recupero delle assegnazioni per percorso ${pathwayId}:`, err);
      assignmentsError.value = err.message || 'Errore sconosciuto nel recupero delle assegnazioni.';
    } finally {
      isLoadingAssignments.value = false;
    }
  }
};

// Funzione per gestire la disassegnazione di un percorso da uno studente
const handleUnassignPathway = async (assignmentId: number, pathwayId: number) => {
  unassignError.value = null;
  isUnassigning.value = assignmentId;
  const confirmationMessage = `Sei sicuro di voler disassegnare questo percorso (ID Assegnazione: ${assignmentId})?`;

  if (!confirm(confirmationMessage)) {
    isUnassigning.value = null;
    return;
  }

  try {
    await unassignPathwayFromStudent(assignmentId);
    alert(`Percorso disassegnato con successo.`);
    // Rimuovi l'assegnazione dalla lista locale
    if (selectedPathwayId.value === pathwayId && selectedPathwayAssignments.value) {
      selectedPathwayAssignments.value.assignments = selectedPathwayAssignments.value.assignments.filter(a => a.id !== assignmentId); // Aggiorna l'array interno

      // Aggiorna il conteggio nel riepilogo delle statistiche
      selectedPathwayAssignments.value.stats.assigned_count -= 1;

      // Se la lista delle assegnazioni per questo percorso è ora vuota,
      // rimuovi il percorso dalla lista principale 'assignedPathways'.
      if (selectedPathwayAssignments.value.assignments.length === 0) {
        assignedPathways.value = assignedPathways.value.filter(p => p.id !== pathwayId);
        // Nascondi anche la sezione delle assegnazioni
        selectedPathwayId.value = null;
      }
    }
  } catch (err: any) {
    console.error(`Errore durante la disassegnazione del percorso (Assignment ID: ${assignmentId}):`, err);
    unassignError.value = err.response?.data?.detail || err.message || `Errore sconosciuto durante la disassegnazione.`;
  } finally {
    isUnassigning.value = null;
  }
};

// Funzione eliminazione (commentata)
/*
const deleteAssignedPathway = async (id: number) => {
  if (!confirm(`Sei sicuro di voler eliminare l'istanza percorso con ID ${id}?`)) {
    return;
  }
  try {
    await deletePathwayApi(id);
    assignedPathways.value = assignedPathways.value.filter(p => p.id !== id);
    console.log(`Istanza percorso ${id} eliminata.`);
  } catch (err: any) {
    console.error(`Errore eliminazione istanza percorso ${id}:`, err);
    error.value = `Errore eliminazione istanza percorso: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
  }
};
*/
</script>

<style scoped>
/* Stili simili a PathwayTemplatesView e AssignedQuizzesView */
.assigned-pathways-view {
  padding: 20px;
}
.loading, .error-message, .no-pathways, .no-assignments {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}
.error-message {
  color: red;
  font-weight: bold;
}
.pathways-list {
  margin-top: 20px;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
  vertical-align: top; /* Allinea in alto per la riga espansa */
}
th {
  background-color: #f2f2f2;
}
.assignment-list {
  list-style: disc;
  margin-left: 20px;
  margin-top: 5px;
}
.assignment-list li {
  margin-bottom: 5px;
  display: flex; /* Per allineare bottone */
  justify-content: space-between; /* Spazio tra testo e bottone */
  align-items: center;
}
.no-assignments {
    font-style: italic;
    color: #888;
    margin-top: 5px;
}
.loading.small, .error-message.small {
    font-size: 0.9em;
    margin-top: 5px;
    padding: 10px; /* Aggiunge padding dentro la cella */
}
.btn-xs, .ml-2 { /* Copiato da AssignedQuizzesView */
    padding: 2px 6px; font-size: 0.8rem; line-height: 1.2; border-radius: 0.2rem; margin-left: 0.5rem;
}
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; } /* Aggiunto per coerenza */
.mb-1 { margin-bottom: 0.25rem; }
.mb-3 { margin-bottom: 0.75rem; } /* Aggiunto per coerenza */
.stats-section { border-bottom: 1px solid #e2e8f0; } /* gray-300 */
</style>