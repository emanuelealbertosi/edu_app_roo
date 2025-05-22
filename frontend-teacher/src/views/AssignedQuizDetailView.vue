<template>
  <div class="assigned-quiz-detail-view p-4 md:p-6">
    <div class="mb-6">
      <BaseButton @click="goBack" variant="secondary-outline">&larr; Torna ai Quiz Assegnati</BaseButton>
    </div>

    <!-- Titolo e Sottotitolo Aggiornati -->
    <div class="bg-primary text-white p-4 rounded-md mb-6">
      <h2 class="text-3xl font-bold mb-1">Dettaglio Quiz Assegnato</h2>
      <p class="text-xl opacity-90">
        Visualizza i dettagli e le statistiche del quiz: {{ quizDetails?.title || quizId }}
      </p>
    </div>
    
    <div v-if="isLoading && !quizDetails" class="text-center py-10 text-neutral-dark">Caricamento dettagli quiz...</div>
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>
    
    <div v-else-if="quizDetails">
      <p class="mb-4">Dettagli per il quiz assegnato con ID: <strong>{{ quizId }}</strong></p>
      <!-- 
        Sezioni da implementare come da piano:
        - Sezione 1: Riepilogo Quiz (Titolo, Descrizione, Template Sorgente, N. Domande, Tipologie)
        - Sezione 2: Statistiche di Completamento (Grafici, % completamento, punteggio medio)
        - Sezione 3: Studenti Assegnatari e Stati (Tabella, filtri, link a correzione/visualizzazione tentativi)
      -->
      <BaseCard :title="quizDetails.title || 'Riepilogo Quiz'">
        <div v-if="quizDetails" class="space-y-3">
          <div>
            <span class="font-semibold text-neutral-dark">Descrizione:</span>
            <p class="ml-2 text-neutral-darkest whitespace-pre-wrap">{{ quizDetails.description || 'Nessuna descrizione.' }}</p>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
            <div>
              <span class="font-semibold text-neutral-dark">ID Quiz:</span>
              <span class="ml-2 text-neutral-darkest">{{ quizDetails.id }}</span>
            </div>
            <div>
              <span class="font-semibold text-neutral-dark">Creato il:</span>
              <span class="ml-2 text-neutral-darkest">{{ new Date(quizDetails.created_at).toLocaleString() }}</span>
            </div>
            <div>
              <span class="font-semibold text-neutral-dark">Numero Domande:</span>
              <span class="ml-2 text-neutral-darkest">{{ quizDetails.question_count }}</span>
            </div>
            <div v-if="quizDetails.source_template_id">
              <span class="font-semibold text-neutral-dark">Template Sorgente ID:</span>
              <span class="ml-2 text-neutral-darkest">{{ quizDetails.source_template_id }}</span>
            </div>
            <div v-if="quizDetails.subject_name">
              <span class="font-semibold text-neutral-dark">Materia:</span>
              <span class="ml-2 text-neutral-darkest">{{ quizDetails.subject_name }}</span>
            </div>
            <div v-if="quizDetails.topic_name">
              <span class="font-semibold text-neutral-dark">Argomento:</span>
              <span class="ml-2 text-neutral-darkest">{{ quizDetails.topic_name }}</span>
            </div>
          </div>
          <div v-if="quizDetails.image_url" class="mt-3">
            <span class="font-semibold text-neutral-dark block mb-1">Immagine di Copertina:</span>
            <img :src="quizDetails.image_url" alt="Immagine quiz" class="max-w-xs rounded-md shadow-sm">
          </div>
        </div>
      </BaseCard>

      <BaseCard title="Statistiche di Completamento" class="mt-6">
        <div v-if="isLoadingCompletionStats" class="text-center py-4">Caricamento statistiche...</div>
        <div v-else-if="completionStatsError" class="text-error">{{ completionStatsError }}</div>
        <div v-else-if="quizCompletionStats">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 text-center md:text-left">
            <div>
              <span class="block text-xs font-medium text-neutral-darker">Assegnato a</span>
              <span class="block text-xl font-bold text-neutral-darkest">{{ quizCompletionStats.total_assigned }} Stud.</span>
            </div>
            <div>
              <span class="block text-xs font-medium text-neutral-darker">Hanno Iniziato</span>
              <span class="block text-xl font-bold text-neutral-darkest">{{ quizCompletionStats.total_started }} Stud.</span>
            </div>
            <div>
              <span class="block text-xs font-medium text-neutral-darker">Completato Correttamente</span>
              <span class="block text-xl font-bold text-success-dark">{{ quizCompletionStats.total_completed }} Stud. ({{ quizCompletionStats.completion_rate_percentage?.toFixed(1) ?? '0.0' }}%)</span>
            </div>
            <div>
              <span class="block text-xs font-medium text-neutral-darker">Punteggio Medio (Completati)</span>
              <span class="block text-xl font-bold text-neutral-darkest">{{ quizCompletionStats.average_score_completed?.toFixed(1) ?? 'N/D' }}</span>
            </div>
          </div>
          <div>
            <h4 class="text-md font-semibold text-neutral-dark mb-2">Distribuzione Punteggi:</h4>
            <apexchart
              v-if="scoreDistributionChartOptions.series[0].data.length > 0"
              type="bar"
              height="300"
              :options="scoreDistributionChartOptions"
              :series="scoreDistributionChartOptions.series"
            ></apexchart>
            <p v-else class="text-neutral-dark">Nessun dato disponibile per la distribuzione dei punteggi.</p>
          </div>
        </div>
        <div v-else>
          <p class="text-neutral-dark">Nessuna statistica di completamento disponibile.</p>
        </div>
      </BaseCard>

      <BaseCard title="Studenti Assegnatari" class="mt-6">
        <div class="mb-4">
          <label for="statusFilter" class="block text-sm font-medium text-neutral-darker mb-1">Filtra per stato:</label>
          <select id="statusFilter" v-model="selectedStatusFilter" class="block w-full md:w-1/3 rounded-md border-neutral-light shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2">
            <option value="">Tutti gli stati</option>
            <option v-for="status in assigneeStatusOptions" :key="status.value" :value="status.value">
              {{ status.text }}
            </option>
          </select>
        </div>

        <div v-if="isLoadingAssignees" class="text-center py-4">Caricamento studenti assegnati...</div>
        <div v-else-if="assigneesError" class="text-error">{{ assigneesError }}</div>
        <div v-else-if="filteredAssignees && filteredAssignees.length > 0">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-neutral-DEFAULT">
              <thead class="bg-neutral-lightest">
                <tr>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Studente</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Stato</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Punteggio</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Ultima Attività</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-neutral-DEFAULT">
                <tr v-for="assignee in filteredAssignees" :key="getAssigneeKey(assignee)" class="hover:bg-neutral-lightest transition-colors duration-150">
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-neutral-darkest">{{ assignee.student_name || assignee.group_name }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm">
                    <span :class="getAssigneeStatusClass(assignee.status)" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full">
                      {{ getAssigneeStatusText(assignee.status) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-neutral-darker">{{ assignee.score ?? 'N/D' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-neutral-darker">{{ assignee.last_activity_at ? new Date(assignee.last_activity_at).toLocaleString() : 'N/A' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm font-medium">
                    <div class="flex items-center space-x-2">
                      <BaseButton
                        v-if="assignee.status === 'pending_manual_grading' || assignee.status === 'completed' || assignee.status === 'graded'"
                        variant="info"
                        size="sm"
                        @click="viewOrGradeAttempt(assignee)"
                        class="p-1 text-xs"
                        :title="assignee.status === 'pending_manual_grading' ? 'Correggi Tentativo' : 'Visualizza Tentativo'"
                      >
                        <EyeIcon class="h-4 w-4 mr-1 inline-block" />
                        {{ assignee.status === 'pending_manual_grading' ? 'Correggi' : 'Dettagli' }}
                      </BaseButton>
                      
                      <RouterLink
                        v-if="assignee.student_id"
                        :to="{ name: 'student-progress-detail', params: { studentId: assignee.student_id.toString() } }"
                        class="p-1 text-xs inline-flex items-center text-secondary hover:text-secondary-dark bg-secondary-lightest hover:bg-secondary-lighter rounded"
                        title="Visualizza Progressi Studente"
                      >
                        <ChartBarIcon class="h-4 w-4 mr-1" />
                        Progressi
                      </RouterLink>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else>
          <p class="text-neutral-dark">Nessun studente assegnato trovato (o corrispondente ai filtri).</p>
        </div>
      </BaseCard>

    </div>
    <div v-else class="text-center py-10 text-neutral-dark">
      Nessun dettaglio trovato per questo quiz assegnato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import BaseButton from '@/components/common/BaseButton.vue';
import BaseCard from '@/components/common/BaseCard.vue';
import VueApexCharts from 'vue3-apexcharts';
import { EyeIcon, ChartBarIcon } from '@heroicons/vue/24/outline'; // Aggiunto ChartBarIcon
import apiClient from '@/api/config'; // Per chiamate API future
 
const route = useRoute();
const router = useRouter();

// 'id' è il nome del parametro come definito nella rotta '/assigned-quizzes/:id'
const quizId = computed(() => route.params.id as string); 

const isLoading = ref(false);
const error = ref<string | null>(null);
const isLoadingCompletionStats = ref(false);
const completionStatsError = ref<string | null>(null);
const isLoadingAssignees = ref(false);
const assigneesError = ref<string | null>(null);

// Interfaccia per i dettagli del quiz (già presente)
interface AssignedQuizUIDetails {
  id: string | number;
  title: string;
  description: string | null;
  source_template_id: number | null;
  created_at: string; // ISO Date string
  subject_name?: string | null;
  topic_name?: string | null;
  image_url?: string | null;
  question_count: number;
}
const quizDetails = ref<AssignedQuizUIDetails | null>(null);

// Interfacce per le statistiche di completamento del quiz
interface ScoreDistributionPoint {
  score_range: string; // Es. "0-10", "11-20", o punteggi specifici
  count: number;       // Numero di studenti in quel range
}

interface QuizCompletionStatsData {
  quiz_id: string | number;
  total_assigned: number;
  total_started: number;
  total_completed: number; // Studenti che hanno superato la soglia di completamento
  completion_rate_percentage: number;
  average_score_completed: number | null; // Punteggio medio solo per chi ha completato
  score_distribution: ScoreDistributionPoint[];
}
const quizCompletionStats = ref<QuizCompletionStatsData | null>(null);

// Interfacce e dati per Studenti Assegnatari
type AssigneeQuizStatus = 'not_started' | 'in_progress' | 'pending_manual_grading' | 'completed' | 'graded';

interface QuizAssignee {
  id: string; // ID univoco fornito dal backend (es. "student-1-quiz-2" o "group-1-student-1-quiz-2")
  student_id?: number; // Opzionale se è un gruppo
  student_name?: string;
  student_code?: string;
  group_id?: number | null;
  group_name?: string | null;
  status: AssigneeQuizStatus;
  score: number | null;
  attempt_id?: number | null;
  assigned_at: string; // ISO Date string
  last_activity_at?: string | null; // ISO Date string
}
const quizAssignees = ref<QuizAssignee[]>([]);
const selectedStatusFilter = ref<AssigneeQuizStatus | ''>('');

const assigneeStatusOptions = [
  { value: 'not_started', text: 'Non Iniziato' },
  { value: 'in_progress', text: 'In Corso' },
  { value: 'pending_manual_grading', text: 'Da Correggere' },
  { value: 'completed', text: 'Completato (Valutato Auto)' },
  { value: 'graded', text: 'Valutato (Manualmente)' },
];

const filteredAssignees = computed(() => {
  if (!selectedStatusFilter.value) {
    return quizAssignees.value;
  }
  return quizAssignees.value.filter(assignee => assignee.status === selectedStatusFilter.value);
});

// Opzioni per il grafico di distribuzione punteggi
const scoreDistributionChartOptions = computed(() => ({
  chart: {
    type: 'bar',
    height: 300,
    toolbar: { show: false }
  },
  plotOptions: {
    bar: {
      horizontal: false,
      columnWidth: '50%',
      // endingShape: 'rounded' // Se si preferiscono barre arrotondate
    },
  },
  dataLabels: {
    enabled: false
  },
  stroke: {
    show: true,
    width: 2,
    colors: ['transparent']
  },
  xaxis: {
    categories: quizCompletionStats.value?.score_distribution.map(p => p.score_range) || [],
    title: { text: 'Fascia di Punteggio' }
  },
  yaxis: {
    title: {
      text: 'Numero Studenti'
    },
    labels: {
      formatter: function (val: number) { // Assicura che vengano mostrati solo interi
        return val.toFixed(0);
      }
    }
  },
  fill: {
    opacity: 1
  },
  tooltip: {
    y: {
      formatter: function (val: number) {
        return val + " studenti"
      }
    }
  },
  series: [{
    name: 'Numero Studenti',
    data: quizCompletionStats.value?.score_distribution.map(p => p.count) || []
  }],
  noData: {
    text: 'Nessun dato per la distribuzione.',
    align: 'center',
    verticalAlign: 'middle',
  }
}));


const goBack = () => {
  router.push({ name: 'assigned-quizzes' }); // Nome della rotta della lista quiz assegnati
};

const fetchAssignedQuizDetails = async (id: string) => {
  // isLoading.value è già gestito in onMounted
  error.value = null;
  try {
    // Endpoint ipotetico, es: /api/teacher/assigned-quizzes/{quiz_id}/details/
    // o potrebbe essere /api/education/assigned-quizzes/{quiz_id}/ se segue la struttura di quizzes.ts
    const response = await apiClient.get(`/education/quizzes/${id}/details/`);
    quizDetails.value = response.data;
  } catch (err: any) {
    console.error(`Errore nel caricamento dei dettagli del quiz assegnato ${id}:`, err);
    error.value = err.response?.data?.detail || err.message || 'Errore sconosciuto nel caricare i dettagli del quiz.';
    quizDetails.value = null;
  }
  // isLoading.value sarà gestito da onMounted
};

const fetchQuizCompletionStats = async (id: string) => {
  isLoadingCompletionStats.value = true;
  completionStatsError.value = null;
  try {
    // Endpoint ipotetico: /api/teacher/assigned-quizzes/{quiz_id}/stats/
    const response = await apiClient.get(`/education/quizzes/${id}/stats/`);
    quizCompletionStats.value = response.data;
  } catch (err: any) {
    console.error(`Errore nel caricamento delle statistiche di completamento per il quiz ${id}:`, err);
    completionStatsError.value = err.response?.data?.detail || err.message || "Errore caricamento statistiche.";
    quizCompletionStats.value = null;
  } finally {
    isLoadingCompletionStats.value = false;
  }
};

const fetchQuizAssignees = async (id: string) => {
  isLoadingAssignees.value = true;
  assigneesError.value = null;
  try {
    // Endpoint ipotetico: /api/teacher/assigned-quizzes/{quiz_id}/assignees/
    const response = await apiClient.get(`/education/quizzes/${id}/assignees/`);
    // Mappa i dati dell'API all'interfaccia QuizAssignee del frontend
    quizAssignees.value = response.data.map((apiAssignee: any) => {
      const studentInfo = apiAssignee.student_info;
      const groupInfo = apiAssignee.group_info;

      return {
        id: apiAssignee.id, // ID univoco fornito dal backend
        // Mappatura da student_info e group_info
        student_id: studentInfo?.id,
        student_name: studentInfo?.full_name || (studentInfo ? `${studentInfo.first_name || ''} ${studentInfo.last_name || ''}`.trim() : undefined),
        student_code: studentInfo?.student_code,
        group_id: groupInfo?.id, // ID del gruppo originale, se l'assegnazione era a un gruppo
        group_name: groupInfo?.name, // Nome del gruppo originale
        
        // Campi ora forniti dal backend (calcolati nel serializer)
        status: apiAssignee.status || 'not_started',
        score: apiAssignee.score ?? null,
        attempt_id: apiAssignee.attempt_id ?? null,
        last_activity_at: apiAssignee.last_activity_at ?? null,

        // Campi direttamente disponibili dall'API (passati dal backend nel payload)
        assigned_at: apiAssignee.assigned_at,
      };
    });
  } catch (err: any) {
    console.error(`Errore nel caricamento degli studenti assegnatari per il quiz ${id}:`, err);
    assigneesError.value = err.response?.data?.detail || err.message || "Errore caricamento studenti assegnati.";
    quizAssignees.value = []; // Resetta a un array vuoto in caso di errore
  } finally {
    isLoadingAssignees.value = false;
  }
};

const viewOrGradeAttempt = (assignee: QuizAssignee) => {
  if (assignee.attempt_id) {
    console.log(`TODO: Naviga alla correzione/visualizzazione per attempt ID: ${assignee.attempt_id}`);
    // Esempio: router.push({ name: 'GradingAttemptView', params: { attemptId: assignee.attempt_id.toString() } });
    // Assicurarsi che la rotta 'GradingAttemptView' esista e accetti 'attemptId'
    if (assignee.status === 'pending_manual_grading' || assignee.status === 'graded' || assignee.status === 'completed') {
       router.push({ name: 'GradingAttemptView', params: { attemptId: assignee.attempt_id.toString() } });
    } else {
      // Forse una vista diversa per 'in_progress' o 'not_started' se cliccabile
      alert(`Tentativo ID: ${assignee.attempt_id} (Stato: ${assignee.status})`);
    }
  } else {
    alert(`Nessun tentativo registrato per ${assignee.student_name || assignee.group_name}`);
  }
};

// Funzioni helper per lo stato dell'assegnatario
const getAssigneeStatusText = (status: AssigneeQuizStatus): string => {
  const map: Record<AssigneeQuizStatus, string> = {
    not_started: 'Non Iniziato',
    in_progress: 'In Corso',
    pending_manual_grading: 'Da Correggere',
    completed: 'Completato', // Potrebbe significare auto-valutato
    graded: 'Valutato' // Corretto manualmente
  };
  return map[status] || status;
};

const getAssigneeStatusClass = (status: AssigneeQuizStatus): string => {
  const map: Record<AssigneeQuizStatus, string> = {
    not_started: 'bg-neutral-lightest text-neutral-dark',
    in_progress: 'bg-warning/20 text-warning-dark',
    pending_manual_grading: 'bg-info/20 text-info-dark',
    completed: 'bg-success/20 text-success-dark',
    graded: 'bg-purple-500/20 text-purple-700' // Esempio per 'graded'
  };
  return map[status] || 'bg-neutral-light text-neutral-dark';
};

// Funzione per generare una chiave univoca per gli assegnatari nella tabella
const getAssigneeKey = (assignee: QuizAssignee): string => {
  // Utilizza l'ID univoco fornito dal backend
  return assignee.id;
};

onMounted(async () => {
  if (quizId.value) {
    isLoading.value = true;
    error.value = null; // Resetta l'errore generale

    await fetchAssignedQuizDetails(quizId.value);

    if (!error.value && quizDetails.value) {
      // Resetta errori specifici prima delle chiamate parallele
      completionStatsError.value = null;
      assigneesError.value = null;

      await Promise.all([
        fetchQuizCompletionStats(quizId.value),
        fetchQuizAssignees(quizId.value)
      ]);
    }
    isLoading.value = false;
  }
});
</script>

<style scoped>
/* Stili specifici per AssignedQuizDetailView, se necessari */
</style>