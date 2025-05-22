<template>
  <div class="student-progress-detail-view p-4 md:p-6">
    <div class="mb-6">
      <BaseButton @click="goBack" variant="secondary-outline">&larr; Torna ai Progressi</BaseButton>
    </div>

    <!-- Titolo e Sottotitolo Aggiornati -->
    <div class="bg-primary text-white p-4 rounded-md mb-6">
      <h2 class="text-3xl font-bold mb-1">Dettaglio Progressi Studente</h2>
      <p class="text-xl opacity-90">
        Visualizza i progressi e le statistiche dello studente: {{ studentDetails?.full_name || studentId }}
      </p>
    </div>
    
    <div v-if="isLoading && !studentDetails" class="text-center py-10 text-neutral-dark">Caricamento dettagli...</div>
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>
    
    <div v-else-if="studentDetails">
      <p class="mb-4">Dettagli per lo studente con ID: <strong>{{ studentId }}</strong></p>
      <!-- 
        Qui verranno implementate le sezioni usando BaseCard come da piano:
        - Sezione 1: Riepilogo Generale Studente (Nome, codice, statistiche chiave)
        - Sezione 2: Andamento e Statistiche (Grafici)
        - Sezione 3: Dettaglio Quiz Svolti (Tabella, link a risposte)
        - Sezione 5: Storico Ricompense e Punti (Bilancio, Ricompense acquistate, Badge)
      -->
      <BaseCard title="Riepilogo Generale Studente">
        <div v-if="studentDetails" class="space-y-3">
          <div>
            <span class="font-semibold text-neutral-dark">Nome Completo:</span>
            <span class="ml-2 text-neutral-darkest">{{ studentDetails.full_name }}</span>
          </div>
          <div>
            <span class="font-semibold text-neutral-dark">Codice Studente:</span>
            <span class="ml-2 text-neutral-darkest">{{ studentDetails.student_code }}</span>
          </div>
          <div>
            <span class="font-semibold text-neutral-dark">Quiz Completati:</span>
            <span class="ml-2 text-neutral-darkest">{{ studentDetails.completed_quizzes_count ?? 0 }}</span>
          </div>
          <div>
            <span class="font-semibold text-neutral-dark">Punti Totali Guadagnati:</span>
            <span class="ml-2 text-neutral-darkest">{{ studentDetails.total_points_earned ?? 0 }}</span>
          </div>
        </div>
      </BaseCard>

      <!-- Placeholder per le altre sezioni -->
      <BaseCard title="Andamento e Statistiche" class="mt-6">
        <div v-if="studentAnalytics">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <h4 class="text-md font-semibold text-neutral-dark mb-1">Punteggio Medio Generale:</h4>
              <p class="text-2xl font-bold text-neutral-darkest">
                {{ studentAnalytics.overall_stats.average_score !== null ? studentAnalytics.overall_stats.average_score.toFixed(1) : 'N/D' }}
              </p>
            </div>
            <!-- Altre statistiche testuali possono essere aggiunte qui -->
          </div>
          <div>
            <h4 class="text-md font-semibold text-neutral-dark mb-2">Andamento Punteggi Quiz:</h4>
            <apexchart
              v-if="chartOptions.series[0].data.length > 0"
              type="line"
              height="350"
              :options="chartOptions"
              :series="chartOptions.series"
            ></apexchart>
            <p v-else class="text-neutral-dark">Nessun dato disponibile per visualizzare l'andamento dei punteggi.</p>
          </div>
        </div>
        <div v-else>
          <p class="text-neutral-dark">Caricamento statistiche...</p>
        </div>
      </BaseCard>

      <BaseCard title="Dettaglio Quiz Svolti" class="mt-6">
        <div v-if="isLoadingQuizAttempts" class="text-center py-4">Caricamento tentativi quiz...</div>
        <div v-else-if="quizAttemptsError" class="text-error">{{ quizAttemptsError }}</div>
        <div v-else-if="studentQuizAttempts && studentQuizAttempts.length > 0">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-neutral-DEFAULT">
              <thead class="bg-neutral-lightest">
                <tr>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Quiz</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Data Svolgimento</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Punteggio</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Stato</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-neutral-DEFAULT">
                <tr v-for="attempt in studentQuizAttempts" :key="attempt.attempt_id" class="hover:bg-neutral-lightest transition-colors duration-150">
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-neutral-darkest">{{ attempt.quiz_title }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-neutral-darker">{{ attempt.completed_at ? new Date(attempt.completed_at).toLocaleDateString() : 'Iniziato' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-neutral-darker">{{ attempt.score ?? 'N/D' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm">
                    <span :class="getStatusClass(attempt.status)" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full">
                      {{ getStatusText(attempt.status) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm font-medium">
                    <BaseButton variant="info" size="sm" @click="viewQuizAttemptDetails(attempt.attempt_id)" class="p-1 text-xs" title="Visualizza Risposte">
                      <EyeIcon class="h-4 w-4 mr-1 inline-block" /> Dettagli
                    </BaseButton>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else>
          <p class="text-neutral-dark">Nessun tentativo di quiz trovato per questo studente.</p>
        </div>
      </BaseCard>


      <BaseCard title="Storico Ricompense e Punti" class="mt-6">
        <div v-if="isLoadingWallet || isLoadingRewardPurchases" class="text-center py-4">Caricamento dati ricompense...</div>
        <div v-else-if="walletError || rewardPurchasesError" class="text-error">
          <p v-if="walletError">Errore caricamento portafoglio: {{ walletError }}</p>
          <p v-if="rewardPurchasesError">Errore caricamento ricompense acquistate: {{ rewardPurchasesError }}</p>
        </div>
        <div v-else class="space-y-6">
          <!-- Sotto-sezione: Bilancio Punti -->
          <div>
            <h4 class="text-md font-semibold text-neutral-dark mb-2">Bilancio Punti</h4>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <span class="block text-xs font-medium text-neutral-darker">Punti Guadagnati</span>
                <span class="block text-xl font-bold text-neutral-darkest">{{ studentDetails?.total_points_earned ?? 'N/D' }}</span>
              </div>
              <div>
                <span class="block text-xs font-medium text-neutral-darker">Punti Spesi</span>
                <span class="block text-xl font-bold text-neutral-darkest">{{ totalPointsSpent ?? 'N/D' }}</span>
              </div>
              <div>
                <span class="block text-xs font-medium text-neutral-darker">Saldo Attuale</span>
                <span class="block text-xl font-bold text-success-dark">{{ studentWallet?.current_points ?? 'N/D' }}</span>
              </div>
            </div>
          </div>

          <!-- Sotto-sezione: Ricompense Acquistate -->
          <div>
            <h4 class="text-md font-semibold text-neutral-dark mb-2">Ricompense Acquistate</h4>
            <div v-if="studentRewardPurchases && studentRewardPurchases.length > 0" class="overflow-x-auto">
              <table class="min-w-full divide-y divide-neutral-DEFAULT">
                <thead class="bg-neutral-lightest">
                  <tr>
                    <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Ricompensa</th>
                    <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Punti Spesi</th>
                    <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Data Acquisto</th>
                    <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Stato Consegna</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-neutral-DEFAULT">
                  <tr v-for="purchase in studentRewardPurchases" :key="purchase.purchase_id" class="hover:bg-neutral-lightest transition-colors duration-150">
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-neutral-darkest">{{ purchase.reward_name }}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-neutral-darker">{{ purchase.points_spent }}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-neutral-darker">{{ new Date(purchase.purchased_at).toLocaleDateString() }}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm">
                      <span :class="getRewardStatusClass(purchase.status)" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full">
                        {{ getRewardStatusText(purchase.status) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else>
              <p class="text-neutral-dark">Nessuna ricompensa acquistata da questo studente.</p>
            </div>
          </div>
          <!-- TODO: Sotto-sezione: Badge Ottenuti (se applicabile) -->
        </div>
      </BaseCard>

      </div>
    <div v-else class="text-center py-10 text-neutral-dark">
      Nessun dettaglio trovato per questo studente.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import BaseButton from '@/components/common/BaseButton.vue';
import BaseCard from '@/components/common/BaseCard.vue';
import VueApexCharts from 'vue3-apexcharts';
import { EyeIcon } from '@heroicons/vue/24/outline'; // Importa EyeIcon
import apiClient from '@/api/config'; // Da usare per le chiamate API

// Interfaccia per i dettagli base dello studente (già presente)
interface StudentProgressDetail {
  id: string;
  full_name: string;
  student_code: string;
  completed_quizzes_count: number | null;
  total_points_earned: number | null;
  // TODO: Aggiungere altri campi rilevanti se necessario (es. email, data_iscrizione)
}

// Interfacce per i dati analitici
interface ScoreTrendPoint {
  date: string; // Formato 'YYYY-MM-DD' o timestamp ISO
  score: number;
  quiz_title?: string;
}

interface OverallStats {
  average_score: number | null;
  // TODO: Aggiungere altre statistiche se definite nell'API (es. total_quizzes_attempted)
}

interface StudentAnalyticsData {
  score_trend: ScoreTrendPoint[];
  overall_stats: OverallStats;
}

const route = useRoute();
const router = useRouter();

const studentId = computed(() => route.params.studentId as string);

const isLoading = ref(true);
const isLoadingAnalytics = ref(false);
const isLoadingQuizAttempts = ref(false);
const isLoadingWallet = ref(false); // Nuovo stato di caricamento
const isLoadingRewardPurchases = ref(false); // Nuovo stato di caricamento
const error = ref<string | null>(null);
const quizAttemptsError = ref<string | null>(null);
const walletError = ref<string | null>(null); // Nuovo stato di errore
const rewardPurchasesError = ref<string | null>(null); // Nuovo stato di errore
const studentDetails = ref<StudentProgressDetail | null>(null);
const studentAnalytics = ref<StudentAnalyticsData | null>(null);

// Interfaccia per i tentativi di quiz dello studente (già presente)
type QuizAttemptStatus = 'in_progress' | 'pending_manual_grading' | 'completed';

interface StudentQuizAttempt {
  attempt_id: number;
  quiz_id: number;
  quiz_title: string;
  started_at: string;
  completed_at: string | null;
  score: number | null;
  status: QuizAttemptStatus;
  // duration_minutes?: number; // Opzionale
}
const studentQuizAttempts = ref<StudentQuizAttempt[] | null>(null);


// Interfacce per Wallet e Ricompense Acquistate
interface StudentWallet {
  current_points: number;
  // Altri campi se necessari, es. total_points_spent_ever
}
const studentWallet = ref<StudentWallet | null>(null);

type RewardPurchaseStatus = 'purchased' | 'delivered' | 'cancelled';
interface RewardPurchaseItem {
  purchase_id: number;
  reward_name: string;
  points_spent: number;
  purchased_at: string; // ISO Date string
  status: RewardPurchaseStatus;
}
const studentRewardPurchases = ref<RewardPurchaseItem[] | null>(null);

const totalPointsSpent = computed(() => {
  if (!studentRewardPurchases.value) return 0;
  return studentRewardPurchases.value.reduce((sum, purchase) => sum + purchase.points_spent, 0);
});


// Opzioni di base per ApexCharts
const chartOptions = computed(() => {
  const options = {
    chart: {
      height: 350,
      type: 'line',
      zoom: {
        enabled: true
      },
      toolbar: {
        show: true
      }
    },
    stroke: {
      curve: 'smooth',
      width: 3
    },
    markers: {
      size: 5
    },
    xaxis: {
      type: 'datetime',
      categories: studentAnalytics.value?.score_trend.map(item => new Date(item.date).getTime()) || [],
      title: {
        text: 'Data Svolgimento'
      },
      labels: {
        datetimeUTC: false, // Mostra date nel fuso orario locale
      }
    },
    yaxis: {
      title: {
        text: 'Punteggio'
      },
      min: 0,
      max: 100 // O basato sul punteggio massimo possibile
    },
    tooltip: {
      x: {
        format: 'dd MMM yyyy'
      },
      y: {
        formatter: (val: number, { series, seriesIndex, dataPointIndex, w }: any) => {
          const point = studentAnalytics.value?.score_trend[dataPointIndex];
          let tooltipText = `${val}`;
          if (point?.quiz_title) {
            tooltipText += ` (Quiz: ${point.quiz_title})`;
          }
          return tooltipText;
        }
      }
    },
    series: [
      {
        name: 'Punteggio Ottenuto',
        data: studentAnalytics.value?.score_trend.map(item => item.score) || []
      }
    ],
    noData: {
      text: 'Nessun dato sui punteggi disponibile.',
      align: 'center',
      verticalAlign: 'middle',
      offsetX: 0,
      offsetY: 0,
      style: {
        fontSize: '16px',
      }
    }
  };
  return options;
});


const goBack = () => {
  router.push({ name: 'student-progress' });
};

const fetchStudentDetails = async (id: string) => {
  isLoading.value = true; // isLoading principale per i dettagli base
  error.value = null;
  
  try {
    // Endpoint ipotetico, da verificare con la definizione reale dell'API
    // Assumiamo che l'endpoint per i dettagli dello studente sia qualcosa come /api/teacher/students/{studentId}/
    const response = await apiClient.get(`/students/${id}/`);
    studentDetails.value = response.data;
  } catch (err: any) {
    console.error(`Errore nel caricamento dei dettagli dello studente ${id}:`, err);
    error.value = err.response?.data?.detail || err.message || 'Errore sconosciuto nel caricare i dettagli studente.';
    studentDetails.value = null;
  } finally {
    // isLoading.value sarà gestito da onMounted
  }
};

const fetchStudentAnalytics = async (id: string) => {
  isLoadingAnalytics.value = true;
  // error.value per analytics non è definito separatamente, usiamo quello generale o aggiungiamo se necessario
  try {
    // Endpoint ipotetico: /api/teacher/students/{studentId}/analytics/
    const response = await apiClient.get(`/students/${id}/analytics/`);
    studentAnalytics.value = response.data;
  } catch (err: any) {
    console.error(`Errore nel caricamento dei dati analytics per lo studente ${id}:`, err);
    // Potremmo voler impostare un errore specifico per analytics o usare error.value
    // Per ora, resettiamo i dati analytics in caso di errore.
    studentAnalytics.value = null;
  } finally {
    isLoadingAnalytics.value = false;
  }
};

const fetchQuizAttempts = async (id: string) => {
  isLoadingQuizAttempts.value = true;
  quizAttemptsError.value = null;
  try {
    // Endpoint ipotetico: /api/teacher/students/{studentId}/quiz-attempts/
    const response = await apiClient.get(`/students/${id}/quiz-attempts/`);
    studentQuizAttempts.value = response.data;
  } catch (err: any) {
    console.error("Errore nel caricamento dei tentativi quiz:", err);
    quizAttemptsError.value = err.response?.data?.detail || err.message || 'Errore sconosciuto nel caricare i tentativi quiz.';
    studentQuizAttempts.value = null;
  } finally {
    isLoadingQuizAttempts.value = false;
  }
};


const fetchStudentWallet = async (id: string) => {
  isLoadingWallet.value = true;
  walletError.value = null;
  try {
    // Endpoint ipotetico: /api/teacher/students/{studentId}/wallet/
    const response = await apiClient.get(`/students/${id}/wallet/`);
    studentWallet.value = response.data;
  } catch (err: any) {
    console.error("Errore nel caricamento del wallet:", err);
    walletError.value = err.response?.data?.detail || err.message || 'Errore sconosciuto nel caricare il wallet.';
    studentWallet.value = null;
  } finally {
    isLoadingWallet.value = false;
  }
};

const fetchStudentRewardPurchases = async (id: string) => {
  isLoadingRewardPurchases.value = true;
  rewardPurchasesError.value = null;
  try {
    // Endpoint ipotetico: /api/teacher/students/{studentId}/reward-purchases/
    const response = await apiClient.get(`/students/${id}/reward-purchases/`);
    studentRewardPurchases.value = response.data;
  } catch (err: any) {
    console.error("Errore nel caricamento delle ricompense acquistate:", err);
    rewardPurchasesError.value = err.response?.data?.detail || err.message || 'Errore sconosciuto nel caricare le ricompense acquistate.';
    studentRewardPurchases.value = null;
  } finally {
    isLoadingRewardPurchases.value = false;
  }
};

const viewQuizAttemptDetails = (attemptId: number) => {
  console.log(`TODO: Visualizza dettagli/risposte per il tentativo quiz ID: ${attemptId}`);
  // Qui si potrebbe navigare a una vista di dettaglio del tentativo o aprire una modale
};


// Funzioni helper per lo stato del quiz
const getStatusText = (status: QuizAttemptStatus): string => {
  const map: Record<QuizAttemptStatus, string> = {
    completed: 'Completato',
    in_progress: 'In Corso',
    pending_manual_grading: 'Da Correggere'
  };
  return map[status] || status;
};

const getStatusClass = (status: QuizAttemptStatus): string => {
  const map: Record<QuizAttemptStatus, string> = {
    completed: 'bg-success/20 text-success-dark',
    in_progress: 'bg-warning/20 text-warning-dark',
    pending_manual_grading: 'bg-info/20 text-info-dark'
  };
  return map[status] || 'bg-neutral-light text-neutral-dark';
};


// Funzioni helper per lo stato delle ricompense
const getRewardStatusText = (status: RewardPurchaseStatus): string => {
  const map: Record<RewardPurchaseStatus, string> = {
    purchased: 'Acquistata',
    delivered: 'Consegnata',
    cancelled: 'Annullata'
  };
  return map[status] || status;
};

const getRewardStatusClass = (status: RewardPurchaseStatus): string => {
  const map: Record<RewardPurchaseStatus, string> = {
    purchased: 'bg-info/20 text-info-dark',
    delivered: 'bg-success/20 text-success-dark',
    cancelled: 'bg-error/20 text-error-dark' // Assicurati che error-dark sia definito o usa text-error
  };
  return map[status] || 'bg-neutral-light text-neutral-dark';
};

onMounted(async () => {
  if (studentId.value) {
    isLoading.value = true; // Imposta isLoading generale all'inizio
    error.value = null;    // Resetta l'errore generale
    // Resetta anche gli altri stati di errore e dati
    studentDetails.value = null;
    studentAnalytics.value = null;
    studentQuizAttempts.value = null;
    studentWallet.value = null;
    studentRewardPurchases.value = null;
    quizAttemptsError.value = null;
    walletError.value = null;
    rewardPurchasesError.value = null;

    try {
      await fetchStudentDetails(studentId.value); // Carica prima i dettagli base

      if (!error.value && studentDetails.value) { // Procedi solo se i dettagli base sono stati caricati con successo
        // Ora carica gli altri dati in parallelo
        // isLoadingAnalytics, isLoadingQuizAttempts, etc. sono gestiti nelle rispettive funzioni
        
        await Promise.all([
          fetchStudentAnalytics(studentId.value),
          fetchQuizAttempts(studentId.value),
          fetchStudentWallet(studentId.value),
          fetchStudentRewardPurchases(studentId.value)
        ]);
      } else if (!error.value && !studentDetails.value) {
        // Se non c'è stato un errore di fetch ma studentDetails è ancora null,
        // potrebbe significare che l'API ha restituito 200 OK ma con corpo vuoto o non conforme.
        error.value = "Dettagli studente non trovati o formato risposta non valido dall'API.";
      }
    } catch (e) {
      // Questo catch è per errori imprevisti non gestiti all'interno delle funzioni di fetch,
      // anche se dovrebbero già gestire i propri errori.
      console.error("Errore imprevisto in onMounted:", e);
      if (!error.value) { // Se nessun errore specifico è stato impostato dalle fetch
        error.value = "Si è verificato un errore imprevisto durante il caricamento dei dati.";
      }
    } finally {
      isLoading.value = false; // Assicura che lo stato di caricamento principale sia disattivato
    }
  } else {
    error.value = "ID studente non fornito.";
    isLoading.value = false;
  }
});
</script>

<style scoped>
/* Stili specifici per StudentProgressDetailView, se necessari */
</style>